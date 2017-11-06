from ggplib.util import log

class MatchPlayer:
    ' defines interface '
    def __init__(self, name=None):
        if name is None:
            name = str(self.__class__.__name__)
        self.name = name
        self.match = None

    def get_name(self):
        return self.name

    def reset(self, match):
        log.info("Player reset with %s" % match.match_id)
        self.match = match

    def on_meta_gaming(self, finish_time):
        pass

    def on_apply_move(self, move):
        pass

    def on_next_move(self, finish_time):
        assert False, "Not implemented"

    def cleanup(self):
        ' clean up any memory allocated, etc '
        pass

class RandomPlayer(MatchPlayer):
    ' plays randomly '

    def on_next_move(self, finish_time):
        import time
        import random

        # get the statemachine...
        sm = self.match.sm

        # constraint: state machine will be correct
        ls = sm.get_legal_state(self.match.our_role_index)

        # a random choice
        return ls.get_legal(random.randrange(0, ls.get_count()))

