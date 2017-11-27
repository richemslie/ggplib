from ggplib.util import log
from ggplib.propnet.getpropnet import get_with_game
from ggplib.statemachine import builder
from ggplib import interface
from ggplib.statemachine.depthcharges import depth_charges


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
        yield g, get_with_game(g)


def test_building_print():
    for game, propnet in get_propnets():
        print game, propnet
        builder.do_build(propnet, the_builder=builder.BuilderBase(propnet))


def test_building_json():
    for game, propnet in get_propnets():
        log.warning("test_building_json() for: %s" % game)
        sm = builder.do_build(propnet, the_builder=builder.BuilderJson(propnet))

        # test from c++
        log.info("Doing depth charges on %s" % sm)
        msecs_taken, rollouts, _ = interface.depth_charge(sm, 1)
        rollouts_per_second = (rollouts / float(msecs_taken)) * 1000
        log.info("rollouts per second %.2f" % rollouts_per_second)

        # test from python
        depth_charges(sm, 1)


def test_variations():
    def go(game, fn, propnet, do_depth_charges=True):
        log.verbose("Doing %s for %s" % (fn.func_name, game))
        sm = fn(propnet)
        sm.reset()

        sm2 = sm.dupe()
        interface.dealloc_statemachine(sm)
        sm2.reset()

        if do_depth_charges:
            log.info("Doing depth charges on %s" % sm2)
            msecs_taken, rollouts, _ = interface.depth_charge(sm2, 2)
            rollouts_per_second = (rollouts / float(msecs_taken)) * 1000
            log.info("rollouts per second %.2f" % rollouts_per_second)

            # test from python
            depth_charges(sm2, 1)

        interface.dealloc_statemachine(sm2)

    for game, propnet in get_propnets():
        print game, propnet

        go(game, builder.build_standard_sm, propnet)
        go(game, builder.build_goals_only_sm, propnet, do_depth_charges=False)
        go(game, builder.build_combined_state_machine, propnet)
        go(game, builder.build_goalless_sm, propnet)
        go(game, builder.build_sm, propnet)
