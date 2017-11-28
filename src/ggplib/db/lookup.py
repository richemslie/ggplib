import os
import sys
import traceback

from collections import OrderedDict

import json

from ggplib.util import log
from ggplib.db.signature import get_index, build_symbol_map

from ggplib.propnet import getpropnet
from ggplib.statemachine import builder


class Model(object):
    def __init__(self):
        # will populate later
        self.roles = []
        self.bases = []
        self.actions = []

    def to_json(self):
        d = OrderedDict()
        d['roles'] = self.roles
        d['bases'] = self.bases
        d['actions'] = self.actions
        return json.dumps(d, indent=4)

    def load_from_file(self, filename):
        d = json.loads(open(filename).read())
        self.roles = d["roles"]
        self.bases = d["bases"]
        self.actions = d["actions"]

    def save_to_file(self, filename):
        open(filename, "w").write(self.to_json())

    def from_propnet(self, propnet):
        self.roles = [ri.role for ri in propnet.role_infos]
        self.bases = []
        self.actions = [[] for ri in propnet.role_infos]

        for b in propnet.base_propositions:
            self.bases.append(str(b.meta.gdl))

        for ri in propnet.role_infos:
            actions = self.actions[ri.role_index]

            for a in ri.inputs:
                actions.append(str(a.meta.gdl))


class GameInfo(object):
    def __init__(self, game, idx, sig, symbol_map):
        self.game = game
        self.idx = idx
        self.sig = sig
        self.symbol_map = symbol_map

        # lazy loads
        self.propnet = None
        self.sm = None
        self.model = None

    def lazy_load(self):
        if self.propnet is None:
            log.info("Lazy loading propnet and statemachine for %s" % self.game)
            self.propnet = getpropnet.get_with_game(self.game)
            self.sm = builder.build_sm(self.propnet)
            log.verbose("Lazy loading done for %s" % self.game)

            # create the model
            self.model = Model()
            self.model.from_propnet(self.propnet)
            print self.model.to_json()

    def get_sm(self):
        return self.sm.dupe()


class TempGameInfo(object):
    def __init__(self, game, propnet, sm):
        self.game = game

        self.propnet = propnet
        # XXX will leak sm, but thats ok
        self.sm = sm
        self.model = Model()
        self.model.from_propnet(self.propnet)

    def get_sm(self):
        return self.sm.dupe()


###############################################################################

class LookupFailed(Exception):
    pass


class Database:
    def __init__(self, directory):
        self.directory = directory
        self.idx_mapping = {}
        self.game_mapping = {}

    @property
    def all_games(self):
        return self.game_mapping.keys()

    def load(self, verbose=True):
        filenames = os.listdir(self.directory)
        mapping = {}
        for fn in sorted(filenames):
            # skip tmp files (XXX remove this once we remove the creation of tmp files)
            if fn.startswith("tmp"):
                continue

            if not fn.endswith(".kif"):
                continue

            game = fn.replace(".kif", "")
            if verbose:
                log.verbose("adding game: %s" % game)

            # get the gdl
            file_path = os.path.join(self.directory, fn)
            gdl_str = open(file_path).read()

            idx, sigs = get_index(gdl_str, verbose=False)

            # add in to the temporary mapping
            mapping[game] = idx, sigs

            # finally add a symbol map
            symbol_map = build_symbol_map(sigs, verbose=False)
            if symbol_map is None:
                log.warning("FAILED to add: %s" % fn)

        # use the mapping, and remap to using idx.
        idx_2_infos = {}
        for game, (idx, sigs) in mapping.items():
            idx_2_infos.setdefault(idx, []).append((game, sigs))

        # look for dupes
        for idx, infos in idx_2_infos.items():
            assert infos
            if len(infos) > 1:
                log.warning("DUPE GAMES: %s %s" % (idx, [game for game, _ in infos]))
                raise Exception("Dupes not allowed in database")

            game, sigs = infos[0]
            symbol_map = build_symbol_map(sigs, verbose=False)
            assert symbol_map is not None

            assert game not in self.game_mapping

            info = GameInfo(game, idx, sigs, symbol_map)
            self.idx_mapping[idx] = info
            self.game_mapping[game] = info

    def get_by_name(self, name):
        if name not in self.game_mapping:
            raise LookupFailed("Did not find game")
        info = self.game_mapping[name]
        info.lazy_load()
        return info

    def lookup(self, gdl_str):
        idx, sig = get_index(gdl_str, verbose=False)

        if idx not in self.idx_mapping:
            raise LookupFailed("Did not find game : %s" % idx)
        info = self.idx_mapping[idx]

        # create the symbol map for this gdl_str
        symbol_map = build_symbol_map(sig, verbose=False)

        new_mapping = {}

        # remap the roles back
        roles = info.sig.roles.items()
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

        log.info("Lookup - found game %s in database" % info.game)
        info.lazy_load()
        return info, new_mapping


###############################################################################

the_database = None


###############################################################################
# The API:

def get_database(db_path=None, verbose=True):
    if db_path is None:
        from ggplib.propnet.getpropnet import rulesheet_dir
        db_path = rulesheet_dir

    global the_database
    if the_database is None:
        if verbose:
            log.info("Building the database")
        the_database = Database(db_path)
        the_database.load(verbose=verbose)

    return the_database


def get_all_game_names():
    return get_database().all_games


def by_name(name, build_sm=True):
    db = get_database(verbose=False)
    return db.get_by_name(name)


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

        except Exception:
            etype, value, tb = sys.exc_info()
            traceback.print_exc()
            raise LookupFailed("Did not find game")

        return mapping, info

    except LookupFailed as exc:
        # creates temporary files
        log.error("Lookup failed: %s" % exc)
        propnet = getpropnet.get_with_gdl(gdl, "unknown_game")
        propnet_symbol_mapping = None
        sm = builder.build_sm(propnet)
        game_name = "unknown"

        return None, TempGameInfo(game_name, propnet, sm)
