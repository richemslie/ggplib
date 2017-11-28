"""
Given some symbols (which is a game in gdl).  Create a signature.  If the signature maps, then maps
the underlying symbols to the player.

This is incredibly crude.  Was a stop gap implementation that is Tiltyard specific.  It only works
since it see things in a certain order and numbers are not remapped.
"""

import pprint
from collections import OrderedDict

from ggplib.symbols import SymbolFactory, Term, ListTerm

root_constants = "role init base input true next legal terminal does goal".split()

###############################################################################

def facts(gdl):
    for s in gdl:
        assert isinstance(s, ListTerm)
        if s[0] != "<=":
            yield s


def rules(gdl):
    for s in gdl:
        assert isinstance(s, ListTerm)
        if s[0] == "<=":
            yield s


def extract_terms(*args):
    seen = set()

    def extract_terms_(*args):
        for a in args:
            if isinstance(a, ListTerm):
                for e in a:
                    for x in extract_terms_(e):
                        yield x

            elif isinstance(a, Term):
                if a not in seen:
                    yield a
                seen.add(a)

            else:
                assert isinstance(a, Literal)
                for e in a:
                    for x in extract_terms_(e):
                        yield extract_terms_(x)

    for x in extract_terms_(*args):
        yield x

###############################################################################

def get_variable(e, variables):
    if e not in variables:
        variables[e] = len(variables) + 1
    return variables[e]

###############################################################################

class Literal:
    def literal(self):
        return True


class SingleLiteral(Literal):
    def __init__(self, e):
        self.e = e

    def __iter__(self):
        yield self.e

    def __str__(self):
        return str(self.e)


class CompoundLiteral(Literal, ListTerm):
    pass


class NotLiteral(Literal):
    def __init__(self, lit):
        assert lit.literal()
        self.lit = lit

    def __iter__(self):
        yield self.lit

    def __str__(self):
        return "(not %s)" % str(self.lit)


class DistinctLiteral(Literal):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __iter__(self):
        yield self.lhs
        yield self.rhs

    def __str__(self):
        return "(distinct %s %s)" % (self.lhs, self.rhs)


class OrLiteral(Literal):
    def __init__(self, body):
        self.body = body

    def __iter__(self):
        for e in self.body:
            yield e

    def __str__(self):
        return "(or %s)" % " ".join(str(x) for x in self.body)

###############################################################################

class Fact:
    def __init__(self, head, body):
        '''
Facts can be a mapping from a term to
    * term
    * a number of terms
A term can be simple, or composite.  If compound - it is of one level (a function).
        '''
        assert isinstance(head, Term)
        self.head = head
        self.body = body

        for e in body:
            if isinstance(e, ListTerm):
                assert e.function()
                assert e.is_constant

        self.all_terms = list(extract_terms(self.head, *self.body))

        for a in self.all_terms:
            assert isinstance(a, Term)
            assert a.is_constant

    def arity(self):
        return len(self.body)

    def __repr__(self):
        return "(%s %s)" % (self.head, " ".join(str(e) for e in self.body))


def establish_positions(tup1, tup2):
    # takes two tuples and return the joint values

    def filter_constant(e1):
        if isinstance(e1, str):
            return False
        # XXX magic number
        return e1 > 100

    def walker(tup1, tup2):
        assert isinstance(tup1, tuple)
        assert isinstance(tup2, tuple)
        assert len(tup1) == len(tup2)
        for e1, e2 in zip(tup1, tup2):
            if isinstance(e1, tuple):
                assert isinstance(e2, tuple)
                for ee1, ee2 in walker(e1 , e2):
                    if filter_constant(ee1):
                        yield ee1, ee2
            else:
                assert not isinstance(e2, tuple)
                if filter_constant(e1):
                    yield e1, e2

    return list(walker(tup1, tup2))


class Signature:
    def __init__(self, manager, gdl):
        self.gdl = gdl
        self.manager = manager
        self.variables = {}

    def set_zero_sig(self, tup):
        self.zero_sig = tup
        self.zero_sig_hash = hash(tup)

    def set_num_sig(self, tup):
        self.num_sig = tup

    def set_value_sig(self, tup):
        self.value_sig = tup

    def __repr__(self):
        return repr(self.num_sig)


class SignatureFactory:
    def __init__(self):
        self.roles = {}
        self.constants = set(root_constants)
        self.constants.update("not or distinct".split())
        self.constants.update(str(i) for i in range(1000))

        self.mutable_constants = {}

        # the result
        self.sigs = []

    def get_constant(self, t):
        assert t.is_constant
        assert t not in self.constants
        if t not in self.mutable_constants:
            self.mutable_constants[t] = len(self.mutable_constants) + 100
        return self.mutable_constants[t]

    def function(self, f, variables):
        return tuple(["function", tuple(self.term(t, variables) for t in f)])

    def literal(self, l, variables):
        assert l.literal()

        if isinstance(l, SingleLiteral):
            return self.term(l.e, variables)

        if isinstance(l, NotLiteral):
            return tuple(["not", self.literal(l.lit, variables)])

        if isinstance(l, DistinctLiteral):
            return tuple(["distinct", self.term(l.lhs, variables), self.term(l.rhs, variables)])

        if isinstance(l, OrLiteral):
            return tuple(["distinct"] + [self.literal(x, variables) for x in l])

        assert isinstance(l, CompoundLiteral)
        return tuple(self.term(t, variables) for t in l)

    def term1(self, t, variables=None):
        if isinstance(t, Term):
            if t in self.roles:
                return self.roles[t]

            if t in self.constants:
                return t
            if variables is not None:
                if t.is_variable:
                    return get_variable(t, variables)
            else:
                assert not t.is_variable
            return 0
        else:
            assert t.function()
            return self.function(t, variables)

    def term2(self, t, variables=None):
        res = self.term1(t, variables)
        if res == 0:
            assert t.is_constant
            return self.get_constant(t)
        return res

    def term3(self, t, variables=None):
        res = self.term1(t, variables)
        if res == 0:
            return t
        return res

    def add_rule(self, r):
        s = Signature(self, r)
        self.term = self.term1
        s.set_zero_sig(tuple(["rule",
                              self.literal(r.head, s.variables),
                              tuple(self.literal(l, s.variables) for l in r.body)]))
        self.term = self.term2
        s.set_num_sig(tuple(["rule",
                             self.literal(r.head, s.variables),
                             tuple(self.literal(l, s.variables) for l in r.body)]))

        self.term = self.term3
        s.set_value_sig(tuple(["rule",
                               self.literal(r.head, s.variables),
                               tuple(self.literal(l, s.variables) for l in r.body)]))

        self.sigs.append(s)

    def add_fact(self, f):
        # add roles
        if f.head == "role":
            self.roles[f.body[0]] = "role%d" % len(self.roles)

        s = Signature(self, f)
        self.term = self.term1
        s.set_zero_sig(tuple(["fact",
                              self.term(f.head),
                              tuple(self.term(t) for t in f.body)]))
        self.term = self.term2
        s.set_num_sig(tuple(["fact",
                             self.term(f.head),
                             tuple(self.term(t) for t in f.body)]))

        self.term = self.term3
        s.set_value_sig(tuple(["fact",
                               self.term(f.head),
                               tuple(self.term(t) for t in f.body)]))

        self.sigs.append(s)


def to_literal(e):
    if isinstance(e, Term):
        assert e.is_constant
        return SingleLiteral(e)

    if e[0] == "not":
        assert len(e) == 2
        return NotLiteral(to_literal(e[1]))

    if e[0] == "distinct":
        assert len(e) == 3
        return DistinctLiteral(e[1], e[2])

    if e[0] == "or":
        return OrLiteral([to_literal(x) for x in e[1:]])

    return CompoundLiteral(e)


class Rule:
    def __init__(self, head, body):
        self.head = to_literal(head)
        self.body = [to_literal(e) for e in body]

        self.all_terms = list(extract_terms(self.head, *self.body))

    def arity(self):
        return len(self.body)

    def constants(self):
        return [t for t in self.all_terms if t.is_constant]

    def variables(self):
        return [t for t in self.all_terms if t.is_variable]

    def __repr__(self):
        return "(<= %s %s)" % (self.head, " ".join(str(e) for e in self.body))

###############################################################################

def build_symbol_map(sig, verbose=False):
    def make_counter():
        x = 0
        while True:
            yield x
            x += 1
    counter = make_counter()

    sigs = sig.sigs
    constant_mapping = {}
    group_by_hash = {}
    for s in sigs:
        info = establish_positions(s.num_sig, s.value_sig)
        if info:
            for l in info:
                assert len(l) == len(info[0])

            group_by_hash.setdefault(s.zero_sig_hash, []).append(info)

    # use new mapping
    groups = {}
    for k, v in group_by_hash.items():
        groups[counter.next()] = v

    for ii in range(100):
        # remove anything that is empty
        for k, left in groups.items():
            assert len(left) != 0
            if not left[0]:
                for l in left:
                    assert not l
                groups.pop(k)

        if verbose:
            print 'removed empty'

        # pop anything known now in constant_mapping
        for k, left in groups.items():
            something_popped = True
            left = left[:]
            while something_popped:
                something_popped = False
                for idx, l in enumerate(left):
                    all_known = True
                    for const, value in l:
                        if const not in constant_mapping:
                            all_known = False
                    if all_known:
                        something_popped = True
                        left.pop(idx)
                        break

            # so everything is known, nothing to see here
            if not left:
                if verbose:
                    print "removing since everything is known anyway", left
                groups.pop(k)
                continue

        # only one rule, we can update constant_mapping
        for k, left in groups.items():
            if len(left) == 1:
                for const, value in left[0]:
                    if const in constant_mapping:
                        assert constant_mapping[const] == value
                    constant_mapping[const] = value
                if verbose:
                    print "removing single rule", left
                groups.pop(k)

        # ok now, we go through column by column
        for k, left in groups.items():
            assert len(left) > 1

            columns = zip(*left)
            something_popped = True
            while something_popped:
                something_popped = False
                for ii in range(len(columns)):
                    col = columns[ii]

                    # same test:
                    if len(set(col)) == 1:
                        # if they are all the same - no ambiguity - we can add to constant_mapping, and pop from row

                        # add:
                        const, value = col[0]
                        if const in constant_mapping:
                            assert constant_mapping[const] == value
                        constant_mapping[const] = value

                        if verbose:
                            print "popping same col"
                        something_popped = True
                        columns.pop(ii)
                        break

                    # if they are all known - then pop from row
                    everything_known = True
                    for const, value in col:
                        if const not in constant_mapping:
                            everything_known = False
                            break

                    if everything_known:
                        if verbose:
                            print "popping everything_known col"
                        something_popped = True
                        columns.pop(ii)
                        break

                if len(columns) == 1:
                    break

            if len(columns) == 1:
                for const, value in columns[0]:
                    if const in constant_mapping:
                        assert constant_mapping[const] == value
                    constant_mapping[const] = value
                groups.pop(k)

            if len(columns) == 0:
                groups.pop(k)

        for k, left in groups.items():
            did_something = True
            while did_something:
                did_something = False
                only_one_left = {}
                for r in left:
                    knowns = [(idx, v) for idx, v in enumerate(r) if v[0] in constant_mapping]
                    unknowns = [(idx, v) for idx, v in enumerate(r) if v[0] not in constant_mapping]
                    if len(unknowns) == 1:
                        only_one_left.setdefault(tuple(knowns), []).append(unknowns)
                for unknowns in only_one_left.values():
                    if len(unknowns) == 1:
                        const, value = unknowns[0][0][1]
                        if const not in constant_mapping:
                            constant_mapping[const] = value
                        did_something = True

        if not groups:
            if verbose:
                print "DONE!"
            break

        if verbose:
            print
            print "pass done - more to do:"
            print "======================="
            pprint.pprint(groups)
            pprint.pprint(constant_mapping)

    if not groups:
        return constant_mapping
    else:
        return None

###############################################################################

def get_index(gdl_str, verbose=False):
    factory = SymbolFactory()
    ruleset = list(factory.to_symbols(gdl_str))

    # XXX bah, only works if rules/facts are in same order
    fact_db = OrderedDict()
    rule_db = OrderedDict()
    for lit in root_constants:
        fact_db[lit] = []
        rule_db[lit] = []

    for fact in facts(ruleset):
        assert isinstance(fact, ListTerm)
        name = fact[0]
        f = Fact(name, list(fact[1:]))
        fact_db.setdefault(name, []).append(f)

    for rule in rules(ruleset):
        assert isinstance(rule, ListTerm)
        head = rule[1]
        if isinstance(head, ListTerm):
            name = head[0]
        else:
            name = head
        r = Rule(head, factory.create(ListTerm, rule[2:]))
        rule_db.setdefault(name, []).append(r)

    if verbose:
        print "FACTS:"
        for lit in root_constants:
            print "%s:" % lit
            pprint.pprint(fact_db[lit])

        for h, b in fact_db.items():
            if h not in root_constants:
                print "%s:" % h
                pprint.pprint(fact_db[h])

        print "RULES:"
        for lit in root_constants:
            print "%s:" % lit
            pprint.pprint(rule_db[lit])

        for h, b in rule_db.items():
            if h not in root_constants:
                print "%s:" % h
                pprint.pprint(rule_db[h])

    sig = SignatureFactory()
    for lit in root_constants:
        for f in fact_db[lit]:
            sig.add_fact(f)

    for h, b in fact_db.items():
        if h not in root_constants:
            for f in fact_db[h]:
                sig.add_fact(f)

    for lit in root_constants:
        for r in rule_db[lit]:
            sig.add_rule(r)

    for h, b in rule_db.items():
        if h not in root_constants:
            for r in rule_db[h]:
                sig.add_rule(r)

    if verbose:
        print "Signature:"
        pprint.pprint(sig)

    hashed_sigs = []
    for s in sig.sigs:
        if verbose:
            print s, s.zero_sig_hash

        hashed_sigs.append(s.zero_sig_hash)
    hashed_sigs.sort()
    final_value = hash(tuple(hashed_sigs))

    # this is a reconstruct phase (testing)
    return final_value, sig
