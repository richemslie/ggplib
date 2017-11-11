import random

from ggplib.player.base import MatchPlayer


class RandomPlayer(MatchPlayer):
    ' plays randomly '

    def on_next_move(self, finish_time):
        # get the statemachine...
        sm = self.match.sm

        # constraint: state machine will be correct
        ls = sm.get_legal_state(self.match.our_role_index)

        # a random choice
        return ls.get_legal(random.randrange(0, ls.get_count()))
