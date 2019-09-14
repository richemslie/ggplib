import os

from ggplib.non_gdl_games.draughts import gencode


def setup():
    from ggplib.util.init import setup_once
    setup_once(__file__)

    if os.path.exists("tmp.cpp"):
        os.unlink("tmp.cpp")


def test_gen_code():
    gens = [gencode.GenCodeFn(6)]
    gencode.create_cpp_file("tmp.cpp", gens)
    os.unlink("tmp.cpp")
