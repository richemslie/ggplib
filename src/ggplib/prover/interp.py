' moved some WIP code in here...  temporary graveyard, will come back to life. '''

###############################################################################
# XXX not used currently.  I think we will need caching......

class FunctionDatabase:
    def __init__(self):
        self.facts_db = {}

    def add_fact_function(self, query):
        # it is the signature of the query that is important.  First we to determine variables in
        # query literal.

        print 'here', query.lit
        count = 0
        sig = []
        for term in extract_terms(query.lit):
            if isinstance(term, Term):
                if term.is_variable:
                    term = "?ro_%s" % count
                    count += 1

                sig.append(term)
            else:
                XXX

        sig = tuple(sig)
        if sig in self.facts_db:
            print ":::: SEEN already", sig
        else:
            print ":::: ADDING", sig
            self.facts_db[sig] = query


class QueryFact(Query):
    def subsitute(self):
        ' yield all values of the query.  Does yield dupes. '
        for _, u in self.facts:
            new_terms = []
            for t in self.lit:

                if is_function(t):
                    function_terms = []
                    for tt in t:
                        if tt.is_variable:
                            assert tt in u.unified_vars
                            tt = u.unified_vars[tt]
                        function_terms.append(t)
                    t = CompoundLiteral(function_terms)

                elif t.is_variable:
                    assert t in u.unified_vars
                    t = u.unified_vars[t]
                new_terms.append(t)
            yield CompoundLiteral(new_terms)

class QueryRule(Query):
    def subsitute(self):

        print "subsitute QueryRule1: lit= %s" % str(self.lit)
        print "we want to return lit, with variables in lit subsituted."
        print "we want to return lit, with variables in lit subsituted."
        print


        print "WTFsubsitute QueryRule2", self.variables

        print "for each rule and unified, we look at renaming.  Then we use the rhs of renamings to figure what variables we want from claus."

        for (r, u), rqc in zip(self.rules, self.rules_query_clauses):
            print "Rule and Unified:", r, u

            want_variables = set()
            for term in u.renaming.values():

                # need variables from head
                assert isinstance(term, (Term, ListTerm))

                if is_function(term):
                    for tt in term:
                        if tt.is_variable:
                            want_variables.add(tt)
                elif term.is_variable:
                    want_variables.add(term)

            print "want_variables", want_variables

            print "rule query clauses", rqc

            for f in rqc.subqueries:
                # for now we only support query facts.  This will go away when we to only rules.  Thankfuck.

                assert isinstance(f, QueryFact), "For now we only support factsXXX"
                print f
                for _, u in f.facts:
                    print u

            # so what we can do is something like
            prev_gen = None
            for f in reversed(rqc.subqueries):
                prev_gen = self.create_gen(f.fact, prev_gen)

    def create_gen(self, facts, prev):
        if prev is None:
            def gen():
                for _, u in facts:
                    yield x
            return gen
