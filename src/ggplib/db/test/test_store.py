import os
from ggplib.db import store


def test_create():
    root = store.get_root()
    rulesheets = root.get_directory("rulesheets")
    games = root.get_directory("games")
    print rulesheets
    print games

    try:
        root.get_directory("i dont exist")
        assert False, "does not get here"
    except store.StoreException:
        pass

    # pretty unsafe test, but whatever
    abc = root.get_directory("abc", create=True)
    assert root.get_directory("abc", create=True) == abc
    os.rmdir(abc.path)


def test_import_store():
    root = store.get_root()
    rulesheets = root.get_directory("rulesheets")

    assert len(rulesheets.listdir("connectFour.kif")) == 1
    assert len(rulesheets.listdir("ticTacToe.kif")) == 1
    assert len(rulesheets.listdir("*.kif")) > 1
    print rulesheets.listdir("*.kif")

