import time

from ggplib import symbols
from ggplib.prover import parse
from ggplib.propnet import lookup

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

def test_facts():
    description = """
    (mapping 1 (f1 1 3) (f2 1 3))
    (mapping 1 (f1 1 3) (f2 2 3))
    (mapping 1 (f1 2 3) (f2 1 3))
    (mapping 1 (f1 2 5) (f2 2 3))
    (mapping 1 (f1 2 3) (f2 2 3))
    (mapping 1 (f1 2 3) (f2 1 3))
    (mapping 1 (f1 3 6) (f2 2 3))
    (mapping 1 (f1 3 6) 64)
    (mapping 1 (f1 3 6) (f3 3 5))
    (mapping 1 (f1 3 6))
    (mapping 5 (f1 1 6))
    (mapping 3 23)
    (mapping 5 8)
    (mapping 1 42)
    (mapping 3 23)
    (mapping 5 8)
    """

    symbol_factory = symbols.SymbolFactory()
    gdl = list(symbol_factory.to_symbols(description))
    dump(gdl)


test_all_games_DEBUG = False
def test_all_games():
    " tests that all games do not have function terms "

    for game in lookup.get_all_game_names():
        if test_all_games_DEBUG:
            print
            print game
            print "=" * len(game)
        gdl = lookup.get_gdl_for_game(game)

        all_fact_terms = set()
        base_facts = {}
        for terms in parse.find_facts(gdl):
            assert isinstance(terms, symbols.ListTerm)
            fact = parse.Fact(terms)

            if fact.base_term in ("base", "input", "init"):
                continue

            else:
                for t in fact.terms:
                    assert not symbols.is_function(t)

            all_fact_terms.update(list(parse.extract_terms(fact.body)))

            base_facts.setdefault(fact.base_term, []).append(fact)

        domains = {}

        # check facts have of the same base_term all of the same arity
        for b, facts in base_facts.items():
            first = facts[0]
            for f in facts[1:]:
                assert f.arity() == first.arity()

            # calculate domain
            domain = [set() for _ in range(first.arity() - 1)]
            for f in facts:
                for t, s in zip(f.body, domain):
                    s.add(t)
            domains[b] = domain

        # check that the fact_terms are not in base_terms of facts
        all_bases = set(base_facts)
        assert len(all_bases.intersection(all_fact_terms)) == 0

        if test_all_games_DEBUG:
            for b, domain in domains.items():
                print "%s: %s" % (b, list(domain))

            print "All:"
            print list(all_fact_terms)

def test_speed():

    for ii in range(100):
        s = time.time()
        test_all_games()
        print (time.time() - s)
