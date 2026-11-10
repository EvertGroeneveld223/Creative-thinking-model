"""A gap really asks the page; the world still has the last word. Uses fake pages, no network."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "s1_rulebook"))
import rulebook as R
ONE, TWO = ("+", ("1",), ("1",)), ("2",)
GOOD = "| '''A2:''' || ''a'' + ''S''(''b'') = ''S''(''a'' + ''b'')"
BAD = "a + S(b) = S(S(a + b))"
def base(): return {k: v for k, v in R.RULES_ALL.items() if k != "A2"}
class T(unittest.TestCase):
    def test_rule_from_a_page_closes_the_gap(self):
        rules = base(); rid, _ = R.ask_the_web(ONE, TWO, rules, lambda u: GOOD)
        self.assertEqual(rules[rid]["who"], R.PAGES[0])
        self.assertEqual(R.send("g", ONE, TWO, rules)["status"], "EXPLAINED")
    def test_wrong_rule_on_a_page_is_refused(self):
        rules = base(); rid, rep = R.ask_the_web(ONE, TWO, rules, lambda u: BAD)
        self.assertIsNone(rid); self.assertTrue(any("rejected" in x for x in rep))
        self.assertEqual(R.send("g", ONE, TWO, rules)["status"], "WORKS-BUT-UNEXPLAINED")
    def test_no_network_leaves_the_gap_open(self):
        def down(u): raise OSError("offline")
        rules = base(); rid, rep = R.ask_the_web(ONE, TWO, rules, down)
        self.assertIsNone(rid); self.assertTrue(all(x["status"] == "UNCHECKED" for x in rep))
        self.assertEqual(R.send("g", ONE, TWO, rules)["status"], "WORKS-BUT-UNEXPLAINED")
    def test_unrelated_equation_is_ignored(self):
        rules = base(); rid, _ = R.ask_the_web(ONE, TWO, rules, lambda u: "a + 0 = a")
        self.assertIsNone(rid)
    def test_parser(self):
        self.assertEqual(R.parse_term("a + S(b)"), ("+", "?a", ("S", "?b")))
        self.assertIsNone(R.parse_term("a + c")); self.assertIsNone(R.parse_term("S(a"))
if __name__ == "__main__": unittest.main()
