from ggplib.player.base import MatchPlayer


class LegalPlayer(MatchPlayer):
    ' plays randomly '

    def on_next_move(self, finish_time):
        # get the statemachine...
        sm = self.match.sm

        # constraint: state machine will be correct
        ls = sm.get_legal_state(self.match.our_role_index)

        # a first choice
        return ls.get_legal(0)
