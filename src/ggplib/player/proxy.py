import time
import random

from ggplib.util import log
from ggplib.player.base import MatchPlayer
from ggplib.statemachine import builder
from ggplib import interface


class MatchInfo:
    def __init__(self, sm):
        self.sm = sm
        self.two_player_fixed_sum = True
        self.simultaneous_game_detected = False

        self.static_joint_move = self.sm.get_joint_move()
        self.static_basestate = self.sm.new_base_state()

    def do_basic_depth_charge(self):
        ''' identifies types of moves '''
        self.sm.reset()
        role_count = len(self.sm.get_roles())

        while True:
            if self.sm.is_terminal():
                break

            choice_counts_more_than_1 = 0
            for idx, r in enumerate(range(role_count)):
                ls = self.sm.get_legal_state(idx)
                choice = ls.get_legal(random.randrange(0, ls.get_count()))
                self.static_joint_move.set(idx, choice)

                assert ls.get_count()

                if ls.get_count() > 1:
                    choice_counts_more_than_1 += 1

            if not self.simultaneous_game_detected and choice_counts_more_than_1 > 1:
                self.simultaneous_game_detected = True

            self.sm.next_state(self.static_joint_move, self.static_basestate)
            self.sm.update_bases(self.static_basestate)

        if role_count > 1:
            total_score = 0
            for idx, _ in enumerate(self.sm.get_roles()):
                total_score += self.sm.get_goal_value(idx)

            if total_score != 100:
                self.two_player_fixed_sum = False


class CppPlayer(MatchPlayer):
    def __init__(self, name=None):
        if name is None:
            name = self.player_cpp
        MatchPlayer.__init__(self, name)
        self.proxy = None
        self.sm = None

        self.match_info = None

    def cleanup(self):
        if self.proxy:
            self.proxy.cleanup()
        self.proxy = None

    def meta_create_player(self):
        assert False, "Abstract, not implemented"

    def on_meta_gaming(self, finish_time):
        log.info("%s meta Gaming: match: %s" % (self.name, self.match.match_id))

        # try building a combined state machine (this needs work determining which is fastest etc)
        self.sm = builder.build_combined_state_machine(self.match.propnet)
        if self.sm is None:
            self.sm = builder.build_goaless_sm(self.match.propnet)

        self.proxy = interface.CppProxyPlayer(self.meta_create_player())

        # ensure we are in the right state
        self.sm.update_bases(self.match.get_current_state())
        self.proxy.on_meta_gaming(finish_time)

    def on_apply_move(self, move):
        self.sm.update_bases(self.match.get_current_state())
        self.proxy.on_apply_move(move)

    def on_next_move(self, finish_time):
        self.sm.update_bases(self.match.get_current_state())
        return self.proxy.on_next_move(finish_time)


class CppRandomPlayer(CppPlayer):
    def meta_create_player(self):
        return interface.create_random_player(self.sm, self.match.our_role_index)


class CppLegalPlayer(CppPlayer):
    def meta_create_player(self):
        return interface.create_legal_player(self.sm, self.match.our_role_index)


class SimpleMctsPlayer(CppPlayer):
    skip_single_moves = False
    max_tree_search_time = -1
    max_memory = 1024 * 1024 * 1024 * 6
    max_tree_playout_iterations = 1000000
    max_number_of_nodes = 1000000
    ucb_constant = 1.15
    select_random_move_count = 16
    dump_depth = 2
    next_time = 2.5

    def meta_create_player(self):
        role_count = len(self.sm.get_roles())
        if role_count > 1:
            info = MatchInfo(self.sm)
            for i in range(5):
                info.do_basic_depth_charge()
            # simultaneous games not supported, return random player
            if info.simultaneous_game_detected:
                return interface.create_random_player(self.sm, self.match.our_role_index)

        return interface.create_simple_mcts_player(self.sm, self.match.our_role_index,
                                                   self.skip_single_moves,
                                                   self.max_tree_search_time,
                                                   self.max_memory,
                                                   self.max_tree_playout_iterations,
                                                   self.max_number_of_nodes,
                                                   self.ucb_constant,
                                                   self.select_random_move_count,
                                                   self.dump_depth,
                                                   self.next_time)


class GGTestPlayer1(SimpleMctsPlayer):
    skip_single_moves = True
    max_tree_search_time = 3


class GGTestPlayer2(GGTestPlayer1):
    pct_of_random_moves = 0.25

    def on_next_move(self, finish_time):
        self.sm.update_bases(self.match.get_current_state())
        ls = self.sm.get_legal_state(self.match.our_role_index)

        # get move from proxy
        alternative_finish_time = min(time.time() + self.max_tree_search_time, finish_time)
        res = self.proxy.on_next_move(alternative_finish_time)

        role_count = len(self.sm.get_roles())

        # for non single player games, play a random move some % of the time
        if role_count != 1 and ls.get_count() > 1:
            if random.random() > (1.0 - self.pct_of_random_moves):
                # return statemachine to correct state (proxy will share statemachine, and it can leave it any state)
                self.sm.update_bases(self.match.get_current_state())
                old_res = res
                res = ls.get_legal(random.randrange(0, ls.get_count()))
                log.warning("PLAYING RANDOM MOVE was %s, now %s" % (old_res, res))

        # artificially slow things down (even on finalised)
        finish_time -= 2
        while True:
            if time.time() > finish_time:
                break

            time.sleep(0.5)

        return res
