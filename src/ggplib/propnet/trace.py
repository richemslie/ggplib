from ggplib.propnet.constants import OR, AND, NOT, PROPOSITION, TRANSITION

FALSE = "false"
TRUE = "true"
EITHER = "either"
BASE = "base"


class SeenInput(Exception):
    pass


class Node:
    def __init__(self, c, v, id):
        self.component = c
        self.values = v
        self.id = id
        self.simplified = False

    @property
    def ct(self):
        return self.component.component_type

    def simplify(self):
        if self.simplified:
            return

        for v in self.values:
            if isinstance(v, Node):
                v.simplify()

        while True:
            did_something = False

            values = []
            for v in self.values:
                if isinstance(v, Node):

                    # compact or/ands with only one value
                    if v.ct in (OR, AND) and len(v.values) == 1:
                        v = v.values[0]
                        did_something = True

                    # remove NOT/NOT
                    if isinstance(v, Node) and v.ct == NOT:
                        assert len(v.values) == 1
                        e = v.values[0]
                        if isinstance(e, Node) and e.ct == NOT:
                            assert len(e.values) == 1
                            v = e.values[0]
                            did_something = True

                values.append(v)

            # remove dupes in AND, OR
            if self.ct in (OR, AND):
                unique_values = set()

                for v in values:
                    if v in unique_values:
                        did_something = True
                        continue
                    unique_values.add(v)

                values = list(unique_values)

            # condense layers of and/ors
            new_values = []
            if self.ct in (OR, AND):

                for v in values:
                    if isinstance(v, Node) and v.ct == self.ct:
                        new_values += v.values
                        did_something = True
                    else:
                        new_values.append(v)
            else:
                new_values = values

            self.values = new_values
            if not did_something:
                break

        self.simplified = True

    def tuple(self):
        if not self.simplified:
            self.simplify()

        res = []
        for ii in self.values:
            if isinstance(ii, Node):
                res.append(ii.tuple())
            else:
                res.append(ii)

        return (str(self),) + tuple(res)

    def __repr__(self):
        return "%s.%d(%s)" % (self.component.typename, self.id, len(self.values))


class DependencyComponent:
    def __init__(self, *inputs):
        ''' idea is to back-prop and see make a guess what the value is based on '''
        self.input_set = set()
        for i in inputs:
            self.input_set.add(i)

        self.bases = set()
        self.mapping = {}
        self.cached_nodes = {}
        self.next_count = 0

        # just used for debugging (and timing constraints)
        self.flow_count = 0

        self.raise_on_seeing_input = False

    def reset(self):
        self.flow_count = 0

    def inputs_seen(self):
        res = []
        for c in self.mapping:
            if c.component_type == PROPOSITION:
                if c.meta.is_input:
                    res.append(c)
                else:
                    assert c.meta.is_base
        return res

    def create_flow_control(self, c):
        if c in self.cached_nodes:
            return self.cached_nodes[c]

        self.flow_count += 1

        l = []
        for i in c.inputs:
            if i in self.bases:
                l.append(str(i.meta.gdl[1]))
            else:
                v = self.mapping[i]
                assert v is not EITHER
                if v in (FALSE, TRUE):

                    # optimization, XXX but not sure we should do this here
                    if c.component_type == OR:
                        assert v != TRUE
                        continue
                    if c.component_type == AND:
                        assert v != FALSE
                        continue

                    l.append(v)
                else:
                    l.append(self.create_flow_control(i))

        # XXX another optimization, should not do this here?
        if c.component_type in (AND, OR) and len(l) == 1:
            return l[0]

        node = Node(c, l, self.next_count)
        self.next_count += 1
        self.cached_nodes[c] = node
        return node

    def passthrough(self, c):
        assert c.component_type == TRANSITION
        # must be cached nodes.
        r = self.cached_nodes[c]
        t = r.tuple()
        if len(t) == 1:
            return False
        assert len(t) == 2, "len %s c=%s" % (t, c)
        return t[1] == str(c.fish_gdl()[1])

    def get_component_value2(self, c):
        if c.component_type == OR:
            assert len(c.inputs) >= 1
            res = FALSE
            for i in c.inputs:
                value = self.get_component_value(i)
                if value == TRUE:
                    return TRUE
                elif value == FALSE:
                    continue
                elif value == BASE:
                    res = BASE
                else:
                    assert value == EITHER
                    if res is None:
                        res = EITHER
            return res

        elif c.component_type == AND:
            assert len(c.inputs) >= 1
            res = None
            for i in c.inputs:
                value = self.get_component_value(i)
                if value == FALSE:
                    return FALSE
                elif value == TRUE:
                    continue
                elif value == BASE:
                    if res is None:
                        res = BASE
                else:
                    assert value == EITHER
                    res = EITHER
            return res

        elif c.component_type == NOT:
            assert len(c.inputs) == 1
            value = self.get_component_value(c.inputs[0])
            if value == FALSE:
                return TRUE
            elif value == TRUE:
                return FALSE
            else:
                return value

        elif c.component_type == TRANSITION:
            # ZXZZZZXXXXXX
            if not c.inputs:
                # there is no inputs, these are imaginary inputs (since they always constant)
                return "xtrue" if c.count else "xfalse"
            assert len(c.inputs) == 1
            return self.get_component_value(c.inputs[0])

        elif c.component_type == PROPOSITION:
            if c.meta.is_base or c.meta.is_input:
                assert len(c.inputs) == 0
                if c.meta.is_base:
                    self.bases.add(c)
                    return BASE
                elif c.meta.is_input:
                    if self.raise_on_seeing_input:
                        raise SeenInput()
                    if c in self.input_set:
                        return TRUE
                    else:
                        return FALSE
            else:
                assert c.meta.is_goal or c.meta.is_terminal or c.meta.is_legal

                if c.meta.is_legal:
                    assert len(c.outputs) == 0

                # special case for weird legals...
                if len(c.inputs) == 0 and c.meta.is_legal:
                    return "none"  # XXX

                assert len(c.inputs) == 1, c
                return self.get_component_value(c.inputs[0])

    def get_component_value(self, c):
        if c in self.mapping:
            # print("Already in mapping", c)
            return self.mapping[c]

        value = self.get_component_value2(c)
        self.mapping[c] = value
        return value

###############################################################################


def get_controls(propnet, verbose=False):
    controls = {}
    # one time pass looking for controls
    all_transitions = set(propnet.transitions)
    dc = DependencyComponent()
    dc.raise_on_seeing_input = True
    for t in all_transitions:
        try:
            dc.get_component_value(t)
            assert len(dc.inputs_seen()) == 0
            if verbose:
                print('Adding control', t)
            controls[t.cid] = t

        except SeenInput:
            pass
    return controls
