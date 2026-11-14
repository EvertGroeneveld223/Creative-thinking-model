"""The period machinery against plain computation, with big integers where it is cheap. No network used."""
import os, random, sys, tempfile, unittest
HERE = os.path.dirname(__file__)
for d in ("s4_merging", "s6_patches", "s7_novelty", "s8_proofs", "calibration"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
sys.dont_write_bytecode = True
import engine1 as g, merge as M, tables as TB, general as G, sym9, ledger as K
class Merge(unittest.TestCase):
    def test_proof_matches_brute_force_on_random_expressions(self):
        rng = random.Random(11); B = ["fib", "luc", "tri", "sq"]; n = 0
        for _ in range(60):
            p = dict(base=rng.choice(B), m=rng.randint(2, 16), ops=[[rng.choice(["add", "mul", "comp"]), rng.choice(B)] for _ in range(rng.randint(0, 2))])
            L = M.explain(p)[0]
            s, W = g.world(g.tree(p), p["m"], N=max(300, 3*L + 20))
            if len(s) >= 3*L:
                n += 1; self.assertEqual(W, L, p)
        self.assertGreater(n, 30)
    def test_digit_sum_has_no_proof_outside_divisors_of_nine(self):
        self.assertIsNone(M.explain(dict(base="ds", m=7, ops=[]))[0])
        self.assertEqual(M.explain(dict(base="ds", m=9, ops=[]))[0], 9)
class Formula(unittest.TestCase):
    def test_theorem_1_with_exact_inner_index(self):
        lt = G.table("L", 625); a, b = 2, 1; s = []
        for n in range(600):
            s.append(lt[a % len(lt)]); a, b = b, a + b
        self.assertTrue(all(s[i] == s[i+150] for i in range(450)))
        self.assertFalse(all(s[i] == s[i+30] for i in range(450)))
    def test_known_savings_and_a_conflict(self):
        self.assertEqual(G.predict_q("L", "L", 13)[0], 24); self.assertEqual(G.true_period("L", "L", 13), 24)
        self.assertEqual(G.predict_q("L", "F", 73)[0], 114); self.assertEqual(G.true_period("L", "F", 73), 114)
        self.assertEqual(G.predict_q("L", "F", 61)[1], "no common shift"); self.assertEqual(G.true_period("L", "F", 61), G.bound("L", "F", 61))
    def test_formula_on_small_m(self):
        for m in range(2, 150):
            for f in "FL":
                for h in "FL":
                    self.assertEqual(G.predict(f, h, m), G.true_period(f, h, m), (f, h, m))
class Block(unittest.TestCase):
    def test_the_example_that_motivated_it(self):
        self.assertEqual(sym9.crt_block(list("LLF"), 3, 1)[0], 12)
    def test_never_below_the_truth(self):
        import sym9_tests as S
        for ch in ("FTT", "LLF", "QQL", "PFT"):
            for m in (3, 4, 6, 13):
                t = S.true_period(list(ch), m)
                if t: self.assertGreaterEqual(sym9.crt_block(list(ch), m, 2)[0], t[0], (ch, m))
class Ledger(unittest.TestCase):
    def setUp(self):
        self.p = os.path.join(tempfile.mkdtemp(), "l.jsonl")
    def test_chain_catches_an_edit(self):
        K.commit(.8, "a", "b", self.p); K.commit(.3, "c", "d", self.p); K.resolve("P001", 1, "e", self.p)
        self.assertTrue(K.verify(self.p)[0])
        rows = open(self.p).read().replace('"p": 0.3', '"p": 0.9'); open(self.p, "w").write(rows)
        self.assertFalse(K.verify(self.p)[0])
    def test_a_result_cannot_be_rewritten(self):
        K.commit(.8, "a", "b", self.p); K.resolve("P001", 0, "e", self.p)
        with self.assertRaises(ValueError): K.resolve("P001", 1, "f", self.p)
    def test_certainty_is_refused(self):
        with self.assertRaises(ValueError): K.commit(1.0, "a", "b", self.p)
    def test_score(self):
        K.commit(.9, "a", "b", self.p); K.commit(.2, "c", "d", self.p); K.resolve("P001", 1, "e", self.p); K.resolve("P002", 1, "f", self.p)
        s = K.score(self.p); self.assertAlmostEqual(s["brier"], (.01 + .64)/2); self.assertEqual(s["hit_rate"], .5)
class Docs(unittest.TestCase):
    def test_handoff_cites_only_real_claims(self):
        import re
        root = os.path.join(HERE, "..")
        ids = set(re.findall(r'@claim\("(C\d+)"', open(os.path.join(root, "claims.py")).read()))
        cited = set(re.findall(r"\bC\d\d\b", open(os.path.join(root, "HANDOFF.md")).read()))
        self.assertTrue(cited); self.assertEqual(cited - ids, set()); self.assertEqual(ids - cited, set())
    def test_prompt_fills_every_marker(self):
        import re
        sys.path.insert(0, os.path.join(HERE, "..")); import make_prompt as P
        ids = re.findall(r'@claim\("(C\d+)"', open(os.path.join(HERE, "..", "claims.py")).read())
        text = P.build([f"- **{c}** COMPUTED. Placeholder." for c in ids], "2000-01-01")
        self.assertNotIn("<<", text); self.assertEqual(text.count("`" * 3), 2)
        for c in ids: self.assertIn(f"- {c} COMPUTED", text)
        for part in ("Conjecture 2 (exact formula)", "Return to sender", "Prove or refute Conjecture 2", "Evidence only counts", "L(L(n)) mod 5^k, k = 2..4: 6 30 150"):
            self.assertIn(part, text)
if __name__ == "__main__": unittest.main()
