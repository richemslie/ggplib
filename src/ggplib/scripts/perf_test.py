import sys
import time
import random
import traceback

from ggplib.util.log import Log, LogLevel

from ggplib import interface
from ggplib.propnet import getpropnet
from ggplib.statemachine import builder

# module level logger
log = Log()

VERSION = "ggplib_v2_01_alpha"

###############################################################################

# NOTE: much faster if in c++.  Although the biggest bottleneck is the propnet.  random here is slow.

def go(game_file, output_file, seconds_to_run, rollouts_in_c=False):
    msecs_taken = None
    rollouts = 0
    num_state_changes = 0
    error_str = None

    try:
        propnet = getpropnet.get_with_filename(game_file)
        role_count = len(propnet.roles)

        sm = builder.build_combined_state_machine(propnet)
        if sm is None:
            sm = builder.build_goaless_sm(propnet)

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

            role_count_range = range(role_count)

            end_time = time.time() + seconds_to_run

            # resolution is assumed to be good enough not to cheat too much here (we return
            # msecs_taken so it is all good)
            start_time = time.time()
            end_time = start_time + seconds_to_run
            while True:
                cur_time = time.time()
                if cur_time > end_time:
                    msecs_taken = int(1000 * (cur_time - start_time))
                    break

                sm.reset()
                depth = 0
                while True:
                    if sm.is_terminal():
                        break

                    for idx in role_count_range:
                        ls = sm.get_legal_state(idx)
                        choice = ls.get_legal(random.randrange(0, ls.get_count()))
                        joint_move.set(idx, choice)

                    # play move
                    sm.next_state(joint_move, base_state)
                    sm.update_bases(base_state)
                    depth += 1

                scores = [sm.get_goal_value(r) for r in range(role_count)]
                rollouts += 1
                num_state_changes += depth

    except Exception, exc:
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
        log.info("ran for %.3f seconds, state changes %s, rollouts %s" % ((msecs_taken / 1000.0), num_state_changes, rollouts))
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
        print "GAME_FILE", game_file
        print "OUTPUT_FILE", output_file
        print "SECONDS_TO_RUN", seconds_to_run

    from ggplib import interface
    import ggplib.util.log
    interface.initialise_k273(1, log_name_base="perf_test")
    ggplib.util.log.initialise()

    # two versions, python or c++
    go(game_file, output_file, seconds_to_run, rollouts_in_c=True)
