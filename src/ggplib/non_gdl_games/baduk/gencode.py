from ggplib.non_gdl_games.baduk import desc


incl_file_header = '''

// local includes
#include "desc.h"
#include "board.h"

// k273 includes
#include <k273/util.h>
#include <k273/logging.h>
#include <k273/exception.h>

using namespace Baduk;

'''


indent = "    "


def newline(f, count=1):
    for ii in range(count):
        print >>f, ""


def bool_value_str(v):
    return str(bool(v)).lower()


class GenCodeFn:
    def __init__(self, board_size):
        self.board_desc = desc.BoardDesc(board_size)

        # find the start of role indices
        def legal_index_start(role_str):
            for i, legal in enumerate(self.board_desc.all_legals):
                if role_str in legal:
                    assert "noop" in legal
                    return i
            assert False, "did not find legal?"

        def legal_count_start(role_str):
            count = 0
            for i, legal in enumerate(self.board_desc.all_legals):
                if role_str in legal:
                    count += 1
            return count

        self.legal_black_index = legal_index_start("black")
        self.legal_white_index = legal_index_start("white")

        self.num_legals_black = legal_count_start("black")
        self.num_legals_white = legal_count_start("white")

    def legal_index_start(self, role_str):
        for i, legal in enumerate(self.board_desc.all_legals):
            if role_str in legal:
                return i

    def gen_legal_moves(self, role):
        role_str = desc.role_str(role)

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
        yield ""

        yield "// Initial state"
        for l in self.gen_initial_state():
            yield l
        yield ""
        yield ""

        for role in (desc.BLACK, desc.WHITE):

            yield ""
            yield "// generating moves for %s" % (desc.role_str(role))
            for l in self.gen_legal_moves(role):
                yield l

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
    board_sizes = 9, 13, 19
    gens = [GenCodeFn(sz) for sz in board_sizes]
    create_cpp_file("../../../cpp/statemachine/external/baduk/init.cpp", gens)
