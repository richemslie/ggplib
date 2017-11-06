import sys
import time
import pprint
import traceback

from ggplib.util import log

from ggplib.propnet import getpropnet
from ggplib.statemachine import builder

###############################################################################

CUSHION_TIME = 1.0

class BadGame(Exception):
    pass

class CriticalError(Exception):
    pass

###############################################################################

class Match:
    def __init__(self, match_id, role, meta_time, move_time, player, gdl):
        assert gdl is not None

        self.match_id = match_id
        self.role = role
        self.gdl = gdl
        self.meta_time = meta_time
        self.move_time = move_time

        self.moves = []
        self.states = []

        self.last_played_move = None

        self.joint_move = None
        self.player = player

    def get_current_state(self):
        # do not change this
        return self.states[-1]

    def do_start(self):
        enter_time = time.time()
        end_time = enter_time + self.meta_time - CUSHION_TIME

        log.debug("Match.do_start(), time = %.1f" % (end_time - enter_time))

        self.propnet = getpropnet.get_with_gdl(self.gdl, self.match_id)

        log.info("Got propnet - building statemachine")
        self.sm = builder.build_standard_sm(self.propnet)
        self.sm.reset()
        self.states.append(self.sm.get_initial_state())

        log.debug("Got state machine %s" % self.sm)

        # store a joint move internally
        self.joint_move = self.sm.get_joint_move()

        # set our role index
        for idx, r in enumerate(self.sm.get_roles()):
            if r == self.role:
                self.our_role_index = idx
                break

        log.info('roles : %s, our_role : %s, role_index : %s' % (self.sm.get_roles(),
                                                                 self.role,
                                                                 self.our_role_index))
        assert self.our_role_index != -1

        # FINALLY : call the meta gaming stage on the player
        self.player.reset(self)
        self.player.on_meta_gaming(end_time)

    def apply_move(self, moves):
        log.debug("apply moves: %s" % (moves,))

        # get the previous state - incase our statemachine is out of sync
        self.sm.update_bases(self.get_current_state())

        # fish tediously for move in available legals
        our_move = None
        for role_index, move in enumerate(moves):
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
                msg = "Gamemaster sent back a different move from played move %s != %s" % (self.last_played_move, our_move)
                log.critical(msg)
                raise CriticalError(msg)

        new_base_state = self.sm.new_base_state()
        self.sm.next_state(self.joint_move, new_base_state)
        self.sm.update_bases(new_base_state)

        # save for next time / prospserity
        self.moves.append(moves)
        self.states.append(new_base_state)

        # in case player needs to cleanup some state
        self.player.on_apply_move(self.joint_move)

    def do_play(self, move):
        enter_time = time.time()
        log.debug("do_play: %s" % (move,))

        if move is not None:
            self.apply_move(move)

        current_state = self.get_current_state()
        str_state = self.propnet.to_gdl([current_state.get(i)
                                         for i in range(len(self.propnet.base_propositions))])
        log.info("Current state : '%s'" % str_state)
        self.sm.update_bases(current_state)
        if self.sm.is_terminal():
            return "done"

        end_time = enter_time + self.move_time - CUSHION_TIME
        choice = self.player.on_next_move(end_time)

        # we have no idea what on_next_move() left the state machine.  So reverting it back to
        # correct state here.
        self.sm.update_bases(self.get_current_state())

        # get possible possible legal moves and check 'move' is a valid
        ls = self.sm.get_legal_state(self.our_role_index)
        legal_choices = [ls.get_legal(ii) for ii in range(ls.get_count())]

        if choice not in legal_choices:
            msg = "Choice was %d not in legal choices %s" % (choice, legal_choices)
            log.critical(msg)
            raise CriticalError(msg)

        # ok we need to return a string
        move = self.sm.legal_to_move(self.our_role_index, choice)

        # store last move
        self.last_played_move = move

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
        log.info(pprint.pformat(self.moves))
        self.cleanup()
        log.info("DONE!")

    def do_abort(self):
        log.warning("abort match %s" % self.match_id)
        self.cleanup()
        return "aborted"

    def cleanup(self):
        try:
            self.player.cleanup()
        except Exception, exc:
            log.error("FAILED TO CLEANUP PLAYER: %s" % exc)
            type, value, tb = sys.exc_info()
            log.error(traceback.format_exc())

        # XXX cleanup any stuff here

    def __repr__(self):
        return "(id:%s role:%s meta:%s move:%s)" % (self.match_id,
                                                    self.role,
                                                    self.meta_time,
                                                    self.move_time)
