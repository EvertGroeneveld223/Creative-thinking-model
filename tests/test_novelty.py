"""python -m unittest discover -s tests   (from the project root; no network used)"""
import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "s7_novelty"))
import novelty as N
FFD = "0,1,1,1,2,5,21,233,10946"
def cache(): return N.Cache(path=None)
def oeis(rows):
    return lambda url: json.dumps(rows)
class T(unittest.TestCase):
    def test_exact_match_is_known(self):
        r = N.check([0,1,1,1,2,5,21,233], cache=cache(), fetch=oeis([dict(number=7570, data=FFD, name="F(F(n))")]))
        self.assertEqual((r["verdict"], r["n"]), ("KNOWN", 0))
        self.assertEqual(r["searched"]["oeis-terms"]["hits"][0]["id"], "A007570")
    def test_loose_oeis_hit_is_not_a_match(self):   # the terms are absent, or only part of a larger number
        for data in ("9,9,9,9", "10,1,1,1,2,5,21,2334"):
            r = N.check([0,1,1,1,2,5,21,233], cache=cache(), fetch=oeis([dict(number=1, data=data, name="x")]))
            self.assertEqual(r["verdict"], "NOT-FOUND", data)
    def test_no_match_not_found(self):
        r = N.check([3,1,4,7,4,24,3,1], cache=cache(), fetch=lambda u: "null")
        self.assertEqual((r["verdict"], r["n"]), ("NOT-FOUND", 1))
    def test_outage_is_never_novelty(self):
        def down(url): raise N.Unavailable("HTTP 429")
        r = N.check([3,1,4,7,4,24,3,1], cache=cache(), fetch=down)
        self.assertEqual((r["verdict"], r["n"]), ("UNCHECKED", None))
    def test_failure_not_cached_but_success_is(self):
        c = cache(); calls = []
        def down(url): raise N.Unavailable("x")
        N.oeis_terms([1,2,3,4,5,6], c, down)
        def up(url): calls.append(url); return "null"
        N.oeis_terms([1,2,3,4,5,6], c, up); N.oeis_terms([1,2,3,4,5,6], c, up)
        self.assertEqual(len(calls), 1)
    def test_non_json_is_unchecked(self):
        r = N.check([3,1,4,7,4,24,3,1], cache=cache(), fetch=lambda u: "<html>busy</html>")
        self.assertEqual(r["verdict"], "UNCHECKED")
    def test_trivial_not_searched(self):
        def boom(url): raise AssertionError("must not search")
        for terms in ([1,2,1,2,1,2,1,2], [1,2,3]):
            self.assertEqual(N.check(terms, cache=cache(), fetch=boom)["verdict"], "TRIVIAL")
    def test_bot_check_page_is_unchecked(self):
        self.assertEqual(N.duckduckgo("x", cache(), lambda u: "<html>please confirm you are human</html>")["status"], "UNCHECKED")
    def test_crossref_needs_all_words_in_title(self):
        body = json.dumps(dict(message=dict(items=[dict(title=["Fibonacci numbers modulo p"], DOI="a"), dict(title=["Period of <i>nested</i> Fibonacci"], DOI="b")])))
        r = N.crossref("q", ["nested", "fibonacci"], cache(), lambda u: body)
        self.assertEqual([h["url"] for h in r["hits"]], ["https://doi.org/b"])
if __name__ == "__main__": unittest.main()
