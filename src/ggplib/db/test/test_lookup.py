import pdb
import sys
import traceback

import py

from ggplib.util import log

from ggplib.db import lookup

from ggplib import interface
from ggplib.statemachine.depthcharges import depth_charges


######################################################################

_setup_once = False
def setup():
    global _setup_once
    if not _setup_once:
        from ggplib import interface
        interface.initialise_k273(1)

        import ggplib.util.log
        ggplib.util.log.initialise()

        lookup.get_database()


def get_gdl_for_game(game):
    from ggplib.propnet.getpropnet import get_filename_for_game
    f = open(get_filename_for_game(game))
    return f.read()


def test_compare_same():
    game_a = get_gdl_for_game("ticTacToe")
    game_b = get_gdl_for_game("ticTacToe")

    idx1, sig1 = lookup.get_index(game_a, verbose=False)
    idx2, sig2 = lookup.get_index(game_b, verbose=False)

    sigs1 = sig1.sigs[:]
    sigs1.sort()

    sigs2 = sig1.sigs[:]
    sigs2.sort()

    for x, y in zip(sig1.sigs, sig2.sigs):
        x, y = x.zero_sig, y.zero_sig
        assert x == y


def test_with_database():
    gdl_str = get_gdl_for_game("connectFour")

    mapping, sm, game_name = lookup.by_gdl(gdl_str)
    assert game_name == "connectFour"
    assert mapping is None

    # ensure keeps returning valid statemachines
    for ii in range(10):
        new_mapping, new_sm, new_game_name = lookup.by_gdl(gdl_str)

        assert new_game_name == "connectFour"
        assert new_mapping is None
        assert new_sm != sm
        assert id(new_sm) != id(sm)
        assert new_sm.get_initial_state() == sm.get_initial_state()
        interface.dealloc_statemachine(new_sm)

    # finally run rollouts in c++ on the original sm
    log.info("Testing sm %s" % sm)
    msecs_taken, rollouts, _ = interface.depth_charge(sm, 1)
    rollouts_per_second = (rollouts / float(msecs_taken)) * 1000
    log.info("c++ rollouts per second %.2f" % rollouts_per_second)



def test_not_in_database():
    some_simple_game = """
  (role white)
  (role black)

  (init o1)

  (legal white a)
  (legal white b)
  (legal black a)

  (<= (next o2) (does white a) (true o1))
  (<= (next o3) (does white b) (true o1))

  (<= (goal white 0) (true o1))
  (<= (goal white 10) (true o2))
  (<= (goal white 90) (true o3))

  (<= (goal black 0) (true o1))
  (<= (goal black 90) (true o2))
  (<= (goal black 10) (true o3))

  (<= terminal (true o2))
  (<= terminal (true o3))
    """

    mapping, sm, game_name = lookup.by_gdl(some_simple_game)
    assert game_name == "unknown"

    # run rollouts in c++
    msecs_taken, rollouts, _ = interface.depth_charge(sm, 1)
    rollouts_per_second = (rollouts / float(msecs_taken)) * 1000
    log.info("c++ rollouts per second %.2f" % rollouts_per_second)


def test_lookup_for_all_games():
    py.test.skip("this is super slow")
    failed = []
    known_to_fail = ['amazonsTorus_10x10', 'atariGoVariant_7x7', 'gt_two_thirds_4p', 'gt_two_thirds_6p', 'linesOfAction']
    for game in lookup.get_all_game_names():
        if game not in known_to_fail:
            try:
                sm = lookup.by_name(game, build_sm=False)
                log.verbose("DONE GETTING Statemachine FOR GAME %s %s" % (game, sm))
            except:
                failed.append(game)

    if failed:
        log.error("Failed games %s" % (failed,))
        assert False, failed

