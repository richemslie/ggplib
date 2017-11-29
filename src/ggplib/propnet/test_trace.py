def flow(self, c, value, seen=None, transitions=None):
        if seen is None:
            seen = set()
        if transitions is None:
            transitions = set()

        seen.add(c)
        if len(c.outputs) == 0 and c.component_type == TRANSITION:
            transitions.add((value, c))

        else:
            next_flow_value = None
            if c.component_type == OR:
                if value == TRUE:
                    next_flow_value = TRUE
                else:
                    next_flow_value = self.get_component_value(c)

            elif c.component_type == AND:
                if value == TRUE:
                    next_flow_value = self.get_component_value(c)
                else:
                    next_flow_value = FALSE

            elif c.component_type == NOT:
                if value == TRUE:
                    next_flow_value = FALSE
                elif value == FALSE:
                    next_flow_value = TRUE
                else:
                    next_flow_value = self.get_component_value(c)

            elif c.component_type == PROPOSITION:
                assert len(c.inputs) == 0
                next_flow_value = value
            else:
                XXX

        for o in c.outputs:
            if o in seen:
                continue

            self.flow(o, next_flow_value, seen, transitions)

        return transitions


def get_transitions(c, seen=None, transitions=None):
        if seen is None:
            seen = set()
        if transitions is None:
            transitions = set()

        seen.add(c)
        if len(c.outputs) == 0 and c.component_type == TRANSITION:
            transitions.add(c)
        else:
            for o in c.outputs:
                if o in seen:
                    continue

                get_transitions(o, seen, transitions)

        return transitions

def strip_goals(propnet):
    propnet = propnet.dupe()

    print "remove goasl"
    print "============"
    propnet.unlink_deadends(propnet.all_set_without_goals())
    for r in propnet.role_infos:
        old_goals = r.goals
        r.goals = []
        for g in old_goals:
            if g.cid in propnet.components:
                r.goals.append(g)

    propnet.optimize()
    propnet.ensure_valid()
    print "======DONE======"
    propnet.print_summary()

    return propnet

def strip_inputs(propnet):
    propnet = propnet.dupe()

    print "stripping inputs"
    print "================"

    print "Before summmary:"
    propnet.print_summary()

    propnet.strip_inputs()

    propnet.unlink_deadends(propnet.all_inbound(do_inputs=False).union(propnet.all_outbound(do_goals=True, do_transitions=False)))
    propnet.transitions = []
    for r in propnet.role_infos:
        r.inputs = []
    propnet.input_propositions = []
    propnet.optimize()
    propnet.ensure_valid()

    propnet.print_summary()
    print "======DONE======"

    #pprint([c for c in propnet.components.values() if not c.inputs])
    return propnet

def dump_transitions(propnet, verbose=False):
    show_passthroughs = False
    skip_controls = True
    controls = get_controls(propnet, verbose=verbose)

    input_propositions_passthrough_type = 0
    all_transitions = set(propnet.transitions)

    for i in propnet.input_propositions:
        #transitions = get_transitions(i)
        #if len(transitions) == 0:
        #    transitions = all_transitions

        #x = all_transitions.difference(transitions)
        #pprint(x)
        #print

        if verbose:
            print
        print "DOING:", i

        dc = DependencyComponent(i)
        controls_seen = 0

        all_passthrough_type = True
        for t in all_transitions:
            if t.cid in controls:
                controls_seen += 1
                if skip_controls:
                    continue

            # WHY CANT REMOVE THIS OUT OF THE LOOP?  It is really slow otherwise...  I think just
            # because of control logic... it needs to identify if it hit any inputs, and we cahced
            # the inputs.... hmmmm.  Should be easy to fix.

            #dc = DependencyComponent(i)
            #dc.reset()

            dc.reset()
            v = dc.get_component_value(t)

            if skip_controls:
                assert len(dc.inputs_seen()) > 0

            s = dc.create_flow_control(t)

            if dc.passthrough(t):
                if show_passthroughs and verbose:
                    print "PASSTHROUGH", t.fish_gdl()
            else:
                tup = s.tuple()
                if not s.component.component_type == TRANSITION or tup[1] not in ["false", "true"]:
                    all_passthrough_type = False
                    if not verbose:
                        print "fail", t, dc.passthrough(t)
                        pprint(tup)

                if verbose:
                    print t, v, len(dc.bases), len(dc.mapping), s, "Flow:", dc.flow_count
                    pprint(tup)

        if verbose and controls_seen:
            print "CONTROLS_SEEN", controls_seen
        if all_passthrough_type:
            input_propositions_passthrough_type += 1

    print
    print "Total input propositions: %d, passthrough type: %d" % (len(propnet.input_propositions),
                                                                  input_propositions_passthrough_type)

    print
    print "Controls:"
    print "---------"
    pprint(controls)
    for t in controls.values():
        dc = DependencyComponent(i)
        v = dc.get_component_value(t)
        n = dc.create_flow_control(t)
        print
        print t, v, n, "Flow:", dc.flow_count
        pprint(n.tuple())

    if len(propnet.input_propositions) == input_propositions_passthrough_type:
        strip_inputs(propnet)

def dump_legals(propnet):
    propnet = strip_goals(propnet)
    propnet = strip_inputs(propnet)

    all_legals = set()
    for r in propnet.role_infos:
        for l in r.legals:
            all_legals.add(l)

    verbose = True
    dc = DependencyComponent()
    for l in all_legals:
        dc.reset()
        v = dc.get_component_value(l)
        n = dc.create_flow_control(l)
        if verbose:
            print
            print l, v, n, "Flow:", dc.flow_count
            pprint(n.tuple())

def dump_goals(propnet):
    propnet = strip_inputs(propnet)

    dc = DependencyComponent()
    def do(s, c):
        print
        print s
        print len(s) * '='

        dc.reset()
        v = dc.get_component_value(c)
        n = dc.create_flow_control(c)
        print v, n, "flow_count:", dc.flow_count
        pprint(n.tuple(), indent=2)

    # dump the goals
    for r in propnet.role_infos:
        for g in r.goals:
            s = "%s : %s" % (r.role, g)
            do(s, g)

    # dump the terminal
    do("terminal", propnet.terminal_proposition)

def dump_terminal(propnet):
    propnet = strip_inputs(propnet)

    dc = DependencyComponent()
    def do(s, c):
        print
        print s
        print len(s) * '='

        dc.reset()
        v = dc.get_component_value(c)
        n = dc.create_flow_control(c)
        print v, n, "flow_count:", dc.flow_count
        pprint(n.tuple(), indent=2)

    # dump the terminal
    do("terminal", propnet.terminal_proposition)

def scan_dump_goals_terminal(propnet):

    dc = DependencyComponent()
    def do(s, c):
        print
        print s
        print len(s) * '='

        dc.reset()
        v = dc.get_component_value(c)
        n = dc.create_flow_control(c)
        pprint(n.tuple(), indent=2)
        return dc.flow_count

    # flow count for the goals
    goals_flow_count = 0
    for r in propnet.role_infos:
        for g in r.goals:
            s = "%s : %s" % (r.role, g)
            goals_flow_count = max(goals_flow_count, do(s, g))

    # flow count the terminals
    terminal_flow_count = do("terminal", propnet.terminal_proposition)

    print "goals", goals_flow_count, "terminals", terminal_flow_count
    return goals_flow_count, terminal_flow_count

def dump_propositions(propnet):
    for b in propnet.base_propositions:
        print b

###############################################################################

if __name__ == "__main__":
    import sys
    from galvanise import interface
    from galvanise.propnet import lookup

    interface.initialise_k273(1)

    game = sys.argv[1]
    propnet = lookup.get_propnet_by_name(game)

    #dump_propositions(propnet)
    dump_goals(propnet)
    #dump_transitions(propnet, verbose=True)
    #dump_legals(propnet)

    #scan_dump_goals_terminal(get_propnet(kif_name))

