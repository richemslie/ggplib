import sys
import time
import random

from ggplib.non_gdl_games.draughts import spec

class Perft:
    def __init__(self, board_desc, fen, killer_mode):
        self.board_desc = board_desc
        self.sm = spec.SM(board_desc, killer_mode=killer_mode)
        self.sm.parse_fen(fen)
        self.sm.update_legal_choices()

    def gen_moves(self):
        self.sm.update_legal_choices()

        role = self.sm.whos_turn()
        opp = spec.WHITE if role == spec.BLACK else spec.BLACK
        joint_moves = []

        assert len(self.sm.choices[opp]) == 1
        noop = self.sm.choices[opp][0]
        for l in self.sm.choices[role]:
            if role == spec.WHITE:
                joint_moves.append(spec.JointMove((l, noop)))
            else:
                joint_moves.append(spec.JointMove((noop, l)))

        return joint_moves

    def go(self, depth, state_map=None):
        if depth == 0:
            return 1

        node_count = 0
        clone_sm = self.sm.clone()

        for move in self.gen_moves():
            self.sm.play_move(move)

            # needed for is_terminal()
            self.sm.update_legal_choices()

            if state_map is not None:
                state = tuple(self.sm.basestate)
                if state in state_map:
                    # undo move
                    self.sm = clone_sm.clone()
                    continue

                state_map.add(state)

            if self.sm.is_terminal():
                # only add if terminal states are of correct depth
                if depth == 1:
                    node_count += 1

                # undo move and continue
                self.sm = clone_sm.clone()
                continue

            if self.sm.check_interim_status():
                # need expand paths and eliminate dupe cycles
                if state_map is None:
                    state_map = set()

                node_count += self.go(depth, state_map)
            else:
                node_count += self.go(depth - 1)

            # undo move
            self.sm = clone_sm.clone()

        return node_count


def perft(fen, max_depth, killer_mode=False):
    p = Perft(spec.BoardDesc(10), fen, killer_mode=killer_mode)

    print 'Running Perft for FEN', fen
    p.sm.print_board()

    results = []
    for depth in range(1, max_depth + 1):
        start_time = time.time()
        nodes = p.go(depth)
        time_taken = time.time() - start_time
        print "depth %d, %d nodes, %.3f sec" % (depth, nodes, time_taken)
        results.append(nodes)

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-p":
        import cProfile
        cProfile.run('play_randomly()')

    elif len(sys.argv) > 1 and sys.argv[1] == "-r":
        # play_randomly(True, 1)
        play_randomly()

    else:
        # fen = "W:WK31,K32,K33,K34,K35,K36,K37,K38,K39,K40,K41,K42,K43,K44,K45,K46,K47,K48,K49,K50:BK1," \
        #      "K2,K3,K4,K5,K6,K7,K8,K9,K10,K11,K12,K13,K14,K15,K16,K17,K18,K19,K20."

        # fen = "W:W6,7,8,9,10:B41,42,43,44,45."

        # inital state:
        #fen = "W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:" \
        #     "B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"

        # 14 captures crazyiness
        # fen = "B:W6,9,10,11,20,21,22,23,30,K31,33,37,41,42,43,44,46:BK17,K24"

        # end game
        fen = "W:W25,27,28,30,32,33,34,35,37,38:B12,13,14,16,18,19,21,23,24,26"

        depth = int(sys.argv[1])
        perft(fen, depth)
