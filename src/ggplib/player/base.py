from ggplib.util import log


class MatchPlayer(object):
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
        ' note: on_meta_gaming must use self.match.get_current_state() and NOT initial_base_state '
        pass

    def on_apply_move(self, move):
        pass

    def on_next_move(self, finish_time):
        assert False, "Not implemented"

    def cleanup(self):
        ' clean up any memory allocated, etc '
        pass
