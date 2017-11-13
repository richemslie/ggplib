import pdb
import sys
import traceback

from ggplib.util import log

from ggplib.db import lookup


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
    f = open(get_filename_for_game("ticTacToe"))
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
    gdl_str = get_gdl_for_game("ticTacToe")

    propnet, mapping, sm, game_name = lookup.by_gdl(gdl_str)
    assert game_name == "ticTacToe"
    assert mapping is None

    # ensure keeps returning same propnet
    for ii in range(10):
        new_propnet, new_mapping, new_sm, new_game_name = lookup.by_gdl(gdl_str)

        assert new_game_name == "ticTacToe"
        assert new_mapping is None
        assert new_propnet == propnet
        assert id(new_propnet) == id(propnet)
        assert new_sm != sm
        assert id(new_sm) != id(sm)


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

    propnet, mapping, sm, game_name = lookup.by_gdl(some_simple_game)
    assert game_name == "unknown"


def test_lookup_for_all_games():
    log.verbose("Note: Will be slow first time around.")
    failed = []
    known_to_fail = ['amazonsTorus_10x10', 'atariGoVariant_7x7', 'gt_two_thirds_4p', 'gt_two_thirds_6p', 'linesOfAction']
    for game in lookup.get_all_game_names():
        if game not in known_to_fail:
            try:
                propnet, _ = lookup.by_name(game, build_sm=False)
                log.verbose("DONE GETTING PROPNET FOR GAME %s %s" % (game, propnet))
            except:
                failed.append(game)

    if failed:
        log.error("Failed games %s" % (failed,))
        assert False, failed

