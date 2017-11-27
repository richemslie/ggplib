from ggplib.util import log
from ggplib.player.base import MatchPlayer


class ProxyPlayer(MatchPlayer):
    def __init__(self, name=None):
        if name is None:
            name = self.__class__.__name__
        MatchPlayer.__init__(self, name)
        self.proxy = None
        self.sm = None

    def cleanup(self):
        if self.proxy:
            self.proxy.cleanup()
        self.proxy = None

    def meta_create_player(self):
        # IMPORTANT: self.sm should be passed in to underlying player.  The underlying player will
        # cleanup the statemachine.
        assert False, "Abstract, not implemented"

    def on_meta_gaming(self, finish_time):
        log.info("%s meta Gaming: match: %s" % (self.name, self.match.match_id))

        self.sm = self.match.sm.dupe()

        self.proxy = self.meta_create_player()

        # ensure we are in the right state
        self.sm.update_bases(self.match.get_current_state())
        self.proxy.on_meta_gaming(finish_time)

    def before_apply_info(self):
        self.proxy.before_apply_info()

    def on_apply_move(self, move):
        self.sm.update_bases(self.match.get_current_state())
        self.proxy.on_apply_move(move)

    def on_next_move(self, finish_time):
        self.sm.update_bases(self.match.get_current_state())
        return self.proxy.on_next_move(finish_time)

