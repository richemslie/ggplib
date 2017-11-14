'''
TODO
* add tests
* maybe come up with a diagram as to what it actually does
* clean up - is an absolute mess
* remame roleinfo.role' should be 'roleinfo.name'
'''

from ggplib.propnet.constants import AND, OR, NOT, PROPOSITION, TRANSITION, CONSTANT, UNKNOWN, MAX_FAN_OUT_SIZE
from ggplib import symbols
from ggplib.util import log

DEBUG = False

###############################################################################
# basic type hierarchy (inheritance here doesn't actually do very much)
###############################################################################


class ComponentBase(object):
    component_type = UNKNOWN
    increment_multiplier = 1
    topological_order = 0

    def __init__(self, cid, count, inputs, outputs):
        self.cid = cid
        self.inputs = inputs
        self.outputs = outputs

        self.count = count
        self.required_count_true = 1
        self.required_count_false = 0

    @property
    def typename(self):
        d = {AND : "And",
             OR : "Or",
             NOT : "Not",
             PROPOSITION : "Proposition",
             TRANSITION : "Transition",
             CONSTANT : "Constant",
             UNKNOWN : "Unknown"}
        return d[self.component_type]

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (self.typename, self.cid, self.count, len(self.inputs), len(self.outputs))


class Proposition(ComponentBase):
    component_type = PROPOSITION

    def __init__(self, cid, count, inputs, outputs, meta):
        ComponentBase.__init__(self, cid, count, inputs, outputs)
        self.meta = meta

    def __repr__(self):
        return "%s(%s, %s, %s, %s, %s)" % (self.typename, self.cid, self.count,
                                           self.meta.gdl, len(self.inputs), len(self.outputs))


class Or(ComponentBase):
    component_type = OR


class And(ComponentBase):
    component_type = AND

    def __init__(self, *args):
        ComponentBase.__init__(self, *args)
        self.required_count_true = len(self.inputs)
        self.required_count_false = self.required_count_true - 1


class Not(ComponentBase):
    component_type = NOT
    increment_multiplier = -1


class Transition(ComponentBase):
    component_type = TRANSITION

    def __init__(self, *args):
        ComponentBase.__init__(self, *args)

    def fish_gdl(self):
        if hasattr(self, "base_proposition"):
            return self.base_proposition.meta.gdl
        else:
            return self.outputs[0].meta.gdl if self.outputs else "none"

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (self.typename, self.cid, self.count, len(self.inputs), self.fish_gdl())


class Constant(ComponentBase):
    component_type = CONSTANT

###############################################################################


class MetaProposition:
    is_base = False
    is_input = False
    is_legal = False
    is_goal = False
    is_init = False
    is_terminal = False

    # as a symbol
    gdl = None

    # as a symbol
    move = None

    # as a string (XXX check)
    role = None

    # mapping for the legal, to an input
    legals_input = None

    # reverse mapping for the input, to an legal (for debugging)
    the_legal = None

    # integer 0-100 value
    goal_value = None

    def __repr__(self):
        s = "MetaProposition "
        for t in "is_base is_input is_legal is_goal is_init is_terminal".split():
            if getattr(self, t):
                s += "%s = %s" % (t, getattr(self, t))
        return s


def create_component(args, symbol_factory):
    if len(args) == 5:
        cid, count, t, inputs, outputs = args
        if t == AND:
            return And(cid, count, inputs, outputs)

        elif t == OR:
            return Or(cid, count, inputs, outputs)

        elif t == NOT:
            assert len(inputs) == 1
            return Not(cid, count, inputs, outputs)

        elif t == TRANSITION:
            assert len(inputs) <= 1
            return Transition(cid, count, inputs, outputs)

        elif t == CONSTANT:
            assert len(inputs) == 0
            return Constant(cid, count, inputs, outputs)

    elif len(args) == 7:
        mp = MetaProposition()
        mp.gdl = symbol_factory.symbolize(args[6])
        cid, count, t, inputs, outputs, prop_t = args[0:6]

        assert len(inputs) <= 1
        # assert t == PROPOSITION

        if prop_t == 'base':
            mp.is_base = True
            assert len(mp.gdl) == 2
            assert mp.gdl[0] == 'true'

        elif prop_t == 'input':
            mp.is_input = True
            assert len(mp.gdl) == 3
            assert mp.gdl[0] == 'does'
            mp.role = str(mp.gdl[1])
            mp.move = str(mp.gdl[2])

        elif prop_t == 'legal':
            mp.is_legal = True
            assert len(mp.gdl) == 3
            assert mp.gdl[0] == 'legal'
            mp.role = str(mp.gdl[1])
            mp.move = str(mp.gdl[2])

        elif prop_t == 'goal':
            mp.is_goal = True
            assert len(mp.gdl) == 3
            assert mp.gdl[0] == 'goal'
            mp.role = str(mp.gdl[1])
            mp.goal_value = int(mp.gdl[2])

        elif prop_t == 'init':
            assert mp.gdl == 'init'
            mp.is_init = True

        elif prop_t == 'terminal':
            assert mp.gdl == 'terminal'
            mp.is_terminal = True

        elif prop_t == 'other':
            pass

        else:
            assert False, "WTF is this proposition: %s" % (args,)

        return Proposition(cid, count, inputs, outputs, mp)

    else:
        assert False, "WTF is this component %s" % (args,)

###############################################################################


class RoleInfo:
    def __init__(self, role, idx):
        # inputs and legals should be 1-1 (unless we remove them)

        self.role = role
        self.role_index = idx
        self.inputs = []
        self.legals = []
        self.goals = []


class Propnet:
    # verify is slow, and always passes unless there is a bug... so disabling for when not testing
    # some new code.
    disable_verify = True

    def __init__(self, roles, component_map):
        self.roles = roles
        self.components = component_map

        # inputs and outputs now links
        for c in self.components.values():
            c.inputs = [component_map[ii] for ii in c.inputs]
            c.outputs = [component_map[oo] for oo in c.outputs]

        self.already_reordered = False

    @property
    def legal_propositions(self):
        # XXX legacy - remove
        legals = {}
        for rinfo in self.role_infos:
            legals[rinfo.role] = rinfo.legals[:]
        return legals

    def init(self):
        log.debug("Building propnet... @Propnet.init()")

        if DEBUG:
            print("* recording")
        self.record()
        if DEBUG:
            self.print_summary()

        if DEBUG:
            print("* unlink transitions")
        self.unlink_transitions()

        if DEBUG:
            print("* remove passthrough propositions")
        self.unlink_passthrough_components(do_list=(PROPOSITION,))
        if DEBUG:
            self.print_summary()

        if DEBUG:
            print("* optmizing")
        self.optimize(once=True)
        if DEBUG:
            self.print_summary()

        if DEBUG:
            print("* ensure legal endpoints")
        self.ensure_legal_endpoints()

        if DEBUG:
            print("* getting initial state")
        self.initial_state = [int(s) for s in self.do_initial_state()]

        if DEBUG:
            print("initial", self.to_gdl(self.initial_state))
            self.print_summary()

        if DEBUG:
            print("* constant propagate stuff not needed anymore")
        cp = ConstantPropagator(self)
        for c in self.components.values():
            if isinstance(c, Constant):
                if DEBUG:
                    print("propagating", c)

                cp.constant_propagate(c, c.count)

        if DEBUG:
            print("* propagating", self.initial_proposition)
        cp.constant_propagate(self.initial_proposition, self.initial_proposition.count)

        # complete remove initial_proposition
        self.components.pop(self.initial_proposition.cid)
        self.initial_proposition = None

        if DEBUG:
            print("* optimizing again")
        self.optimize(once=True)
        if DEBUG:
            self.print_summary()

        if DEBUG:
            print("* weird dangling")
        danglers = self.find_weird_dangling_stuff()
        for d in danglers:
            if DEBUG:
                print("Constant propagating dangler", d)
            cp.constant_propagate(d, d.count == d.required_count_true)

        self.input_propositions, old_input_propositions = [], self.input_propositions
        for ip in old_input_propositions:
            if ip.meta.the_legal is None:
                # print("The following input does not have a corresponding legal", ip)
                cp.constant_propagate(ip, False)
                self.components.pop(ip.cid)
                continue
            self.input_propositions.append(ip)

        for i in self.components.values():
            if not i.inputs:
                if i not in self.base_propositions and i not in self.input_propositions:
                    meta = ""
                    if i.component_type == PROPOSITION:
                        meta = str(i.meta)
                    if i.component_type == TRANSITION:
                        # print("+++ note transition may have side affect of unsetting initial state")
                        pass
                    else:
                        # this is perfectly valid
                        if i.meta.is_legal and i.count == 0:
                            if DEBUG:
                                print("XXX This needs to be removed:", i, meta)

        self.breakup_large_inputs()
        for c in self.components.values():
            assert len(c.inputs) <= MAX_FAN_OUT_SIZE

        if DEBUG:
            print("* remove useless bases:",)
        removed = self.remove_useless_bases()
        if DEBUG:
            print(removed)
        if removed:
            self.optimize()
            if DEBUG:
                self.print_summary()

        # XXX why dont we do this everytime anyways?
        self.do_backpropagate_on([c for c in self.components.values() if not c.outputs and c.inputs])

        if DEBUG:
            print("* topological_ordering")
        self.topological_ordering()
        self.verify()

        self.print_summary()
        print

    def remove_useless_bases(self):
        new_bases = []
        new_transitions = []
        new_initial_state = []
        count = 0
        for b, t, i in zip(self.base_propositions, self.transitions, self.initial_state):
            if not b.outputs and not t.inputs:
                self.components.pop(b.cid)
                self.components.pop(t.cid)
                count += 1
            else:
                new_bases.append(b)
                new_transitions.append(t)
                new_initial_state.append(i)

        if count:
            self.base_propositions = new_bases
            self.transitions = new_transitions
            self.initial_state = new_initial_state

        return count

    def look_for_useless_endpoints(self):
        for idx, t in enumerate(self.transitions):
            roots = self.determine_unsetables(t)
            if not roots:
                # then we can constant propagate its input
                b = self.base_propositions[idx]
                print("unsettable...", b, t)
                # self.constant_propagate(b, XX)

        for r in self.role_infos:
            for l in r.legals:
                roots = self.determine_unsetables(t)
                if not roots:
                    # then we can constant propagate its input
                    b = self.base_propositions[idx]
                    print("unsettable...", b, t)
                    # self.constant_propagate(b, XX)

    def determine_unsetables(self, c):
        seen_root = set()
        seen = set()

        def go(x):
            for i in x.inputs:
                if i in seen:
                    continue

                if not i.inputs:
                    seen_root.add(i)

                seen.add(i)
                go(i)
        go(c)
        assert c not in seen
        return seen_root

    def dupe(self):
        for c in self.components.values():
            assert self.components[c.cid] == c

        new_component_map = {}
        for c in self.components.values():
            if c.component_type == OR:
                assert c.cid not in new_component_map
                new_component_map[c.cid] = Or(c.cid, c.count,
                                              [i.cid for i in c.inputs],
                                              [o.cid for o in c.outputs])
            elif c.component_type == AND:
                assert c.cid not in new_component_map
                new_component_map[c.cid] = And(c.cid, c.count,
                                               [i.cid for i in c.inputs],
                                               [o.cid for o in c.outputs])
            elif c.component_type == NOT:
                assert c.cid not in new_component_map
                new_component_map[c.cid] = Not(c.cid, c.count,
                                               [i.cid for i in c.inputs],
                                               [o.cid for o in c.outputs])
            elif c.component_type == TRANSITION:
                assert c.cid not in new_component_map
                new_component_map[c.cid] = Transition(c.cid, c.count,
                                                      [i.cid for i in c.inputs],
                                                      [o.cid for o in c.outputs])

            else:
                assert c.component_type == PROPOSITION
                meta = MetaProposition()
                meta.is_base = c.meta.is_base
                meta.is_input = c.meta.is_input
                meta.is_legal = c.meta.is_legal
                meta.is_goal = c.meta.is_goal
                meta.is_init = c.meta.is_init
                meta.is_terminal = c.meta.is_terminal
                meta.gdl = c.meta.gdl
                meta.move = c.meta.move
                meta.goal_value = c.meta.goal_value
                meta.role = c.meta.role
                meta.legals_input = None

                assert c.cid not in new_component_map
                new_component_map[c.cid] = Proposition(c.cid, c.count,
                                                       [i.cid for i in c.inputs],
                                                       [o.cid for o in c.outputs], meta)

        duped_propnet = Propnet(self.roles[:], new_component_map)
        for c in duped_propnet.components.values():
            assert duped_propnet.components[c.cid] == c

        duped_propnet.base_propositions = [new_component_map[b.cid] for b in self.base_propositions]
        duped_propnet.input_propositions = [new_component_map[i.cid] for i in self.input_propositions]
        duped_propnet.initial_proposition = None
        duped_propnet.terminal_proposition = new_component_map[self.terminal_proposition.cid]

        for k, v in self.legal_propositions.items():
            for l in v:
                l = new_component_map[l.cid]
                # we need to link the legal to input (so we match in by role and move)
                # if there is no input, then legal must be invalid
                for ip in duped_propnet.input_propositions:
                    if ip.meta.role == l.meta.role and ip.meta.move == l.meta.move:
                        l.meta.legals_input = ip
                        break

                assert l.meta.legals_input, "legal %s, does not have input" % l

        duped_propnet.goal_propositions = {}
        for k, v in self.goal_propositions.items():
            try:
                duped_propnet.goal_propositions[k] = [new_component_map[p.cid] for p in v]

            except Exception as exc:
                duped_propnet.goal_propositions[k] = []
                print("TODO goal_propositions missing...XXX something sensible here", exc)

        duped_propnet.transitions = [new_component_map[t.cid] for t in self.transitions]
        for b, t in zip(duped_propnet.base_propositions, duped_propnet.transitions):
            t.base_proposition = b

        for c in self.components.values():
            dc = duped_propnet.components[c.cid]
            dc.required_count_true = c.required_count_true
            dc.required_count_false = c.required_count_false
            dc.topological_order = c.topological_order

        duped_propnet.topological_size = self.topological_size
        duped_propnet.initial_state = self.get_initial_state()

        duped_propnet.role_infos = [RoleInfo(r, idx) for idx, r in enumerate(self.roles)]
        for c in duped_propnet.components.values():
            if c.component_type == PROPOSITION:
                p = c
                for role_info in duped_propnet.role_infos:
                    if p.meta.role != role_info.role:
                        continue

                    if p.meta.is_legal:
                        for ip in duped_propnet.input_propositions:
                            if ip.meta.role == p.meta.role and ip.meta.move == p.meta.move:
                                p.meta.legals_input = ip
                                ip.meta.the_legal = p
                                role_info.legals.append(p)
                                role_info.inputs.append(ip)

                    elif p.meta.is_goal:
                        assert p.meta.role in self.roles

                        # santity check that doesnt go anywhere
                        self.goal_propositions.setdefault(p.meta.role, []).append(p)
                        role_info.goals.append(p)

        # XXX this is slow, and not sure why we are doing it?
        duped_propnet.topological_ordering()
        return duped_propnet

    def strip_inputs(self):
        cp = ConstantPropagator(self)
        for i in self.all_inbound(do_bases=False):
            cp.constant_propagate(i, 0)

        if DEBUG:
            cp.report()
        self.optimize()

    def get_initial_state(self):
        return self.initial_state[:]

    def record(self):
        # all propositions
        propositions = [c for c in sorted(self.components.values(), key=lambda c: c.cid) if isinstance(c, Proposition)]

        # base propositions
        self.base_propositions = [p for p in propositions if p.meta.is_base]

        # just checking...
        for b in self.base_propositions:
            assert (len(b.inputs) == 1), "base proposition should have one and only one input"

        # input propositions
        self.input_propositions = [p for p in propositions if p.meta.is_input]

        # just check it is sane
        for i in self.input_propositions:
            assert len(i.inputs) == 0

        # terminal/init
        self.initial_proposition = None
        self.terminal_proposition = None
        for p in propositions:
            if p.meta.is_terminal:
                assert self.terminal_proposition is None
                self.terminal_proposition = p

            if p.meta.is_init:
                assert self.initial_proposition is None
                self.initial_proposition = p

        assert self.terminal_proposition is not None

        # there are now a games (gt_two_thirds family) that doesnt come with initial_proposition set in ggp-base.
        # Super annoying.  And broken IMO.  This is a workaround hack.  XXXX
        if self.initial_proposition is None:
            mp = MetaProposition()
            mp.is_init = True
            mp.gdl = "faked"
            ip = Proposition(self.new_component_id(), 0, [], [], mp)
            self.components[ip.cid] = ip
            self.initial_proposition = ip
            assert ip.cid in self.components
        assert self.initial_proposition is not None or len(self.initial_proposition.inputs) == 0

        # role to goals
        self.goal_propositions = {}

        # create roleinfos
        self.role_infos = [RoleInfo(r, idx) for idx, r in enumerate(self.roles)]
        for role_info in self.role_infos:

            for p in propositions:
                if p.meta.is_legal:
                    assert p.meta.role in self.roles
                    if p.meta.role != role_info.role:
                        continue

                    # we need to link the legal to input (so we match in by role and move)
                    # if there is no input, then legal must be invalid
                    for ip in self.input_propositions:
                        # KKK add the input proposition to role info
                        if ip.meta.role == p.meta.role and ip.meta.move == p.meta.move:
                            p.meta.legals_input = ip
                            ip.meta.the_legal = p
                            role_info.legals.append(p)
                            role_info.inputs.append(ip)
                            break

                    if not p.meta.legals_input:
                        print("WARNING legal %s, does not have input" % p)

                if p.meta.is_goal:
                    assert p.meta.role in self.roles
                    if p.meta.role != role_info.role:
                        continue

                    # santity check that doesnt go anywhere
                    self.goal_propositions.setdefault(p.meta.role, []).append(p)
                    role_info.goals.append(p)

        # initial transitions
        all_transitions = [c for c in self.components.values() if isinstance(c, Transition)]

        # transitions must be ordered as per bases
        self.transitions = []
        for b in self.base_propositions:
            assert len(b.inputs) == 1
            t = b.inputs[0]
            assert isinstance(t, Transition)
            self.transitions.append(t)

        assert set(all_transitions) == set(self.transitions)
        if DEBUG:
            print('DONE recording operations')

    def ensure_valid(self):
        self.optimize()
        self.do_backpropagate_on([c for c in self.components.values() if not c.outputs and c.inputs])
        self.topological_ordering()
        self.verify()
        if DEBUG:
            self.print_summary()

    def find_weird_dangling_stuff(self):
        danglers = set()
        for c in self.components.values():
            if c.component_type in (AND, OR, NOT) and not c.inputs:
                danglers.add(c)
        return danglers

    def ensure_legal_endpoints(self):
        total = 0
        for legals in self.legal_propositions.values():
            for l in legals:
                if len(l.outputs):
                    assert len(l.inputs) == 1
                    the_input = l.inputs[0]

                    # create an or link (note it will be optimizied out, but this is cleanest way to do this)
                    new_component = Or(self.new_component_id(), -1, [the_input], [l] + l.outputs)
                    self.components[new_component.cid] = new_component

                    # rewire the input to point to new component
                    the_input.outputs.remove(l)
                    the_input.outputs.append(new_component)

                    # fix up l
                    old_outputs = l.outputs
                    l.inputs = [new_component]
                    l.outputs = []

                    # fix up old_outputs
                    for o in old_outputs:
                        o.inputs.remove(l)
                        o.inputs.append(new_component)
                    total += 1
        if total:
            if DEBUG:
                print("ensure_legal_endpoints", total)

    def breakup_large_inputs(self):
        did_something = True
        while did_something:
            did_something = False
            for c in self.components.values():
                if len(c.inputs) > MAX_FAN_OUT_SIZE:
                    did_something = True
                    assert c.component_type in (OR, AND)

                    # now no outputs on c
                    old_inputs, c.inputs = c.inputs, []

                    # need to introduce an (perhaps more than one) intermediate Or...

                    while old_inputs:
                        # get first MAX_FAN_OUT_SIZE
                        new_inputs = old_inputs[:MAX_FAN_OUT_SIZE]
                        old_inputs = old_inputs[MAX_FAN_OUT_SIZE:]

                        if c.component_type == AND:
                            clz = And
                        elif c.component_type == OR:
                            clz = Or
                        else:
                            assert False, "Should never get here"

                        new_component = clz(self.new_component_id(), c.count, new_inputs, [c])
                        self.components[new_component.cid] = new_component

                        # add in as an intermediate output to c
                        c.inputs.append(new_component)

                        # fix up downstream
                        for o in new_inputs:
                            o.outputs.remove(c)
                            o.outputs.append(new_component)

    def unlink_transitions(self):
        # we just don't propagate transitions
        for t in self.transitions:
            assert isinstance(t, Transition)

            assert len(t.inputs) == 1
            assert len(t.outputs) == 1

            # remove the input from base proposition
            the_output = t.outputs[0]
            assert isinstance(the_output, Proposition) and the_output.meta.is_base
            the_output.inputs = []

            # remove the output from transition
            t.outputs = []
            t.base_proposition = the_output

    def optimize(self, once=False, all_features=False, verbose=False):

        while True:
            total = 0

            # remove anything leftover
            total += self.unlink_deadends(self.all_set(), verbose=verbose)
            total += self.subexpr_elimination()

            if all_features:
                total += self.do_x_over_y(AND, OR)
                total += self.do_x_over_y(OR, AND)
                total += self.do_x_over_y(OR, OR)
                total += self.do_x_over_y(AND, AND)

                total += self.subexpr_elimination()

            total += self.unlink_passthrough_components()

            total += self.sanitize_input_outputs()

            if all_features:
                total += self.eliminate_expr_to_expr(NOT)
                total += self.eliminate_expr_to_expr(AND)
                total += self.eliminate_expr_to_expr(OR)

            if once or total == 0:
                break

            if verbose:
                "did total stuff in optimize()... %d - restarting" % total

        self.fixup_requires()

    def fixup_requires(self):
        # set all the requires values
        for c in self.components.values():
            if c.component_type == AND:
                c.required_count_true = len(c.inputs)
                c.required_count_false = c.required_count_true - 1

    def do_backpropagate_on(self, components, trace=False):
        seen = set()
        cb = BackPropagator(self, trace=trace)
        for c in components:
            cb.back_propagate(c, seen)

    def dump(self, component):
        Trace(self).trace(component)

    def do_initial_state(self):

        # we set all the inputs we know about (Constant, bases, game inputs)

        # set the constant
        for c in self.components.values():
            if isinstance(c, Constant):
                assert c.count != -1

            if isinstance(c, Proposition):

                if c.meta.is_base or c.meta.is_input or c.meta.is_input:
                    assert not c.inputs
                elif c.meta.is_legal:
                    assert not c.outputs
                elif c.meta.is_terminal or c.meta.is_goal:
                    pass
                else:
                    assert "What is this proposition", c

        for p in self.base_propositions:
            p.count = 0

        for p in self.input_propositions:
            p.count = 0

        # set initial_proposition
        self.initial_proposition.count = 1

        # now we go through all our components and back_propagate everything
        self.do_backpropagate_on([c for c in self.components.values() if not c.outputs and c.inputs])

        # need to copy out the value
        result = [t.count for t in self.transitions]

        # done
        sm = ForwardPropagator(self)
        sm.propagate(self.initial_proposition, 0)
        return result

    def dump_dependencies(self):
        if DEBUG:
            print("Dumping dependencies")
            print("====================")
        cb = BackPropagator(self, trace=False)

        for r in self.role_infos:
            for l in r.legals:
                cb.dependencies(l)

        # for t in self.transitions:
        #     cb.dependencies(t)

    def print_summary(self):
        # everything
        total_components = len(self.components)
        total_inputs = len([c for c in self.components.values() if not c.inputs])
        total_outputs = len([c for c in self.components.values() if not c.outputs])
        total_outputs_real = len([c for c in self.components.values() if not c.outputs and c.inputs])
        total_transitions = len([c for c in self.components.values() if isinstance(c, Transition)])
        total_constants = len([c for c in self.components.values() if isinstance(c, Constant)])

        args1 = (total_components,
                 len(self.base_propositions),
                 len(self.input_propositions),
                 total_inputs,
                 total_outputs,
                 total_outputs_real,
                 total_transitions,
                 total_constants)

        total_propositions = len([c for c in self.components.values() if isinstance(c, Proposition)])
        total_ands = len([c for c in self.components.values() if isinstance(c, And)])
        total_ors = len([c for c in self.components.values() if isinstance(c, Or)])
        total_nots = len([c for c in self.components.values() if isinstance(c, Not)])
        links = sum(len(c.outputs) for c in self.components.values())
        average_fan_out = links / float(total_components - total_outputs)

        args2 = (total_propositions,
                 total_ands,
                 total_ors,
                 total_nots,
                 links,
                 average_fan_out)

        log.debug("SUMMARY: total:%s  bases:%d ins:%s inputs:%d outputs:%d/%d trans:%d const:%d" % args1)
        log.debug("         props: %d ands:%d ors:%d nots:%d links:%d av_fan_out:%.2f" % args2)

    def all_inbound(self, do_bases=True, do_inputs=True):
        result = set()

        # add bases (inbound)
        if do_bases:
            result.update(self.base_propositions)

        # add inputs (inbound)
        if do_inputs:
            result.update(self.input_propositions)

        if self.initial_proposition:
            result.add(self.initial_proposition)

        # XXX constants should be here?
        return result

    def all_outbound(self, do_legals=True, do_goals=True, do_transitions=True, do_terminal=True):
        result = set()

        # add legals (outbound)
        if do_legals:
            for legals in self.legal_propositions.values():
                result.update(legals)

        # add goals (outbound)
        if do_goals:
            for goals in self.goal_propositions.values():
                result.update(goals)

        # add transitions (outbound)
        if do_transitions:
            result.update(self.transitions)

        # add terminal (outbound)
        if do_terminal:
            result.add(self.terminal_proposition)
        return result

    def all_set(self):
        return self.all_inbound().union(self.all_outbound())

    def all_set_without_goals(self):
        # a network just for goals:
        return self.all_inbound().union(self.all_outbound(do_goals=False))

    def sanitize_input_outputs(self):
        " if a more than one link between component exists - remove it "
        total = 0
        for c in self.components.values():
            if len(c.outputs) != len(set(c.outputs)):
                old_outputs = c.outputs
                c.outputs = list(set(c.outputs))
                for o in c.outputs:
                    # remove only one instance
                    old_outputs.remove(o)
                for o in old_outputs:
                    total += 1
                    o.inputs.remove(c)
        if total:
            if DEBUG:
                print("removed %d duplicate links in sanitize_input_outputs()" % total)
        return total

    def unlink_deadends(self, keep, verbose=False):
        total = 0

        # dump everything that is not in keep
        candidates = [c for c in self.components.values() if not c.outputs]
        while candidates:
            c = candidates.pop()

            # skip anything already done or in keep
            if c in keep:
                continue

            assert c.cid in self.components, c
            assert not c.outputs, c

            # we have to remove c from the outputs if connected to c
            for a_input in c.inputs:
                a_input.outputs.remove(c)
                if not a_input.outputs:
                    # print("adding", a_input)
                    candidates.append(a_input)

            if verbose:
                print('unlinked', c)
            self.components.pop(c.cid)
            total += 1
        if total:
            if DEBUG:
                print("total %d components removed via unlink_deadends" % total)
        return total

    def subexpr_elimination(self):
        # IMPORTANT, type ordering (XXX use name rather than 3)
        inputs_to_node = {}
        total = 0

        # XXX large part of slowness in this is that removing inputs/ouputs is expensive with
        # python list
        for c in self.components.values():
            t = c.component_type
            if t in (NOT, AND, OR):
                if not c.inputs:
                    continue

                inputs_as_list = [i.cid for i in c.inputs]
                inputs_as_list.sort()
                key = tuple(inputs_as_list)

                if key in inputs_to_node:
                    existing = inputs_to_node[key]
                    if existing.component_type == t:
                        # fix weird case where both c and existing have the same outputs
                        for o in c.outputs:
                            if o in existing.outputs:
                                existing.outputs.remove(o)
                                o.inputs.remove(existing)

                        # go through inputs of c, and remove their outputs c
                        for i in c.inputs:
                            i.outputs.remove(c)
                        for o in c.outputs:
                            assert o not in existing.outputs
                            existing.outputs.append(o)
                            o.inputs.remove(c)
                            o.inputs.append(existing)

                        total += 1
                        self.components.pop(c.cid)
                else:
                    inputs_to_node[key] = c

        if total:
            if DEBUG:
                print("removed %d components via subexpr_elimination" % total)
        return total

    def unlink_passthrough_components(self, do_list=(AND, OR, PROPOSITION)):
        ' this is count/required_count safe '
        all_propositions = self.all_set()
        total = 0
        for c in self.components.values():
            if c.component_type not in do_list:
                continue

            if c in all_propositions:
                continue

            if len(c.inputs) == 1 and c.outputs:
                the_input = c.inputs[0]

                # this must die
                # print(c, the_input, " -> ", len(c.outputs))
                for the_output in c.outputs:
                    replace_count = 0

                    # replace the output of the the_input with the the_output
                    for idx, o in enumerate(the_input.outputs):
                        if o == c:
                            the_input.outputs[idx] = the_output
                            replace_count += 1
                            break

                    # did not find the same input, append
                    if replace_count == 0:
                        the_input.outputs.append(the_output)
                        replace_count += 1

                    # replace the input of the the_output with the the_input
                    for idx, o in enumerate(the_output.inputs):
                        if o == c:
                            the_output.inputs[idx] = the_input
                            replace_count += 1
                            break

                    assert replace_count == 2

                # and remove it
                self.components.pop(c.cid)
                total += 1

        if total:
            if DEBUG:
                print('unlinked passthrough components', total)
        return total

    def eliminate_expr_to_expr(self, do_type):
        total = 0
        for c in self.components.values():
            t = c.component_type
            if t == do_type:
                all_do_type_ouputs = True
                for o in c.outputs:
                    if o.component_type != do_type:
                        all_do_type_ouputs = False
                        break

                # ZZZXXX this value seems to make a big difference
                # wihtout speedChess is 10% faster... huh
                # if len(c.outputs) < len(c.inputs):
                #    continue
                # if len(c.outputs) > 5 or len(c.outputs) > len(c.inputs):
                #    continue

                # I don't know how much this helps when the size is > 1, and it is also causing crashes... so meh...
                # XXX need to figure this out
                if all_do_type_ouputs:
                    # the idea is that this gate, c, can be eliminated and merged upstream
                    # so we re-route all the inputs of c, to the outputs of c

                    # remove the connect of c from all the inputs
                    for i in c.inputs:
                        i.outputs.remove(c)

                    # for each output of c we must
                    #  * unlink c's outputs
                    for o in c.outputs:
                        # remove the connect of c from outputs component o
                        o.inputs.remove(c)

                        # add the output directly to i
                        for i in c.inputs:
                            if o not in i.outputs:
                                i.outputs.append(o)

                            # add the input directly to o
                            if i not in o.inputs:
                                o.inputs.append(i)

                    # and remove it
                    self.components.pop(c.cid)
                    total += 1
                    # print('AFTER', c.inputs, c.outputs)

        if do_type == AND:
            s = "ANDs"
        elif do_type == OR:
            s = "ORs"
        elif do_type == NOT:
            s = "NOTs"
        if DEBUG:
            if total:
                print('number of eliminated %s : %s' % (s, total))
        return total

    def eliminate_nots(self):
        for c in self.components.values():
            all_nots = True
            for o in c.outputs:
                if o.component_type != NOT:
                    all_nots = False

            if all_nots:
                the_outputs = c.outputs[:]
                for o in the_outputs:
                    assert len(o.inputs) == 1
                    # remove NOT
                    c.outputs.remove(o)
                    for not_o in o.outputs:
                        not_o.inputs.remove(o)
                        assert c not in not_o.inputs
                        not_o.inputs.append(c)
                    c.outputs += o.outputs
                    c.increment_multiplier *= -1
                    self.components.pop(o.cid)
                    if DEBUG:
                        print("eliminate not", o)

    def do_x_over_y(self, X=AND, Y=OR):
        total = 0
        for c in self.components.values():
            if c.component_type == Y:
                # if all the inputs to an OR are ANDS...
                look_for_inputs = [i for i in c.inputs if (i.component_type == X and len(i.outputs) == 1)]
                if len(look_for_inputs) == 1:
                    continue
                if len(look_for_inputs) == len(c.inputs):

                    # check if there are any common inputs to the ANDS
                    common_inputs = None
                    for a in look_for_inputs:
                        if common_inputs is None:
                            common_inputs = set(a.inputs)
                        else:
                            common_inputs = common_inputs.intersection(a.inputs)

                    if not common_inputs:
                        continue

                    for i in look_for_inputs:
                        if len(i.outputs) != 1:
                            if DEBUG:
                                print('skipping in do_x_over_y since > 1 outputs', i)
                            continue

                    # print("XXXXXXXXXXXXXX", c, common_inputs)

                    # remove commons from the ands (only if the and has one output, being c)
                    for common in common_inputs:
                        # just checking.  but this would be messed up, as the ands could be eliminated entirely
                        assert common not in c.inputs
                        # only do this if the 'and' gate here has one output
                        for a in look_for_inputs:
                            assert len(a.outputs) == 1
                            # print(common, 'removing link to and', a)
                            common.outputs.remove(a)
                            a.inputs.remove(common)

                    # create a new And which will have all the common inputs and c
                    new_outputs, c.outputs = c.outputs, []
                    if X == AND:
                        clz = And
                    elif X == OR:
                        clz = Or
                    elif X == NOT:
                        clz = Not
                    else:
                        assert False, "Should never get here"

                    new_component = clz(self.new_component_id(), -1, list(common_inputs) + [c], new_outputs)
                    self.components[new_component.cid] = new_component

                    # patch up new_component inputs
                    for i in new_component.inputs:
                        # nothing to remove, since c removed all outputs, and all common are dangling
                        i.outputs.append(new_component)
                        # print(i, 'addin to', new_component)

                    # patch up component outputs
                    for o in new_component.outputs:
                        o.inputs.remove(c)
                        o.inputs.append(new_component)

                    total += 1

        d = {AND : "AND",
             OR : "OR",
             NOT : "NOT"}

        if DEBUG:
            if total:
                print("moved %s %s over %s" % (total, d[X], d[Y]))
        return total

    def new_component_id(self):
        cid = len(self.components) * 2
        while cid in self.components:
            cid += 1
        return cid

    def to_gdl(self, base_map):
        ' helper to dump info '
        result = []
        for p, v in zip(self.base_propositions, base_map):
            if v:
                result.append(str(p.meta.gdl))
        return " ".join(result)

    #####################################################################

    def topological_ordering(self):
        ' NOTE: expects constants and initial propositions to be constant propagated'
        self.levels = []

        # start with the base/input propositions
        components = set(self.components.values())

        seen = set()
        level = set()
        for p in self.base_propositions:
            seen.add(p)
            level.add(p)
            components.remove(p)

        for p in self.input_propositions:
            seen.add(p)
            level.add(p)
            components.remove(p)

        # may not exist
        if self.initial_proposition:
            seen.add(self.initial_proposition)
            level.add(self.initial_proposition)
            components.remove(self.initial_proposition)

        # add in the constants (if any)
        for c in self.components.values():
            if isinstance(c, Constant):
                seen.add(c)
                level.add(c)
                components.remove(c)

        # this first level is the input level
        self.levels.append(level)

        candidates = set()
        for c in level:
            # since input level
            assert len(c.inputs) == 0
            for o in c.outputs:
                candidates.add(o)

        # create legal and transition sets (these go last)
        legals_set = set()
        for legals in self.legal_propositions.values():
            for l in legals:
                assert len(l.outputs) == 0
                legals_set.add(l)

        transitions_set = set(self.transitions)

        while candidates:
            # this is our new level
            level = set()

            todo = list(candidates)
            candidates = set()

            new_seen = set()
            for c in todo:
                if c in seen or c in legals_set or c in transitions_set:
                    continue

                seen_all_inputs = True
                for i in c.inputs:
                    if i not in seen:
                        seen_all_inputs = False
                        break

                if not seen_all_inputs:
                    candidates.add(c)

                else:
                    level.add(c)
                    new_seen.add(c)
                    components.remove(c)

                    # add in all outputs
                    for o in c.outputs:
                        candidates.add(o)

            if not level:
                control_flow_leftover = [c for c in candidates if c.component_type in (AND, OR, NOT)]
                if len(control_flow_leftover) == 0:
                    break
                if DEBUG:
                    print("Loops???? WTF..  Ok add them all in, and leave everything else leftover")
                level = control_flow_leftover
                for c in control_flow_leftover:
                    components.remove(c)
                    new_seen.add(c)

                for c in control_flow_leftover:
                    for o in c.outputs:
                        if o not in new_seen or o not in seen:
                            candidates.add(o)

            seen.update(new_seen)
            self.levels.append(level)

        # add in transitions (we are guaranteed to only have one output in a transition)
        level = []
        for t in transitions_set:
            level.append(t)
            components.remove(t)
        self.levels.append(level)

        # finally add in legals
        level = []
        for l in legals_set:
            level.append(l)
            components.remove(l)

        self.levels.append(level)

        # if goals are leftover, add them.  (This is for very strange gdl created for testing gdl
        # players from standford)
        goal_level = []
        for c in components:
            if c.component_type == PROPOSITION and c.meta.is_goal:
                goal_level.append(c)

        if goal_level:
            self.levels.append(goal_level)
            for g in goal_level:
                components.remove(g)

        if components:
            if DEBUG:
                print("LEFTOVER", len(components))

            def find_root_input(x, roots):
                if not x.inputs:
                    if x not in seen:
                        roots.add(x)
                    return
                for i in x.inputs:
                    find_root_input(i, roots)

            # empty loops
            for c in list(components):
                d = set()
                find_root_input(c, d)

                xxx = list(d)
                if len(xxx) == 1 and xxx[0] == c:
                    components.remove(c)
                    continue

                if DEBUG:
                    print(c, d, c.inputs, c.outputs)

            if DEBUG:
                print("After removing empty loops, LEFTOVER", len(components))

            if components:
                if DEBUG:
                    print("important: this doesn't mean not reachable from set of inputs, it means",
                          "that there is at least one input up the line missing")
                assert False, "figure out wtf is going on"

        for e, l in enumerate(self.levels):
            for c in l:
                c.topological_order = e
        self.topological_size = len(self.levels)

    def verify(self):
        if self.disable_verify:
            return
        if DEBUG:
            print("verifying")
        for c in self.components.values():
            # if c.component_type in (AND, OR):
            #     assert 0 <= c.count <= len(c.inputs)
            # else:
            #     assert 0 <= c.count <= 1

            # if c.component_type == AND:
            #     assert len(c.inputs) == c.required_count_true
            #     assert len(c.inputs) - 1 == c.required_count_false

            # check all the outputs, have us as an input
            for o in c.outputs:
                assert o.cid in self.components
                assert c in o.inputs

            # check all the input, have us as an output
            for i in c.inputs:
                assert i.cid in self.components
                assert c in i.outputs

            # check we still base_propositions and inputs
            for ib in self.base_propositions:
                assert ib.cid in self.components

            for ip in self.input_propositions:
                assert ip.cid in self.components

        cb = BackPropagator(self, trace=False, compare=True)
        for c in self.components.values():
            if (not c.outputs and c.inputs):
                try:
                    cb.back_propagate(c, set())
                except:
                    cb = BackPropagator(self, trace=True, compare=True)
                    cb.back_propagate(c, set())

        if DEBUG:
            print("verified")

    def reorder_legals(self):
        if DEBUG:
            print("SORTING LEGALS")

        def gdl_sort(props):
            groups = {}

            # break up into groups
            for p in props:
                gdl = p.meta.gdl[2]
                if isinstance(gdl, symbols.Term):
                    assert str(gdl) not in groups
                    groups.setdefault(gdl, []).append(p)
                else:
                    basic_grouping = gdl[0]
                    groups.setdefault(str(basic_grouping), []).append(p)

            keys = groups.keys()
            keys.sort()

            new_props = []

            # go through the basic groups and keep them in order too
            for k in keys:
                group_props = groups[k]
                sorted_by_str_value = {}
                for p in group_props:
                    sorted_by_str_value[str(p.meta.gdl)] = p
                group_keys = sorted_by_str_value.keys()
                group_keys.sort()
                for k2 in group_keys:
                    new_props.append(sorted_by_str_value[k2])

            new_props.reverse()
            return new_props

        # print("LEN self.input_propositions", len(self.input_propositions))
        new_input_propositions = []
        set_input_propositions_count = 0
        for role_info in self.role_infos:
            new_legals = gdl_sort(role_info.legals)
            assert len(role_info.legals) == len(new_legals)

            # print("pprint(sorted legals:")
            # from pprint import pprint
            # pprint(new_legals)

            new_inputs = []
            for l in new_legals:
                new_inputs.append(l.meta.legals_input)
                assert l.meta.legals_input is not None
                new_input_propositions.append(l.meta.legals_input)

            # XXXXX
            # update
            role_info.legals = new_legals

            # this is a hack to fix another hack.  Seems legals can purged, but inputs must always
            # remain (this is due to how cpp propagate works).  so only update new_inputs, if same
            if len(role_info.legals) != 0:
                assert len(role_info.inputs) == len(new_inputs)
                role_info.inputs = new_inputs
                set_input_propositions_count += 1

        if set_input_propositions_count:
            assert set_input_propositions_count == len(self.role_infos)
            self.input_propositions = new_input_propositions
            # print("LEN X2 self.input_propositions", len(self.input_propositions))

    def reorder_base_propositions(self):
        new_bases = []
        groups = {}

        for b in self.base_propositions:
            gdl = b.meta.gdl[1]
            if isinstance(gdl, symbols.Term):
                assert str(gdl) not in groups
                groups.setdefault(gdl, []).append(b)
            else:
                basic_grouping = gdl[0]
                groups.setdefault(str(basic_grouping), []).append(b)

        keys = groups.keys()
        keys.sort()

        for k in keys:
            bases = groups[k]
            sorted_by_str_value = {}
            for b in bases:
                sorted_by_str_value[str(b.meta.gdl)] = b
            group_keys = sorted_by_str_value.keys()
            group_keys.sort()
            for k2 in group_keys:
                new_bases.append(sorted_by_str_value[k2])

        assert len(self.base_propositions) == len(new_bases)

        new_bases.reverse()
        new_transitions = []
        new_initial_state = []
        for b in new_bases:
            ii = self.base_propositions.index(b)
            new_initial_state.append(self.initial_state[ii])
            new_transitions.append(self.transitions[ii])

        # print(self.initial_state, new_initial_state)
        # print(self.to_gdl(self.initial_state))

        self.base_propositions = new_bases
        self.initial_state = new_initial_state
        self.transitions = new_transitions

    def reorder_components(self):
        if self.already_reordered:
            return

        # reorder all the components (starting from 0)
        component_id = [0]
        components = []
        todo_components = set(self.components.values())

        def do(c):
            c.cid = component_id[0]
            component_id[0] += 1
            components.append(c)
            todo_components.remove(c)
            # print(c

        for l in self.base_propositions:
            do(l)

        for info in self.role_infos:
            for i in info.inputs:
                do(i)

        # do these in topological order:
        for level in self.levels:
            for c in level:
                if c.component_type in (AND, OR, NOT):
                    do(c)

        do(self.terminal_proposition)

        for info in self.role_infos:
            for g in info.goals:
                do(g)

        for t in self.transitions:
            do(t)

        for info in self.role_infos:
            for l in info.legals:
                do(l)

        self.components = {}
        for c in components:
            self.components[c.cid] = c

        assert len(todo_components) == 0

        if DEBUG:
            print("REORDERED COMPONENTS")
        self.already_reordered = True


class Trace:
    def __init__(self, propnet):
        self.propnet = propnet

    def trace(self, component, seen=None, depth=0):
        ' the interface '
        if seen is None:
            seen = set()

        assert self.trace
        if component in seen:
            assert component.count != -1, "in seen (%s) but no value set" % seen
            if DEBUG:
                print("    " * depth, "**", component.count >= component.required_count_true, component)

        seen.add(component)

        assert component.count != -1, "do_back_propagate_xxx() didn't set value %s" % component

        for i in component.inputs:
            self.trace(i, seen, depth + 1)

        res = component.count >= component.required_count_true
        if component.increment_multiplier == -1:
            res = not res
        else:
            assert component.increment_multiplier == 1
        if DEBUG:
            print("    " * depth, res, component)


class BackPropagator:
    ' simple back propagator, but not a state machine '
    def __init__(self, propnet, trace=True, compare=False):
        self.propnet = propnet
        # print(the back propagation as it happens
        self.trace = trace

        # compares what it computes in the component versus what is existing (can be used to
        # vigourously integrity check)
        self.compare = compare

        self.dependent_inputs = None

    def dependencies(self, component):
        # from a end point component, establish which inputs are we dependent upon
        assert len(component.outputs) == 0
        res = self.dependent_inputs = set()
        seen = set()
        self.back_propagate(component, seen)
        self.dependent_inputs = None
        if DEBUG:
            print("dependencies for", component)
            for i in res:
                print("    ", i)

    def back_propagate(self, component, seen, depth=0):
        ' the interface '
        if component in seen:
            if component.count == -1:
                if DEBUG:
                    print("WARNING - loop detected, setting value component to zero value")
                # component.count = 0
                # return

            assert component.count != -1, "in seen (%s) but no value set" % seen
            if self.trace:
                print("    " * depth, "**", component.count, component)

            res = component.count >= component.required_count_true
            if component.component_type == NOT:
                res = not res
            return res

        seen.add(component)

        # simple dispatch on type (keeping code self contained in class)
        methods = {
            PROPOSITION : self.do_back_propagate_proposition,
            OR : self.do_back_propagate_or,
            AND : self.do_back_propagate_and,
            NOT : self.do_back_propagate_not,
            TRANSITION : self.do_back_propagate_transition,
            CONSTANT : self.do_back_propagate_constant}

        method = methods[component.component_type]

        # remember count is the number of inputs that are true
        count = method(component, seen, depth)
        assert count != -1, "do_back_propagate_xxx() didn't set value %s" % component

        if self.compare:
            assert component.count == count, component

        component.count = count

        res = count >= component.required_count_true
        if component.increment_multiplier == -1:
            res = not res
        else:
            assert component.increment_multiplier == 1

        if self.trace:
            print("    " * depth, res, component)

        return res

    def do_back_propagate_proposition(self, component, seen, depth):

        # Notes: there is either one input or none.  If the one input is a transition, ignore it.
        assert len(component.inputs) <= 1, "%s has more than one input %s" % (component, component.inputs)

        if len(component.inputs) == 0 or isinstance(component.inputs[0], Transition):
            # this is a network input

            # for dependency analysis
            if self.dependent_inputs is not None:
                self.dependent_inputs.add(component)

            assert component.count != -1, "a network input (%s) has not been initialsed" % component
            return component.count

        else:
            return 1 if self.back_propagate(component.inputs[0], seen, depth + 1) else 0

    def do_back_propagate_or(self, component, seen, depth):
        input_counts = [self.back_propagate(i, seen, depth + 1) for i in component.inputs]
        return len([c for c in input_counts if c])

    def do_back_propagate_and(self, component, seen, depth):
        input_counts = [self.back_propagate(i, seen, depth + 1) for i in component.inputs]
        return len([c for c in input_counts if c])

    def do_back_propagate_not(self, component, seen, depth):
        assert len(component.inputs) == 1, "%s must have one input" % component
        return 1 if self.back_propagate(component.inputs[0], seen, depth + 1) else 0

    def do_back_propagate_transition(self, component, seen, depth):
        if component.inputs:
            return 1 if self.back_propagate(component.inputs[0], seen, depth + 1) else 0
        else:
            return component.count

    def do_back_propagate_constant(self, component, seen, depth):
        assert len(component.inputs) == 0
        assert component.count != -1
        return component.count

###############################################################################


class ForwardPropagator:
    ' simple forward propagator, but not a state machine '

    def __init__(self, propnet):
        self.propnet = propnet

    def propagate(self, component, value):
        if value != component.count:
            component.count = value
            self.forward_propagate_value(component, 1 if value else -1)

    def forward_propagate_value(self, component, incr):
        # CONSTRAINT: only called if propagation is required

        for o in component.outputs:
            o.count += incr

            if o.outputs:
                if incr > 0 and o.count == o.required_count_true:
                    self.forward_propagate_value(o, incr * o.increment_multiplier)
                elif incr < 0 and o.count == o.required_count_false:
                    self.forward_propagate_value(o, incr * o.increment_multiplier)

###############################################################################


class ConstantPropagator:
    def __init__(self, propnet, verbose=False):
        self.propnet = propnet
        self.fwd_prop = ForwardPropagator(propnet)
        self.legals = []
        self.verbose = verbose
        self.total_propagations = 0

    def report(self):
        print('constant propagated %d components' % self.total_propagations)

    def constant_propagate(self, component, count):
        ''' first of all before calling this, must forward propagate things.  This algorithm will
            expect the forwaring values to be correct. '''

        # a set of deadends we need to deal with once fully propagated
        self.fwd_prop.propagate(component, count)

        if self.verbose:
            print('cp--> constant_propagate', component, bool(component.coun))

        total = self.do_constant_propagate(component, count, 1)
        self.total_propagations += total

        while self.legals:
            legal = self.legals.pop(0)
            component = legal.meta.legals_input

            # can only constant a propagate a legal of 0.
            if legal.count != 0:
                log.warning("would of constant propagated an input on %s" % component)
                continue

            self.fwd_prop.propagate(component, legal.count)

            if self.verbose:
                print('cp--> constant_propagate input', component, bool(legal.count))

            total = self.do_constant_propagate(component, legal.count, 1)
            self.total_propagations += total

        if self.verbose:
            print
            print('constant propagated %d components' % total)

    def do_constant_propagate(self, component, count, depth):
        assert len(component.inputs) == 0
        total = 0

        # say goodbye to this component
        if component.component_type not in (TRANSITION, PROPOSITION):
            self.propnet.components.pop(component.cid)

        # take a copy of the component's outputs
        outputs = [c for c in component.outputs]

        # go through outputs and remove the inbound connection
        while outputs:
            o = outputs.pop()
            if self.verbose:
                print(depth * '    ' + 'cp-->', o, count)

            # well if some constant propagation done earlier on an earlier popped output, o' - that o' might not be
            # part of the outputs at all anymore.  If that is so we can skip it entirely.  remove from the input.  This
            # might happen for or/and when they got wind of the idea that they were now forced true/false regardless of
            # what the other inputs were - and unhooked itself.  See LLL.

            # assert component in o.inputs
            if component not in o.inputs:
                assert o not in component.outputs, "Cannot be in the outputs anymore - see above comment"
                continue

            o.inputs.remove(component)
            component.outputs.remove(o)

            #  handle each output on per type basis
            if o.component_type == OR:
                if count:
                    # since we already propagated forward, this should indeed be the correct value.
                    assert o.count >= o.required_count_true

                    # LLL: will always be true.  Unlink o from all the other inputs.
                    for i in o.inputs:
                        i.outputs.remove(o)

                        # issue: i may be a new deadend?
                        if self.verbose and not i.outputs:
                            print(i, "has no outputs, a new deadend")

                    o.inputs = []
                    total += self.do_constant_propagate(o, 1, depth + 1)

                else:
                    # o.count - will be correct
                    # o.required_count_true - will be correct
                    # o.required_count_false - will be correct

                    # len(o.inputs) == 1 is a special case, we can rewire output of the remaining
                    # input, so that we don't need this at all anymore done later as separate pass

                    if len(o.inputs) == 0:
                        # assert o.count == 0
                        total += self.do_constant_propagate(o, 0, depth + 1)

            elif o.component_type == AND:
                if count:
                    o.count -= 1
                    o.required_count_true -= 1
                    o.required_count_false -= 1

                    # len(o.inputs) == 1 is a special case, we can rewire output of the remaining
                    # input, so that we don't need this at all anymore done later as separate pass

                    if len(o.inputs) == 0:
                        # I've no idea what the comment even means:  XXX delete this...
                        # XXX this assertion is wrong, only true if we don't do o.count first (NOT
                        # SURE this statement is correct)

                        # assert o.count == 1

                        total += self.do_constant_propagate(o, 1, depth + 1)
                else:
                    # LLL: will always be false.  Unlink o from all the other inputs.
                    assert o.count <= o.required_count_true
                    for i in o.inputs:
                        i.outputs.remove(o)
                        # issue: i may be a new deadend?
                        if self.verbose and not i.outputs:
                            print(i, "has no outputs, a new deadend")

                    o.inputs = []
                    total += self.do_constant_propagate(o, 0, depth + 1)

            elif o.component_type == NOT:
                # Constant_propagate this, as component is only input.
                # assert o.count == count
                total += self.do_constant_propagate(o, 0 if count else 1, depth + 1)

            elif o.component_type == TRANSITION:
                # This will create a loop.  Instead we stop here.
                assert o.count == count
                # print("TRANSITION now constant :", o
                assert len(o.outputs) == 0

            elif o.component_type == PROPOSITION:
                # Constant_propagate this as component is only input.
                assert o.count == count
                # print("PROPOSITION now constant :", o
                assert len(o.outputs) == 0

                if o.meta.is_legal:
                    # ok we can do the input since it can never be set!
                    self.legals.append(o)

            else:
                assert False, "What is this? %s" % o

        total += 1
        return total
