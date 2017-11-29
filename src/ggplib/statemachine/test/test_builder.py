import pprint
from ggplib.util import log
from ggplib.propnet import getpropnet
from ggplib.statemachine import builder


games = ["ticTacToe", "connectFour", "breakthrough", "hex", "speedChess", "reversi"]

_setup_once = False


def setup():
    global _setup_once
    if not _setup_once:
        from ggplib import interface
        interface.initialise_k273(1)

        import ggplib.util.log
        ggplib.util.log.initialise()


def get_propnets():
    for g in games:
        yield g, getpropnet.get_with_game(g)


def test_building_print():
    for game, propnet in get_propnets():
        print game, propnet
        builder.do_build(propnet, the_builder=builder.BuilderBase())


def test_building_desc():
    for game, propnet in get_propnets():
        log.warning("test_building_desc() for: %s" % game)
        desc = builder.do_build(propnet, the_builder=builder.BuilderDescription())
        pprint.pprint(desc)


def test_building_desc_variations():
    for game, propnet in get_propnets():
        log.warning("test_building_desc() for: %s" % game)

        desc = builder.build_standard_sm(propnet)
        pprint.pprint(desc)

        desc = builder.build_goals_only_sm(propnet)
        pprint.pprint(desc)

        desc = builder.build_combined_state_machine(propnet)
        pprint.pprint(desc)

        desc = builder.build_goalless_sm(propnet)
        pprint.pprint(desc)
