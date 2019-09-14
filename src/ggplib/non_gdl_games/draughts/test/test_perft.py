import time

# for py test skipping
import py

from ggplib.non_gdl_games.draughts import desc

# unskip to run all tests, but it will take ages.
skip_slow = False


class Perft(object):
    def __init__(self, fen, killer_mode):
        self.board_desc = desc.BoardDesc(10)

        self.sm = desc.create_board(self.board_desc, fen, killer_mode)
        self.start_state = self.sm.get_current_state()
        self.next_basestate = self.sm.new_base_state()

    def reset(self):
        self.sm.update_bases(self.start_state)

    def gen_moves(self):
        ls0, ls1 = self.sm.get_legal_state(0), self.sm.get_legal_state(1)

        joint_moves = []

        # cross product of legals
        for ii in range(ls0.get_count()):
            for jj in range(ls1.get_count()):
                joint_move = self.sm.get_joint_move()
                joint_move.set(0, ls0.get_legal(ii))
                joint_move.set(1, ls1.get_legal(jj))
                joint_moves.append(joint_move)

        return joint_moves

    def go(self, depth, state_map=None):
        if depth == 0:
            return 1

        node_count = 0

        basestate = self.sm.get_current_state()
        for move in self.gen_moves():
            self.sm.update_bases(basestate)

            self.sm.next_state(move, self.next_basestate)
            self.sm.update_bases(self.next_basestate)

            if state_map is not None:
                state = tuple(self.next_basestate.to_list())
                if state in state_map:
                    continue

                state_map.add(state)

            if self.sm.is_terminal():
                # only add if terminal states are of correct depth
                if depth == 1:
                    node_count += 1

                continue

            if desc.check_interim_status(self.board_desc, self.next_basestate):
                # need expand paths and eliminate dupe cycles
                if state_map is None:
                    state_map = set()

                node_count += self.go(depth, state_map)
            else:
                node_count += self.go(depth - 1)

        return node_count


def perft(fen, max_depth, killer_mode=False, verbose=True):
    p = Perft(fen, killer_mode=killer_mode)

    if verbose:
        print 'Running Perft for FEN', fen
        desc.print_board_sm(p.board_desc, p.sm)

    results = []
    for depth in range(1, max_depth + 1):
        start_time = time.time()
        p.reset()
        nodes = p.go(depth)
        time_taken = time.time() - start_time
        if verbose:
            print "depth %d, %d nodes, %.3f sec" % (depth, nodes, time_taken)
        results.append(nodes)

    return results


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
    if skip_slow:
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
    if skip_slow:
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
