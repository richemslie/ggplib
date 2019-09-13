from ggplib.non_gdl_games.draughts import spec, perft
from ggplib.non_gdl_games.draughts.test.test_spec import check_maximal_count


def test_407():
    # initial position with all men replaced by kings
    fen = "W:WK4,K5,K15,K16,K26,K36,K46:B7,8,11,13,19-21,29-31,33,38,41,42"
    assert perft.perft(fen, 2, True) == [407, 4501]

    sm = spec.SM(spec.BoardDesc(10))
    sm.parse_fen(fen)
    sm.update_legal_choices()

    print len(sm.choices[spec.WHITE])
    print [sm.board_desc.all_legals[x] for x in sm.choices[spec.WHITE]]


def test_path_vs_endpoint():
    # ZZZ MAN beats flying KING example
    desc = spec.BoardDesc(10)
    sm = spec.SM(desc)
    fen = "W:WK48:B31,42,21,22,19,10,39,29"

    sm.parse_fen(fen)
    sm.print_board()

    check_maximal_count(sm, 48, 6, [34, 37])

    # follow both paths
    def play(sm, move_to, expected_moves=1):
        sm_next = sm.clone()
        sm_next.update_legal_choices()

        assert expected_moves == len(sm_next.choices[0])

        choice = None
        for legal in sm_next.choices[0]:
            mapping = sm.board_desc.reverse_legal_mapping[spec.WHITE][legal]
            what, from_pos, to_pos, _ = mapping
            print "%s %s:%s" % (spec.piece_str(what), from_pos, to_pos)
            if to_pos == move_to:
                assert choice is None
                choice = legal

        assert choice is not None
        s = spec.piece_str(what)[0].upper()

        sm_next.play_move(spec.JointMove((choice, sm_next.choices[1][0])))
        sm_next.print_board()
        return sm_next

    sm_next = play(sm, 34, 2)
    sm_next = play(sm_next, 12)
    sm_next = play(sm_next, 26)
    sm_next = play(sm_next, 37)
    sm_next = play(sm_next, 14)
    sm_next = play(sm_next, 5)

    sm_next = play(sm, 37, 2)
    sm_next = play(sm_next, 26)
    sm_next = play(sm_next, 17, 2) # the other is 8, but different end point
    sm_next = play(sm_next, 28, 2) # the other is 33, but different end point
    sm_next = play(sm_next, 14)
    sm_next = play(sm_next, 5)

    # so move 48x5 has different captures... just wanted to prove that to myself!
