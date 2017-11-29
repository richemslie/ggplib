import time
import random

from ggplib.util import log


def depth_charges(sm, seconds):
    # play for n seconds
    seconds = float(seconds)

    log.info("depth_charges() : playing for %s seconds" % seconds)

    role_count = len(sm.get_roles())

    # cache some objects
    joint_move = sm.get_joint_move()
    base_state = sm.new_base_state()

    # resolution is assumed to be good enough not to cheat too much here (we return
    # msecs_taken so it is all good)
    start_time = cur_time = time.time()
    end_time = start_time + seconds

    rollouts = 0
    num_state_changes = 0

    all_scores = [[] for i in range(role_count)]

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
        for ri in range(role_count):
            all_scores[ri].append(sm.get_goal_value(ri))

        # stats
        rollouts += 1
        num_state_changes += depth

        # update the time
        cur_time = time.time()

    rollouts_per_second = rollouts / seconds
    log.info("rollouts per second %s" % rollouts_per_second)
    log.info("average time msecs %s" % ((seconds / rollouts) * 1000))
    log.info("average depth %s" % (num_state_changes / rollouts))

    for ri, role in enumerate(sm.get_roles()):
        total_score = sum(all_scores[ri])
        log.info("average score for %s : %s" % (role, total_score / float(rollouts)))

