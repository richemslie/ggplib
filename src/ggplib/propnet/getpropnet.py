import os
import glob
import uuid
import importlib

from ggplib.util import log
from ggplib.util.runcmd import run
from ggplib.util.util import path_back

from ggplib.propnet.factory import Propnet, create_component
from ggplib import symbols

rulesheet_dir = os.path.join(path_back(__file__, 3), "rulesheets")
props_dir = os.path.join(path_back(__file__, 1), "props")


def kif_filename_to_propfile(kif_filename):
    basename = os.path.basename(kif_filename)
    basename = basename.replace(".", "_")
    if basename[0] in "0123456789":
        basename = "props_" + basename

    props_file = os.path.join(props_dir, basename + ".py")
    return basename, props_file


def load_module(kif_filename):
    ''' attempts to load a python module with the same filename.  If it does not exist, will run
        java and use ggp-base to create the module. '''

    basename, props_file = kif_filename_to_propfile(kif_filename)
    for cmd in ["java -J-XX:+UseSerialGC -J-Xmx8G propnet_convert.Convert %s %s" % (kif_filename, props_file),
                "java propnet_convert.Convert %s %s" % (kif_filename, props_file),
                "SOMETHING IS BROKEN in install ..."]:
        try:
            # rather unsafe cache, if kif file changes underneath our feet - tough luck.
            module = importlib.import_module("ggplib.props." + basename)
            break
        except ImportError:
            # run java ggp-base to create a propnet.  The resultant propnet will be in props_dir, which can be imported.
            log.debug("Running: %s" % cmd)
            return_code, out, err = run(cmd, shell=True, timeout=60)
            if return_code != 0:
                log.warning("Error code: %s" % err)
            else:
                for l in out.splitlines():
                    log.info("... %s" % l)

            if "SOMETHING" in cmd:
                raise

    return module


def get_with_filename(filename):
    module = load_module(filename)
    symbol_factory = symbols.SymbolFactory()
    components = {}
    for c in [create_component(e, symbol_factory) for e in module.entries]:
        if c:
            components[c.cid] = c

    propnet = Propnet(module.roles, components)
    propnet.init()
    propnet.verify()
    propnet.reorder_base_propositions()
    propnet.reorder_legals()
    propnet.reorder_components()
    propnet.verify()

    return propnet


def get_filename_for_game(game):
    return os.path.join(rulesheet_dir, game + ".kif")


def get_with_game(game):
    return get_with_filename(get_filename_for_game(game))


def get_with_gdl(gdl, name_hint=""):
    # create a temporary file:
    name_hint += "__" + str(uuid.uuid4())
    name_hint = name_hint.replace('-', '_')
    name_hint = name_hint.replace('.', '_')

    # ensure we have gdl symbolized
    if isinstance(gdl, str):
        gdl = symbols.SymbolFactory().to_symbols(gdl)

    # this is very very very likely to be unique, but perhaps we should still check XXX
    name = "tmp_%s" % name_hint
    fn = os.path.join(os.path.join(rulesheet_dir, name + ".kif"))
    log.debug('writing kif file %s' % fn)

    # write file
    f = open(fn, "w")
    for l in gdl:
        print >>f, l
    f.close()

    propnet = get_with_filename(fn)

    # cleanup temp files afterwards
    basename, props_file = kif_filename_to_propfile(fn)
    os.remove(fn)
    os.remove(props_file)
    for f in glob.glob(os.path.join(props_dir, "__pycache__", basename) + '*.pyc'):
        os.remove(str(f))

    return propnet
