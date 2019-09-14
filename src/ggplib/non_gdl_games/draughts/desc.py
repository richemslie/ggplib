# This Python file uses the following encoding: utf-8


import re
import string

import colorama

from ggplib.db import lookup

###############################################################################

colorama.init()


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

    def state_from_fen(self, fen):
        """ Parses a string in Forsyth-Edwards Notation into a Position """

        # fresh basestate
        basestate = [0 for i in range(len(self.bases))]

        def bs_set_helper(pos, role, what):
            indx = (pos - 1) * NUM_BASES_POS

            if role == BLACK:
                basestate[indx + BASE_WM] = 0
                basestate[indx + BASE_WK] = 0

                if what == KING:
                    basestate[indx + BASE_BM] = 0
                    basestate[indx + BASE_BK] = 1
                else:
                    basestate[indx + BASE_BM] = 1
                    basestate[indx + BASE_BK] = 0
            else:
                if what == KING:
                    basestate[indx + BASE_WM] = 0
                    basestate[indx + BASE_WK] = 1
                else:
                    basestate[indx + BASE_WM] = 1
                    basestate[indx + BASE_WK] = 0

                basestate[indx + BASE_BM] = 0
                basestate[indx + BASE_BK] = 0

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

        # set whos turn
        assert len(turn) == 1
        starting_role = BLACK if turn == 'B' else WHITE
        if starting_role == BLACK:
            basestate[self.meta_index] = 0
            basestate[self.meta_index + 1] = 1
        else:
            basestate[self.meta_index] = 1
            basestate[self.meta_index + 1] = 0

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
                        bs_set_helper(pos, role, what)
                else:
                    bs_set_helper(int(fen_position), role, what)

        return basestate

    def promotion_line(self, role, position):
        _, row = self.mapping_from(position)
        if role == WHITE and row == self.size:
            return True
        elif role == BLACK and row == 1:
            return True

        return False


# helpers for testing

def bs_get(basestate, index):
    try:
        return basestate.get(index)
    except AttributeError:
        return basestate[index]


def check_interim_status(board_desc, basestate):
    return bs_get(basestate, board_desc.interim_status_indx)


def whos_turn(board_desc, basestate):
    indx = board_desc.meta_index
    if bs_get(basestate, indx):
        return WHITE
    else:
        assert bs_get(basestate, indx + 1)
        return BLACK


def print_board(board_desc, basestate):
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

    if not isinstance(basestate, list):
        basestate = basestate.to_list()

    def getAtPos(pos):
        indx = (pos - 1) * NUM_BASES_POS

        wm, wk, bm, bk, interim_pos, captured = basestate[indx:indx + NUM_BASES_POS_USED]

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

    num_spaces = 2
    white_pieces = {MAN : '⛂', KING : '⛃'}
    black_pieces = {MAN : '⛀', KING : '⛁'}

    print("")

    sqrs = board_desc.squares_per_row
    for start_pos in range(1, board_desc.num_positions + 1, sqrs):

        # start:
        numbering = ' %2d - %2d ' % (start_pos, start_pos + sqrs - 1)

        # spaces before row of pieces
        spaces = ' ' * num_spaces

        row = []
        for i in range(sqrs):
            pos = start_pos + i
            role, what, interim_pos, captured = getAtPos(pos)
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


def print_board_sm(board_desc, sm):
    print_board(board_desc, basestate=sm.get_current_state().to_list())


###############################################################################

def create_board(board_desc, fen, killer_mode=False):
    basestate_as_list = board_desc.state_from_fen(fen)

    if killer_mode:
        info = lookup.by_name("draughts_killer_10x10")
    else:
        info = lookup.by_name("draughts_10x10")

    # will dupe / and reset
    sm = info.get_sm()

    # want to create a GGP basestate
    basestate = sm.new_base_state()
    for i, v in enumerate(basestate_as_list):
        basestate.set(i, v)

    sm.update_bases(basestate)
    return sm


def piece_count(board_desc, basestate, role):
    count = 0

    for ii in range(board_desc.num_positions):
        indx = ii * NUM_BASES_POS
        if role == WHITE:
            if bs_get(basestate, indx + BASE_WM) or bs_get(basestate, indx + BASE_WK):
                count += 1
        else:
            if bs_get(basestate, indx + BASE_BM) or bs_get(basestate, indx + BASE_BK):
                count += 1
    return count


def legal_mapping(board_desc, role, legal):
    # XXX ugly hack using gencode - fix to use board_desc only
    from ggplib.non_gdl_games.draughts import gencode
    legal_black_index = gencode.GenCodeFn(10).legal_black_index

    if role == WHITE:
        return board_desc.reverse_legal_mapping[role][legal]
    else:
        return board_desc.reverse_legal_mapping[role][legal + legal_black_index]
