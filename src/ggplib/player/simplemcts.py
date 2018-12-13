import time
import random

from ggplib.util import log
from ggplib import interface
from ggplib.player.proxy import ProxyPlayer


class SimpleMctsPlayer(ProxyPlayer):

    skip_single_moves = True
    max_tree_search_time = 2.0
    max_memory = 1024 * 1024 * 1024 * 12
    max_tree_playout_iterations = 10000000
    max_number_of_nodes = 10000000
    ucb_constant = 1.15
    select_random_move_count = 16
    dump_depth = 2
    next_time = 2.5

    def meta_create_player(self):
        return interface.create_simple_mcts_player(self.sm,
                                                   self.match.our_role_index,
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
    max_tree_search_time = 4.0

    def wait(self, finish_time):
        # artificially slow things down (even on finalised)
        finish_time -= 2
        while True:
            if time.time() > finish_time:
                break

            time.sleep(0.25)

    def on_next_move(self, finish_time):
        res = SimpleMctsPlayer.on_next_move(self, finish_time)
        self.wait(finish_time)
        return res


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

        self.wait(finish_time)
        return res
