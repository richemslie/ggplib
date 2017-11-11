''' bunch of spurious state machines.  Needs lot of rationalisation and commenting.  Completely out
    of whack with c++ statemachines. '''

import time
import random
from ggplib.propnet.constants import NOT

DEBUG = False


class FwdStateMachineBase:

    def __init__(self, propnet):
        self.propnet = propnet

    def update_bases(self, base_map):
        for p, b in zip(self.propnet.base_propositions, base_map):
            self.propagate(p, b)

    def reset(self):
        self.update_bases(self.propnet.get_initial_state())

    def get_legal_moves(self, role_info):
        return [l for l in role_info.legals if l.count]

    def is_terminal(self):
        return self.propnet.terminal_proposition.count

    def goal_value(self, role):
        for g in self.propnet.goal_propositions[role]:
            if g.count:
                return g.meta.goal_value
        return -1

    def get_next_state(self, inputs):
        for p in inputs:
            self.propagate(p, 1)

        result = [p.count for p in self.propnet.transitions]

        for p in inputs:
            self.propagate(p, 0)

        return result

    def __repr__(self):
        state = [p.count for p in self.propnet.base_propositions]
        return self.propnet.to_gdl(state)


class FwdStateMachine(FwdStateMachineBase):
    ''' this was supposedly the fastest (but the clearest way) to do propagation when we wrote this thing. '''

    def propagate(self, component, value):
        if value != component.count:
            component.count = value

            if value:
                self.forward_propagate_positive(component.outputs)
            else:
                self.forward_propagate_negative(component.outputs)

    def forward_propagate_positive(self, outputs):
        # CONSTRAINT: only called if propagation is required

        for o in outputs:
            t = o.component_type
            o.count += 1
            if t < 5:
                if o.count == o.required_count_true and o.outputs:
                    self.forward_propagate_positive(o.outputs)

            elif t == NOT:
                self.forward_propagate_negative(o.outputs)

            else:
                assert False, "What is this? %s" % o

    def forward_propagate_negative(self, outputs):
        # CONSTRAINT: only called if propagation is required

        for o in outputs:
            t = o.component_type
            o.count -= 1
            if t < 5:
                if o.count == o.required_count_false and o.outputs:
                    self.forward_propagate_negative(o.outputs)

            elif t == NOT:
                self.forward_propagate_positive(o.outputs)

            else:
                assert False, "What is this? %s" % o


class FwdStateMachineAnalysis(FwdStateMachineBase):
    def __init__(self, propnet):
        for c in propnet.components.values():
            c.store_propagates = []
            c.count_visits = 0
            c.count_fanning = 0
            c.requires = [c.required_count_false, 0, c.required_count_true]
        FwdStateMachineBase.__init__(self, propnet)

    def dump_visits_counts(self):
        total_fannings = [(c.count_visits * (len(c.outputs) or 1), c) for c in self.components.values()]
        total_fannings.sort(reverse=True)
        for t in total_fannings:
            print t

    def propagate(self, component, value):
        if value != component.count:
            component.count = value
            self.count_visits = 1
            self.count_fanning = 0

            self.forward_propagate(component, value)
            component.store_propagates.append((self.count_visits, self.count_fanning))

    def forward_propagate(self, component, value):
        # CONSTRAINT: only called if propagation is required
        if value:
            self.forward_propagate_positive(component.outputs)
        else:
            self.forward_propagate_negative(component.outputs)

    def forward_propagate_positive(self, outputs):
        # CONSTRAINT: only called if propagation is required

        self.count_visits += 1
        for o in outputs:
            self.count_fanning += 1
            t = o.component_type
            o.count += 1
            if t < 5:
                if o.count == o.required_count_true and o.outputs:
                    o.count_visits += 1
                    self.forward_propagate_positive(o.outputs)

            elif t == NOT:
                o.count_visits += 1
                self.forward_propagate_negative(o.outputs)

            else:
                assert False, "What is this? %s" % o

    def forward_propagate_negative(self, outputs):
        # CONSTRAINT: only called if propagation is required

        self.count_visits += 1
        for o in outputs:
            self.count_fanning += 1
            t = o.component_type
            o.count -= 1
            if t < 5:
                if o.count == o.required_count_false and o.outputs:
                    o.count_visits += 1
                    self.forward_propagate_negative(o.outputs)

            elif t == NOT:
                o.count_visits += 1
                self.forward_propagate_positive(o.outputs)

            else:
                assert False, "What is this? %s" % o


###############################################################################

class FwdStateMachine2(FwdStateMachine):
    def propagate(self, component, value):
        if value != component.count:
            component.count = value
            print 'need to propagte ', component
            self.forward_propagate(component, value)

    def forward_propagate(self, component, value):
        # CONSTRAINT: only called if propagation is required
        self.forward_propagate_value(component, 1 if value else -1)

    def forward_propagate_value(self, component, incr, depth=0):
        print " " * depth + "fwd_prop cid:%d, count %d, incr %d, outputs %d" % (component.cid,
                                                                                component.count,
                                                                                incr,
                                                                                len(component.outputs))

        # CONSTRAINT: only called if propagation is required

        for o in component.outputs:
            new_count = o.count + incr
            assert new_count >= 0
            o.count = new_count

            # XXX setting key value to zero, and using did we propagate
            test = o.requires[incr + 1]
            print "%stesting to cid:%d, test %d/%d" % (" " * (depth + 1), o.cid, o.count, test)
            if new_count == test and o.outputs:
                self.forward_propagate_value(o, incr * o.increment_multiplier, depth + 1)


class FwdStateMachine2_2(FwdStateMachine2):
    def forward_propagate_value(self, component, incrx):
        'non-recursive version of forward_propagate_value1'
        # CONSTRAINT: only called if propagation is required
        todo = [(ox, incrx) for ox in component.outputs]
        for x in todo:
            print 'adding1', (x, incrx)

        while todo:
            print "#outputs", len(todo)
            o, incr = todo.pop()
            print o, incr
            new_count = o.count + incr
            o.count = new_count

            test = o.requires[incr + 1]
            if new_count == test:
                new_increment = incr * o.increment_multiplier
                for o2 in o.outputs:
                    print "adding2", (o2, new_increment)
                    todo.append((o2, new_increment))


class FwdStateMachine2_3(FwdStateMachine2):
    def propagate(self, component, value):
        if value != component.count:
            component.count = value
            self.forward_propagate_value(component.outputs, 1 if value else -1)

    def forward_propagate_value(self, outputs, incrx):
        'propagates breadth wise, instead of depth wise'
        # CONSTRAINT: only called if propagation is required
        todo = [(outputs, incrx)]
        while todo:
            outputs, incr = todo.pop()
            for o in outputs:
                o.count += incr
                if o.count == o.requires[incr + 1]:
                    todo.append((o.outputs, incr * o.increment_multiplier))

######################################################################

class Level:
    def __init__(self, capacity):
        self.size = 0
        self.components = [None] * capacity

    def __repr__(self):
        return str((self.size, self.components))


class FwdStateMachine3(FwdStateMachine):

    def __init__(self, propnet):
        FwdStateMachine.__init__(self, propnet)
        s = len(self.propnet.components)
        self.context = [Level(s) for _ in range(self.propnet.topological_size)]

    def update_bases(self, base_map):
        level = self.context[0]
        assert level.size == 0
        for base, value in zip(self.propnet.base_propositions, base_map):
            if value != base.count:
                level.components[level.size] = (base, 1 if value else -1)
                level.size += 1

        self.propagate()

    def get_next_state(self, inputs):
        level = self.context[0]

        # pass through inputs
        assert level.size == 0
        for p in inputs:
            level.components[level.size] = (p, 1)
            level.size += 1
        self.propagate()

        result = [p.count for p in self.propnet.transitions]

        assert level.size == 0
        for p in inputs:
            level.components[level.size] = (p, -1)
            level.size += 1
        self.propagate()

        return result

    # def propagate(self):
    #     context = self.context

    #     for components in context:
    #         for o, incr in components:
    #             o.count += incr
    #             if o.count == o.requires[incr + 1]:
    #                 for o2 in o.outputs:
    #                     context[o2.topological_order].append((o2, incr * o.increment_multiplier))
    #         del components[:]

    def propagate(self):
        for level in self.context:
            idx = 0
            while idx < level.size:
                o, incr = level.components[idx]
                o.count += incr
                if o.count == o.requires[incr + 1]:
                    for o2 in o.outputs:
                        next_level = self.context[o2.topological_order]
                        next_level.components[next_level.size] = (o2, incr * o.increment_multiplier)
                        next_level.size += 1
                idx += 1
            level.size = 0

###############################################################################

class FwdTraceStateMachine(FwdStateMachine2):
    def forward_propagate(self, component, count):
        # CONSTRAINT: only called if propagation is required
        assert 0 <= count <= 1
        assert component.count == count
        print 'TRACE1 +:%s - %s' % (count, component)
        self.forward_propagate_trace(component.outputs, 1 if count else -1, 1)

    def forward_propagate_trace(self, outputs, incr, depth):
        # CONSTRAINT: only called if propagation is required

        for o in outputs:
            print '    ' * depth + 'TRACE2 +:%s / %s' % (incr, o)
            new_count = o.count + incr
            o.count = new_count

            # XXX setting key value to zero, and using did we propagate
            test = o.requires[incr + 1]
            if new_count == test:
                self.forward_propagate_trace(o.outputs, incr * o.increment_multiplier, depth + 1)


class FwdStateMachineCombined(FwdStateMachine):

    def __init__(self, propnets, goal_propnet):
        FwdStateMachine.__init__(self, propnets[0])
        self.propnets = propnets
        if goal_propnet:
            self.goal_sm = FwdStateMachine(goal_propnet)
        else:
            self.goal_sm = None

        self.base_indexes = []
        for pn in self.propnets:
            count = 0
            for b in pn.base_propositions:
                if b == pn.fixed_base:
                    if DEBUG:
                        print "base index of %s for %s propnet" % (count, b)
                    self.base_indexes.append(count)
                    break
                count += 1
        assert len(self.base_indexes) == len(self.propnets)

    def update_bases(self, base_map):
        new_propnet = None
        count = 0
        for indx in self.base_indexes:
            if base_map[indx]:
                assert new_propnet is None
                new_propnet = self.propnets[count]
            count += 1

        assert new_propnet

        self.propnet = new_propnet
        FwdStateMachine.update_bases(self, base_map)

    def goal_value(self, role):
        if self.goal_sm is None:
            return FwdStateMachine.goal_value(self, role)

        # ensure goal propnet up to date
        self.goal_sm.update_bases([b.count for b in self.propnet.base_propositions])
        assert self.goal_sm.is_terminal()

        for g in self.goal_sm.propnet.goal_propositions[role]:
            if g.count:
                return g.meta.goal_value
        return -1

###############################################################################

def play_comparison(sm1, sm2, verbose=True):
    # reset
    depth = 0
    base_map = sm1.propnet.get_initial_state()

    def compare_state():
        state1 = [b.count for b in sm1.propnet.base_propositions]
        state2 = [b.count for b in sm2.propnet.base_propositions]
        assert state1 == state2

    sm1.update_bases(base_map)
    sm2.update_bases(base_map)
    compare_state()
    if verbose:
        print 'inital_state:', sm2

    while True:
        assert sm1.is_terminal() == sm2.is_terminal()
        if sm2.is_terminal():
            break

        x1 = [set(x.cid for x in sm1.get_legal_moves(ri)) for ri in sm1.propnet.role_infos]
        x2 = [set(x.cid for x in sm2.get_legal_moves(ri)) for ri in sm2.propnet.role_infos]
        assert x1 == x2, "%s == %s" % (x1, x2)
        randoms = [random.choice(range(len(x1[0]))), random.choice(range(len(x1[1])))]
        random_legals1 = [sm1.get_legal_moves(ri)[randoms[indx]] for indx, ri in enumerate(sm1.propnet.role_infos)]
        random_legals2 = [sm2.get_legal_moves(ri)[randoms[indx]] for indx, ri in enumerate(sm2.propnet.role_infos)]

        inputs1 = [p.meta.legals_input for p in random_legals1]
        inputs2 = [p.meta.legals_input for p in random_legals2]

        if verbose:
            print 'playing', inputs1
        base_map1 = sm1.get_next_state(inputs1)
        base_map2 = sm2.get_next_state(inputs2)
        assert base_map1 == base_map2, "%s == %s" % (base_map1, base_map2)

        sm1.update_bases(base_map1)
        sm2.update_bases(base_map2)
        depth += 1
        compare_state()

        if verbose:
            print "@ depth %d : %s" % (depth, sm2)

        assert depth < 1000

    # check final game state
    assert sm1.is_terminal() and sm2.is_terminal()
    for ri1, ri2 in zip(sm1.propnet.role_infos, sm2.propnet.role_infos):
        assert sm1.goal_value(ri1.role) == sm2.goal_value(ri2.role)

    if verbose:
        print "Played to depth %d" % depth

        for r in sm2.propnet.roles:
            print "Final score for %s : %s " % (r, sm2.goal_value(r))

###############################################################################

def play_verbose(sm, seconds):
    # reset
    end_time = time.time() + seconds

    while time.time() < end_time:
        base_map = sm.propnet.get_initial_state()
        sm.update_bases(base_map)
        print 'inital_state:', sm
        depth = 0
        while True:
            if sm.is_terminal():
                break

            terminate = False
            for ri in sm.propnet.role_infos:
                if not sm.get_legal_moves(ri):
                    terminate = True
                    break
            if terminate:
                print "terminate XXX"
                break

            random_legals = [random.choice(sm.get_legal_moves(ri)) for ri in sm.propnet.role_infos]
            inputs = [p.meta.legals_input for p in random_legals]

            print 'playing', inputs
            base_map = sm.get_next_state(inputs)

            sm.update_bases(base_map)
            depth += 1

            print "@ depth %d : %s" % (depth, sm)
            if depth > 200:
                break

        print "Played to depth %d" % depth
        for r in sm.propnet.roles:
            print "Final score for %s : %s " % (r, sm.goal_value(r))


def depth_charges(sm, n, state_watcher=None):
    # play for n seconds
    print "playing for %s seconds" % n
    end_time = time.time() + n
    iterations = 0
    scores = []
    depths = []

    while time.time() < end_time:
        # reset
        depth = 0
        base_map = sm.propnet.get_initial_state()
        sm.update_bases(base_map)

        while True:
            if sm.is_terminal():
                break

            random_legals = [random.choice(sm.get_legal_moves(ri)) for ri in sm.propnet.role_infos]
            inputs = [p.meta.legals_input for p in random_legals]

            base_map = sm.get_next_state(inputs)
            sm.update_bases(base_map)
            if state_watcher:
                state_watcher(base_map)
            depth += 1

        # done match
        goals = [sm.goal_value(r) for r in sm.propnet.roles]
        scores.append(goals)
        depths.append(depth)
        iterations += 1

    iterations_per_second = iterations / float(n)
    print "iterations per second", iterations_per_second
    print "average time msecs", (float(n) / iterations) * 1000
    print "average depth", sum(depths) / float(iterations)
    for idx, r in enumerate(sm.propnet.roles):
        total_score = sum(s[idx] for s in scores)
        print "average score for %s : %s" % (r, total_score / float(iterations))
    return iterations_per_second
