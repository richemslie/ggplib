import time
import traceback

from ggplib.util import log
from ggplib.propnet.constants import OR, AND, NOT, PROPOSITION, TRANSITION, MAX_FAN_OUT_SIZE

DEBUG = False


class Builder:
    def __init__(self, interface, verbose=True):
        self.sm = None
        self.interface = interface
        self.verbose = verbose

    def create_state_machine(self, role_count, num_bases, num_transitions,
                             num_components, num_outputs, topological_size):
        if self.verbose:
            print "Creating SM with role_count: %s, "\
                  "bases: %s, #trans %s, #comps %s, #outputs %s, topo %s" % (role_count,
                                                                             num_bases,
                                                                             num_transitions,
                                                                             num_components,
                                                                             num_outputs,
                                                                             topological_size)
            print

        # create the c statemachine
        self.sm = self.interface.StateMachine(role_count, num_bases,
                                              num_transitions, num_components,
                                              num_outputs, topological_size)

    def set_role(self, role_index, name, input_start_index, legal_start_index,
                 goal_start_index, num_inputs_legals, num_goals):
        if self.verbose:
            print "Creating Role %s/%s with input/legal/goals"\
                  "%s/%s/%s #inputs/goals %s/%s" % (role_index,
                                                    name,
                                                    input_start_index,
                                                    legal_start_index,
                                                    goal_start_index,
                                                    num_inputs_legals,
                                                    num_goals)

        self.sm.set_role(role_index, name, input_start_index,
                         legal_start_index, goal_start_index, num_inputs_legals, num_goals)

    def set_component(self, component_id, required_count_false, required_count_true,
                      output_index, number_outputs, initial_count, incr, topological_order):

        self.sm.set_component(component_id, required_count_false, required_count_true,
                              output_index, number_outputs, initial_count, incr, topological_order)

    def set_output(self, output_index, component_id):
        self.sm.set_output(output_index, component_id)

    def record_finalise(self, control_flows, terminal_index):
        self.sm.record_finalise(control_flows, terminal_index)

    def set_meta_proposition(self, component_id, typename, gdl_str, move, goal_value):
        self.sm.set_meta_component(component_id, typename, gdl_str, move, goal_value)

    def set_meta_transition(self, component_id, typename, gdl_str):
        self.sm.set_meta_component(component_id, typename, gdl_str, "", -1)

    def set_meta_component(self, component_id, typename):
        self.sm.set_meta_component(component_id, typename, "", "", -1)

    def add_roles(self, propnet):
        self.sm.roles = [str(ri.role) for ri in propnet.role_infos]

    def do_initial_state(self, propnet):
        # set initial state:
        self.sm.initial_base_state = self.sm.new_base_state()
        for idx, value in enumerate(propnet.get_initial_state()):
            self.sm.initial_base_state.set(idx, value)
            assert self.sm.initial_base_state.get(idx) == value

        self.sm.set_initial_state(self.sm.initial_base_state)
        self.sm.update_bases(self.sm.initial_base_state)

    def do_build(self, propnet):
        propnet.reorder_components()
        propnet.verify()

        role_count = len(propnet.role_infos)

        def get_number_outputs(c):
            return len(c.outputs) + 1

        # create the state machine:
        args = (role_count,
                len(propnet.base_propositions),
                len(propnet.transitions),
                len(propnet.components),
                sum(get_number_outputs(c) for c in propnet.components.values()),
                propnet.topological_size)

        self.create_state_machine(*args)

        # create the roles:
        for i, role_info in enumerate(propnet.role_infos):
            args = (i, role_info.role,
                    role_info.inputs[0].cid,
                    # XXX another hack...
                    role_info.legals[0].cid if role_info.legals else -1,
                    role_info.goals[0].cid if role_info.goals else 0,
                    len(role_info.inputs),
                    len(role_info.goals))
            self.set_role(*args)

        # create component and outputs:
        components_outs_count = 0
        for cid in sorted(propnet.components):
            c = propnet.components[cid]
            assert len(c.inputs) <= MAX_FAN_OUT_SIZE
            args = (cid, c.required_count_false, c.required_count_true,
                    components_outs_count, len(c.outputs), c.count, c.increment_multiplier, c.topological_order)

            if self.verbose:
                if c.component_type == PROPOSITION and c.meta.is_input:
                    print "-->", c

            self.set_component(*args)

            sorted_outputs = c.outputs[:]
            sorted_outputs.sort(key=lambda x: x.cid, reverse=False)

            for o in sorted_outputs:
                assert o.cid < len(propnet.components)
                self.set_output(components_outs_count, o.cid)
                components_outs_count += 1

            self.set_output(components_outs_count, -1)
            components_outs_count += 1

        assert components_outs_count == sum(get_number_outputs(c) for c in propnet.components.values())

        # finalize components / outputs:
        total_control_flow = 0
        for c in propnet.components.values():
            if c.component_type in (AND, OR, NOT):
                total_control_flow += 1
        self.record_finalise(total_control_flow, propnet.terminal_proposition.cid)

        # set the meta information:
        for cid in sorted(propnet.components):
            c = propnet.components[cid]
            if c.component_type == PROPOSITION:
                goal_value = c.meta.goal_value if c.meta.goal_value is not None else -1
                move = str(c.meta.move) if c.meta.move is not None else ""
                self.set_meta_proposition(c.cid, c.typename, str(c.meta.gdl), move, goal_value)
            elif c.component_type == TRANSITION:
                gdl = c.fish_gdl()
                self.set_meta_transition(c.cid, c.typename, str(gdl))

            else:
                self.set_meta_component(c.cid, c.typename)

        # and do initial state
        self.add_roles(propnet)
        self.do_initial_state(propnet)

###############################################################################

def build_goals_only_sm(propnet):
    from ggplib import interface
    propnet = propnet.dupe()

    log.info("Building terminal/goal based state machine")
    goal_builder = Builder(interface, verbose=False)

    if DEBUG:
        print "Stripping inputs"
    propnet.strip_inputs()
    s = propnet.all_inbound().union(propnet.all_outbound(do_legals=False,
                                                         do_transitions=False))
    propnet.unlink_deadends(s)

    # this is hacking things too much XXX
    propnet.transitions = []
    for ri in propnet.role_infos:
        ri.legals = []
    if DEBUG:
        print "goal builder - final optimze"
    propnet.ensure_valid()
    propnet.optimize()

    propnet.print_summary()
    print

    goal_builder.do_build(propnet)
    return goal_builder.sm


def build_combined_state_machine(propnet):
    from ggplib.statemachine.forwards import FwdStateMachineAnalysis, depth_charges
    from ggplib.statemachine.controls import do_we_have_control_bases, get_control_flow_states, ControlBase

    from ggplib.propnet import trace

    log.info("Building combined based state machine")

    controls = trace.get_controls(propnet)

    loop_controls = get_control_flow_states(controls)
    if len(loop_controls) == 1:
        loop_control = loop_controls.pop()
        control_bases = ControlBase(list(loop_control.bases), strip_goals=True)
        return build_combined_state_machine_refactoring(propnet.dupe(), control_bases)

    # elif len(loop_controls) == 2:
    #    split_network_1 = do_split_network(propnet, loop_controls, 0, 1)
    #    split_network_2 = do_split_network(propnet, loop_controls, 1, 0)

    # fall back to statistical methods
    test_sm = FwdStateMachineAnalysis(propnet)

    # run for 1 second
    if DEBUG:
        print 'Start', test_sm
    depth_charges(test_sm, 1)

    # determine most used props
    most_used_props = [(sum(visits for visits, _ in x.store_propagates), x)
                       for x in propnet.base_propositions + propnet.input_propositions]
    most_used_props.sort(reverse=True)
    control_bases = do_we_have_control_bases(propnet, most_used_props, strip_goals=True)
    if DEBUG:
        print "CONTROL_BASES:", control_bases
    if not control_bases:
        return None

    return build_combined_state_machine_refactoring(propnet.dupe(), control_bases, strip_goals=True)


def build_combined_state_machine_refactoring(propnet, control_bases, strip_goals=True):
    from ggplib import interface
    from ggplib.statemachine.forwards import FwdStateMachineAnalysis, FwdStateMachineCombined, play_comparison
    test_sm = FwdStateMachineAnalysis(propnet)
    test_sm.update_bases(propnet.get_initial_state())

    control_bases.constant_propagate(propnet)

    goal_propnet = None
    if strip_goals:
        goal_propnet = propnet.dupe()
    combined_py_sm = FwdStateMachineCombined(control_bases.networks, goal_propnet=goal_propnet)
    success = True
    try:
        # test it for second
        end_time = time.time() + 1.0
        count = 0
        while time.time() < end_time:
            play_comparison(combined_py_sm, test_sm, verbose=False)
            count += 1
    except Exception, exc:
        print exc
        traceback.print_exc()
        success = False

    if not success:
        log.warning("Failed to run sucessful rollouts in combined statemachine")
        return None

    log.info("Ok played for one second in combined statemachine, did %s sucessful rollouts" % count)

    if strip_goals:
        goal_sm = build_goals_only_sm(propnet)
    else:
        goal_sm = None

    controls = []
    for p in control_bases.networks:
        b = Builder(interface, verbose=False)
        b.do_build(p)
        controls.append((p.fixed_base.cid, b.sm))

    return interface.CombinedStateMachine(goal_sm, controls)


def build_goaless_sm(propnet):
    from ggplib import interface
    propnet = propnet.dupe()
    goal_sm = build_goals_only_sm(propnet)

    # strip goals in propnet
    propnet = propnet.dupe()
    propnet.unlink_deadends(propnet.all_set_without_goals())

    # manually have to remove these (XXX - ughh) ZZZXXXZZZZ remove these lines.  Was this just to
    # make the reorder_components() work?  we need to dupe_no_goals() - where goals that are
    # dependent on something, need to be replaced with ors
    for r in propnet.role_infos:
        old_goals = r.goals
        r.goals = []
        for g in old_goals:
            if g.cid in propnet.components:
                r.goals.append(g)

    propnet.ensure_valid()

    builder2 = Builder(interface, verbose=False)
    builder2.do_build(propnet)
    goalless_sm = builder2.sm

    role_count = len(propnet.role_infos)
    return interface.GoallessStateMachine(role_count,
                                          goalless_sm,
                                          goal_sm)


def build_standard_sm(propnet):
    from ggplib import interface
    propnet = propnet.dupe()
    builder = Builder(interface, verbose=False)
    builder.do_build(propnet)
    return builder.sm

###############################################################################

def build_sm(propnet, combined=True):
    role_count = len(propnet.role_infos)

    sm = None
    if combined and role_count == 2:
        # this is a try except because we can fail for any that doesn't have controls...
        # XXX this is unclean.  Better to return None from build_combined_state_machine
        try:
            sm = build_combined_state_machine(propnet)
        except Exception, exc:
            print exc
            traceback.print_exc()

    if sm is None:
        sm = build_goaless_sm(propnet)
        # sm = build_standard_sm(propnet)

    return sm
