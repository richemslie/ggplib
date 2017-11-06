import pprint
from collections import OrderedDict

from ggplib.symbols import Term, ListTerm, is_function

root_constants = "role init base input true next legal terminal does goal".split()
root_constants = set(root_constants)

# 1024? - largest game I know of gt_two_thirds_6p.kif - which goes 600
specials = "<= not or distinct " + " ".join(str(ii) for ii in range(1024))
specials = set(specials.split())

###############################################################################

def indent(level):
    return " " * 2 * level

# XXX there is a counter in itertools.  remove
def counter():
    def incr():
        count = 0
        while True:
            yield count
            count += 1
    return incr().next

###############################################################################

def find_facts(gdl):
    for s in gdl:
        assert isinstance(s, ListTerm)
        if s[0] != "<=":
            yield s

def find_rules(gdl):
    for s in gdl:
        assert isinstance(s, ListTerm)
        if s[0] == "<=":
            yield s

###############################################################################

class Register:
    def __init__(self, name):
        self.name = name
        self.value = None

    def __repr__(self):
        return "%s:%s" % (self.name, self.value)

###############################################################################

class Literal(object):
    ''' Literals are top level statements in gdl.  They also include clauses of rules. '''
    @property
    def arity(self):
        return -1

class SingleLiteral(Literal):
    def __init__(self, term):
        assert isinstance(term, Term)
        self.term = term

    @property
    def arity(self):
        return 0

    @property
    def base(self):
        return self.term

    def __iter__(self):
        yield self.term

    def __str__(self):
        return str(self.term)

    __repr__ = __str__


class CompoundLiteral(Literal, ListTerm):
    @property
    def arity(self):
        return len(self)

    @property
    def base(self):
        return self[0]


class NotLiteral(Literal):
    def __init__(self, lit):
        assert isinstance(lit, Literal)
        self.lit = lit

    def __iter__(self):
        yield self.lit

    def __str__(self):
        return "(not %s)" % str(self.lit)
    __repr__ = __str__


class DistinctLiteral(Literal):
    def __init__(self, lhs, rhs):
        # lhs/rhs are terms, not literals
        assert isinstance(lhs, Term)
        assert isinstance(rhs, Term)
        self.lhs = lhs
        self.rhs = rhs

    def __iter__(self):
        yield self.lhs
        yield self.rhs

    def __str__(self):
        return "(distinct %s %s)" % (self.lhs, self.rhs)
    __repr__ = __str__


class OrLiteral(Literal):
    def __init__(self, body):
        self.body = body

    def __iter__(self):
        for e in self.body:
            yield e

    def __str__(self):
        return "(or %s)" % " ".join(str(x) for x in self.body)
    __repr__ = __str__


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

# ZZZzzz write tests

def rewrite_literal(lit, mapping):
    ''' rewrite a literal substituting variables from mapping. '''

    if isinstance(lit, (SingleLiteral, DistinctLiteral)):
        return lit

    assert not isinstance(lit, OrLiteral), "TODO"

    assert isinstance(lit, CompoundLiteral)

    new_terms = []

    for t in lit:
        if is_function(t):
            new_function_term = []
            for tt in t:
                if tt.is_variable and tt in mapping:
                    tt = mapping[tt]
                    if isinstance(tt, Register):
                        tt = tt.value
                new_function_term.append(tt)

            t = CompoundLiteral(new_function_term)
        else:
            if t.is_variable and t in mapping:
                t = mapping[t]
                if isinstance(t, Register):
                    t = t.value

        new_terms.append(t)

    return CompoundLiteral(new_terms)

def string_to_literal(symbol_factory, s):
    symbols = symbol_factory.to_symbols(s)
    symbols = list(symbols)
    assert len(symbols) == 1
    symbol = symbols[0]

    return to_literal(symbol)

def walk_terms(lit, fn):
    for t in lit:
        if is_function(t):
            for tt in t:
                fn(tt, True)
        else:
            fn(t, False)

###############################################################################

def extract_terms(x):
    ' extract the unique terms from a literal, list of literals, or ListTerm of literals. '

    if isinstance(x, Term):
        yield x
        return

    seen = set()

    def recur(some_list):
        for a in some_list:
            if isinstance(a, (ListTerm, Literal)):
                for x in recur(a):
                    yield x

            else:
                assert isinstance(a, Term)
                if a not in seen:
                    yield a
                seen.add(a)

    for t in recur(x):
        yield t

def extract_variables(x):
    ' extract the unique terms for a list '
    for t in extract_terms(x):
        if t.is_variable:
            yield t

def extract_constants(x):
    ' extract the unique terms for a list '
    for t in extract_terms(x):
        if t.is_constant:
            yield t

# ZZZzzz write tests

###############################################################################

class Fact:
    def __init__(self, terms):
        '''
Facts can be a mapping from a term to
    * term
    * a number of terms
A term can be simple, or composite.  If compound - it is of one level (a function).
        '''
        assert len(terms) > 1

        self.literal = to_literal(terms)

        head = terms[0]
        assert isinstance(head, Term)
        assert head.is_constant

        self.base_term = head
        self.terms = terms
        self.body = terms[1:]

        # check the body is either a term, or list term.  If it is a list term, ensure it is a gdl
        # 'function'.
        for e in self.terms:
            if isinstance(e, ListTerm):
                assert e.function()
                assert e.is_constant
            else:
                assert e.is_constant

        # unique list of terms
        self.all_terms = list(extract_terms(terms))

    def arity(self):
        return len(self.terms)

    def __repr__(self):
        return "(%s)" % " ".join(str(e) for e in self.literal)

class Rule:
    def __init__(self, rule_terms):
        assert isinstance(rule_terms, ListTerm)
        assert rule_terms[0] == "<="
        self.head = to_literal(rule_terms[1])
        self.body = [to_literal(e) for e in rule_terms[2:]]

        self.base_term = list(self.head)[0]

        self.head_terms = list(extract_terms([self.head]))
        self.all_terms = list(extract_terms([self.head] + self.body))

        sig_strs = []
        for t in self.head:
            if is_function(t):
                sig_strs.append("F")
                for tt in t:
                    if tt.is_variable:
                        tt = tt.replace("?", "V")
                    sig_strs.append(tt)
            else:
                if t.is_variable:
                    t = t.replace("?", "V")
                sig_strs.append(t)
        self.sig = "_".join(sig_strs)

    def arity(self):
        return len(self.body)

    def constants(self):
        return [t for t in self.all_terms if t.is_constant]

    def variables(self):
        return [t for t in self.all_terms if t.is_variable]

    def head_constant(self):
        return [t for t in self.head_terms if t.is_constant]

    def head_variables(self):
        return [t for t in self.head_terms if t.is_variable]

    def richrepr(self):
        return "(<= %s %s)" % (self.head, self.body)

    def __repr__(self):
        return "(<= %s ...)" % (self.head,)

###############################################################################

class Var:
    ' Populated in creating queries and propgated via context. '
    def __init__(self, term):
        self.term = term
        self.bound = False
        self.possible_values = []

    def __repr__(self):
        if self.possible_values:
            assert self.bound
            return "{%s: [%s]}" % (self.term, ", ".join(p for p in self.possible_values))
        elif self.bound:
            return "{%s ...}" % self.term
        else:
            return "{%s}" % self.term

class Context:
    def __init__(self, unified):
        # what do we need to get out of this
        variables_seen = set()
        for lit in unified.renaming.values():
            variables_seen.update(extract_variables(lit))

        self.variables_required = variables_seen

        self.mapping = {}

    def update(self, query):
        " update after subquery unified "
        for v in query.variables:
            if v.term not in self.mapping:
                bound_v = Var(v.term)
                self.mapping[v.term] = bound_v

            else:
                bound_v = self.mapping[v.term]

            # actually now bound
            bound_v.bound = True

            if isinstance(query, (QueryFact, QueryFactAndRule)):
                for f, u in query.facts:
                    if u.unified_vars[v.term] not in bound_v.possible_values:
                        bound_v.possible_values.append(u.unified_vars[v.term])

    def __repr__(self):
        return "Context(req:%s, bound:%s)" % (self.variables_required, self.mapping.values())

###############################################################################

class Query:
    def __init__(self, lit, context=None):
        self.lit = lit

        # list of variables we want for this query.  We use the context to identify whether the
        # variable was bound and has been assigned values up front.
        self.variables = []

        for term in extract_variables(self.lit):
            v = Var(term)

            if context is not None:
                # inherit bounded-ness
                if v in context.mapping:
                    vc = context.mapping[v.term]
                    v.bound = vc.bound

                    # inherit values?  These values are narrowing. (not sure if there is merit in this?)
                    v.possible_values = vc.possible_values[:]

            self.variables.append(v)

    def signature(self):
        next_num = counter()
        mapping = {}
        signature = []
        def f(term, in_function):
            if term.is_variable:
                if term in mapping:
                    term = mapping[term]
                else:
                    new_term = "?r%s" % next_num()
                    mapping[term] = new_term

        walk_terms(self.lit, f)
        return rewrite_literal(self.lit, mapping)

    @property
    def is_ground(self):
        raise NotImplemented

    def __repr__(self):
        return "%s %s" % (self.__class__, self.lit)

class QueryTrue(Query):
    @property
    def is_ground(self):
        raise True

class QueryDoes(Query):
    @property
    def is_ground(self):
        raise True

class QueryFact(Query):
    def __init__(self, lit, facts, context=None):
        Query.__init__(self, lit, context=context)

        # tuple: fact, unified
        self.facts = facts

    @property
    def is_ground(self):
        # always true for facts
        return True

    def get_results(self):
        seen = set()
        results = []

        for f, u in self.facts:
            assert not u.renaming and not u.bound_ct_vars
            res = tuple(u.unified_vars[v.term] for v in self.variables)

            # hack for later, when we gen code for loop
            # it needs to handle
            # for x0, x1 in ZZZ
            # for x0 in ZZZ
            if len(res) == 1:
                res = res[0]

            if res not in seen:
                results.append(res)
                seen.add(res)

        return results

    def def_sig(self):
        s = "gen_fact_" + self.lit.base
        args = "_".join(v.term for v in self.variables)
        args = args.replace("?", "V")
        if args:
            s += "_" + args
        return s

    def get_regs(self):
        return ["reg_%s" % ii for ii, _ in enumerate(self.variables)]

    def gen_defn(self, regs):
        yield "def %s(%s):" % (self.def_sig(), ", ".join(regs))

    def gen_lines(self, regs, next_tmp_var):
        args = ["x_%s" % (next_tmp_var()) for ii, _ in enumerate(self.variables)]
        assert len(regs) == len(args)

        yield "for %s in %s:" % (", ".join(args), self.get_results())
        for ii, a in enumerate(args):
            yield "    %s.value = %s" % (regs[ii], a)

    def gen_function(self):
        # this is split up over three lines, as we want to inline in rules
        regs = self.get_regs()

        for l in self.gen_defn(regs):
            yield l

        for l in self.gen_lines(regs, next_tmp_var=counter()):
            yield "    " + l

        yield "        yield"

class QueryRule(Query):
    def __init__(self, lit, rules, context=None):
        Query.__init__(self, lit, context=context)
        # tuple: rules, unified
        self.rules = rules

        # for each rule we create QueriedRule
        self.queried_rules = []

    def sig(self):
        s = "gen_rule_" + self.lit.base
        args = "_".join(v.term for v in self.variables)
        args = args.replace("?", "V")
        if args:
            s += "_" + args

        return s

class QueryFactAndRule:
    def __init__(self, q_fact, q_rule):
        self.q_fact = q_fact
        self.facts = self.q_fact.facts

        self.q_rule = q_rule
        self.rules = self.q_rule.rules

class QueryDistinct(Query):
    pass

class QueryNot(Query):
    def __init__(self, lit, not_query, context=None):
        Query.__init__(self, lit, context=context)
        self.not_query = not_query

class QueryOr(Query):
    def __init__(self, lit, or_queries, context=None):
        Query.__init__(self, lit, context=context)
        self.or_queries = or_queries

class QueriedRule:
    def __init__(self, rule, unified):
        self.rule = rule

        # these are the variables passed in
        self.variables = self.rule.head_variables()

        # QueriedRule is interested in bound_ct_vars
        self.unified = unified

        self.subqueries = []
        self.grounded = None

    def sig(self):
        return "gen_qrule_" + self.rule.sig

    def finalise(self):
        # set all seen variables
        self.variables = set()

    @property
    def is_ground(self):
        if self.grounded is None:
            self.grounded = True
            for q in self.subqueries:
                if not q.is_grounded:
                    self.grounded = False
                    break

        return self.grounded

    def gen_function(self):
        # reset next_tmp_var
        self.next_tmp_var = counter()

        # need all bound and unbound variables for registers
        yield "def %s(%s):" % (self.sig(), ", ".join("reg_%s" % ii for ii, _ in enumerate(self.variables)))

        indent_level = 1
        for ii, sq in enumerate(self.subqueries):
            gen = self.lookup_gen(sq)
            for l in gen:
                yield indent_level * "    " + l

            yield ""
            indent_level += 1

        # final yield
        yield indent_level * "    " + "yield"

    def lookup_gen(self, q):
        if isinstance(q, QueryFact):
            return self.gen_fact(q)

        elif isinstance(r, QueryRule):
            TODO

        elif isinstance(r, QueryDistinct):
            TODO

    def gen_fact(self, fact):
        yield "# %s" % fact

        fact_variables_terms = [v.term for v in fact.variables]
        for t in fact_variables_terms:
            assert t in self.variables

        regs = ["reg_%s" % self.variables.index(t) for t in fact_variables_terms]

        for l in fact.gen_lines(regs, next_tmp_var=self.next_tmp_var):
            yield l

###############################################################################

class UnifyResult:
    def __init__(self):
        # bound compile time vars.  That is a fact or rule, will have a variable with a known value
        # at compile time.  It can be constant propogated.
        self.bound_ct_vars = {}

        # These are results for the query.  Known at compile time.
        self.unified_vars = {}

        # The variable in the query will adopt the name in the context.
        # Or map from clause variable name to the query variable name.
        self.renaming = {}

    def add_to_result(self, t1, t2):
        assert not is_function(t1) and not is_function(t2)

        # is this fact/rule a variable?
        #print 'kkk', t1, t2
        if t2.is_constant:
            assert t1.is_variable
            self.bound_ct_vars[t1] = t2

        elif t1.is_constant:
            assert t2.is_variable
            self.unified_vars[t2] = t1

        else:
            self.renaming[t2] = t1

    def add_to_result_fn(self, t1, t2):
        #print 'kkk', t1, t2
        if t1.is_constant:
            self.unified_vars[t2] = t1
        else:
            self.renaming[t2] = t1

    def __repr__(self):
        s = "UnifyResult("
        if self.bound_ct_vars:
            s += "bound_ct: "
            s += ", ".join("%s=%s" % (k, v) for k, v in self.bound_ct_vars.items())
            s += " "

        if self.unified_vars:
            s += "unified: "
            s += ", ".join("%s=%s" % (k, v) for k, v in self.unified_vars.items())
            s += " "

        if self.renaming:
            s += "renaming:"
            s += ", ".join("%s=%s" % (k, v) for k, v in self.renaming.items())
        s += ")"
        return s

def abstract_unify(lit1, lit2, context):
    ''' custom unify for matching our fact/rules.

    * lit1 is a fact / head of rule.
    * lit2 is our query.
    * context stores any previous runtime /compile time, bound variables (these are for clause queries)
    * result provides information about the unify, which should be enough to generate code.
    '''

    result = UnifyResult()

    #print 'kkk HERE1', lit1, lit2, "-" if context is None else context.mapping.values()
    if lit1.arity != lit2.arity:
        return None

    for t1, t2 in zip(lit1, lit2):

        #print 'kkk HERE2', t1, t2

        if context and t2 in context.mapping:
            assert not is_function(t2) and t2.is_variable
            if t1.is_constant:
                #print 'kkk HERE3', t1, context.mapping[t2]
                if context.mapping[t2].possible_values and t1 not in context.mapping[t2].possible_values:
                    return None

        if not is_function(t1) and not is_function(t2):
            #print 'non function matching'
            if t1.is_constant and t2.is_constant:
                if t1 != t2:
                    return None
                else:
                    continue

            result.add_to_result(t1, t2)

        elif is_function(t1) and is_function(t2):
            if len(t1) != len(t2):
                return None

            for ft1, ft2 in zip(t1, t2):
                assert isinstance(ft1, Term)
                assert isinstance(ft2, Term)
                if ft1.is_constant and ft2.is_constant:
                    if ft1 != ft2:
                        return None
                    else:
                        continue

                result.add_to_result(ft1, ft2)

        elif is_function(t1) and not is_function(t2):
            # special case of matching say : (mark ?x ?y) ?x
            if not t2.is_variable:
                return None

            result.add_to_result_fn(t1, t2)

        else:
            return None

    return result

###############################################################################

class NoRule(Exception):
    def __init__(self, lit):
        Exception.__init__(self, "No rule found for %s" % str(lit))
        self.lit = lit

###############################################################################

class GameDescription:
    def __init__(self, symbol_factory, gdl):
        self.symbol_factory = symbol_factory
        self.gdl = gdl

        # This is a single database of facts and rules.  We preserve gdl order for no good reason.
        self.db = OrderedDict()

    def process(self):
        for lit in root_constants:
            self.db[lit] = []

        for fact_terms in find_facts(self.gdl):
            assert isinstance(fact_terms, ListTerm)
            fact = Fact(fact_terms)
            self.db.setdefault(fact.base_term, []).append(fact)

        for rule_terms in find_rules(self.gdl):
            assert isinstance(rule_terms, ListTerm)
            rule = Rule(rule_terms)
            self.db.setdefault(rule.base_term, []).append(rule)

    def dump(self):
        def print_helper(heading, some_list):
            if some_list:
                s = "%s:" % heading
                print s
                print "=" * len(s)
                pprint.pprint(some_list)
                print

        print
        print "** FACTS:"
        print

        for lit in root_constants:
            facts = [f for f in self.db[lit] if isinstance(f, Fact)]
            print_helper(lit, facts)

        for base, l in self.db.items():
            facts = [f for f in self.db[base] if isinstance(f, Fact)]
            if base not in root_constants and facts:
                print_helper(base, facts)

        print
        print "** RULES:"
        print
        for lit in root_constants:
            rules = [r for r in self.db[lit] if isinstance(r, Rule)]
            print_helper(lit, rules)

        for base, l in self.db.items():
            rules = [r for r in self.db[base] if isinstance(r, Rule)]
            if base not in root_constants and rules:
                print_helper(base, rules)

    def build_query_string(self, query_string, vebose=True):
        if vebose:
            print
            print "BUILD_QUERY:"
            print query_string
            print len(query_string) * "="

        # turn into symbols, the turn symbols into literal
        return self.build_query(string_to_literal(self.symbol_factory, query_string))

    def build_query(self, lit, seen=None, context=None, level=0, verbose=True):
        if verbose:
            print
            print indent(level), "->:", lit
            if seen is not None:
                print indent(level), "SEEEEEEEEEEN:", seen

        assert isinstance(lit, (SingleLiteral, CompoundLiteral))

        # constraint: symbol needs to have a valid signature against facts/rules

        # special cases against knowledge base:
        if lit.base == "true":
            assert lit.arity == 2
            return QueryTrue(lit)

        elif lit.base == "does":
            assert lit.arity == 3
            return QueryDoes(lit)

        elif lit.base not in self.db:
            raise NoRule(lit)

        #if seen is not None and r in seen:
        #    print "RECURSION DETECTED", r
        #    continue

        facts = []
        rules = []
        for e in self.db[lit.base]:
            if isinstance(e, Fact):
                res = abstract_unify(e.literal, lit, context)
                if res:
                    facts.append((e, res))
            else:
                assert isinstance(e, Rule)

                res = abstract_unify(e.head, lit, context)
                if res:
                    rules.append((e, res))


        if verbose:
            if facts:
                print indent(level), "found facts", facts

            if rules:
                print indent(level), "found rules", [(r.richrepr(), u) for r, u in rules]

        q_fact = None
        if facts:
            q_fact = QueryFact(lit, facts, context=context)

            if not rules:
                print "Signature:", q_fact.signature()
                return q_fact

        q_rule = None
        if rules:
            q_rule = QueryRule(lit, rules, context=context)
            self.expand_rules(q_rule, seen, level + 1)
            if not facts:
                print "Signature:", q_rule.signature()
                return q_rule

        # both
        if q_rule and q_fact:
            return QueryFactAndRule(q_fact, q_rule)

        raise NoRule(lit)

    def expand_rules(self, query, seen, level):
        assert isinstance(query, QueryRule)

        # add in requires to rule.  We get those from the u.renaming.  Needs to be able to handle various function objects.

        #TODO or do we wait to gencode?

        ok_rules = []
        for r, u in query.rules:
            try:
                if seen is None:
                    seen = []
                else:
                    seen = seen[:]

                qr = QueriedRule(r, u)
                print indent(level), "Expand rule:", r.richrepr(), u

                # create a context with the compile time constants
                context = Context(u)
                seen.append(r)
                for lit in r.body:
                    sub = self.build_query_clause(lit, u, context, seen, level + 1)
                    qr.subqueries.append(sub)
                seen.pop()

                ok_rules.append((r, u))
                query.queried_rules.append(qr)

            except NoRule:
                print indent(level), "Fail in expand_rules, NoRule: :", r.richrepr()

        if len(ok_rules) != len(query.rules):
            print "Reduced rules..."
            if len(ok_rules) == 0:
                raise NoRule("Query reduced to zero rules!! %s" % query)
            query.rules = ok_rules

    def build_query_clause(self, lit, unified, context, seen, level):
        print indent(level), "Doing clause", lit, unified, context
        if isinstance(lit, OrLiteral):
            #TODOZZZ rewrite rule as
            or_queries = [self.build_query_clause(l, unified, context, seen, level + 1) for l in lit]
            res = QueryOr(lit, or_queries)

        elif isinstance(lit, NotLiteral):
            # TODOZZZ rewrite rule as - rationalise, test
            notlit = rewrite_literal(lit.lit, unified.bound_ct_vars)
            #notlit = rewrite_literal(lit.lit, unified.unified_vars)

            # TODOZZZ assert everything is bound...
            q_not = self.build_query_clause(notlit, unified, context, seen, level + 1)
            res = QueryNot(lit, q_not)

        elif isinstance(lit, DistinctLiteral):
            # TODOZZZ assert everything is bound...
            q = QueryDistinct(lit, context=context)
            #TODOZZZcontext.update_distinct(q)
            res = q

        elif isinstance(lit, CompoundLiteral):
            lit = rewrite_literal(lit, unified.bound_ct_vars)
            #XXXlit = rewrite_literal(lit, unified.unified_vars)
            q = self.build_query(lit, context=context, seen=seen, level=level + 1)
            context.update(q)
            res = q

        else:
            assert isinstance(lit, SingleLiteral)
            q = self.build_query(lit, context=context, seen=seen, level=level + 1)
            context.update(q)
            res = q

        print indent(level), "DONE clause", res, context
        print
        return res
