import time
from pprint import pprint

from ggplib.util import log, symbols

from ggplib.propnet.constants import PROPOSITION, MAX_FAN_OUT_SIZE
from ggplib.propnet.factory import ConstantPropagator
from ggplib.propnet import trace

from ggplib.statemachine.forwards import FwdStateMachineAnalysis, FwdStateMachineCombined, depth_charges, play_comparison


DEBUG = False

###############################################################################

class ControlBase:
    def __init__(self, bases, strip_goals):
        self.bases = bases
        self.strip_goals = strip_goals

        # the result of constant_propagate()
        self.networks = []

    def constant_propagate(self, propnet):
        count = 0
        while count < len(self.bases):
            log.info("splitting network for %s " % self.bases[count])

            # dupe the propnet
            split_propnet = propnet.dupe()
            if self.strip_goals:
                if DEBUG:
                    print 'removing goals from network'
                    split_propnet.print_summary()

                split_propnet.unlink_deadends(split_propnet.all_set_without_goals())
                split_propnet.ensure_valid()
                if DEBUG:
                    split_propnet.print_summary()

                # manually have to remove these (XXX - ughh) ZZZXXXZZZZ remove these lines.  Was
                # this just to make the reorder_components() work?  we need to dupe_no_goals() -
                # where goals that are dependent on something, need to be replaced with ors
                for r in split_propnet.role_infos:
                    old_goals = r.goals
                    r.goals = []
                    for g in old_goals:
                        if g.cid in split_propnet.components:
                            r.goals.append(g)

                split_propnet.optimize()

            cp = ConstantPropagator(split_propnet)

            # set this one to true
            s = split_propnet.components[self.bases[count].cid]
            if DEBUG:
                print 'SETTING TRUE', s
            cp.constant_propagate(s, 1)
            split_propnet.verify()
            # # set the rest to false
            index = 0
            while index < len(self.bases):
                if index != count:
                    b = split_propnet.components[self.bases[index].cid]
                    if DEBUG:
                        print 'SETTING FALSE', b
                    cp.constant_propagate(b, 0)
                    split_propnet.verify()
                    if DEBUG:
                        print
                index += 1

            count += 1

            split_propnet.fixed_base = s
            split_propnet.optimize(all_features=True)
            split_propnet.breakup_large_inputs()
            split_propnet.optimize()

            # ugh, well ok then
            for c in split_propnet.components.values():
                assert len(c.inputs) <= MAX_FAN_OUT_SIZE

            # now we go through all our components and back_propagate everything
            comps = [c for c in split_propnet.components.values() if not c.outputs and c.inputs]
            split_propnet.do_backpropagate_on(comps)

            # need to do this again
            split_propnet.topological_ordering()
            split_propnet.verify()
            split_propnet.print_summary()
            self.networks.append(split_propnet)

        assert len(self.networks) == len(self.bases)


def do_we_have_control_bases(propnet, most_used_props, strip_goals=True):
    " heuristically try to establish if this is a control base ? "
    most_used_bases = [p for t, p in most_used_props if p in propnet.base_propositions]
    control_propositions = {}

    for b in propnet.base_propositions:
        gdl = b.meta.gdl
        if isinstance(gdl, symbols.ListTerm):
            assert len(gdl) == 2
            base_gdl = gdl[1]
            if isinstance(base_gdl, symbols.ListTerm) and len(base_gdl) == 2 and base_gdl[1] in propnet.roles:
                control_propositions.setdefault(base_gdl[0], []).append((base_gdl, b))
    print "do_we_have_control_bases?"
    print control_propositions
    print
    best = None
    for name, bases in control_propositions.items():
        if len(bases) == len(propnet.roles):
            print "'%s' is a control base" % name
            print 'ok, are these propositions top of the bases?'
            total = 0
            count = 0
            for _, b in bases:
                if b in most_used_bases[:len(propnet.roles) * 2]:
                    count += 1
                    total += sum(visits for visits, _ in b.store_propagates)
            if count == len(bases):
                print "YES - checking control base proposition", name, total
                new_control = ControlBase([b for x, b in bases], strip_goals)

                # for 'YAY!' debug below
                new_control.control_name = name

                # this is the total number of pushes per input (proposition), as we want to use the best
                new_control.total_pushes = total

                if best is None or new_control.total_pushes > best.total_pushes:
                    best = new_control

    if best:
        print "YAY!", best.control_name
    return best


# ok, bucket the loops into seperate maps
class ControlFlowLoop:
    def __init__(self):
        self.bases = set()
        self.dependencies = {}


def get_control_flow_states(controls, verbose=False):
    # XXX this is function needs broken up
    dependencies = {}
    for t in controls.values():
        # only interested in transitions that have an input (cases where they don't are like (step 1)
        if not t.inputs:
            continue

        i = t.inputs[0]

        # must only be dependent only on one base proposition
        if i.component_type != PROPOSITION or not i.meta.is_base:
            continue

        base = t.base_proposition
        dependencies[base] = i

    # we look for anything that is dependent on something else.  We end up with just things that loops.
    while True:
        did_something = False
        for c in dependencies.keys():
            if dependencies[c] not in dependencies:
                del dependencies[c]
                did_something = True
                break
        if not did_something:
            break

    if verbose:
        pprint(dependencies)

    loop_map = {}
    for k, v in dependencies.items():
        if verbose:
            print "Doing", k

        if k not in loop_map and v not in loop_map:
            loop = ControlFlowLoop()
            loop_map[k] = loop
            loop_map[v] = loop

        else:
            if k in loop_map:
                loop = loop_map[k]
                if v in loop_map:
                    l2 = loop_map[v]
                    # ah shucks, merge it
                    if loop != l2:
                        if verbose:
                            print "MERGEING"
                        for b in l2.bases:
                            loop.bases.add(b)
                            loop_map[b] = loop

                        for kk, vv in l2.dependencies.items():
                            loop.dependencies[kk] = vv

            else:
                loop = loop_map[v]
                loop_map[k] = loop

        loop.bases.add(k)
        loop.bases.add(v)
        assert k not in loop.dependencies
        loop.dependencies[k] = v

    if verbose:
        print "____________________"

    loop_controls = set(loop_map.values())
    if verbose:
        for l in loop_controls:
            print "loop map:"
            pprint(l.bases)
            pprint(l.dependencies)
            print
            print
            print

    return loop_controls

###############################################################################

def print_most_used_props(propnet, show_count=10):
    most_used_props = [(sum(visits for visits, _ in x.store_propagates), x)
                       for x in propnet.base_propositions + propnet.input_propositions]
    most_used_props.sort(reverse=True)
    count = 0
    for total, prop in most_used_props:
        num_visits = len(prop.store_propagates)
        av_visits = (sum(visits for visits, _ in prop.store_propagates) / num_visits if num_visits else 0)
        av_fanning = (sum(fannings for _, fannings in prop.store_propagates) / num_visits if num_visits else 0)
        print "%s %s av %s/%s " % (total, prop, av_visits, av_fanning)
        count += 1
        if count > show_count:
            break

    # XXX hack to keep things working
    return most_used_props


def get_control_bases(propnet):
    controls = trace.get_controls(propnet)

    loop_controls = get_control_flow_states(controls)
    if len(loop_controls) == 1:
        loop_control = loop_controls.pop()
        control_bases = ControlBase(list(loop_control.bases), strip_goals=True)
        return control_bases

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


def get_and_test_control_bases(propnet):
    try:
        control_bases = get_control_bases(propnet)
        if control_bases is None:
            return None

        test_sm = FwdStateMachineAnalysis(propnet)
        test_sm.update_bases(propnet.get_initial_state())

        control_bases.constant_propagate(propnet)

        # this is some kind of hack??? XXX
        goal_propnet = propnet.dupe()


        combined_py_sm = FwdStateMachineCombined(control_bases.networks,
                                                 goal_propnet=goal_propnet)
        success = True

        # test it for second
        end_time = time.time() + 1.0
        count = 0
        while time.time() < end_time:
            play_comparison(combined_py_sm, test_sm, verbose=False)
            count += 1

    except Exception, exc:
        import traceback
        print exc
        traceback.print_exc()
        success = False

    if not success:
        log.warning("Failed to run sucessful rollouts in combined statemachine")
        return None

    log.info("Ok played for one second in combined statemachine, did %s sucessful rollouts" % count)

    return control_bases
