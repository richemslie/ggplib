'''
Very hacked up script to update our all the kif files from tiltyard, using ggp-repository.

Example usage:

$ git clone https://github.com/ggp-org/ggp-repository.git
$ cd ggp-repository/war/root/games/
$ find . -name *.kif | xargs python $GGPLIB_PATH/src/ggplib/scripts/create_rulesheets.py

# update text by chopping from
# https://github.com/ggp-org/ggp-tiltyard/blob/master/src/ggp/tiltyard/scheduling/Scheduling.java

'''

text = '''
		// Game theory games
		new String[] { "gt_attrition", "gt_centipede",
				"gt_chicken", "gt_dollar", "gt_prisoner", "gt_ultimatum", "gt_staghunt",
				"gt_coordination", "gt_tinfoil", "gt_two_thirds_2p", "gt_two_thirds_4p",
				"gt_two_thirds_6p" },
		// Chinese checkers variants
		new String[] { "chineseCheckers1", "chineseCheckers2", "chineseCheckers3",
				"chineseCheckers4", "chineseCheckers6", "solitaireChineseCheckers" },
		// Sudoku variants
		new String[] { "sudokuGrade1", "sudokuGrade2", "sudokuGrade3", "sudokuGrade4",
				"sudokuGrade5", "sudokuGrade6E", "sudokuGrade6H" },
		// Futoshiki variants
		new String[] { "futoshiki4", "futoshiki5", "futoshiki6" },
		// FFA/TTC variants
		new String[] { "2pffa_zerosum", "2pffa", "3pffa", "4pffa",
				"2pttc", "3pttc", "4pttc", "ttcc4_2player", },
		// Checkers variants
		new String[] { "englishDraughts", "checkersSmall", "checkersTiny", "checkers",
				"chinook" },
		// Connect Four variants
		new String[] { "3pConnectFour", "connectFourLarger", "connectFourLarge",
				"connectFour", "connectFourSuicide", "connectFourSimultaneous",
				"connectFour_9x6", "connectFourSuicide_7x7" },
		// Tic-Tac-Toe variants
		new String[] { "ticTacToe", "nineBoardTicTacToe", "cittaceot", "ticTacToeLarge",
				"biddingTicTacToe", "ticTacToeLargeSuicide",
				"biddingTicTacToe_10coins", "nineBoardTicTacToePie" },
		// Gomoku (Connect Five) variants
		new String[] { "connect5", "gomoku_11x11", "gomoku_15x15", "gomoku_swap2_11x11",
		        "gomoku_swap2_15x15", },
		// Breakthrough variants
		new String[] { "knightThrough", "breakthroughWalls", "breakthrough",  "breakthroughSmall",
				"escortLatch", "breakthroughSuicideSmall" },
		// Dots-and-Boxes variants
		new String[] { "dotsAndBoxes", "dotsAndBoxesSuicide" },
		// Pentago variants
		new String[] { "pentago", "pentagoSuicide" },
		// Quarto variants
		new String[] { "quarto", "quartoSuicide" },
		// Knight's Tour variants
		new String[] { "knightsTour", "knightsTourLarge" },
		// Chess variants
		new String[] { "speedChess", "skirmishNew", "skirmishZeroSum", "chess_200", "shogi_ctk" },
		// Peg Jumping variants
		new String[] { "peg", "pegEuro" },
		// Hex variants
		new String[] { "hex", "hexPie", "majorities", "copolymer_4_pie" },
		// Amazons variants
		new String[] { "amazons_8x8", "amazons_10x10", "amazonsSuicide_10x10", "amazonsTorus_10x10" },
		// Queens variants
		new String[] { "queens06ug", "queens08lg", "queens08ug", "queens12ug", "queens16ug" },
		// Othello / Reversi variants
		new String[] { "reversi", "reversiSuicide" },
		// Go variants
		new String[] { "atariGo_7x7", "atariGoVariant_7x7", },
		// Games that fell into no other category, but didn't seem to be
		// significant enough to deserve their own individual categories.
		new String[] { "cephalopodMicro",  "maze", "eightPuzzle", "qyshinsu", "blocker",
				"sheepAndWolf", "max_knights", "untwistycomplex2", "zombieAttack1PL6",
				"urmAdd", "linesOfAction" },
		new String[] { "tron_10x10", "mineClearingSmall", "nonogram_5x5_1", "shmup",
		        "battlebrushes", "rubiksCube", "rubiksCubeSuperflip", "hidato19",
		        "hidato37", "madBishops" },
		// New games, that get an extra promotional boost because they're new or interesting
		new String[] { "gomoku_11x11", "gomoku_15x15", "gomoku_swap2_11x11", "gomoku_swap2_15x15",
		        "zombieAttack1PL6", "shogi_ctk", "urmAdd", "rubiksCubeSuperflip",
		        "linesOfAction", "atariGo_7x7", "atariGoVariant_7x7", },

'''

import os
import re
import sys

from ggplib.propnet.getpropnet import rulesheet_dir

def main():
    pattern = r'"([A-Za-z0-9_\./\\-]*)"'
    games = re.findall(pattern, text)

    mapping = {}
    for fn in sys.argv[1:]:
        a = fn
        # strip this off, comes from 'find ... | xargs ...'
        assert a.startswith("./")
        a = a[2:]

        # the directiory structure in ggp-repository is: game/version/x.kif.  If first version of the directory
        # structure is an implied v0.
        components = a.split('/')
        game = components[0]
        if len(components) == 2:
            version = 0
        else:
            assert len(components) == 3
            version = int(components[1].replace("v", ""))

        # skip games not interested in...
        if game not in games:
            continue

        # create our own mapping of most recent version of game
        if game in mapping:
            if version > mapping[game][0]:
                mapping[game] = (version, fn)
        else:
            mapping[game] = (version, fn)

    # all the games need to exist... or something is wrong
    print set(games) == set(mapping)

    # just copy to our destination_path the kif files
    for game in games:
        fn = mapping[game][1]
        cmd = "cp %s %s/%s.kif" % (fn, rulesheet_dir, game)
        print cmd
        os.system(cmd)

###############################################################################

if __name__ == "__main__":
    main()
