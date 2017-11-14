import random
from ggplib.util import log
from ggplib.db import lookup
from ggplib.player.match import Match
from ggplib.symbols import SymbolFactory


class GameMaster:
    def __init__(self, gdl_str):
        # used to convert to base state
        self.symbol_factory = SymbolFactory()

        self.gdl_str = gdl_str
        _, self.sm, self.game = lookup.by_gdl(gdl_str)

        # store a joint move / basestate internally
        self.joint_move = self.sm.get_joint_move()
        self.next_basestate = self.sm.new_base_state()

        def get_base_tuple(i):
            return tuple(self.symbol_factory.to_symbols(self.sm.get_gdl(i)))[0]
        self.bases = [get_base_tuple(i) for i in range(self.next_basestate.len())]

        self.players = []

        self.depth = 0

        # updated after game is finished
        self.scores = {}

        self.match_id = "a_%s_match_id_%d" % (self.game, random.randint(0, 100000))

        log.info("GAMEMASTER: create a gamemaster for game %s" % self.game)

    def add_player(self, player, role):
        self.players.append((player, role))

    def convert_to_base_state(self, state_str):
        state_set = set()
        for s in self.symbol_factory.to_symbols(state_str):
            state_set.add(s)

        bs = self.sm.new_base_state()
        for i in range(bs.len()):
            # we try both with 'x' and without '(true x)'
            if self.bases[i] in state_set or self.bases[i][1] in state_set:
                bs.set(i, 1)
            else:
                bs.set(i, 0)

        return bs

    def start(self, meta_time=10, move_time=5, initial_basestate=None):
        assert self.players

        if initial_basestate is not None:
            # update the state machine
            self.sm.update_bases(initial_basestate)

            # check the game isn't finished
            assert not self.sm.is_terminal()
        else:
            # reset state machine, returns it to initial state.
            self.sm.reset()

        player_matches = []
        for player, role in self.players:
            match = Match(self.match_id, role, meta_time, move_time, player, self.gdl_str)
            player_matches.append(match)

            # call do start...
            log.verbose("Starting for %s / %s" % (match.role, match.player))
            match.do_start(initial_basestate=initial_basestate)

        # reorder matches to roles (and check that we have them)
        self.matches = []
        for role in self.sm.roles:
            for m in player_matches:
                if role == m.role:
                    self.matches.append(m)
                    break

        assert len(self.matches) == len(self.sm.roles)

    def play_single_move(self, last_move=None):
        actions = []
        new_last_move = []
        for role_index, (m, role) in enumerate(zip(self.matches, self.sm.roles)):
            log.verbose("m.do_play(%s) for %s / %s" % (last_move, role, m.player))
            move = m.do_play(last_move)
            new_last_move.append(move)

            # check the move is in the legals
            ls = self.sm.get_legal_state(role_index)
            choices = [ls.get_legal(ii) for ii in range(ls.get_count())]

            for choice in choices:
                choice_move = self.sm.legal_to_move(role_index, choice)

                if choice_move == move:
                    self.joint_move.set(role_index, choice)
                    actions.append(move)
                    break

        assert len(actions) == len(self.matches)
        log.verbose("playing %s" % (actions,))

        self.sm.next_state(self.joint_move, self.next_basestate)
        self.sm.update_bases(self.next_basestate)

        self.depth += 1
        return tuple(new_last_move)

    def play_to_end(self, last_move=None):
        while True:
            if self.sm.is_terminal():
                break

            last_move = self.play_single_move(last_move)

        log.verbose("Played to depth %d" % self.depth)
        log.verbose("Last move %s" % (last_move,))

        for ri, r in enumerate(self.sm.get_roles()):
            score = self.sm.get_goal_value(ri)
            self.scores[r] = score
            log.verbose("Final score for %s : %s " % (r, score))

        # Need to do the final move for player
        for m in self.matches:
            assert m.do_play(last_move) == "done"

            # and stop them
            m.do_stop()
