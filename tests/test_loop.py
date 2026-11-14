"""The closed loop: rule store, hold-out, refutation, read-back. No network used."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "s9_loop"))
import loop as L
def pts(vals, B=None): return [dict(k=i+1, T=t, B=(B[i] if B else 2*t)) for i, t in enumerate(vals)]
class T(unittest.TestCase):
    def test_world_is_exact(self):
        self.assertEqual(L.world("LL", 25), (6, 12))
        self.assertEqual(L.world("LF", 25), (30, 60))
    def test_fit_needs_two_steps_and_finds_the_tail(self):
        self.assertIsNone(L.fit(pts([6, 30]), 5))
        self.assertEqual(L.fit(pts([6, 6, 30, 150]), 5), (2, 6, 5))
    def test_holdout_rejects(self):
        rules, rej = L.mine({("LL", 5): pts([6, 30, 150, 999, 1])})
        self.assertEqual(rules, {}); self.assertEqual(len(rej), 1)
    def test_no_gap_no_rule(self):
        s = [dict(k=i+1, T=5**i, B=5**i) for i in range(6)]
        self.assertEqual(L.mine({("FF", 5): s})[0], {})
    def test_rule_is_read_back_and_gap_closes(self):
        rules, _ = L.mine({("LL", 5): pts([6, 30, 150, 750, 3750])})
        self.assertEqual(L.value(rules["LL:5"], 7), 6*5**6)
        self.assertEqual(L.predict(rules, "LL", 5**7)[0], 6*5**6)      # read from the store, the tables are not consulted
        self.assertEqual(L.predict(rules, "LL", 5**7)[1], ["LL:5"])
    def test_refuted_rule_stops_firing_and_is_remined(self):
        s = pts([6, 30, 150, 750, 3750])
        rules, _ = L.mine({("LL", 5): s}); self.assertEqual(rules["LL:5"]["status"], "CONJECTURE" if "LL:5" not in L.PROVED else "PROVED")
        bad = pts([6, 30, 150, 750, 3750, 3750, 3750, 3750])
        new = L.reconcile(rules, "LL:5", bad[5:], 5)
        self.assertEqual((new["r"], new["status"]), (1, "CONJECTURE"))
        rules["FF:5"] = dict(rules["LL:5"], id="FF:5", status="REFUTED", chain="FF")
        self.assertEqual(L.predict(rules, "FF", 5)[1], [])
    def test_learned_rule_removes_the_surprise(self):
        rules, _ = L.mine({("LL", 5): pts([6, 6, 30, 150, 750, 3750], [6, 12, 60, 300, 1500, 7500])})
        before, after = L.learned_worth(rules, "LL", 25)
        self.assertEqual(before, 0.5); self.assertEqual(after, 0)
    def test_scrambled_data_gives_no_ladder_here(self):
        data = {("LL", 5): pts([6, 6, 30, 150, 750, 3750], [6, 12, 60, 300, 1500, 7500])}
        self.assertEqual(L.mine(L.scramble(data, "t"))[0], {})
    def test_a_passing_rule_is_not_called_explained(self):
        self.assertIn("e=0", L.cube(dict(status="CONJECTURE")))
        self.assertEqual(L.cube(dict(status="CONJECTURE", novelty=dict(n=1))), "DISCOVERY")
        self.assertEqual(L.cube(dict(status="PROVED", novelty=dict(n=0))), "KNOWN")
if __name__ == "__main__": unittest.main()
