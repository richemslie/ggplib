import time
import traceback

import json

from ggplib.util import log
from ggplib import interface
from ggplib.propnet.constants import OR, AND, NOT, PROPOSITION, TRANSITION, MAX_FAN_OUT_SIZE

DEBUG = False


class BuilderBase:
    ''' Just prints what it would do '''
    def __init__(self, propnet):
        self.propnet = propnet

    def create_state_machine(self, role_count, num_bases, num_transitions,
                             num_components, num_outputs, topological_size):
        print("Creating SM with role_count: %s, "
              "bases: %s, #trans %s, #comps %s, #outputs %s, topo %s" % (role_count,
                                                                         num_bases,
                                                                         num_transitions,
                                                                         num_components,
                                                                         num_outputs,
                                                                         topological_size))
        print("")

    def set_role(self, role_index, name, input_start_index, legal_start_index,
                 goal_start_index, num_inputs_legals, num_goals):
        print("Creating Role %s/%s with input/legal/goals "
              "%s/%s/%s, num inputs/goals %s/%s" % (role_index,
                                                    name,
                                                    input_start_index,
                                                    legal_start_index,
                                                    goal_start_index,
                                                    num_inputs_legals,
                                                    num_goals))
        print("")

    def set_meta_proposition(self, component_id, typename, gdl_str, move, goal_value):
        if goal_value != -1:
            print("meta %s id=%d : goal_value=%d" % (typename,
                                                     component_id,
                                                     goal_value))
        elif move != '':
            print("meta %s id=%d : gdl=%s, move=%s" % (typename,
                                                       component_id,
                                                       gdl_str,
                                                       move))
        else:
            print("meta %s id=%d : gdl=%s" % (typename,
                                              component_id,
                                              gdl_str))

    def set_meta_transition(self, component_id, typename, gdl_str):
        print("mate %s id=%d : gdl='%s'" % (typename, component_id, gdl_str))

    def set_meta_component(self, component_id, typename):
        print("meta %s id=%d" % (typename, component_id))

    def set_component(self, component_id, required_count_false, required_count_true,
                      output_index, number_outputs, initial_count, incr, topological_order):

        print("")
        print("Set id=%s -> required_counts %d/%d, output_index=%d, number_outputs=%d, "
              "initial_count=%d, incr=%d, topological_order=%d" % (component_id,
                                                                   required_count_false,
                                                                   required_count_true,
                                                                   output_index, number_outputs,
                                                                   initial_count,
                                                                   incr,
                                                                   topological_order))

    def set_output(self, output_index, component_id):
        if component_id == -1:
            component_str = "terminate"
        else:
            component_str = str(component_id)
        print("output_index(%d) -> %s" % (output_index, component_str))

    def finalise(self, control_flows, terminal_index):
        print("********")
        print("finalise - control_flows %d, terminal_index %d" % (control_flows, terminal_index))
        print("********")
        print("")
        return None


class BuilderJson(BuilderBase):
    ''' Just prints what it would do '''
    def __init__(self, propnet):
        self.propnet = propnet
        self.create_dict = None
        self.roles = []
        self.metas = []
        self.components = []
        self.outputs = []
        self.lib = interface.lib

    def create_state_machine(self, role_count, num_bases, num_transitions,
                             num_components, num_outputs, topological_size):
        self.create_dict = dict(role_count=role_count,
                                num_bases=num_bases,
                                num_transitions=num_transitions,
                                num_components=num_components,
                                num_outputs=num_outputs,
                                topological_size=num_outputs)

    def set_role(self, role_index, name, input_start_index, legal_start_index,
                 goal_start_index, num_inputs_legals, num_goals):
        r = dict(role_index=role_index,
                 name=name,
                 input_start_index=input_start_index,
                 legal_start_index=legal_start_index,
                 goal_start_index=goal_start_index,
                 num_inputs_legals=num_inputs_legals,
                 num_goals=num_goals)
        self.roles.append(r)

    def add_meta(self, component_id, typename, gdl_str="", move="", goal_value=-1):
        meta = dict(component_id=component_id,
                    typename=typename,
                    gdl_str=gdl_str,
                    move=move,
                    goal_value=goal_value)
        self.metas.append(meta)

    def set_meta_proposition(self, component_id, typename, gdl_str, move, goal_value):
        self.add_meta(component_id, typename, gdl_str=gdl_str, move=move, goal_value=goal_value)

    def set_meta_transition(self, component_id, typename, gdl_str):
        self.add_meta(component_id, typename, gdl_str=gdl_str)

    def set_meta_component(self, component_id, typename):
        self.add_meta(component_id, typename)

    def set_component(self, component_id, required_count_false, required_count_true,
                      output_index, number_outputs, initial_count, incr, topological_order):
        component = (component_id, required_count_false, required_count_true,
                     output_index, number_outputs, initial_count, incr, topological_order)
        self.components.append(component)

    def set_output(self, output_index, component_id):
        output = (output_index, component_id)
        self.outputs.append(output)

    def finalise(self, control_flows, terminal_index):
        master = dict(create=self.create_dict,
                      roles=self.roles,
                      metas=self.metas,
                      components=self.components,
                      outputs=self.outputs,
                      initial_state=self.propnet.get_initial_state(),
                      control_flows=control_flows,
                      terminal_index=terminal_index)
        log.verbose("Before dumps()")
        buf = json.dumps(master)
        log.verbose("after dumps()")

        c_statemachine = interface.create_statemachine_from_json(buf)
        log.verbose("after sm creation")

        # XXX WHY> DONT DO THIS
        # get roles and initial state
        roles = [str(ri.role) for ri in self.propnet.role_infos]

        # XXX OR THIS
        # set the initial state
        initial_base_state = interface.BaseState(self.lib.StateMachine__newBaseState(c_statemachine))

        for idx, value in enumerate(self.propnet.get_initial_state()):
            initial_base_state.set(idx, value)
            assert initial_base_state.get(idx) == value


        return interface.StateMachine(c_statemachine,
                                      initial_base_state, roles)

class BuilderCpp(BuilderBase):
    ''' calls c++ code to construct state machine '''

    def __init__(self, propnet):
        self.propnet = propnet
        self.build_sm = None
        self.lib = interface.lib
        self.c_statemachine = None

    def create_state_machine(self, role_count, num_bases, num_transitions,
                             num_components, num_outputs, topological_size):

        self.c_statemachine = self.lib.createStateMachine(role_count, num_bases, num_transitions,
                                                          num_components, num_outputs, topological_size)

    def set_role(self, role_index, name, input_start_index, legal_start_index,
                 goal_start_index, num_inputs_legals, num_goals):
        self.lib.StateMachine__setRole(self.c_statemachine, role_index, name, input_start_index,
                                       legal_start_index, goal_start_index,
                                       num_inputs_legals, num_goals)

    def set_meta_proposition(self, component_id, typename, gdl_str, move, goal_value):
        self.lib.StateMachine__setMetaComponent(self.c_statemachine, component_id,
                                                typename, gdl_str, move, goal_value)

    def set_meta_transition(self, component_id, typename, gdl_str):
        self.lib.StateMachine__setMetaComponent(self.c_statemachine, component_id, typename, gdl_str, "", -1)

    def set_meta_component(self, component_id, typename):
        self.lib.StateMachine__setMetaComponent(self.c_statemachine, component_id, typename, "", "", -1)

    def set_component(self, component_id, required_count_false, required_count_true,
                      output_index, number_outputs, initial_count, incr, topological_order):
        self.lib.StateMachine__setComponent(self.c_statemachine, component_id, required_count_false,
                                            required_count_true, output_index, number_outputs,
                                            initial_count, incr, topological_order)

    def set_output(self, output_index, component_id):
        self.lib.StateMachine__setOutput(self.c_statemachine, output_index, component_id)

    def finalise(self, control_flows, terminal_index):
        self.lib.StateMachine__recordFinalise(self.c_statemachine, control_flows, terminal_index)

        # set the initial state
        initial_base_state = interface.BaseState(self.lib.StateMachine__newBaseState(self.c_statemachine))

        for idx, value in enumerate(self.propnet.get_initial_state()):
            initial_base_state.set(idx, value)
            assert initial_base_state.get(idx) == value

        self.lib.StateMachine__setInitialState(self.c_statemachine, initial_base_state.c_base_state)
        self.lib.StateMachine__reset(self.c_statemachine)

        # XXX delete basestate or was it consumed?

        # get roles and initial state
        roles = [str(ri.role) for ri in self.propnet.role_infos]

        return interface.StateMachine(self.c_statemachine,
                                      initial_base_state, roles)


def do_build(propnet, the_builder=None):
    if the_builder is None:
        the_builder = BuilderCpp(propnet)

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

    the_builder.create_state_machine(*args)

    # create the roles:
    for i, role_info in enumerate(propnet.role_infos):
        args = (i, role_info.role,
                role_info.inputs[0].cid,
                # XXX another hack...
                role_info.legals[0].cid if role_info.legals else -1,
                role_info.goals[0].cid if role_info.goals else 0,
                len(role_info.inputs),
                len(role_info.goals))
        the_builder.set_role(*args)

    # set the meta information:
    for cid in sorted(propnet.components):
        c = propnet.components[cid]
        if c.component_type == PROPOSITION:
            goal_value = c.meta.goal_value if c.meta.goal_value is not None else -1
            move = str(c.meta.move) if c.meta.move is not None else ""
            the_builder.set_meta_proposition(c.cid, c.typename, str(c.meta.gdl), move, goal_value)
        elif c.component_type == TRANSITION:
            gdl = c.fish_gdl()
            the_builder.set_meta_transition(c.cid, c.typename, str(gdl))

        else:
            the_builder.set_meta_component(c.cid, c.typename)

    # create component and outputs:
    components_outs_count = 0
    for cid in sorted(propnet.components):
        c = propnet.components[cid]
        assert len(c.inputs) <= MAX_FAN_OUT_SIZE
        args = (cid, c.required_count_false, c.required_count_true,
                components_outs_count, len(c.outputs), c.count, c.increment_multiplier, c.topological_order)

        the_builder.set_component(*args)

        sorted_outputs = c.outputs[:]
        sorted_outputs.sort(key=lambda x: x.cid, reverse=False)

        for o in sorted_outputs:
            assert o.cid < len(propnet.components)
            the_builder.set_output(components_outs_count, o.cid)
            components_outs_count += 1

        the_builder.set_output(components_outs_count, -1)
        components_outs_count += 1

    assert components_outs_count == sum(get_number_outputs(c) for c in propnet.components.values())

    # finalize components / outputs:
    total_control_flow = 0
    for c in propnet.components.values():
        if c.component_type in (AND, OR, NOT):
            total_control_flow += 1

    return the_builder.finalise(total_control_flow, propnet.terminal_proposition.cid)


###############################################################################

def build_goals_only_sm(propnet):
    propnet = propnet.dupe()

    log.info("Building terminal/goal based state machine")

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

    return do_build(propnet)


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


# XXX think the name of this function is a hint (it is a mess)
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


    # the combined statemachine
    c_statemachine = interface.lib.createCombinedStateMachine(len(control_bases.networks))

    if strip_goals:
        # create and add goal statemachine
        goal_sm = build_goals_only_sm(propnet)
        interface.lib.CombinedStateMachine__setGoalStateMachine(c_statemachine, goal_sm.c_statemachine)

    # create and add control statemachine
    control_sm = None
    for idx, p in enumerate(control_bases.networks):
        control_sm = do_build(p)
        interface.lib.CombinedStateMachine__setControlStateMachine(c_statemachine, idx,
                                                                   p.fixed_base.cid,
                                                                   control_sm.c_statemachine)

    # this needs to be called after setting the controls
    interface.lib.StateMachine__reset(c_statemachine)

    assert control_sm is not None
    combined_sm = interface.StateMachine(c_statemachine, control_sm.get_initial_state(), control_sm.get_roles())

    return combined_sm

def build_goalless_sm(propnet):
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

    goalless_sm = do_build(propnet)

    role_count = len(propnet.role_infos)

    c_statemachine = interface.lib.createGoallessStateMachine(role_count,
                                                              goalless_sm.c_statemachine,
                                                              goal_sm.c_statemachine)

    return interface.StateMachine(c_statemachine, goal_sm.get_initial_state(), goal_sm.get_roles())


def build_standard_sm(propnet):
    propnet = propnet.dupe()
    return do_build(propnet)

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
        sm = build_goalless_sm(propnet)
        # sm = build_standard_sm(propnet)

    return sm
