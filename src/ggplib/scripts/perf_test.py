import sys
import time
import random
import traceback

from ggplib.util.log import Log

from ggplib import interface
from ggplib.propnet import getpropnet
from ggplib.statemachine import builder

# module level logger
log = Log()

VERSION = "ggplib_v0.9999"

###############################################################################
# XXX tmp
# def do(game_file):
#    propnet = getpropnet.get_with_filename(game_file)
#    sm = builder.build_standard_sm(propnet)
# sm = builder.build_goaless_sm(propnet)
# sm = builder.build_standard_sm(propnet)
# import cProfile
# cProfile.run('do(game_file)')

###############################################################################

# NOTE: will be faster if in c++.  The biggest bottleneck is the propnet, but the biggest
# difference between code is random here is slow.


def go(game_file, output_file, seconds_to_run, rollouts_in_c=False):
    msecs_taken = None
    rollouts = 0
    num_state_changes = 0
    error_str = None
    all_scores = []

    try:
        propnet = getpropnet.get_with_filename(game_file)
        role_count = len(propnet.roles)
        sm = builder.build_sm(propnet)

        if output_file is None:
            log()
            log()
            log("running depth charges for %s seconds %s" % (seconds_to_run, "(in c)" if rollouts_in_c else ""))

        if rollouts_in_c:
            msecs_taken, rollouts, num_state_changes = interface.depth_charge(sm, seconds_to_run)

        else:

            # cache some objects
            joint_move = sm.get_joint_move()
            base_state = sm.new_base_state()

            # resolution is assumed to be good enough not to cheat too much here (we return
            # msecs_taken so it is all good)
            start_time = cur_time = time.time()
            end_time = start_time + seconds_to_run

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

                # get the scores from the statemachine
                scores = [sm.get_goal_value(r) for r in range(role_count)]
                all_scores.append(scores)

                # stats
                rollouts += 1
                num_state_changes += depth

                # update the time
                cur_time = time.time()

            msecs_taken = int(1000 * (cur_time - start_time))

    except Exception as exc:
        error_str = "Error %s" % exc
        type, value, tb = sys.exc_info()
        traceback.print_exc()

    # write the result
    if output_file is not None:
        f = open(output_file, "w")

        # no version yet
        print >>f, "version=%s" % VERSION
        if msecs_taken is not None:
            assert error_str is None
            print >>f, "millisecondsTaken=%s" % msecs_taken
            print >>f, "numStateChanges=%s" % num_state_changes
            print >>f, "numRollouts=%s" % rollouts

        else:
            assert error_str is not None
            print >>f, "errorMessage=%s" % (error_str,)

        f.close()
    else:
        log.info("====================================================")
        log.info("performance test game %s" % game_file)
        log.info("ran for %.3f seconds, state changes %s, rollouts %s" % ((msecs_taken / 1000.0),
                                                                          num_state_changes,
                                                                          rollouts))
        log.info("rollouts per second: %s" % (rollouts / (msecs_taken / 1000.0)))
        log.info("====================================================")


###############################################################################

debug = True

if __name__ == "__main__":
    game_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        seconds_to_run = int(sys.argv[3])
    else:
        output_file = None
        seconds_to_run = 10

    if debug:
        print("GAME_FILE", game_file)
        print("OUTPUT_FILE", output_file)
        print("SECONDS_TO_RUN", seconds_to_run)

    interface.initialise_k273(1, log_name_base="perf_test")

    import ggplib.util.log
    ggplib.util.log.initialise()

    # two versions, python or c++
    go(game_file, output_file, seconds_to_run, rollouts_in_c=True)
