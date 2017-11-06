import pdb
import sys
import traceback

from ggplib.propnet import lookup

blacklist = ["linesOfAction"]

def test_compare_same():
    game_a = "\n".join(str(t) for t in lookup.get_gdl_for_game("ticTacToe"))
    game_b = "\n".join(str(t) for t in lookup.get_gdl_for_game("ticTacToe"))

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
    db = lookup.get_database()
    tic_tac_toe_str = "\n".join(str(t) for t in lookup.get_gdl_for_game("ticTacToe"))

    propnet = lookup.get_propnet(tic_tac_toe_str)

    # ensure keeps returning same propnet
    for ii in range(10):
        assert propnet == lookup.get_propnet(tic_tac_toe_str)
###############################################################################

def main():
    print "Note: Will be slow first time around."
    for game in lookup.get_all_game_names():
        if game in blacklist:
            continue
        propnet = lookup.get_propnet_by_name(game)
        print "DONE GETTING PROPNET FOR GAME", game, propnet

if __name__ == "__main__":
    try:
        main()

    except:
        etype, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
