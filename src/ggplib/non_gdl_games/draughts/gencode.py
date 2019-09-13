from ggplib.non_gdl_games.draughts import spec


incl_file_header = '''

// local includes
#include "draughts_desc.h"
#include "draughts_board.h"

// k273 includes
#include <k273/util.h>
#include <k273/logging.h>
#include <k273/exception.h>

using namespace InternationalDraughts;

'''


indent = "    "


def newline(f, count=1):
    for ii in range(count):
        print >>f, ""


def bool_value_str(v):
    return str(bool(v)).lower()


class GenCodeFn:
    def __init__(self, board_size):
        self.board_desc = spec.BoardDesc(board_size)

        # find the start of role indices
        def legal_index_start(role_str):
            for i, legal in enumerate(self.board_desc.all_legals):
                if role_str in legal:
                    assert "noop" in legal
                    return i
            assert False, "WTF?"

        def legal_count_start(role_str):
            count = 0
            for i, legal in enumerate(self.board_desc.all_legals):
                if role_str in legal:
                    count += 1
            return count

        self.legal_white_index = legal_index_start("white")
        self.legal_black_index = legal_index_start("black")

        self.num_legals_white = legal_count_start("white")
        self.num_legals_black = legal_count_start("black")

    def all_diagonal_data(self, role, what, pos, direction):
        all_directions = self.board_desc.get_diagonals_for_position(pos)
        diagonals = all_directions[direction]

        for i, to_pos in enumerate(diagonals.steps):
            if what == spec.MAN and i == 2:
                break

            try:
                legal = self.board_desc.legal_mapping[role][(what, pos, to_pos)]

            except KeyError:
                legal = -1

            yield to_pos, legal

    def generate_reverse_lookup(self, role, what, from_pos, direction, ddi):
        """
        ReverseLegalLookup(Role role,
                           Piece what,
                           Position from_pos,
                           Position to_pos,
                           Direction direction) :
        """

        legal_index_start = self.legal_white_index if role == spec.WHITE else self.legal_black_index

        map_variable = "reverse_legal_lookup_"

        if role == spec.WHITE:
            role = "Role::White"
            map_variable += "white"

        else:
            role = "Role::Black"
            map_variable += "black"

        if what == spec.MAN:
            what = "Piece::Man"
        else:
            what = "Piece::King"

        for to_pos, legal in ddi:
            if legal == -1:
                continue

            assert 0 <= legal - legal_index_start < self.num_legals_white
            yield "this->%s[%s] = ReverseLegalLookup(%s, %s, %s, %s, %s);" % (
                map_variable,
                legal - legal_index_start,
                role,
                what,
                from_pos,
                to_pos,
                spec.direction_str(direction))

    def generate_ddi(self, role, direction, ddi):
        legal_index_start = self.legal_white_index if role == spec.WHITE else self.legal_black_index

        yield "DiagonalDirectionInfo* ddi = new DiagonalDirectionInfo;"
        yield "ddi->direction = %s;" % spec.direction_str(direction)
        yield "ddi->diagonals.reserve(%d);" % len(ddi)

        for to_pos, legal in ddi:
            if legal == -1:
                legal_desc = "invalid"
            else:
                legal_desc = self.board_desc.all_legals[legal]

            legal -= legal_index_start
            yield "// to position %d, legal: %s" % (to_pos, legal_desc)
            yield "ddi->diagonals.emplace_back(%d, %d);" % (to_pos, legal)
            yield ""

    def legal_index_start(self, role_str):
        for i, legal in enumerate(self.board_desc.all_legals):
            if role_str in legal:
                return i

    def gen_promotion_lines(self, role):
        value_strs = []
        for ii in range(self.board_desc.num_positions):
            pos = ii + 1
            value = self.board_desc.promotion_line(role, pos)
            value_strs.append(bool_value_str(value))

        yield "this->%s_promotion_line = {%s};" % (spec.role_str(role), ", ".join(value_strs))

    def gen_legal_moves(self, role):
        role_str = spec.role_str(role)

        legal_strs = []
        for legal in self.board_desc.all_legals:
            # XXX is this right?
            action = legal.replace("(legal", "").strip()
            action = action[:-1]
            if role_str in action:
                move = action.replace(role_str, "").strip()
                legal_strs.append('"%s"' % move)

        yield 'this->%s_legal_moves = {%s};' % (role_str, ", ".join(legal_strs))

    def gen_initial_state(self):
        values = [bool_value_str(v) for v in self.board_desc.get_initial_state()]

        yield 'this->initial_state = {%s};' % (", ".join(values),)

    def body(self):
        positions = self.board_desc.num_positions

        yield "this->num_positions = %d;" % positions
        yield "this->white_noop = 0;"
        yield "this->black_noop = 0;"
        yield "this->diagonal_data.resize(%d);" % (positions * 4)

        yield "// Reserve the map size upfront, hopefully memory will be contiguous (XXX check)"
        yield "this->reverse_legal_lookup_white.resize(%d);" % self.num_legals_white
        yield "this->reverse_legal_lookup_black.resize(%d);" % self.num_legals_black

        yield ""

        yield "// Initial state"
        for l in self.gen_initial_state():
            yield l
        yield ""
        yield ""

        for role in (spec.WHITE, spec.BLACK):

            yield ""
            yield "// generating promotion line for %s" % (spec.role_str(role))
            for l in self.gen_promotion_lines(role):
                yield l

            yield ""

            yield ""
            yield "// generating moves for %s" % (spec.role_str(role))
            for l in self.gen_legal_moves(role):
                yield l

            for what in (spec.MAN, spec.KING):
                index = (role * 2 + what) * positions

                for ii in range(positions):
                    pos_index = index + ii
                    pos = ii + 1

                    for direction in spec.Diagonals.all_directions:
                        ddi = list(self.all_diagonal_data(role, what, pos, direction))

                        if ddi:
                            yield "// generating for %s %s %s %s" % (spec.role_str(role),
                                                                     spec.piece_str(what),
                                                                     pos,
                                                                     spec.direction_str(direction))
                            yield "{"
                            for l in self.generate_ddi(role, direction, ddi):
                                yield indent + l

                            yield indent + "this->diagonal_data[%s].push_back(ddi);" % pos_index
                            yield ""
                            yield ""

                            for l in self.generate_reverse_lookup(role, what, pos, direction, ddi):
                                yield indent + l

                            yield "}"

    def fn_decl(self):
        sz = self.board_desc.size
        return "void Description::initBoard_%sx%s() {" % (sz, sz)


def create_cpp_file(filename, gens):

    with open(filename, 'w') as init_file:

        # generate header filess
        print >>init_file, incl_file_header
        newline(init_file, 2)

        for gen in gens:

            print >>init_file, gen.fn_decl()
            newline(init_file, 1)

            for l in gen.body():
                if l.strip():
                    print >>init_file, indent + l
                else:
                    print >>init_file, ""

            newline(init_file, 2)
            print >>init_file, "} // end of BoardDescription::initBoard_%sx%s" % (sz, sz)

        print >>init_file, "// end of file"
        newline(init_file, 1)


if __name__ == "__main__":
    board_sizes = 8, 10
    gens = [GenCodeFn(sz) for sz in board_sizes]

    create_cpp_file("../../cpp/draughts_init.cpp", gens)
