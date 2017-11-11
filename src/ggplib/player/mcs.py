import math
import time
import random

from ggplib.statemachine import builder
from ggplib.player.base import MatchPlayer


class MoveStat:
    def __init__(self, choice, move, role_count):
        self.choice = choice
        self.move = move
        self.scores = [0.0 for ii in range(role_count)]
        self.visits = 0

    def get(self, role_index):
        # avoid division by zero
        if self.visits == 0:
            return 0.0

        return (self.scores[role_index] / self.visits) / 100.0

    def add(self, scores):
        for ri, score in enumerate(scores):
            self.scores[ri] += float(score)
        self.visits += 1


class McsPlayerMeta:
    """ McsPlayerMeta, is just a player without any match state.  This is how all our players
        should be! """

    max_run_time = -1
    max_iterations = -1

    def __init__(self, propnet, our_role_index):
        # try creating a combined state machine, if that fails return a standard statemachine
        self.sm = builder.build_combined_state_machine(propnet)
        if self.sm is None:
            self.sm = builder.build_standard_sm(propnet)

        self.our_role_index = our_role_index
        self.role_count = len(self.sm.get_roles())

        # get and cache fast move and legals
        self.joint_move = self.sm.get_joint_move()
        self.depth_charge_joint_move = self.sm.get_joint_move()
        self.depth_charge_state = self.sm.new_base_state()

        self.current_state = None

        self.ucb_constant = random.gauss(1.2, 0.2)

    def do_depth_charge(self):
        # performs the simplest depth charge, returning our score
        self.sm.update_bases(self.depth_charge_state)

        while True:
            if self.sm.is_terminal():
                break

            # randomly assign move for each player
            for idx, r in enumerate(self.sm.get_roles()):
                ls = self.sm.get_legal_state(idx)
                choice = ls.get_legal(random.randrange(0, ls.get_count()))
                self.depth_charge_joint_move.set(idx, choice)

            # play move
            self.sm.next_state(self.depth_charge_joint_move, self.depth_charge_state)
            self.sm.update_bases(self.depth_charge_state)

        # we are only intereted in our score
        return [self.sm.get_goal_value(ii) for ii in range(self.role_count)]

    def select_move(self, choices, visits, all_scores):
        # here we build up a list of possible candidates, and then return on of them randomly.
        # Most of the time there will only be one candidate.

        candidates = []

        # add any choices, where it hasn't played at least 3 times
        for c in choices:
            stat = all_scores[c]
            if stat.visits < 3:
                candidates.append(c)

        if not candidates:
            best_score = -1
            log_visits = math.log(visits)
            for c in choices:
                stat = all_scores[c]

                # we can be assured that having no candidates means stat.visits >= 3
                score = stat.get(self.our_role_index) + self.ucb_constant * math.sqrt(log_visits / stat.visits)
                if score < best_score:
                    continue

                if score > best_score:
                    best_score = score
                    candidates = []

                candidates.append(c)

        assert candidates
        return random.choice(candidates)

    def perform_mcs(self, finish_by):
        self.depth_charge_state.assign(self.current_state)
        self.sm.update_bases(self.depth_charge_state)

        ls = self.sm.get_legal_state(self.our_role_index)
        our_choices = [ls.get_legal(ii) for ii in range(ls.get_count())]

        if len(our_choices) == 1:
            choice = our_choices[0]
            move = self.sm.legal_to_move(self.our_role_index, choice)
            # ZZZZZZ this is too much of a hack
            if "noop" in move:
                return MoveStat(choice, move, self.role_count)

        # now create some stats with depth charges
        all_scores = {}
        for choice in our_choices:
            move = self.sm.legal_to_move(self.our_role_index, choice)
            all_scores[choice] = MoveStat(choice, move, self.role_count)

        root_visits = 1
        while True:
            if time.time() > finish_by:
                break

            if self.max_iterations > 0 and root_visits > self.max_iterations:
                break

            # return to current state
            self.depth_charge_state.assign(self.current_state)
            self.sm.update_bases(self.depth_charge_state)

            assert not self.sm.is_terminal()

            # select and set our move
            choice = self.select_move(our_choices, root_visits, all_scores)
            self.joint_move.set(self.our_role_index, choice)

            # and a random move from other players
            for idx, r in enumerate(self.sm.get_roles()):
                if idx != self.our_role_index:
                    ls = self.sm.get_legal_state(idx)
                    choices = [ls.get_legal(ii) for ii in range(ls.get_count())]

                    # only need to set this once :)
                    self.joint_move.set(idx, choices[random.randrange(0, ls.get_count())])

            # create a new state
            self.sm.next_state(self.joint_move, self.depth_charge_state)

            # do a depth charge, and update scores
            scores = self.do_depth_charge()
            all_scores[choice].add(scores)

            # and update the number of visits
            root_visits += 1

        best_score = -1
        best_selection = None

        # 5% of time a complete random choice (honestly, we should sample from moves)
        sample_visits_move = random.randrange(root_visits)
        sample_selection = None
        acc_visits = 0

        print("Total visits", root_visits)
        # ok - now we dump everything for debug, and return the best score
        for stat in sorted(all_scores.values(), key=lambda x: x.get(self.our_role_index), reverse=True):
            score_str = " / ".join(("%.2f" % stat.get(ii)) for ii in range(self.role_count))
            print("Move %s, visits %d, scored %s" % (stat.move, stat.visits, score_str))

            if sample_selection is None:
                acc_visits += stat.visits
                if acc_visits > sample_visits_move:
                    sample_selection = stat

            s = stat.get(self.our_role_index)
            if s > best_score:
                best_score = s
                best_selection = stat

        print("chose", sample_selection.move)

        assert best_selection is not None, "WTF best_selection should never be None"
        return best_selection

    def set_current_state(self, state):
        self.current_state = state

    def on_meta_gaming(self, finish_time):
        assert self.current_state is not None

    def on_apply_move(self, move):
        assert self.current_state is not None

    def on_next_move(self, finish_time):
        assert self.current_state is not None

        self.sm.update_bases(self.current_state)

        # all our choices
        ls = self.sm.get_legal_state(self.our_role_index)
        choices = [ls.get_legal(ii) for ii in range(ls.get_count())]

        if len(choices) == 1:
            # single choice
            choice = choices[0]

        else:
            cur_time = time.time()
            if self.max_run_time > 0 and cur_time + self.max_run_time < finish_time:
                finish_time = cur_time + self.max_run_time

            # run monte carlo sims
            choice = self.perform_mcs(finish_time).choice

        return choice


class MCSPlayer(MatchPlayer):
    def reset(self, match):
        MatchPlayer.reset(self, match)
        self.match = self.match

    def on_meta_gaming(self, finish_time):
        self.meta = McsPlayerMeta(self.match.propnet, self.match.our_role_index)
        self.meta.set_current_state(self.match.get_current_state())
        self.meta.on_meta_gaming(finish_time)

    def on_apply_move(self, move):
        self.meta.on_apply_move(move)

    def on_next_move(self, finish_time):
        self.meta.set_current_state(self.match.get_current_state())
        return self.meta.on_next_move(finish_time)

