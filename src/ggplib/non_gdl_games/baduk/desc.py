# This Python file uses the following encoding: utf-8

import string

BLACK, WHITE = 0, 1


def role_str(r):
    return "white" if r == WHITE else "black"


class BoardDesc:

    def __init__(self, size):
        self.size = size
        self.cords = string.ascii_letters[:size]

        self.bases = self.create_bases()
        self.create_legals()

    def create_bases(self):
        bases = []
        add = bases.append

        for j in self.cords:
            for i in range(1, self.size + 1):
                for role in (BLACK, WHITE):
                    add("(cell %s %s %s)" % (role_str(role), j, i))

                add("(ko_point %s %s)" % (j, i))
                add("(ko_captured %s %s)" % (j, i))

        # control states
        add("(control white)")
        add("(control black)")

        add("(passed black)")
        add("(passed white)")

        # optimisation, flag so that don't have to spin over ko_point / ko_captured each turn
        add("ko_set")

        return bases

    def create_legals(self):
        # 1/3 step moves for man
        # n step moves for king
        self.all_legals = []
        self.legal_mapping = {
            BLACK : {}, WHITE : {}
        }

        self.reverse_legal_mapping = {
            BLACK : {}, WHITE : {}
        }

        self.legal_noop_mapping = {}

        def legal_add(role, x, y):
            self.all_legals.append("(legal %s (place %s %s))" % (role_str(role), x, y))

            legal_index = len(self.all_legals) - 1
            self.legal_mapping[role][(x, y)] = legal_index
            self.reverse_legal_mapping[role][legal_index] = x, y

        for role in (WHITE, BLACK):
            self.all_legals.append("(legal %s noop)" % role_str(role))

            legal_index = len(self.all_legals) - 1
            self.legal_mapping[role]["noop"] = legal_index
            self.legal_noop_mapping[legal_index] = legal_index

            self.all_legals.append("(legal %s pass)" % role_str(role))
            legal_index = len(self.all_legals) - 1
            self.legal_mapping[role]["pass"] = legal_index
            self.legal_noop_mapping[legal_index] = legal_index

            for j in self.cords:
                for i in range(1, self.size + 1):
                    legal_add(role, j, i)

    def get_initial_state(self):
        basestate = [0 for i in range(len(self.bases))]

        # start with control to black
        basestate[self.size * self.size] = 1

        return basestate
