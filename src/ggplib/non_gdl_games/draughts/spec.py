# This Python file uses the following encoding: utf-8


import re
import string

import colorama
colorama.init()


########################
# c++ statemachine stuff
########################

class JointMove(tuple):
    pass


############
# constants
############

MAX_N_RULE_STATES = 0

MAN, KING = 0, 1

WHITE, BLACK = 0, 1

NE, NW, SE, SW = 0, 1, 2, 3


# readable bases lookup
# this is so we can array of chars in c (easiest for now)
BASE_WM = 0
BASE_WK = 1
BASE_BM = 2
BASE_BK = 3
BASE_LAST = 4
BASE_CAPTURE = 5
BASE_PAD0 = 6
BASE_PAD1 = 7

NUM_BASES_POS = 8
NUM_BASES_POS_USED = 6


def role_str(r):
    return "white" if r == WHITE else "black"


def piece_str(p):
    return "man" if p == MAN else "king"


def direction_str(d):
    if d == NE:
        return "NE"
    elif d == NW:
        return "NW"
    elif d == SE:
        return "SE"
    elif d == SW:
        return "SW"

    assert False, "WTF"


class Diagonals:
    all_directions = NE, NW, SE, SW

    def __init__(self, position, direction):
        self.position = position
        self.direction = direction
        self.steps = []

    def add(self, pos):
        self.steps.append(pos)

    def __repr__(self):
        s = "Diagonal(%s, %s, %s)" % (self.position,
                                      direction_str(self.direction),
                                      str(self.steps))
        return s


class BoardDesc:
    # use same represententation for BT ID, just change termination rules.

    def __init__(self, size):
        self.size = size
        self.cords = string.ascii_letters[:size]
        self.bases, self.num_positions = self.create_bases()

        self.diagonals = self.create_all_diagonals()

        self.create_legals()

        # helpers...
        self.zeros_empty = tuple(0 for _ in range(NUM_BASES_POS_USED))

        self.interim_status_indx = self.meta_index + 2

    @property
    def squares_per_row(self):
        return self.size / 2

    def create_bases(self):
        def board_cords():
            for i in range(self.size, 0, -1):
                s = 0 if i % 2 == 1 else 1
                for j in self.cords[s:self.size + s:2]:
                    yield i, j

        bases = []
        add = bases.append

        num_positions = 0
        for i, j in board_cords():
                for role in (WHITE, BLACK):
                    for piece in ("man", "king"):
                        add("(cell %s %s %s %s)" % (role_str(role), j, i, piece))

                add("(last_at %s %s)" % (j, i))
                add("(capturing_piece %s %s)" % (j, i))
                add("(pad_0 %s %s)" % (j, i))
                add("(pad_1 %s %s)" % (j, i))
                num_positions += 1

        self.draw_20_rule_index = len(bases)

        # N rule counter
        for i in range(MAX_N_RULE_STATES):
            add("(20_rule_step_%s)" % i)

        self.meta_index = len(bases)

        # control states
        add("(control white)")
        add("(control black)")

        # set as quick lookup
        add("interim_status")

        return bases, num_positions

    def mapping_from(self, pos):
        assert pos > 0 and pos <= self.num_positions

        # position maps from top right hand square leftward, downwards
        row, col = (pos - 1) / self.squares_per_row, pos % self.squares_per_row
        row = self.size - 1 - row
        s = 1 if row % 2 == 1 else 0
        cord = self.cords[s:self.size + s:2][col - 1]
        return cord, row + 1

    def mapping_to(self, col, row):
        p = (self.size - row) * self.squares_per_row

        s = 1 if row % 2 == 0 else 0
        possible_cords = self.cords[s:self.size + s:2]

        p += possible_cords.index(col) + 1
        return p

    def create_all_diagonals(self):

        def next_position(d):
            col, row = self.mapping_from(d.position)
            col_index = self.cords.index(col)

            # east
            col_incr = 1 if (d.direction == NE or d.direction == SE) else -1

            # north
            row_incr = 1 if (d.direction == NE or d.direction == NW) else -1

            while True:
                row += row_incr
                col_index += col_incr

                # row is indexed from 1, hence the weirdness here
                if row < 1 or row > self.size:
                    break

                if col_index < 0 or col_index >= self.size:
                    break

                yield self.mapping_to(self.cords[col_index], row)

        # for each position, add maximum diagonals
        all_diagonals = []
        for pos in range(1, self.num_positions + 1):
            for d in [NE, NW, SE, SW]:
                d = Diagonals(pos, d)
                all_diagonals.append(d)

                for p in next_position(d):
                    d.add(p)

        return all_diagonals

    def get_diagonals_for_position(self, pos):
        indx = (pos - 1) * 4
        return self.diagonals[indx:indx + 4]

    def get_move_from_legals(self, white_legal, black_legal):
        if white_legal in self.legal_noop_mapping:
            role = BLACK
            legal = black_legal

        else:
            assert black_legal in self.legal_noop_mapping
            role = WHITE
            legal = white_legal

        what, choice_from_pos, choice_to_pos, direction = self.reverse_legal_mapping[role][legal]
        return role, what, choice_from_pos, choice_to_pos, direction

    def create_legals(self):
        # 1/3 step moves for man
        # n step moves for king
        self.all_legals = []
        self.legal_mapping = {
            WHITE : {}, BLACK : {}
        }

        self.reverse_legal_mapping = {
            WHITE : {}, BLACK : {}
        }

        self.legal_noop_mapping = {}

        def legal_add(role, what, from_pos, to_pos, direction):
            col0, row0 = self.mapping_from(from_pos)
            col1, row1 = self.mapping_from(to_pos)
            self.all_legals.append("(legal %s (move %s %s %s %s %s))" % (role_str(role),
                                                                         piece_str(what),
                                                                         col0,
                                                                         row0,
                                                                         col1,
                                                                         row1))
            legal_index = len(self.all_legals) - 1
            self.legal_mapping[role][(what, from_pos, to_pos)] = legal_index
            self.reverse_legal_mapping[role][legal_index] = (what, from_pos, to_pos, direction)

        for role, fwd_direction in zip((WHITE, BLACK),
                                       [(NE, NW), (SE, SW)]):

            self.all_legals.append("(legal %s noop)" % role_str(role))
            legal_index = len(self.all_legals) - 1
            self.legal_mapping[role]["noop"] = legal_index
            self.legal_noop_mapping[legal_index] = legal_index

            for ii in range(self.num_positions):
                pos = ii + 1

                diagonals = self.get_diagonals_for_position(pos)

                # man single move
                for d in fwd_direction:
                    if len(diagonals[d].steps):
                        next_pos = diagonals[d].steps[0]
                        legal_add(role, MAN, pos, next_pos, d)

                # man jump move
                for d in Diagonals.all_directions:
                    if len(diagonals[d].steps) >= 2:
                        next_pos = diagonals[d].steps[1]
                        legal_add(role, MAN, pos, next_pos, d)

                # king jump move (at the end, as we strip these when generating model for BT variant)
                for d in NE, NW, SE, SW:
                    for next_pos in diagonals[d].steps:
                        legal_add(role, KING, pos, next_pos, d)

    def get_gdl_base(self, index):
        return self.bases[index]

    def get_initial_state(self):
        basestate = [0 for i in range(len(self.bases))]

        # set first step
        basestate[self.draw_20_rule_index] = 1

        # start with control to white
        basestate[self.meta_index] = 1

        # XXX by eyeballing initial boards, I see there are 2 blank rows on games I have seen.  I
        # doubt this is correct though.
        starting_men = (self.num_positions - self.squares_per_row * 2) / 2

        for ii in range(starting_men):
            # black
            indx = ii * NUM_BASES_POS
            basestate[indx + BASE_BM] = 1

            # white
            indx = (self.num_positions - ii - 1) * NUM_BASES_POS
            basestate[indx + BASE_WM] = 1

        return basestate

    def promotion_line(self, role, position):
        _, row = self.mapping_from(position)
        if role == WHITE and row == self.size:
            return True
        elif role == BLACK and row == 1:
            return True

        return False


class SM:
    def __init__(self, board_desc,
                 breakthrough_mode=False, killer_mode=False, basestate=None):

        # static
        self.board_desc = board_desc
        self.killer_mode = killer_mode
        self.breakthrough_mode = breakthrough_mode

        if basestate is None:
            basestate = board_desc.get_initial_state()
        else:
            basestate = basestate[:]

        self.basestate = basestate

    def get_current_state(self):
        return self.basestate

    def clone(self, basestate=None):
        if basestate is None:
            basestate = self.basestate
        return SM(self.board_desc,
                  breakthrough_mode=self.breakthrough_mode,
                  killer_mode=self.killer_mode,
                  basestate=basestate)

    def get(self, pos):
        indx = (pos - 1) * NUM_BASES_POS

        wm, wk, bm, bk, interim_pos, captured = self.basestate[indx:indx + NUM_BASES_POS_USED]

        role = None
        if wm or wk:
            role = WHITE
            what = MAN if wm else KING

        if bm or bk:
            role = BLACK
            what = MAN if bm else KING

        if role is None:
            return None, None, None, None

        return role, what, interim_pos, captured

    def raw_pos_get(self, pos):
        indx = (pos - 1) * NUM_BASES_POS
        raw = (indx, self.basestate[indx:indx + NUM_BASES_POS_USED])
        return raw

    def raw_update(self, raw):
        indx, state = raw
        self.basestate[indx:indx + NUM_BASES_POS_USED] = state

    def is_empty(self, pos):
        role, _, _, _ = self.get(pos)
        return role is None

    def is_opponent_and_not_captured(self, our_role, pos):
        indx = (pos - 1) * NUM_BASES_POS
        bs = self.basestate
        if our_role == WHITE:
            return ((bs[indx + BASE_BM] or bs[indx + BASE_BK]) and
                    not bs[indx + BASE_CAPTURE])
        else:
            return ((bs[indx + BASE_WM] or bs[indx + BASE_WK]) and
                    not bs[indx + BASE_CAPTURE])

    def set(self, pos, role, what):
        indx = (pos - 1) * NUM_BASES_POS

        if role == BLACK:
            self.basestate[indx + BASE_WM] = 0
            self.basestate[indx + BASE_WK] = 0

            if what == KING:
                self.basestate[indx + BASE_BM] = 0
                self.basestate[indx + BASE_BK] = 1
            else:
                self.basestate[indx + BASE_BM] = 1
                self.basestate[indx + BASE_BK] = 0
        else:
            if what == KING:
                self.basestate[indx + BASE_WM] = 0
                self.basestate[indx + BASE_WK] = 1
            else:
                self.basestate[indx + BASE_WM] = 1
                self.basestate[indx + BASE_WK] = 0

            self.basestate[indx + BASE_BM] = 0
            self.basestate[indx + BASE_BK] = 0

    def set_captured(self, pos):
        indx = (pos - 1) * NUM_BASES_POS
        self.basestate[indx + BASE_CAPTURE] = 1

    def unset_captured(self, pos):
        indx = (pos - 1) * NUM_BASES_POS
        self.basestate[indx + BASE_CAPTURE] = 0

    def remove_interim_position(self, pos):
        indx = (pos - 1) * NUM_BASES_POS
        self.basestate[indx + BASE_LAST] = 0

        # unset flag
        self.basestate[self.board_desc.interim_status_indx] = 0

    def set_interim_position(self, pos):
        indx = (pos - 1) * NUM_BASES_POS
        self.basestate[indx + BASE_LAST] = 1

        # set flag
        self.basestate[self.board_desc.interim_status_indx] = 1

    def check_interim_status(self):
        return self.basestate[self.board_desc.interim_status_indx]

    def interim_status(self):
        # spin through board, return captures and interim position
        for ii in range(self.board_desc.num_positions):
            index = ii * NUM_BASES_POS
            pos = ii + 1
            if self.basestate[index + BASE_LAST]:
                if self.basestate[index + BASE_WM]:
                    return WHITE, pos, MAN
                elif self.basestate[index + BASE_WK]:
                    return WHITE, pos, KING
                elif self.basestate[index + BASE_BM]:
                    return BLACK, pos, MAN
                elif self.basestate[index + BASE_BK]:
                    return BLACK, pos, KING

                assert False, "BROKEN!"

    def promote(self, role, pos):
        indx = (pos - 1) * NUM_BASES_POS

        if role == WHITE:
            self.basestate[indx + BASE_WM] = 0
            self.basestate[indx + BASE_WK] = 1
        else:
            self.basestate[indx + BASE_BM] = 0
            self.basestate[indx + BASE_BK] = 1

    def clear_captures(self):
        for ii in range(self.board_desc.num_positions):
            indx = ii * NUM_BASES_POS
            if self.basestate[indx + BASE_CAPTURE]:
                pos = ii + 1
                self.clear(pos)

    def switch_role(self):
        indx = self.board_desc.meta_index
        if self.basestate[indx]:
            self.basestate[indx] = 0
            self.basestate[indx + 1] = 1
        else:
            assert self.basestate[indx + 1]
            self.basestate[indx] = 1
            self.basestate[indx + 1] = 0

    def clear(self, pos=None):
        if pos is None:
            for ii in range(self.board_desc.num_positions):
                self.clear(ii + 1)
        else:
            indx = (pos - 1) * NUM_BASES_POS
            self.basestate[indx:indx + NUM_BASES_POS_USED] = self.board_desc.zeros_empty

    def all_for_role(self, for_role):
        if for_role == WHITE:
            for ii in range(self.board_desc.num_positions):
                indx = ii * NUM_BASES_POS
                if self.basestate[indx + BASE_WM]:
                    yield ii + 1, MAN
                elif self.basestate[indx + BASE_WK]:
                    yield ii + 1, KING
        else:
            for ii in range(self.board_desc.num_positions):
                indx = ii * NUM_BASES_POS
                if self.basestate[indx + BASE_BM]:
                    yield ii + 1, MAN
                elif self.basestate[indx + BASE_BK]:
                    yield ii + 1, KING

    def whos_turn(self):
        indx = self.board_desc.meta_index
        if self.basestate[indx]:
            return WHITE
        else:
            assert self.basestate[indx + 1]
            return BLACK

    def print_board(self):
        """
  1 -  5      ⛂   ⛂   ⛂   ⛂   ⛂
  6 - 10    ⛂   ⛂   ⛂   ⛂   ⛂
 11 - 15      ⛂   ⛂   ⛂   ⛂   ⛂
 16 - 20    ⛂   ⛂   ⛂   ⛂   ⛂
 21 - 25      ·   ·   ·   ·   ·
 26 - 30    ·   ·   ·   ·   ·
 31 - 35      ⛀   ⛀   ⛀   ⛀   ⛀
 36 - 40    ⛀   ⛀   ⛀   ⛀   ⛀
 41 - 45      ⛀   ⛀   ⛀   ⛀   ⛀
 46 - 50    ⛀   ⛀   ⛀   ⛀   ⛀
"""

        num_spaces = 2
        white_pieces = {MAN : '⛂', KING : '⛃'}
        black_pieces = {MAN : '⛀', KING : '⛁'}

        print("")

        sqrs = self.board_desc.squares_per_row
        for start_pos in range(1, self.board_desc.num_positions + 1, sqrs):

            # start:
            numbering = ' %2d - %2d ' % (start_pos, start_pos + sqrs - 1)

            # spaces before row of pieces
            spaces = ' ' * num_spaces

            row = []
            for i in range(sqrs):
                pos = start_pos + i
                role, what, interim_pos, captured = self.get(pos)
                if role is None:
                    piece_str = "."

                else:
                    if role == WHITE:
                        piece_str = white_pieces[what]
                    else:
                        piece_str = black_pieces[what]

                    if interim_pos:
                        piece_str = colorama.Fore.GREEN + piece_str + colorama.Style.RESET_ALL

                    elif captured:
                        piece_str = colorama.Fore.RED + piece_str + colorama.Style.RESET_ALL

                row.append(piece_str)

            pieces = '   '.join(row)

            print(numbering + '   ' + spaces + pieces)

            # alternate spaces between rows
            num_spaces = 0 if num_spaces > 0 else 2

        print("")

    def print_state(self):
        for v, base in zip(self.basestate, self.board_desc.bases):
            if v:
                print base

    def parse_fen(self, fen):
        """ Parses a string in Forsyth-Edwards Notation into a Position """

        self.clear()

        # remove all spaces
        fen = fen.replace(" ", "")

        # cut off info (.xxx) at the end
        fen = re.sub(r'\..*$', '', fen)

        # empty FEN Position
        if fen == '':
            fen = 'W:B:W'
        elif fen == 'W::':
            fen = 'W:B:W'
        elif fen == 'B::':
            fen = 'B:B:W'

        fen = re.sub(r'.::$', 'W:W:B', fen)

        parts = fen.split(':')
        turn = parts[0]

        assert len(turn) == 1
        starting_role = BLACK if turn == 'B' else WHITE
        if self.whos_turn() != starting_role:
            self.switch_role()

        for part in parts[1:]:
            role = BLACK if part[0] == 'B' else WHITE
            positions = part[1:]
            if not positions:
                continue

            for fen_position in positions.split(','):
                what = MAN
                if fen_position[0] == 'K':
                    what = KING
                    fen_position = fen_position[1:]

                is_range = "-" in fen_position
                if is_range:
                    start, end = map(int, fen_position.split('-'))
                    for pos in range(start, end + 1):
                        self.set(pos, role, what)
                else:
                    self.set(int(fen_position), role, what)

    def non_capture_moves(self, role, pos, what):
        # constraint: must not be called if there are captures to be made

        diagonals = self.board_desc.get_diagonals_for_position(pos)
        if what == MAN:
            directions = (NE, NW) if role == WHITE else (SE, SW)
            for d in directions:
                if not diagonals[d].steps:
                    continue
                next_pos = diagonals[d].steps[0]
                if self.is_empty(next_pos):
                    yield next_pos

        elif what == KING:
            for d in Diagonals.all_directions:
                for next_pos in diagonals[d].steps:
                    if not self.is_empty(next_pos):
                        break

                    yield next_pos

    def immediate_captures(self, role, pos, what):
        diagonals = self.board_desc.get_diagonals_for_position(pos)
        for d in Diagonals.all_directions:
            steps = diagonals[d].steps
            if what == MAN:
                if len(steps) >= 2:
                    captured_pos = steps[0]
                    next_pos = steps[1]

                    if (self.is_empty(next_pos) and
                        self.is_opponent_and_not_captured(role, captured_pos)):
                        yield next_pos, captured_pos, True
            else:
                assert what == KING

                for ii, next_pos in enumerate(steps):
                    if self.is_empty(next_pos):
                        continue

                    if self.is_opponent_and_not_captured(role, next_pos):
                        # all proceeding empty diagonals are valid moves

                        captured_pos = next_pos
                        first_after = True
                        for next_pos in steps[ii + 1:]:
                            if self.is_empty(next_pos):
                                yield next_pos, captured_pos, first_after
                                first_after = False
                            else:
                                break

                    # cannot capture beyond this
                    break

    def maximal_captures(self, role, pos, what, moves=None):
        if moves is not None:
            raw = self.raw_pos_get(pos)
            self.clear(pos)

        best_mc = 0

        # find if there are immediate captures
        for landing_pos, capture_pos, first_after in self.immediate_captures(role, pos, what):

            # add capture to stack by modifying board state
            self.set_captured(capture_pos)
            mc = self.maximal_captures(role, landing_pos, what)
            self.unset_captured(capture_pos)

            if self.killer_mode and mc == 0:
                # we are at last point, check capture_pos was king
                _, captured_what, _, _ = self.get(capture_pos)
                if captured_what == KING:
                    if not first_after:
                        continue

            count = mc + 1
            if count > best_mc:
                if moves is not None:
                    del moves[:]
                best_mc = count

            if moves is not None and count == best_mc:
                moves.append(landing_pos)

        if moves is not None:
            self.raw_update(raw)

        return best_mc

    def update_legal_choices(self):
        lm = self.board_desc.legal_mapping

        # reset old choices, pair of choices for white/black respectively:
        self.choices = [[lm[WHITE]["noop"]], [lm[BLACK]["noop"]]]

        # who's turn is it?
        role = self.whos_turn()

        # are we in interim position?
        moves = []
        if self.check_interim_status():
            interim_who, interim_pos, interim_what = self.interim_status()
            assert interim_who == role

            to_positions = []
            self.maximal_captures(role, interim_pos, interim_what, to_positions)
            moves = [(interim_what, interim_pos, to_pos) for to_pos in to_positions]

        if not moves:
            # go through all role's pieces, and calculate maximal_captures - add in best
            best_mc = 0
            for from_pos, what in self.all_for_role(role):
                to_positions = []
                mc = self.maximal_captures(role, from_pos, what, to_positions)

                if mc > best_mc:
                    moves = []
                    best_mc = mc

                if mc == best_mc:
                    moves += [(what, from_pos, to_pos) for to_pos in to_positions]

        if not moves:
            # othewise do all non-capture moves
            for from_pos, what in self.all_for_role(role):
                for to_pos in self.non_capture_moves(role, from_pos, what):
                    moves.append((what, from_pos, to_pos))

        # update choices
        legals = [lm[role][what, from_pos, to_pos] for what, from_pos, to_pos in moves]
        self.choices[role] = legals

    def play_move(self, joint_move):
        assert isinstance(joint_move, JointMove)

        # joint_move is an index into legals
        # legals must be valid (or SM broken)

        # reverse look up on legals and get info from board
        role, what, choice_from_pos, choice_to_pos, direction = self.board_desc.get_move_from_legals(*joint_move)
        role_check, what_check, is_interim, _ = self.get(choice_from_pos)

        diagonals = self.board_desc.get_diagonals_for_position(choice_from_pos)
        steps = diagonals[direction].steps

        captured_pos = None

        # all points must be empty, except we allow one and only one opponent piece (the captured_pos)

        for cur_pos in steps:
            if cur_pos == choice_to_pos:
                break

            if self.is_empty(cur_pos):
                continue

            captured_pos = cur_pos

        # move and add capture piece (if one)
        self.clear(choice_from_pos)
        self.set(choice_to_pos, role, what)

        if captured_pos:
            self.set_captured(captured_pos)

        # note the capture might be immediately removed if not a new interim position.
        # this is keep things readable (we'll let the c++ version be completely unreadable!).

        if is_interim:
            # remove previous interim_pos
            self.remove_interim_position(choice_from_pos)

        if captured_pos:
            for _ in self.immediate_captures(role, choice_to_pos, what):
                self.set_interim_position(choice_to_pos)
                return

            # ensure all captures are removed from board
            self.clear_captures()

        # promote to king?
        if what == MAN and self.board_desc.promotion_line(role, choice_to_pos):
            self.promote(role, choice_to_pos)

        # and switch role...
        self.switch_role()

    def any_king(self):
        # XXX todo
        return False

    def is_terminal(self):
        if self.breakthrough_mode:
            if self.any_king():
                return True

        white_choices, black_choices = self.choices
        if not white_choices or not black_choices:
            return True
        return False
