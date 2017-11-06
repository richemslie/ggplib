from os.path import join as j

from ggplib import symbols
from ggplib.prover import parse
from ggplib.propnet.getpropnet import rulesheet_dir

def dump(gdl):
    print "GDL:"
    print gdl

    print "Facts:"
    for f in parse.find_facts(gdl):
        print f

    print "Rules:"
    for r in parse.find_rules(gdl):
        print r

    print "Terms:"
    for t in parse.extract_terms(gdl):
        # skip gdl specific stuff
        if t in parse.specials or t in parse.root_constants:
            continue
        print t

def get_game(symbol_factory, filename):
    contents = file(filename).read()
    return list(symbol_factory.to_symbols(contents))

def test_simple():
    symbol_factory = symbols.SymbolFactory()
    filename = j(rulesheet_dir, "other", "test.kif")
    dump(get_game(symbol_factory, filename))

def test_simple2():
    symbol_factory = symbols.SymbolFactory()
    filename = j(rulesheet_dir, "ticTacToe.kif")
    dump(get_game(symbol_factory, filename))

###############################################################################

def process_test(game):
    symbol_factory = symbols.SymbolFactory()
    filename = j(rulesheet_dir, game)
    gdl = get_game(symbol_factory, filename)
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

def test_process_ttt():
    process_test("ticTacToe.kif")

def test_process_c4():
    process_test("connectFour.kif")

def test_process_guessx6():
    process_test("gt_two_thirds_6p.kif")

###############################################################################

def get(game):
    symbol_factory = symbols.SymbolFactory()
    filename = j(rulesheet_dir, game)
    gdl = get_game(symbol_factory, filename)
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()
    return p

def test_queries_create():
    #p = get("ticTacToe.kif")
    #roles = ("xplayer", "oplayer")

    p = get("connectFour.kif")
    roles = ("red", "black")

    #p = get("breakthrough.kif")
    #roles = ("white", "black")

    #p = get("hex.kif")
    #roles = ("red", "blue")

    #p = get("chess_200.kif")
    #roles = ("white", "black")

    #p = get("reversi.kif")
    #roles = ("black", "red")

    #p = get("amazons_8x8.kif")
    #roles = ("white", "black")

    def run(s):
        q = p.build_query_string(s)
        print s
        print q
        if isinstance(q, parse.QueryFact):
            print q.facts
        else:
            print q.rules
        import time
        time.sleep(1)

    run("(role ?x)")
    run("(base ?x)")

    for r in roles:
        run("(input %s ?x)" % r)

    XX
    run("(init ?x)")

    for r in roles:
        run("(legal %s ?x)" % r)

    run("(next ?x)")

    run("terminal")

    for r in roles:
        run("(goal %s ?x)" % r)


def test_queries_no_context():
    ''' This test includes two facts (role and index).  And 6 rules.  The rules don't need context
        implemented.  Note this is the first 10 lines of tic tac toe! '''

    gdl_str = """
(role xplayer)
(role oplayer)

(index 1)
(index 2)
(index 3)

(<= (base (cell ?x ?y b))
    (index ?x)
    (index ?y))

(<= (base (cell ?x ?y x))
    (index ?x)
    (index ?y))

(<= (base (cell ?x ?y o))
    (index ?x)
    (index ?y))

(<= (base (control ?p))
    (role ?p))

(<= (input ?p (mark ?x ?y))
    (index ?x)
    (index ?y)
    (role ?p))

(<= (input ?p noop)
    (role ?p))

"""

    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(gdl_str))

    # XXX rename GameDescription to parse gdl.  It doesn't need to be a game.
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

    query = p.build_query_string("(role ?x)")
    res = list(query.subsitute())

    query = p.build_query_string("(base ?x)")
    res = list(query.subsitute())
    X
    
def test_facts_upfront_unification():
    description = """
    (parent (person a) paul)
    (parent (person b) paul)
    (parent sally paul)
    (parent x y)
    (parent jim sally)

    (whoami paul)
    (whoami jane)
    (whoami sally)
    (<= (bla ?x) (whoami ?x))
    (<= (bla ?x) (whoami ?x)
                 (parent (person ?y) ?x))
    """

    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(description))
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

    # # first we create the KB
    # rules = [gdl.create(s) for s in symbolize(description)]
    # kb = prover.KnowledgeBase(rules)

    def run(s):
    #     sentence = gdl.create(s)
    #     results = prover.ask(sentence, kb)

    #     print
    #     print 'query:', s
    #     print
    #     if not results:
    #         print "NO"
    #     else:
    #         for r in results:
    #             print r
        print p.build_query_string(s)


    run("(parent (person ?x) paul)")
    run("(bla ?x)")
    run("(bla paul)")
    run("(bla jane)")
    run("(bla sally)")
    run("(bla rick)")


def test_facts_context_unification():
    description = """
    (parent (person a) paul)
    (parent (person b) paul)
    (parent sally paul)
    (parent jim sally)

    (whoami sally)
    (<= (bla ?x) (whoami ?x)
                 (parent ?y ?x))
    """

    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(description))
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

    # # first we create the KB
    # rules = [gdl.create(s) for s in symbolize(description)]
    # kb = prover.KnowledgeBase(rules)

    def run(s):
    #     sentence = gdl.create(s)
    #     results = prover.ask(sentence, kb)

    #     print
    #     print 'query:', s
    #     print
    #     if not results:
    #         print "NO"
    #     else:
    #         for r in results:
    #             print r
        print p.build_query_string(s)


    try:
        run("(bla jim)")
    except parse.NoRule:
        pass

    run("(bla ?who)")

def test_facts_with_variables():
    description = """
    (index 1)
    (index 2)
    (index 3)

    (mapping 1 42)
    (mapping 2 23)
    (mapping 3 7)
    (mapping 5 8)

    (<= (get (mapping ?x ?y))
        (index ?x) (mapping ?x ?y))
    """

    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(description))
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

    p.build_query_string("(get ?x)")


def test_gets():
    description = """
    (index 1)
    (index 2)
    (index 3)

    (mapping 1 42)
    (mapping 2 23)
    (mapping 3 7)
    (mapping 5 8)

    (<= (get (mapping ?x ?y))
        (index ?x) (mapping ?x ?y))

    (<= (get2 (mapping ?x ?y))
        (index ?x) (index ?y))

    (<= (get3 (mapping 1 ?y ?z))
        (index ?x) (index ?y) (index ?z))

    (<= (get4 (mapping ?x ?y ?z))
        (index ?x) (index ?y) (index ?z)
        (distinct ?x 1))

    (<= (get5 (mapping ?x ?y ?z ?w))
        (index ?x) (index ?y) (index ?z) (index ?w)
        (distinct ?x 1)
        (not (distinct ?y 1)))

    """

    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(description))
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

    def run(s):
        print p.build_query_string(s)

    # first in contrained
    run("(get ?x)")

    expect = """
(get (mapping 1 42))
(get (mapping 2 23))
(get (mapping 3 7))
"""

    # second is cross product
    run("(get2 ?x)")

    expect = """
(get2 (mapping 1 1))
(get2 (mapping 1 2))
(get2 (mapping 1 3))
(get2 (mapping 2 1))
(get2 (mapping 2 2))
(get2 (mapping 2 3))
(get2 (mapping 3 1))
(get2 (mapping 3 2))
(get2 (mapping 3 3))
"""

    # cross product
    run("(get3 ?x)")
    expect = """
(get3 (mapping 1 1 1))
(get3 (mapping 1 1 2))
(get3 (mapping 1 1 3))
(get3 (mapping 1 2 1))
(get3 (mapping 1 2 2))
(get3 (mapping 1 2 3))
(get3 (mapping 1 3 1))
(get3 (mapping 1 3 2))
(get3 (mapping 1 3 3))

"""
    # cross product
    run("(get4 ?x)")

    expect = """
(get4 (mapping 2 1 1))
(get4 (mapping 2 1 2))
(get4 (mapping 2 1 3))
(get4 (mapping 2 2 1))
(get4 (mapping 2 2 2))
(get4 (mapping 2 2 3))
(get4 (mapping 2 3 1))
(get4 (mapping 2 3 2))
(get4 (mapping 2 3 3))
(get4 (mapping 3 1 1))
(get4 (mapping 3 1 2))
(get4 (mapping 3 1 3))
(get4 (mapping 3 2 1))
(get4 (mapping 3 2 2))
(get4 (mapping 3 2 3))
(get4 (mapping 3 3 1))
(get4 (mapping 3 3 2))
(get4 (mapping 3 3 3))

"""
    # cross product
    run("(get5 ?x)")

    def fact_index_x(reg_x):
        reg_x.value = 1
        yield
        reg_x.value = 2
        yield
        reg_x.value = 3
        yield

    def fact_index_y(reg_y):
        reg_y.value = 1
        yield
        reg_y.value = 2
        yield
        reg_y.value = 3
        yield

    def fact_index_z(reg_z):
        reg_z.value = 1
        yield
        reg_z.value = 2
        yield
        reg_z.value = 3
        yield

    def fact_index_w(reg_w):
        reg_w.value = 1
        yield
        reg_w.value = 2
        yield
        reg_w.value = 3
        yield

    def get5(reg_x, reg_y, reg_z, reg_w):
        for res in fact_index_x(reg_x):
            if reg_x.value == 1:
                continue
            for _ in fact_index_y(reg_y):
                if reg_y != 1:
                    continue
                for _ in fact_index_z(reg_z):
                    yield

    def get5(reg_x, reg_y, reg_z, reg_w):
        for x in 2, 3:
            y = 1
            for z in (1,2,3):
                for w in (1, 2, 3):
                    res_x.value = x
                    res_y.value = y
                    res_z.value = z
                    res_w.value = w
                    yield


    expect = """
(get5 (mapping 2 1 1 1))
(get5 (mapping 2 1 1 2))
(get5 (mapping 2 1 1 3))
(get5 (mapping 2 1 2 1))
(get5 (mapping 2 1 2 2))
(get5 (mapping 2 1 2 3))
(get5 (mapping 2 1 3 1))
(get5 (mapping 2 1 3 2))
(get5 (mapping 2 1 3 3))
(get5 (mapping 3 1 1 1))
(get5 (mapping 3 1 1 2))
(get5 (mapping 3 1 1 3))
(get5 (mapping 3 1 2 1))
(get5 (mapping 3 1 2 2))
(get5 (mapping 3 1 2 3))
(get5 (mapping 3 1 3 1))
(get5 (mapping 3 1 3 2))
(get5 (mapping 3 1 3 3))
"""

def compile_function(gen, sig):
    fn_str = []
    for l in gen:
        print l
        fn_str.append(l)

    ns = {}
    exec "\n".join(fn_str) in ns
    fn = ns[sig]
    return fn

def rewrite_all(query, *fns):
    rewrites = set()
    register_ns = {}
    registers = []
    for v in query.variables:
        r = register_ns[v.term] = parse.Register(v.term)
        registers.append(r)

    for fn in fns:
        for _ in fn(*registers):
            rewrites.add(parse.rewrite_literal(query.lit, register_ns))
    return rewrites

def create(description):
    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(description))
    p = parse.GameDescription(symbol_factory, gdl)
    p.process()
    p.dump()

    def run(query_str, expect):
        try:
            q = p.build_query_string(query_str)
        except parse.NoRule:
            assert not expect
            return

        expect = set([parse.string_to_literal(symbol_factory, s) for s in expect])

        rewrites = set()
        if isinstance(q, parse.QueryFact):
            #for res in q.get_results():
            #    print res
            #print q.sig()
            if q.variables:
                fn = compile_function(q.gen_function(), q.def_sig())
                rewrites = rewrite_all(q, fn)

        elif isinstance(q, parse.QueryRule):
            print "QueryRule"
            print "top level sig", q.sig()

            fns = []
            for qr in q.queried_rules:
                fn = compile_function(qr.gen_function(), qr.sig())
                fns.append(fn)

            rewrites = rewrite_all(q, *fns)

        assert rewrites == set(expect)

    return run



def test_gen1():
    description = """
    (index 1)
    (index 2)
    (index 3)

    (mapping 1 42)
    (mapping 3 23)
    (mapping 5 8)

    (<= (get ?x ?y)
        (index ?x) (mapping ?x ?y))

    (<= (get 0 0)
        (index ?x)
        (index ?y)
        (index ?z)
        (index ?w)
        (index ?v))

    (<= (get 0 ?z)
        (index ?x)
        (index ?y)
        (index ?z)
        (index ?w)
        (index ?v))

    (<= (get2 ?x ?y)
        (mapping ?x ?y) (index ?x))

    (somevalue 42)
    (somevalue 23)
    (somevalue 100)

    (<= (get_again ?x ?y)
        (somevalue ?y)
        (mapping ?x ?y))

    (<= (get_unbounded ?x)
        (true (abc 1 ?y))
        (mapping ?x ?y))
    """

    run("(index 1)", ["(index 1)"])
    run("(index 4)", None)
    run("(index ?x)", ["(index 1)", "(index 2)", "(index 3)"])

    run("(mapping ?x ?y)", ["(mapping 1 42)", "(mapping 3 23)", "(mapping 5 8)"])
    run("(mapping 3 ?y)", ["(mapping 3 23)"])
    run("(mapping ?x 23)", ["(mapping 3 23)"])

    run("(get ?a ?b)", [])
    run("(get 0 0)", [])

    run("(get2 ?a ?b)", [])
    run("(get_unbounded ?x)", [])


    def get2_gen(reg_a, reg_b):
        # all variables, renaming done upfront:
        reg_x = reg_a
        reg_y = reg_b

        # do first clause
        for x0, y0 in ((1, 42), (3, 23), (5, 8)):
            # do second clause
            for x1 in (1, 2, 3):
                if x0 != x1:
                    continue
                reg_x.value = x0
                reg_y.value = y0
                yield

    run("(get 5 ?b)")


    run("(get 4 ?b)")
    run("(get ?a 23)")
    run("(get ?a 44)")


    # this tests being ?y bound at runtime with a invalid value
    run("(get_again ?a ?b)")

def test_gen_simple1():
    description = """
    (index 1)
    (index 2)
    (index 3)

    (mapping 1 42)
    (mapping 3 23)
    (mapping 5 8)

    (<= (get1 ?x)
        (index ?x))

    (<= (get2 ?x ?y)
        (index ?x)
        (index ?y))
    """

    run = create(description)

    run("(index ?b)", ["(index 1)", "(index 2)", "(index 3)"])
    run("(mapping ?a ?b)", ["(mapping 1 42)", "(mapping 3 23)", "(mapping 5 8)"])
    run("(mapping 1 ?b)", ["(mapping 1 42)"])

    run("(get1 ?a)", ["(get1 1)", "(get1 2)", "(get1 3)"])
    run("(get2 ?b ?c)", ["(get2 1 1)", "(get2 1 2)", "(get2 1 3)",
                         "(get2 2 1)", "(get2 2 2)", "(get2 2 3)",
                         "(get2 3 1)", "(get2 3 2)", "(get2 3 3)"])
    # TODO:
    #run("(get1 1)", [])

def test_gen_simple2():
    description = """
    (mapping 1 42)
    (mapping 3 23)
    (mapping 5 8)

    (<= (get1 ?x ?y)
        (mapping ?x ?y))

    (<= (get2 ?x)
        (mapping ?x ?y))

    """

    run = create(description)

    run("(mapping ?a ?b)", ["(mapping 1 42)", "(mapping 3 23)", "(mapping 5 8)"])
    run("(mapping 1 ?b)", ["(mapping 1 42)"])

    # TODO
    run("(get1 ?b ?c)", ["(get1 1 42)", "(get1 3 23)", "(get1 5 8)"])
    run("(get2 ?a)", ["(get2 1)", "(get1 3)", "(get1 5)"])
    run("(get1 3)", [])


def test_never_bound():
    # should not compile, ?y was never bound.  Compile time error.
    description = """
    (index 1)

    (<= (get ?x ?y)
        (index ?x))
    """
    run = create(description)
    run("(get 1 ?a)", [])
