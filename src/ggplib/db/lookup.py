import sys
import traceback

from ggplib.util import log
from ggplib.statemachine import builder
from ggplib.db import signature


class GameInfo(object):
    def __init__(self, game, gdl_str):
        self.game = game
        self.gdl_str = gdl_str

        # might be None, depends on whether we grab it from sig.json
        self.idx = None

        # lazy loads in get_symbol_map()
        self.sigs = None
        self.symbol_map = None

        # lazy loads
        self.sm = None
        self.model = None

    def get_symbol_map(self):
        if self.sigs is None:
            idx, self.sigs = signature.get_index(self.gdl_str, verbose=False)
            if self.idx is not None:
                assert self.idx == idx
            else:
                self.idx = idx

            self.symbol_map = signature.build_symbol_map(self.sigs, verbose=False)

    def lazy_load(self, the_game_store):
        if self.sm is None:
            # ok here we can cache the game XXX

            self.model, self.sm = builder.build_sm(self.gdl_str,
                                                   the_game_store=the_game_store,
                                                   add_to_game_store=True)

            log.verbose("Lazy loading done for %s" % self.game)

    def get_sm(self):
        return self.sm.dupe()


class TempGameInfo(object):
    def __init__(self, game, gdl_str, sm, model):
        self.game = game
        self.gdl_str = gdl_str
        self.sm = sm
        self.model = model

    def get_sm(self):
        return self.sm.dupe()


###############################################################################

class LookupFailed(Exception):
    pass


class GameDatabase:
    def __init__(self, root_store):
        self.root_store = root_store

        self.rulesheets_store = root_store.get_directory("rulesheets")
        self.games_store = root_store.get_directory("games", create=True)

        self.idx_mapping = {}
        self.game_mapping = {}

    @property
    def all_games(self):
        return self.game_mapping.keys()

    def load(self, verbose=True):
        if verbose:
            log.info("Building the database")

        filenames = self.rulesheets_store.listdir("*.kif")
        for fn in sorted(filenames):
            # skip tmp files
            if fn.startswith("tmp"):
                continue

            game = fn.replace(".kif", "")

            # get the gdl
            gdl_str = self.rulesheets_store.load_contents(fn)

            info = GameInfo(game, gdl_str)

            # first does the game directory exist?
            the_game_store = self.games_store.get_directory(game, create=True)
            if the_game_store.file_exists("sig.json"):
                info.idx = the_game_store.load_json("sig.json")['idx']

            else:
                if verbose:
                    log.verbose("Creating signature for %s" % game)

                info.get_symbol_map()

                if info.symbol_map is None:
                    log.warning("FAILED to add: %s" % game)
                    raise Exception("FAILED TO add %s" % game)

                # save as json
                assert info.idx is not None
                the_game_store.save_json("sig.json", dict(idx=info.idx))

            assert info.idx is not None
            if info.idx in self.idx_mapping:
                other_info = self.idx_mapping[info.idx]
                log.warning("DUPE GAMES: %s %s!=%s" % (info.idx, game, other_info.game))
                raise Exception("Dupes not allowed in database")

            self.idx_mapping[info.idx] = info
            self.game_mapping[info.game] = info

    def get_by_name(self, name):
        if name not in self.game_mapping:
            raise LookupFailed("Did not find game: %s" % name)
        info = self.game_mapping[name]

        # for side effects
        info.get_symbol_map()
        the_game_store = self.games_store.get_directory(name)
        info.lazy_load(the_game_store)

        return info

    def lookup(self, gdl_str):
        idx, sig = signature.get_index(gdl_str, verbose=False)

        if idx not in self.idx_mapping:
            raise LookupFailed("Did not find game : %s" % idx)
        info = self.idx_mapping[idx]

        info.get_symbol_map()

        # create the symbol map for this gdl_str
        symbol_map = signature.build_symbol_map(sig, verbose=False)

        new_mapping = {}

        # remap the roles back
        roles = info.sigs.roles.items()
        for ii in range(len(roles)):
            match = "role%d" % ii
            for k1, v1 in roles:
                if v1 == match:
                    for k2, v2 in sig.roles.items():
                        if v2 == match:
                            new_mapping[k2] = k1
                    break

        # remap the other symbols
        for k1, v1 in info.symbol_map.items():
            new_mapping[symbol_map[k1]] = v1

        # remove if the keys/values all the same in new_mapping
        all_same = True
        for k, v in new_mapping.items():
            if k != v:
                all_same = False
                break
        if all_same:
            new_mapping = None

        # log.info("Lookup - found game %s in database" % info.game)

        the_game_store = self.games_store.get_directory(info.game)
        info.lazy_load(the_game_store)

        return info, new_mapping


###############################################################################
# The API:

the_database = None
def get_database(verbose=True):
    global the_database
    if the_database is None:
        from ggplib.db.store import get_root
        the_database = GameDatabase(get_root())
        the_database.load(verbose=verbose)

    return the_database


def get_all_game_names():
    return get_database().all_games


def by_name(name, build_sm=True):
    try:
        db = get_database(verbose=False)
        return db.get_by_name(name)

    except Exception as exc:
        # creates temporary files
        msg = "Lookup of %s failed: %s" % (name, exc)
        log.error(msg)
        log.error(traceback.format_exc())
        raise LookupFailed(msg)

def by_gdl(gdl):
    try:
        gdl_str = gdl
        if not isinstance(gdl, str):
            lines = []
            for s in gdl:
                lines.append(str(s))
            gdl_str = "\n".join(lines)

        db = get_database()
        try:
            info, mapping = db.lookup(gdl_str)

        except LookupFailed as exc:
            etype, value, tb = sys.exc_info()
            traceback.print_exc()
            raise LookupFailed("Did not find game %s" % exc)

        return mapping, info

    except Exception as exc:
        # creates temporary files
        log.error("Lookup failed: %s" % exc)

        model, sm = builder.build_sm(gdl)
        info = TempGameInfo("unknown", gdl, sm, model)
        return None, info
