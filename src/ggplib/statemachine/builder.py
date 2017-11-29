import traceback

import json

from ggplib.util import log
from ggplib import interface
from ggplib.propnet.constants import (OR, AND, NOT, PROPOSITION,
                                      TRANSITION, MAX_FAN_OUT_SIZE)
from ggplib.propnet import getpropnet
from ggplib.statemachine.controls import get_and_test_control_bases
from ggplib.statemachine.model import StateMachineModel

class BuilderBase:
    ''' Just prints what it would do '''

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

    def set_initial_state(self, initial_state):
        print("initial_state: %s" % (initial_state,))

    def finalise(self, control_flows, terminal_index):
        print("********")
        print("finalise - control_flows %d, terminal_index %d" % (control_flows, terminal_index))
        print("********")
        print("")
        return None

class BuilderDescription(BuilderBase):
    ''' Builds a dictionary description of the statemachine.  Can be sent via json to build
        remotely. '''
    def __init__(self):
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

    def set_initial_state(self, initial_state):
        # python list of 0 and 1s
        self.initial_state = initial_state

    def finalise(self, control_flows, terminal_index):
        return dict(create=self.create_dict,
                    roles=self.roles,
                    metas=self.metas,
                    components=self.components,
                    outputs=self.outputs,
                    initial_state=self.initial_state,
                    control_flows=control_flows,
                    terminal_index=terminal_index)


def do_build(propnet, the_builder=None):
    ''' takes propnet and does some building (depends on the_builder) '''

    if the_builder is None:
        the_builder = BuilderDescription()

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

    the_builder.set_initial_state(propnet.get_initial_state())

    return the_builder.finalise(total_control_flow, propnet.terminal_proposition.cid)


###############################################################################

def build_standard_sm(propnet):
    return do_build(propnet.dupe())


def build_goals_only_sm(propnet):
    propnet = propnet.dupe()

    log.info("Building terminal/goal based state machine")

    propnet.strip_inputs()
    s = propnet.all_inbound().union(propnet.all_outbound(do_legals=False,
                                                         do_transitions=False))
    propnet.unlink_deadends(s)

    # this is hacking things too much XXX
    propnet.transitions = []
    for ri in propnet.role_infos:
        ri.legals = []
    propnet.ensure_valid()
    propnet.optimize()

    propnet.print_summary()

    return do_build(propnet)


def build_goalless_sm(propnet):
    goal_sm_result = build_goals_only_sm(propnet.dupe())

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

    goalless_sm_result = do_build(propnet)

    return dict(role_count=len(propnet.role_infos),
                goal_sm=goal_sm_result,
                goalless_sm=goalless_sm_result)


def build_combined_state_machine(propnet):
    control_bases = get_and_test_control_bases(propnet)
    if control_bases is None:
        return None

    log.info("Building combined based state machine")

    # create and add goal statemachine
    goal_sm_result = build_goals_only_sm(propnet)

    control_sms_result = []
    for idx, p in enumerate(control_bases.networks):
        sm_desc = do_build(p)

        # attach some extra info (easiest to process in c++)
        sm_desc["idx"] = idx
        sm_desc["control_cid"] = p.fixed_base.cid
        control_sms_result.append(sm_desc)

    return dict(num_controls=len(control_sms_result),
                goal_sm=goal_sm_result,
                control_sms=control_sms_result)


###############################################################################
# the api to getting statemachine.  No propnet downwind of this.
###############################################################################

def build_sm(gdl_str,
             try_combined=True,
             no_goalless=False,
             the_game_store=None,
             add_to_game_store=None):

    # bypasses everything below
    if the_game_store is not None:
        if the_game_store.file_exists("sm_info.json"):
            sm_info = the_game_store.load_json("sm_info.json")
            preferred = sm_info['preferred']

            model = StateMachineModel()
            model.from_description(sm_info["model"])

            if preferred == "standard":
                json_str = the_game_store.load_contents("standard_sm.json")
                sm = interface.create_statemachine(json_str, model.roles)

            elif preferred == "goalless":
                json_str = the_game_store.load_contents("goalless_sm.json")
                sm = interface.create_goalless_statemachine(json_str, model.roles)

            elif preferred =="combined":
                json_str = the_game_store.load_contents("combined_sm.json")
                sm = interface.create_combined_statemachine(json_str, model.roles)

            else:
                assert False, "WHAT IS THIS? %s" % preferred

            return model, sm


    propnet = getpropnet.get_with_gdl(gdl_str)
    role_count = len(propnet.role_infos)

    model = StateMachineModel()
    model.from_propnet(propnet)

    sm = None
    json_str = None
    preferred = None

    # guess and see
    if try_combined and role_count == 2:
        desc = build_combined_state_machine(propnet)
        if desc:
            json_str = json.dumps(desc)
            sm = interface.create_combined_statemachine(json_str, model.roles)
            preferred = "combined"

    if sm is None:
        if no_goalless:
            desc = build_standard_sm(propnet)
            json_str = json.dumps(desc)
            sm = interface.create_statemachine(json_str, model.roles)
            preferred = "standard"
        else:
            desc = build_goalless_sm(propnet)
            json_str = json.dumps(desc)
            sm = interface.create_goalless_statemachine(json_str, model.roles)
            preferred = "goalless"

    assert sm is not None and json_str is not None and preferred is not None

    if the_game_store is not None and add_to_game_store:

        sm_info_desc = dict(preferred=preferred,
                            model=model.to_description())

        filename_map = dict(standard="standard_sm.json",
                            goalless="goalless_sm.json",
                            combined="combined_sm.json")

        the_game_store.save_contents(filename_map[preferred], json_str)
        the_game_store.save_json("sm_info.json", sm_info_desc)

    return model, sm
