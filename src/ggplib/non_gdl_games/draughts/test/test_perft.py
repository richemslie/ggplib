''' unskip to run all tests, but it will take ages. '''

import py
from ggplib.non_gdl_games.draughts.perft import perft


def test_perft_fast():
    # initial position with all men replaced by kings
    fen = "W:WK31,K32,K33,K34,K35,K36,K37,K38,K39,K40,K41,K42,K43,K44,K45,K46,K47,K48,K49,K50:BK1," \
          "K2,K3,K4,K5,K6,K7,K8,K9,K10,K11,K12,K13,K14,K15,K16,K17,K18,K19,K20."

    assert perft(fen, 6) == [17, 79, 352, 1399, 7062, 37589]

    # 5 men for each side one row away from promotion
    fen = "W:W6,7,8,9,10:B41,42,43,44,45."
    assert perft(fen, 5) == [9, 81, 795, 7578, 86351]

    # inital state:
    fen = "W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:" \
          "B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"
    assert perft(fen, 5) == [9, 81, 658, 4265, 27117]

    # 14 captures crazyiness
    fen = "B:W6,9,10,11,20,21,22,23,30,K31,33,37,41,42,43,44,46:BK17,K24"
    assert perft(fen, 5) == [14, 55, 1168, 5432, 87195]

    # end game
    fen = "W:W25,27,28,30,32,33,34,35,37,38:B12,13,14,16,18,19,21,23,24,26"
    assert perft(fen, 9) == [6, 12, 30, 73, 215, 590, 1944, 6269, 22369]


def test_perft_slow():
    py.test.skip("too slow")

    # initial position with all men replaced by kings
    fen = "W:WK31,K32,K33,K34,K35,K36,K37,K38,K39,K40,K41,K42,K43,K44,K45,K46,K47,K48,K49,K50:BK1," \
          "K2,K3,K4,K5,K6,K7,K8,K9,K10,K11,K12,K13,K14,K15,K16,K17,K18,K19,K20."

    assert perft(fen, 8) == [17, 79, 352, 1399, 7062, 37589, 217575, 1333217]

    # 5 men for each side one row away from promotion
    fen = "W:W6,7,8,9,10:B41,42,43,44,45."
    assert perft(fen, 7) == [9, 81, 795, 7578, 86351, 936311, 11448262]

    # inital state:
    fen = "W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:" \
          "B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"
    assert perft(fen, 7) == [9, 81, 658, 4265, 27117, 167140, 1049442]

    # 14 captures crazyiness
    fen = "B:W6,9,10,11,20,21,22,23,30,K31,33,37,41,42,43,44,46:BK17,K24"
    assert perft(fen, 7) == [14, 55, 1168, 5432, 87195, 629010, 9041010]

    # end game
    fen = "W:W25,27,28,30,32,33,34,35,37,38:B12,13,14,16,18,19,21,23,24,26"
    assert perft(fen, 12) == [6, 12, 30, 73, 215, 590, 1944, 6269, 22369, 88050, 377436, 1910989]


def test_perft_killer_mode_fast():
    # inital state:
    fen = "W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:" \
          "B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"
    assert perft(fen, 5, True) == [9, 81, 658, 4265, 27117]

    # 14 captures crazyiness
    fen = "B:W6,9,10,11,20,21,22,23,30,K31,33,37,41,42,43,44,46:BK17,K24"
    assert perft(fen, 5, True) == [14, 55, 1168, 5165, 84326]

    # end game
    fen = "W:W25,27,28,30,32,33,34,35,37,38:B12,13,14,16,18,19,21,23,24,26"
    assert perft(fen, 9, True) == [6, 12, 30, 73, 215, 590, 1944, 6269, 22369]


def test_perft_killer_mode():
    py.test.skip("too slow")

    # inital state:
    fen = "W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:" \
          "B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"
    assert perft(fen, 7, True) == [9, 81, 658, 4265, 27117, 167140, 1049442]

    # 14 captures crazyiness
    fen = "B:W6,9,10,11,20,21,22,23,30,K31,33,37,41,42,43,44,46:BK17,K24"
    assert perft(fen, 7, True) == [14, 55, 1168, 5165, 84326, 573965, 8476150]

    # end game
    fen = "W:W25,27,28,30,32,33,34,35,37,38:B12,13,14,16,18,19,21,23,24,26"
    assert perft(fen, 12, True) == [6, 12, 30, 73, 215, 590, 1944, 6269, 22369, 88043, 377339, 1908829]
