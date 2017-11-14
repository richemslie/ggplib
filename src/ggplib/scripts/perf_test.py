import sys
import time
import random
import traceback

from ggplib.util import log

from ggplib import interface
from ggplib.db import lookup

VERSION = "ggplib_v0.9999"

###############################################################################

def go(sm, seconds_to_run):
    log.verbose("running depth charges for %s seconds %s" % (seconds_to_run, "(in c)" if rollouts_in_c else ""))

    if rollouts_in_c:
        return interface.depth_charge(sm, seconds_to_run)

    else:
        role_count = len(sm.get_roles())

        # cache some objects
        joint_move = sm.get_joint_move()
        base_state = sm.new_base_state()

        # resolution is assumed to be good enough not to cheat too much here (we return
        # msecs_taken so it is all good)
        start_time = cur_time = time.time()
        end_time = start_time + seconds_to_run

        rollouts = 0
        num_state_changes = 0

        while cur_time < end_time:
            # the number of moves of the game
            depth = 0

            # tells the state machine to reset everything and return to initial state
            sm.reset()

            # while the game has not ended
            while not sm.is_terminal():
                # choose a random move for each role
                for role_index in range(role_count):
                    ls = sm.get_legal_state(role_index)
                    choice = ls.get_legal(random.randrange(0, ls.get_count()))
                    joint_move.set(role_index, choice)

                # play move, the base_state will be new state
                sm.next_state(joint_move, base_state)

                # update the state machine to new state
                sm.update_bases(base_state)

                # increment the depth
                depth += 1

            # simulate side effect of getting the scores from the statemachine
            scores = [sm.get_goal_value(r) for r in range(role_count)]

            # stats
            rollouts += 1
            num_state_changes += depth

            # update the time
            cur_time = time.time()

        msecs_taken = int(1000 * (cur_time - start_time))

    return msecs_taken, rollouts, num_state_changes


def main_3(game_file, output_file, seconds_to_run):
    # builds without accessing database database
    from ggplib.propnet import getpropnet
    from ggplib.statemachine import builder

    propnet = getpropnet.get_with_filename(game_file)
    sm = builder.build_sm(propnet)

    if debug:
        log.verbose("GAME_FILE", game_file)
        log.verbose("OUTPUT_FILE", output_file)
        log.verbose("SECONDS_TO_RUN", seconds_to_run)

    # for the result
    f = open(output_file, "w")

    try:
        msecs_taken, rollouts, num_state_changes = go(sm)

        # see gdl-perf (XXX do python3 print)
        print >>f, "version=%s" % VERSION
        if msecs_taken is not None:
            print >>f, "millisecondsTaken=%s" % msecs_taken
            print >>f, "numStateChanges=%s" % num_state_changes
            print >>f, "numRollouts=%s" % rollouts

    except Exception as exc:
        error_str = "Error %s" % exc
        type, value, tb = sys.exc_info()
        traceback.print_exc()

        print >>f, "errorMessage=%s" % (error_str,)

    f.close()


def main_2(game_name, seconds_to_run):
    sm = lookup.by_name(game_name)
    msecs_taken, rollouts, num_state_changes = go(sm, seconds_to_run)

    log.info("====================================================")
    log.info("performance test game %s" % game_name)
    log.info("ran for %.3f seconds, state changes %s, rollouts %s" % ((msecs_taken / 1000.0),
                                                                      num_state_changes,
                                                                      rollouts))
    log.info("rollouts per second: %s" % (rollouts / (msecs_taken / 1000.0)))
    log.info("====================================================")


###############################################################################

debug = True
rollouts_in_c = True

if __name__ == "__main__":
    interface.initialise_k273(1, log_name_base="perf_test")

    import ggplib.util.log
    ggplib.util.log.initialise()

    args = sys.argv[1:]

    if len(args) == 3:
        game_file = args[0]
        output_file = args[0]
        seconds_to_run = int(args[2])

        # gdl-perf
        main_3(game_file, output_file, seconds_to_run)
    else:
        # command line
        assert len(args) < 3
        game_name = args[0]
        seconds_to_run = int(args[1]) if len(args) == 2 else 10
        main_2(game_name, seconds_to_run)
