class Term(str):
    @property
    def is_variable(self):
        return self[0] == "?"

    @property
    def is_constant(self):
        return self[0] != "?"

    @property
    def arity(self):
        return 0

class ListTerm(tuple):
    def __init__(self, *args):
        self.is_function = None
        tuple.__init__(self, *args)

    def function(self):
        ' must *only* be one level deep '
        if self.is_function is None:

            self.is_function = True
            for e in self:
                if not isinstance(e, Term):
                    self.is_function = False
                    break

        return self.is_function

    @property
    def is_constant(self):
        ' all elements are constant (recursive definition) '
        for e in self:
            if not e.is_constant:
                return False
        return True

    @property
    def arity(self):
        return len(self)

    def __str__(self):
        return "(%s)" % " ".join(str(x) for x in self)
    __repr__ = __str__

###############################################################################

def is_function(term):
    if isinstance(term, ListTerm):
        return term.function()
    return False

###############################################################################

def tokenize(s):
    return s.replace('(',' ( ').replace(')',' ) ').split()

class SymbolFactory:
    def __init__(self):
        self.symbol_pool = dict()

    def create(self, clz, *args):
        # make args hashable
        new_args = []
        for a in args:
            if isinstance(a, list):
                a = tuple(a)
            new_args.append(a)
        args = tuple(new_args)

        # symbol[clz] -> clz_pool[args] -> instance
        try:
            clz_pool = self.symbol_pool[clz]
        except KeyError:
            clz_pool = self.symbol_pool[clz] = {}

        try:
            instance = clz_pool[args]
        except KeyError:
            instance = clz_pool[args] = clz(*args)

        return instance

    def to_symbols(self, s):
        stack = []
        current_list = []

        # strip comment lines
        lines = []
        for l in s.splitlines():
            l = l.strip()
            useful = l.split(";")
            l = useful[0].strip()
            if l:
                lines.append(l)
        s = " ".join(lines)

        for token in tokenize(s):
            if token == '(':
                stack.append(current_list)
                current_list = []

            elif token == ')':
                sl = self.create(ListTerm, current_list)
                current_list = stack.pop()
                current_list.append(sl)

            else:
                current_list.append(self.create(Term, token))

        for sexpr in current_list:
            assert isinstance(sexpr, (Term, ListTerm))
            yield sexpr

    def symbolize(self, s):
        ' takes a single symbol as a string and internalises '
        l = list(self.to_symbols(s))
        assert len(l) == 1
        return l[0]
