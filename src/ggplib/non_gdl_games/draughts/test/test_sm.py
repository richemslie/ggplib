import time
import random
from pprint import pprint

import py

from ggplib.db import lookup

from ggplib.non_gdl_games.draughts import desc


# unskip to run all tests, but it will take ages.
skip_slow = True


def setup():
    from ggplib.util.init import setup_once
    setup_once(__file__)


def test_create_id_10():
    board_desc = desc.BoardDesc(10)

    info = lookup.by_name("draughts_bt_10x10")

    # will dupe / and reset
    sm = info.get_sm()

    joint_move = sm.get_joint_move()
    base_state = sm.new_base_state()

    base_state.assign(sm.get_current_state())

    board_desc.print_board(base_state)
    pprint(info.model.basestate_to_str(base_state))

    while not sm.is_terminal():
        print "==============="
        print "Dumping legals:"
        print "==============="

        for role_index, role in enumerate(sm.get_roles()):
            ls = sm.get_legal_state(role_index)
            print role, [sm.legal_to_move(role_index, ls.get_legal(ii)) for ii in range(ls.get_count())]

        print
        print "** Choose a random move for each role:"
        for role_index, role in enumerate(sm.get_roles()):
            ls = sm.get_legal_state(role_index)
            choice = ls.get_legal(random.randrange(0, ls.get_count()))
            joint_move.set(role_index, choice)
            print "    %s :" % role, sm.legal_to_move(role_index, choice)
        print

        # play move, the base_state will be new state
        sm.next_state(joint_move, base_state)

        # update the state machine to new state
        sm.update_bases(base_state)

        board_desc.print_board(base_state)


def test_depth_charges():
    board_desc = desc.BoardDesc(10)
    for game in ("draughts_10x10", "draughts_killer_10x10"):

        info = lookup.by_name(game)

        # will dupe / and reset
        sm = info.get_sm()

        joint_move = sm.get_joint_move()
        base_state = sm.new_base_state()
        role_count = len(sm.get_roles())

        all_scores = [[] for i in range(role_count)]

        s = time.time()
        ITERATIONS = 100
        total_depth = 0
        for ii in range(ITERATIONS):
            sm.reset()

            board_desc.print_board_sm(sm)
            while not sm.is_terminal():
                for role_index, role in enumerate(sm.get_roles()):
                    ls = sm.get_legal_state(role_index)
                    choice = ls.get_legal(random.randrange(0, ls.get_count()))
                    joint_move.set(role_index, choice)

                # play move, the base_state will be new state
                sm.next_state(joint_move, base_state)

                # update the state machine to new state
                sm.update_bases(base_state)
                board_desc.print_board_sm(sm)
                total_depth += 1

            for ri in range(role_count):
                all_scores[ri].append(sm.get_goal_value(ri))

        total_time = time.time() - s

        print all_scores
        print "average depth", total_depth / float(ITERATIONS)
        print (total_time / float(ITERATIONS)) * 1000

        print "running %s for 2 seconds in C" % game
        from ggplib.interface import depth_charge

        msecs_taken, rollouts, num_state_changes = depth_charge(sm, 2)

        print "===================================================="
        print "ran for %.3f seconds, state changes %s, rollouts %s" % ((msecs_taken / 1000.0),
                                                                       num_state_changes,
                                                                       rollouts)
        print "rollouts per second: %s" % (rollouts / (msecs_taken / 1000.0))


def create_player():
    from ggplib.player import get
    player = get.get_player("simplemcts")
    player.max_tree_search_time = 0.25
    player.skip_single_moves = True
    player.dump_depth = 1
    return player


def test_play():
    if skip_slow:
        py.test.skip("too slow")

    from ggplib.player.gamemaster import GameMaster

    game_info = lookup.by_name("draughts_killer_10x10")
    gm = GameMaster(game_info, verbose=False)

    # add two python players
    gm.add_player(create_player(), "white")
    gm.add_player(create_player(), "black")

    gm.start(meta_time=2, move_time=2)
    gm.play_to_end()

    # check scores/depth make some sense
    print gm.scores


def dump_legals(sm):
    print "==============="
    print "Dumping legals:"
    print "==============="

    for role_index, role in enumerate(sm.get_roles()):
        ls = sm.get_legal_state(role_index)
        print role, [sm.legal_to_move(role_index, ls.get_legal(ii)) for ii in range(ls.get_count())]


def random_move(sm, verbose=False):
    joint_move = sm.get_joint_move()
    base_state = sm.new_base_state()

    for role_index, role in enumerate(sm.get_roles()):
        ls = sm.get_legal_state(role_index)
        choice = ls.get_legal(random.randrange(0, ls.get_count()))
        joint_move.set(role_index, choice)
        if verbose:
            print "playing    %s :" % role, sm.legal_to_move(role_index, choice)

    if verbose:
        print

    # play move, the base_state will be new state
    sm.next_state(joint_move, base_state)

    # update the state machine to new state
    sm.update_bases(base_state)


def test_captures_king():
    fen = "W:WK48:B31,42,21,22,19,10,39,29"

    board_desc = desc.BoardDesc(10)
    sm = desc.create_sm(board_desc, fen)

    base_state = sm.new_base_state()
    base_state.assign(sm.get_current_state())

    board_desc.print_board(base_state)

    for i in range(7):
        board_desc.print_board(base_state)
        dump_legals(sm)

        if sm.is_terminal():
            break

        # random move
        random_move(sm)
        base_state.assign(sm.get_current_state())


def test_captures_king2():
    fen = "W:WK48:B31,42,21,22,19,10,39,29"

    board_desc = desc.BoardDesc(10)
    sm = desc.create_sm(board_desc, fen)

    base_state = sm.new_base_state()

    base_state.assign(sm.get_current_state())

    for i in range(7):
        board_desc.print_board(base_state)
        dump_legals(sm)

        if sm.is_terminal():
            print "AND DONE"
            break

        # random move
        random_move(sm)
        base_state.assign(sm.get_current_state())


def do_draw_rule(fen, expect_score0, expect_score1, min_game_depth, verbose=False):
    board_desc = desc.BoardDesc(10)

    # keep playing games randomly until we trigger expect_score0

    while True:
        last_step = 1
        sm = desc.create_sm(board_desc, fen)

        base_state = sm.new_base_state()
        base_state.assign(sm.get_current_state())

        depth = 0
        while True:
            if verbose:
                board_desc.print_board(base_state)
                dump_legals(sm)

            if sm.is_terminal():
                break

            # random move
            random_move(sm, verbose=verbose)
            depth += 1

            base_state.assign(sm.get_current_state())

            # the step should be +1 last_step, or reset
            step = board_desc.step_counter(base_state)

            # step is only reset at the end of captures
            if board_desc.check_interim_status(base_state):
                assert step == last_step
                continue

            assert step == 1 or step == last_step + 1
            last_step = step

        if verbose:
            print "depth:", depth
            print "Scores: [%d %d]" % (sm.get_goal_value(0), sm.get_goal_value(1))

        if depth >= min_game_depth and sm.get_goal_value(0) == expect_score0:
            assert sm.get_goal_value(1) == expect_score1
            return board_desc.step_counter(base_state)


def test_draw_once():
    fen = "W:WK48:BK4"
    verbose = True
    assert do_draw_rule(fen, 50, 50, desc.N_RULE_COUNT - 1, verbose=verbose) == desc.N_RULE_COUNT


def test_draw_n_rule():
    verbose = False
    for i in range(10):
        fen = "W:WK48:BK4"
        assert do_draw_rule(fen, 50, 50, desc.N_RULE_COUNT - 1, verbose=verbose) == desc.N_RULE_COUNT
        assert do_draw_rule(fen, 0, 100, desc.N_RULE_COUNT / 2, verbose=verbose) == 1
        assert do_draw_rule(fen, 100, 0, desc.N_RULE_COUNT / 2, verbose=verbose) == 1

    for i in range(10):
        fen = "W:WK48:BK4,26"
        assert do_draw_rule(fen, 50, 50, desc.N_RULE_COUNT * 2, verbose=verbose) == desc.N_RULE_COUNT
        assert do_draw_rule(fen, 0, 100, desc.N_RULE_COUNT * 2, verbose=verbose) == 1
        assert do_draw_rule(fen, 100, 0, desc.N_RULE_COUNT * 2, verbose=verbose) == 1

    for i in range(10):
        fen = "W:WK48,26:BK4"
        assert do_draw_rule(fen, 50, 50, desc.N_RULE_COUNT * 2, verbose=verbose) == desc.N_RULE_COUNT
        assert do_draw_rule(fen, 0, 100, desc.N_RULE_COUNT * 2, verbose=verbose) == 1
        assert do_draw_rule(fen, 100, 0, desc.N_RULE_COUNT * 2, verbose=verbose) == 1
