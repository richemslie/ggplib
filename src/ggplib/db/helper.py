from ggplib.db.store import get_root


def get_gdl_for_game(game, replace_map=None):
    ''' return the gdl from the store '''
    root_store = get_root()
    rulesheets_store = root_store.get_directory("rulesheets")

    gdl = rulesheets_store.load_contents(game + ".kif")
    if replace_map:
        for k, v in replace_map.items():
            gdl.replace(k, v)
    return gdl
