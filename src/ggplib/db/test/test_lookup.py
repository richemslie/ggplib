import pdb
import sys
import traceback

import pytest

from ggplib.util import log

from ggplib.db import lookup, signature
from ggplib.db.helper import get_gdl_for_game, lookup_all_games

from ggplib import interface
from ggplib.statemachine.depthcharges import depth_charges


######################################################################

def setup():
    from ggplib.util.init import setup_once
    setup_once()

def test_compare_same():
    game_a = get_gdl_for_game("ticTacToe")
    game_b = get_gdl_for_game("ticTacToe")

    idx1, sig1 = signature.get_index(game_a, verbose=False)
    idx2, sig2 = signature.get_index(game_b, verbose=False)

    sigs1 = sig1.sigs[:]
    sigs1.sort()

    sigs2 = sig1.sigs[:]
    sigs2.sort()

    for x, y in zip(sig1.sigs, sig2.sigs):
        x, y = x.zero_sig, y.zero_sig
        assert x == y


def test_with_database():
    gdl_str = get_gdl_for_game("connectFour")

    mapping, info = lookup.by_gdl(gdl_str)

    assert mapping is None
    assert info.game == "connectFour"
    sm = info.get_sm()

    # ensure keeps returning valid statemachines
    for ii in range(10):
        new_mapping, new_info = lookup.by_gdl(gdl_str)
        new_sm = new_info.get_sm()

        assert new_mapping is None
        assert new_info is info
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

    mapping, info = lookup.by_gdl(some_simple_game)
    assert info.game == "unknown"
    sm = info.get_sm()

    # run rollouts in c++
    msecs_taken, rollouts, _ = interface.depth_charge(sm, 1)
    rollouts_per_second = (rollouts / float(msecs_taken)) * 1000
    log.info("c++ rollouts per second %.2f" % rollouts_per_second)


# this could be potentially super slow first time around
@pytest.mark.slow
def test_lookup_for_all_games():
    lookup_all_games()
