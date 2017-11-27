import sys
import time
import traceback

from ggplib.util import log
from ggplib.symbols import tokenize

from ggplib.db import lookup
from ggplib import interface

###################################################################################################

# Indicate how much time to give for communication between gamemaster and player.  This is useful
# for when matches are scheduled at other locations around the world and the latency can cause
# timeouts.
# XXX Should be at http level

CUSHION_TIME = 1.5

###################################################################################################

class BadGame(Exception):
    pass


class CriticalError(Exception):
    pass

###################################################################################################

def replace_symbols(s, from_, to_):
    ''' given a string s, will replace each symbol from_ -> to_. '''
    symbols = tokenize(str(s))
    new_symbols = []
    for sym in symbols:
        if sym == from_:
            sym = to_
        new_symbols.append(sym)
    return " ".join(new_symbols).replace('( ', '(').replace(' )', ')')

###################################################################################################

class Match:
    def __init__(self, match_id, role, meta_time, move_time, player, gdl):
        assert gdl is not None

        self.match_id = match_id
        self.role = role
        self.gdl = gdl
        self.meta_time = meta_time
        self.move_time = move_time

        self.move_info = []
        self.moves = []

        self.states = []

        # stores the last played move, to check the gamemaster returns the same move
        self.last_played_move = None

        self.joint_move = None
        self.player = player

        # set in do_start
        self.gdl_symbol_mapping = None
        self.sm = None
        self.game_name = None

    def get_current_state(self):
        # do not change this
        return self.states[-1]

    def do_start(self, initial_basestate=None):
        ''' Optional initial_basestate.  Used mostly for testing. If none will use the inital state
            of state machine. '''

        enter_time = time.time()
        end_time = enter_time + self.meta_time - CUSHION_TIME

        log.debug("Match.do_start(), time = %.1f" % (end_time - enter_time))

        (self.gdl_symbol_mapping,
         self.sm,
         self.game_name) = lookup.by_gdl(self.gdl, end_time)

        self.sm.reset()
        log.debug("Got state machine %s for game '%s' and match_id: %s" % (self.sm,
                                                                           self.game_name,
                                                                           self.match_id))

        if initial_basestate:
            # dupe the state - it could be deleted under our feet
            bs = self.sm.new_base_state()
            bs.assign(initial_basestate)
            initial_basestate = bs

            log.debug("The start state is %s" % self.sm.basestate_to_str(initial_basestate))

            # update the statemachine
            self.sm.update_bases(initial_basestate)

            # check it is not actually finished
            assert not self.sm.is_terminal()

        else:
            initial_basestate = self.sm.get_initial_state()

        self.states.append(initial_basestate)

        # store a joint move internally
        self.joint_move = self.sm.get_joint_move()

        # set our role index
        if self.gdl_symbol_mapping:
            our_role = self.gdl_symbol_mapping[self.role]
        else:
            our_role = self.role

        self.our_mapped_role = our_role
        if our_role not in self.sm.get_roles():
            raise BadGame("Our role not found. %s in %s", (our_role, self.sm.get_roles()))

        self.our_role_index = self.sm.get_roles().index(our_role)
        log.info('roles : %s, our_role : %s, role_index : %s' % (self.sm.get_roles(),
                                                                 our_role,
                                                                 self.our_role_index))
        assert self.our_role_index != -1

        # FINALLY : call the meta gaming stage on the player
        # note: on_meta_gaming must use self.match.get_current_state()
        self.player.reset(self)
        self.player.on_meta_gaming(end_time)

    def apply_move(self, moves):
        log.debug("apply moves: %s" % (moves,))

        # we give the player an one time opportunity to return debug/extra information
        # about the move it just played
        self.move_info.append(self.player.before_apply_info())

        # get the previous state - incase our statemachine is out of sync
        self.sm.update_bases(self.get_current_state())

        # fish tediously for move in available legals
        our_move = None
        preserve_move = []
        for role_index, gamemaster_move in enumerate(moves):
            move = gamemaster_move
            # map the gamemaster move
            if self.gdl_symbol_mapping:
                for k, v in self.gdl_symbol_mapping.items():
                    move = replace_symbols(move, k, v)
                log.debug("remapped move from '%s' -> '%s'" % (gamemaster_move, move))

            preserve_move.append(move)

            # find the move
            found = False

            ls = self.sm.get_legal_state(role_index)
            choices = [ls.get_legal(ii) for ii in range(ls.get_count())]
            for choice in choices:
                choice_move = self.sm.legal_to_move(role_index, choice)
                if choice_move == str(move):
                    found = True

                    if role_index == self.our_role_index:
                        our_move = choice_move

                    self.joint_move.set(role_index, choice)
                    break

            assert found, move

        assert our_move is not None

        # check that our move was the same.  May be a timeout or ther gamemaster due to bad
        # network.  In these cases, we force an abort (locally) to the game..
        if self.last_played_move is not None:
            if self.last_played_move != our_move:
                # all we do is log, and continue.  Really messed up though.
                msg = "Gamemaster sent back a different move from played move %s != %s" % (self.last_played_move,
                                                                                           our_move)
                log.critical(msg)
                raise CriticalError(msg)

        new_base_state = self.sm.new_base_state()
        self.sm.next_state(self.joint_move, new_base_state)
        self.sm.update_bases(new_base_state)

        # save for next time / prospserity
        self.moves.append(preserve_move)
        self.states.append(new_base_state)

        # in case player needs to cleanup some state
        self.player.on_apply_move(self.joint_move)

    def legal_to_gamemaster_move(self, index):
        m = self.sm.legal_to_move(self.our_role_index, index)
        if self.gdl_symbol_mapping:
            for k, v in self.gdl_symbol_mapping.items():
                m = replace_symbols(m, v, k)
        return m

    def do_play(self, move):
        enter_time = time.time()
        log.debug("do_play: %s" % (move,))

        if move is not None:
            self.apply_move(move)

        current_state = self.get_current_state()
        log.info("Current state : '%s'" % self.sm.basestate_to_str(current_state))
        self.sm.update_bases(current_state)
        if self.sm.is_terminal():
            return "done"

        end_time = enter_time + self.move_time - CUSHION_TIME
        legal_choice = self.player.on_next_move(end_time)

        # we have no idea what on_next_move() left the state machine.  So reverting it back to
        # correct state here.
        self.sm.update_bases(self.get_current_state())

        # get possible possible legal moves and check 'move' is a valid
        ls = self.sm.get_legal_state(self.our_role_index)

        # store last move (in our own mapping, *not* gamemaster)
        self.last_played_move = self.sm.legal_to_move(self.our_role_index, legal_choice)

        # check the move remaps and is a legal choice
        move = self.legal_to_gamemaster_move(legal_choice)
        legal_moves = [self.legal_to_gamemaster_move(ls.get_legal(ii)) for ii in range(ls.get_count())]
        if move not in legal_moves:
            msg = "Choice was %s not in legal choices %s" % (move, legal_moves)
            log.critical(msg)
            raise CriticalError(msg)

        log.info("do_play sending move: %s" % move)
        return move

    def do_stop(self):
        log.info("Match done %s" % self.match_id)
        assert self.sm.is_terminal(), "should never be called unless game is finished"

        log.info("Final scores:")
        for idx, role in enumerate(self.sm.get_roles()):
            ourself_str = "(me) " if idx == self.our_role_index else ""
            log.info("  %s %s: %s " % (role,
                                       ourself_str,
                                       self.sm.get_goal_value(idx)))

        log.info("Moves:")
        buf = [""]
        for move in self.moves:
            if isinstance(move, str):
                move_str = move
            else:
                move_str = " ".join(str(t) for t in move)

            buf.append("\t(" + move_str + ")")

        log.info("\n".join(buf))
        self.cleanup()
        log.info("DONE!")

    def do_abort(self):
        log.warning("abort match %s" % self.match_id)
        self.cleanup()
        return "aborted"

    def cleanup(self):
        try:
            self.player.cleanup()
        except Exception as exc:
            log.error("FAILED TO CLEANUP PLAYER: %s" % exc)
            type, value, tb = sys.exc_info()
            log.error(traceback.format_exc())

        # cleanup c++ stuff
        log.warning("cleaning up c++ stuff")

        # all the basestates
        for bs in self.states:
            # cleanup bs
            interface.dealloc_basestate(bs)

        self.states = []

        if self.joint_move:
            interface.dealloc_jointmove(self.joint_move)
            self.joint_move = None

        if self.sm:
            interface.dealloc_statemachine(self.sm)
            self.sm = None

        log.warning("done cleaning up c++ stuff")

    def __repr__(self):
        return "(id:%s role:%s meta:%s move:%s)" % (self.match_id,
                                                    self.role,
                                                    self.meta_time,
                                                    self.move_time)
