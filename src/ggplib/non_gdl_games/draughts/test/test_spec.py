# This Python file uses the following encoding: utf-8

from ggplib.non_gdl_games.draughts import spec


def test_create_8():
    b = spec.BoardDesc(8)
    for base in b.bases:
        print base

    assert b.mapping_from(1) == ('b', 8)
    assert b.mapping_from(2) == ('d', 8)
    assert b.mapping_from(3) == ('f', 8)
    assert b.mapping_from(4) == ('h', 8)

    assert b.mapping_from(5) == ('a', 7)
    assert b.mapping_from(6) == ('c', 7)

    assert b.mapping_from(21) == ('a', 3)
    assert b.mapping_from(29) == ('a', 1)
    assert b.mapping_from(32) == ('g', 1)

    assert b.mapping_to('a', 1) == 29
    assert b.mapping_to('h', 2) == 28
    assert b.mapping_to('b', 8) == 1


def test_create_10():
    b = spec.BoardDesc(10)

    assert b.mapping_from(1) == ('b', 10)
    assert b.mapping_from(2) == ('d', 10)
    assert b.mapping_from(3) == ('f', 10)
    assert b.mapping_from(4) == ('h', 10)
    assert b.mapping_from(5) == ('j', 10)

    assert b.mapping_from(6) == ('a', 9)
    assert b.mapping_from(7) == ('c', 9)

    assert b.mapping_from(36) == ('a', 3)

    assert b.mapping_from(46) == ('a', 1)
    assert b.mapping_from(50) == ('i', 1)

    assert b.mapping_to('a', 1) == 46
    assert b.mapping_to('h', 2) == 44
    assert b.mapping_to('b', 10) == 1


def test_diagonals_10():
    b = spec.BoardDesc(10)

    # diagonals for positions 46
    ne, nw, se, sw = b.get_diagonals_for_position(46)

    assert len(ne.steps) == 9
    assert ne.steps[0] == 41
    assert ne.steps[-1] == 5
    assert nw.steps == []
    assert se.steps == []
    assert sw.steps == []

    ne, nw, se, sw = b.get_diagonals_for_position(5)
    assert ne.steps == []
    assert nw.steps == []
    assert se.steps == []

    assert len(sw.steps) == 9
    assert sw.steps[0] == 10
    assert sw.steps[-1] == 46

    ne, nw, se, sw = b.get_diagonals_for_position(8)

    assert len(ne.steps) == 1
    assert len(nw.steps) == 1
    assert len(sw.steps) == 4
    assert len(se.steps) == 5

    assert ne.steps[0] == 3
    assert nw.steps[0] == 2
    assert se.steps[0] == 13
    assert sw.steps[0] == 12

    ne, nw, se, sw = b.get_diagonals_for_position(50)
    assert len(ne.steps) == 1
    assert len(nw.steps) == 8
    assert len(sw.steps) == 0
    assert len(se.steps) == 0


def test_legals_8():
    b = spec.BoardDesc(8)

    for l in b.all_legals:
        print l


def test_legals_10():
    b = spec.BoardDesc(10)

    for l in b.all_legals:
        print l


def test_legals_12():
    b = spec.BoardDesc(12)

    for l in b.all_legals:
        print l


def test_initial_state_8():
    desc = spec.BoardDesc(8)
    sm = spec.SM(desc)
    sm.print_board()
    sm.print_state()

    assert sm.whos_turn() == spec.WHITE


def test_initial_state_10():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.print_board()

    assert sm.whos_turn() == spec.WHITE

    assert not sm.is_empty(3)
    sm.clear(3)
    assert sm.is_empty(3)
    assert sm.get(3)[0] is None
    print "Clear 3:"
    sm.print_board()

    assert not sm.is_empty(32)
    sm.clear(32)
    assert sm.is_empty(3)
    assert sm.get(32)[0] is None
    print "Clear 32:"
    sm.print_board()

    sm.set(32, spec.BLACK, spec.KING)
    assert not sm.is_empty(32)
    assert sm.get(32)[0] == spec.BLACK
    assert sm.get(32)[1] == spec.KING
    print "Set 32 BK:"
    sm.print_board()

    sm.set(32, spec.WHITE, spec.KING)
    sm.set_interim_position(32)
    assert not sm.is_empty(32)
    assert sm.get(32)[0] == spec.WHITE
    assert sm.get(32)[1] == spec.KING

    print "Set 32 WK interim:"
    sm.print_board()

    for ii in range(16, 21):
        sm.set_captured(ii)

    print "set 16-20 BM captured:"
    sm.print_board()
    sm.print_state()


def test_initial_state_12():
    desc = spec.BoardDesc(12)
    sm = spec.SM(desc)
    sm.print_board()

    assert sm.whos_turn() == spec.WHITE


def dump_legals_non_capture_moves(sm):
    for role in (spec.WHITE, spec.BLACK):
        print spec.role_str(role), ":"
        for from_pos, what in sm.all_for_role(role):
            for to_pos in sm.non_capture_moves(role, from_pos, what):
                # print 'XXX', role, what, from_pos, to_pos
                legal_index = sm.board_desc.legal_mapping[role][what, from_pos, to_pos]
                print sm.board_desc.all_legals[legal_index]


def test_moves_man1():
    desc = spec.BoardDesc(8)
    sm = spec.SM(desc)
    sm.print_board()

    assert set(sm.non_capture_moves(spec.WHITE, 21, spec.MAN)) == set([17])
    assert set(sm.non_capture_moves(spec.WHITE, 23, spec.MAN)) == set([18, 19])
    assert set(sm.non_capture_moves(spec.WHITE, 1, spec.MAN)) == set([])
    assert set(sm.non_capture_moves(spec.WHITE, 32, spec.MAN)) == set([])

    assert set(sm.non_capture_moves(spec.BLACK, 12, spec.MAN)) == set([16])
    assert set(sm.non_capture_moves(spec.BLACK, 10, spec.MAN)) == set([14, 15])
    assert set(sm.non_capture_moves(spec.BLACK, 1, spec.MAN)) == set([])
    assert set(sm.non_capture_moves(spec.BLACK, 32, spec.MAN)) == set([])

    dump_legals_non_capture_moves(sm)


def test_moves_man2():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.print_board()

    sm.clear(10)
    sm.clear(18)
    sm.set(33, spec.WHITE, spec.KING)
    sm.print_board()

    def check(role, pos, what, check_list):
        assert set(sm.non_capture_moves(role, pos, what)) == set(check_list)

    check(spec.BLACK, 4, spec.MAN, [10])
    check(spec.BLACK, 5, spec.MAN, [10])
    check(spec.BLACK, 12, spec.MAN, [18])
    check(spec.BLACK, 20, spec.MAN, [24, 25])

    check(spec.WHITE, 35, spec.MAN, [30])
    check(spec.WHITE, 33, spec.KING, [28, 22, 29, 24])

    check(spec.WHITE, 46, spec.KING, [])

    dump_legals_non_capture_moves(sm)


def test_moves_king():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    fen = "W:WK6,K7,K8:BK41,K42,K43."
    sm.parse_fen(fen)
    sm.print_board()

    def check(pos, check_list):
        role, what, _, _ = sm.get(pos)
        assert set(sm.non_capture_moves(role, pos, what)) == set(check_list)

    check(6, [1, 11, 17, 22, 28, 33, 39, 44, 50])
    check(7, [1, 2, 11, 12, 16, 18, 23, 29, 34, 40, 45])
    check(8, [2, 3, 12, 13, 17, 19, 21, 24, 26, 30, 35])

    check(41, [5, 10, 14, 19, 23, 28, 32, 36, 37, 46, 47])
    check(42, [15, 20, 24, 26, 29, 31, 33, 37, 38, 47, 48])
    check(43, [16, 21, 25, 27, 30, 32, 34, 38, 39, 48, 49])


def check_immediate_captures(sm, pos, check_list):
    role, what, _, _ = sm.get(pos)
    res = [(m, c) for m, c, _ in list(sm.immediate_captures(role, pos, what))]
    assert set(res) == set(check_list)


def test_moves_captures1():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.print_board()

    for ii in range(26, 31):
        sm.set(ii, spec.BLACK, spec.KING)

    sm.print_board()

    check_immediate_captures(sm, 31, [(22, 27)])
    check_immediate_captures(sm, 32, [(23, 28), (21, 27)])
    check_immediate_captures(sm, 33, [(24, 29), (22, 28)])
    check_immediate_captures(sm, 34, [(25, 30), (23, 29)])
    check_immediate_captures(sm, 35, [(24, 30)])

    check_immediate_captures(sm, 31, [(22, 27)])
    check_immediate_captures(sm, 32, [(23, 28), (21, 27)])
    check_immediate_captures(sm, 33, [(24, 29), (22, 28)])
    check_immediate_captures(sm, 34, [(25, 30), (23, 29)])
    check_immediate_captures(sm, 35, [(24, 30)])


def test_moves_captures2():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.print_board()

    sm.print_board()
    for ii in range(1, 36):
        sm.clear(ii)

    for ii in range(36, 51):
        sm.set(ii, spec.BLACK, spec.KING)

    for ii in [1, 6, 10, 17, 21, 22, 29]:
        sm.set(ii, spec.WHITE, spec.MAN)

    sm.print_board()

    for ii in [1, 6, 10, 17, 21, 22, 29]:
        check_immediate_captures(sm, ii, [])

    check_immediate_captures(sm, 36, ([(4, 22), (9, 22), (13, 22), (18, 22)]))
    check_immediate_captures(sm, 37, ([(5, 10)]))
    check_immediate_captures(sm, 38, ([(15, 29), (16, 21), (20, 29), (24, 29)]))
    check_immediate_captures(sm, 39, ([]))
    check_immediate_captures(sm, 40, ([(7, 29), (12, 29), (18, 29), (23, 29)]))

    for ii in range(41, 51):
        check_immediate_captures(sm, ii, ([]))


def check_maximal_count(sm, pos, mc, check_list):
    role, what, _, _ = sm.get(pos)
    moves = []
    res_mc = sm.maximal_captures(role, pos, what, moves=moves)
    assert mc == res_mc
    assert set(moves) == set(check_list)


def test_maximal_jump():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.print_board()

    for ii in range(1, 36):
        sm.clear(ii)

    for ii in range(36, 51):
        sm.set(ii, spec.BLACK, spec.KING)

    for ii in [1, 6, 10, 17, 21, 22, 29]:
        sm.set(ii, spec.WHITE, spec.MAN)

    sm.print_board()

    check_maximal_count(sm, 36, 3, [4])
    check_maximal_count(sm, 37, 1, [5])
    check_maximal_count(sm, 38, 4, [15])
    check_maximal_count(sm, 39, 0, [])
    check_maximal_count(sm, 40, 3, [18])


def test_looping_captures1():
    """ best mc is 5, jumps over itself ending at 46.

  1 -  5      .   .   .   .   .
  6 - 10    .   ⛀   ⛀   .   .
 11 - 15      .   .   .   .   .
 16 - 20    .   .   .   .   .
 21 - 25      .   ⛀   .   .   .
 26 - 30    .   .   ⛃   .   ⛀
 31 - 35      .   ⛀   .   .   .
 36 - 40    .   .   .   .   .
 41 - 45      ⛀   .   .   .   .
 46 - 50    .   .   .   .   .
"""

    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)

    sm.print_board()

    sm.clear()

    sm.set(28, spec.WHITE, spec.KING)
    for ii in [22, 7, 8, 30, 32, 41]:
        sm.set(ii, spec.BLACK, spec.MAN)

    sm.print_board()
    check_maximal_count(sm, 28, 5, [11])

    sm.set_interim_position(28)
    sm.set(44, spec.BLACK, spec.KING)
    sm.set_captured(44)
    sm.print_board()

    check_maximal_count(sm, 28, 5, [11])

    sm.update_legal_choices()
    print [sm.board_desc.all_legals[x] for x in sm.choices[1]]


def test_looping_captures2():
    """ Can end up landing on oneself
  1 -  5      .   .   .   .   .
  6 - 10    .   .   ⛁   .   .
 11 - 15      .   ⛂   ⛂   .   .
 16 - 20    .   .   .   .   .
 21 - 25      ⛂   .   .   ⛂   .
 26 - 30    .   .   .   .   .
 31 - 35      .   .   .   .   .
 36 - 40    .   ⛂   .   ⛂   .
 41 - 45      .   .   .   .   .
 46 - 50    .   .   .   .   .

 """

    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)

    sm.parse_fen("B:BK8:W12,13,21,24,37,39")
    assert sm.whos_turn() == spec.BLACK

    sm.print_board()

    check_maximal_count(sm, 8, 6, [17, 19])

    sm.update_legal_choices()
    print [sm.board_desc.all_legals[x] for x in sm.choices[spec.WHITE]]


def route(sm, role, x):
    mapping = sm.board_desc.reverse_legal_mapping[role][x]
    what, from_pos, to_pos, _ = mapping
    s = spec.piece_str(what)[0].upper()
    return "%s %s:%s" % (spec.piece_str(what), from_pos, to_pos)


def test_legals_from_kings():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)

    sm.parse_fen("B:BK3,K12,K33:W17,20,7,2,44")
    sm.print_board()
    sm.update_legal_choices()

    print [route(sm, spec.BLACK,  x) for x in sm.choices[spec.BLACK]]

    assert len(sm.choices[spec.BLACK]) == 8
    check_maximal_count(sm, 3, 1, [25])
    check_maximal_count(sm, 12, 1, [1, 21, 26])
    check_maximal_count(sm, 33, 1, [6, 11, 15, 50])


def test_14_captures_complex_board():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.parse_fen("B:W6,9,10,11,20,21,22,23,30,K31,33,37,41,42,43,44,46:BK17,K24")
    sm.print_board()

    check_maximal_count(sm, 24, 14, [15, 35, 38])

    sm.update_legal_choices()
    print [sm.board_desc.all_legals[x] for x in sm.choices[1]]
    sm.print_board()


def test_white_to_win():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    sm.parse_fen("W:WK13:B7,8,9,10,17,18,19,20,21,30,31,32,33,34,41,42,43,44")
    sm.print_board()

    sm.update_legal_choices()
    print [route(sm, spec.WHITE, x) for x in sm.choices[spec.WHITE]]

    print "Not sure this is correct..."


def test_maximal_jump2():
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)

    sm.parse_fen("W:WK32:B31,42,21,22,19,10,39,29")
    sm.print_board()

    check_maximal_count(sm, 32, 2, [14])

    sm.parse_fen("W:WK32,37:B31,42,21,22,19,10,39,29")
    sm.print_board()
    check_maximal_count(sm, 37, 3, [26])
    sm.print_board()
