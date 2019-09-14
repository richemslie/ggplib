'''
Rulebook unit tests - suggested by rhalbersma, and adapted from:
        https://github.com/rhalbersma/dctl/blob/master/test/src/core/model/international.cpp
'''

from ggplib.non_gdl_games.draughts import desc


VERBOSE = True


def setup():
    from ggplib.util.init import setup_once
    setup_once(__file__)


class RuleBookRunnerCpp(object):
    def __init__(self, doc, fen, expect_legals):
        self.board_desc = desc.BoardDesc(10)
        self.fen = fen
        self.expect_legals = expect_legals

        print
        print (len(doc) + 1) * "="
        print doc
        print (len(doc) + 1) * "="
        print

        self.sm = desc.create_sm(self.board_desc, self.fen)

    def print_board(self, sm):
        if VERBOSE:
            self.board_desc.print_board_sm(sm)

    def gen_moves(self, sm):
        ls0, ls1 = sm.get_legal_state(0), sm.get_legal_state(1)

        joint_moves = []

        # cross product of legals
        for ii in range(ls0.get_count()):
            for jj in range(ls1.get_count()):
                joint_move = sm.get_joint_move()
                joint_move.set(0, ls0.get_legal(ii))
                joint_move.set(1, ls1.get_legal(jj))
                joint_moves.append(joint_move)

        return joint_moves

    # follow both paths
    def play(self, basestate):
        role = self.board_desc.whos_turn(basestate)
        opponent = desc.BLACK if role == desc.WHITE else desc.WHITE
        for move in self.gen_moves(self.sm):
            mapping = self.board_desc.get_legal_mapping(role, move.get(role))
            what, from_pos, to_pos, _ = mapping
            print "%s %s-%s" % (desc.piece_str(what), from_pos, to_pos)

            self.sm.update_bases(basestate)
            base_state_next = self.sm.new_base_state()
            self.sm.next_state(move, base_state_next)
            self.sm.update_bases(base_state_next)

            captured = (self.board_desc.piece_count(base_state_next, opponent) <
                        self.board_desc.piece_count(basestate, opponent))
            self.print_board(self.sm)

            if self.board_desc.check_interim_status(base_state_next):
                for _, to_pos, _ in self.play(base_state_next):
                    yield from_pos, to_pos, True
            else:
                yield from_pos, to_pos, captured

    def run(self):
        self.print_board(self.sm)

        moves = set()

        for from_pos, to_pos, captures in self.play(self.sm.get_current_state()):
            if captures:
                move = "%02dx%02d" % (from_pos, to_pos)
            else:
                move = "%02d-%02d" % (from_pos, to_pos)
            moves.add(move)

        assert set(moves) == set(self.expect_legals)

###############################################################################


def run_test(doc, fen, expect_legals):
    RuleBookRunnerCpp(doc, fen, expect_legals).run()


def french_tutorial(test_fn):
    """ Positions from the international rules (French tutorial):
        http://www.ffjd.fr/Web/index.php?page=reglesdujeu
    """

    doc = "white pawn move direction / art 3.4"
    fen = "W:W28"
    legals = ["28-22", "28-23"]
    test_fn(doc, fen, legals)

    doc = "pawn promotion / art 3.5"
    fen = "W:W8"
    legals = ["08-02", "08-03"]
    test_fn(doc, fen, legals)

    doc = "white king move range / art 3.9"
    fen = "W:WK28"
    legals = ["28-22", "28-17", "28-11", "28-06",
              "28-23", "28-19", "28-14", "28-10", "28-05",
              "28-32", "28-37", "28-41", "28-46",
              "28-33", "28-39", "28-44", "28-50"]
    test_fn(doc, fen, legals)

    doc = "white king move range / art 3.9"
    fen = "W:WK28"
    legals = ["28-22", "28-17", "28-11", "28-06",
              "28-23", "28-19", "28-14", "28-10", "28-05",
              "28-32", "28-37", "28-41", "28-46",
              "28-33", "28-39", "28-44", "28-50"]
    test_fn(doc, fen, legals)

    doc = "black king move range / Art. 3.9"
    fen = "B:BK1"
    legals = ["01-06", "01-07", "01-12", "01-18", "01-23",
              "01-29", "01-34", "01-40", "01-45"]
    test_fn(doc, fen, legals)

    doc = "pawn jump / Art. 4.2"
    fen = "W:W28,32:B23"
    legals = ["28x19"]
    test_fn(doc, fen, legals)

    doc = "king jump range / Art. 4.3"
    fen = "W:WK46:B23"
    legals = ["46x19", "46x14", "46x10", "46x05"]
    test_fn(doc, fen, legals)

    doc = "pawn jump continuation / Art. 4.5"
    fen = "W:W15:B8,19,20"
    legals = ["15x02"]
    test_fn(doc, fen, legals)

    doc = "king jump continuation / Art. 4.6"
    fen = "W:WK47:B9,12,33"
    legals = ["47x17", "47x21", "47x26"]
    test_fn(doc, fen, legals)

    doc = "no passing jump removal / Art. 4.8"
    fen = "W:WK41,49:B9,10,12,19,38"
    legals = ["41x43"]
    test_fn(doc, fen, legals)

    doc = "quantity precedence / Art. 4.13"
    fen = "W:W48:B24,K31,34,K42,43"
    legals = ["48x19"]
    test_fn(doc, fen, legals)


def italian_rules(test_fn):
    """ Positions from the official international rules (Italian translation):
        http://www.fid.it/regolamenti/2008/RegTec_CAPO_II.pdf
    """

    doc = "KingMoveRange / Art. 3.9"
    fen = "W:WK23"
    legals = ["23-18", "23-12", "23-07", "23-01",
              "23-19", "23-14", "23-10", "23-05",
              "23-28", "23-32", "23-37", "23-41", "23-46",
              "23-29", "23-34", "23-40", "23-45"]
    test_fn(doc, fen, legals)

    doc = "PawnJumpDirections / Art. 4.2"
    fen = "W:W35:B30,K40"
    legals = ["35x24", "35x44"]
    test_fn(doc, fen, legals)

    doc = "KingJumpRange / Art. 4.3"
    fen = "W:WK41:B23"
    legals = ["41x19", "41x14", "41x10", "41x05"]
    test_fn(doc, fen, legals)

    doc = "PawnJumpContinuation / Art. 4.5"
    fen = "W:W47:B13,14,22,24,31,34,K41,44"
    legals = ["47x49"]
    test_fn(doc, fen, legals)

    doc = "KingJumpContinuation / Art. 4.6"
    fen = "W:WK1:B7,9,17,19,20,30,31,33,43,44"
    legals = ["01x15"]
    test_fn(doc, fen, legals)

    doc = "NoPassingJumpRemoval / Art. 4.8"
    fen = "B:W27,28,38,39,42:BK25"
    legals = ["25x33"]
    test_fn(doc, fen, legals)

    doc = "QuantityPrecedence / Art. 4.13"
    fen = "W:WK48:B7,8,31,34,K42,44"
    legals = ["48x50"]
    test_fn(doc, fen, legals)

    doc = "NoContentsPrecedence / Art. 4.14"
    fen = "W:W26:B12,K21,31,32"
    legals = ["26x08", "26x28"]
    test_fn(doc, fen, legals)

    doc = "NoPassingJumpPromotion / Art. 4.15"
    fen = "W:W15:B9,10"
    legals = ["15x13"]
    test_fn(doc, fen, legals)


def test_spec():
    french_tutorial(run_test)
    italian_rules(run_test)
