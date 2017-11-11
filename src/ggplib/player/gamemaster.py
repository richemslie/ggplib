import random
from ggplib.util import log
from ggplib.symbols import SymbolFactory

from ggplib.propnet import getpropnet
from ggplib.statemachine.forwards import FwdStateMachine

from ggplib.player.match import Match


class GameMaster:
    def __init__(self, game):
        filename = getpropnet.get_filename_for_game(game)
        self.symbol_factory = SymbolFactory()
        self.gdl = tuple(self.symbol_factory.to_symbols(open(filename).read()))

        self.players = []

        self.depth = 0

        # updated after game is finished
        self.scores = {}

        self.match_id = "tmp_%s_a_match_id_%d" % (game, random.randint(0, 100000))
        self.propnet = getpropnet.get_with_gdl(self.gdl, self.match_id)
        self.sm = FwdStateMachine(self.propnet)

    def add_player(self, player, role):
        self.players.append((player, role))

    def convert_to_base_state(self, state_str):
        state_set = set()
        for s in self.symbol_factory.to_symbols(state_str):
            state_set.add(s)

        count = 0

        base_states = []
        for b in self.propnet.base_propositions:
            v = 0

            # we try both with 'x' and without '(true x)'
            if b.meta.gdl in state_set or b.meta.gdl[1] in state_set:
                v = 1
                count += 1
            base_states.append(v)

        assert len(self.propnet.get_initial_state()) == len(base_states)
        return base_states

    def start(self, meta_time=10, move_time=5, start_state=None):
        assert self.players

        if start_state is not None:
            # update the state machine
            self.sm.update_bases(start_state)

            # check the game isn't finished
            assert not self.sm.is_terminal()
        else:
            # set propnet to initial state...
            self.sm.update_bases(self.propnet.get_initial_state())

        player_matches = []
        for player, role in self.players:
            match = Match(self.match_id, role, meta_time, move_time, player, self.gdl)
            player_matches.append(match)

            # call do start...
            log.verbose("Starting for %s / %s" % (match.role, match.player))
            match.do_start(start_state=start_state)

        # reorder matches to roles (and check that we have them)
        self.matches = []
        for info in self.propnet.role_infos:
            for m in player_matches:
                if info.role == m.role:
                    self.matches.append(m)
                    break

        assert len(self.matches) == len(self.propnet.role_infos)

    def play_single_move(self, last_move=None):
        actions = []
        new_last_move = []
        for m, ri in zip(self.matches, self.propnet.role_infos):
            log.verbose("m.do_play(%s) for %s / %s" % (last_move, ri.role, m.player))
            move = m.do_play(last_move)
            new_last_move.append(move)

            # check the move is in the legals
            for l in self.sm.get_legal_moves(ri):
                the_role = str(l.meta.gdl[1])
                assert the_role == m.role

                the_move = str(l.meta.gdl[2])
                if the_move == move:
                    actions.append(l.meta.legals_input)
                    break

        assert len(actions) == len(self.matches)
        log.verbose("playing %s" % (actions,))
        base_map = self.sm.get_next_state(actions)
        self.sm.update_bases(base_map)

        last_move = self.symbol_factory.symbolize("(" + (" ".join(new_last_move)) + ")")

        self.depth += 1
        return last_move

    def play_to_end(self, last_move=None):
        while True:
            if self.sm.is_terminal():
                break

            last_move = self.play_single_move(last_move)

        log.verbose("Played to depth %d" % self.depth)
        log.verbose("Last move %s" % (last_move,))

        for r in self.propnet.roles:
            score = self.sm.goal_value(r)
            self.scores[r] = score
            log.verbose("Final score for %s : %s " % (r, score))

        # Need to do the final move for player
        for m in self.matches:
            assert m.do_play(last_move) == "done"

            # and stop them
            m.do_stop()
