from ggplib.util import log
from ggplib import interface

from ggplib.db.store import get_root
from ggplib.db import lookup


def get_gdl_for_game(game, replace_map=None):
    ''' return the gdl from the store '''
    root_store = get_root()
    rulesheets_store = root_store.get_directory("rulesheets")

    gdl = rulesheets_store.load_contents(game + ".kif")
    if replace_map:
        for k, v in replace_map.items():
            gdl.replace(k, v)
    return gdl


def lookup_all_games():
    # ensure things are initialised
    from ggplib.util.init import setup_once
    setup_once()

    failed = []
    known_to_fail = ['amazonsTorus_10x10', 'atariGoVariant_7x7', 'gt_two_thirds_4p', 'gt_two_thirds_6p', 'linesOfAction']
    for game in lookup.get_all_game_names():
        if game not in known_to_fail:
            try:
                game_info = lookup.by_name(game, build_sm=False)
                assert game_info.game == game
                sm = game_info.get_sm()

                # run some depth charges to ensure we have valid statemachine
                interface.depth_charge(sm, 1)

                log.verbose("DONE GETTING Statemachine FOR GAME %s %s" % (game, sm))
            except lookup.LookupFailed as exc:
                log.warning("Failed to lookup %s: %s" % (game, exc))
                failed.append(game)

    if failed:
        log.error("Failed games %s" % (failed,))
        assert False, failed


