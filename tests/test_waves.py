"""Logged wave runs replay exactly, and a changed log is caught. Uses a temp folder, not s6_patches/runs."""
import json, os, random, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "s6_patches"))
sys.dont_write_bytecode = True
import waves4 as W, channel as C
class T(unittest.TestCase):
    def go(self, mode, seed):
        d = tempfile.mkdtemp(); return W.logged_run(25, mode, seed, d)[0]
    def test_replay_all_modes(self):
        for mode in ("base", "polar", "off", "shuffled", "polar_shuffled"):
            self.assertTrue(W.replay(self.go(mode, "abc123")), mode)
    def test_return_noise_never_changes_truth(self):   # same seed with and without the return channel: only the resend count may differ
        def steps(mode, ret):
            d = tempfile.mkdtemp(); p = W.logged_run(25, mode, "c0de", d, ret=ret)[0]
            return [json.loads(x) for x in open(p)]
        for mode in ("base", "polar", "shuffled"):
            a, b = steps(mode, False), steps(mode, True)
            sa = [r for r in a if r["type"] == "step"]; sb = [{k: v for k, v in r.items() if k != "resends"} for r in b if r["type"] == "step"]
            self.assertEqual(sa, sb, mode)
            self.assertGreater(sum(r.get("resends", 0) for r in b if r["type"] == "step"), 0, mode)   # the channel really did corrupt something
    def test_return_run_replays(self):
        d = tempfile.mkdtemp(); self.assertTrue(W.replay(W.logged_run(25, "polar", "ab12", d, ret=True)[0]))
    def test_corrupted_reply_is_caught(self):
        msg = '["EXPLAINED", 12]'; rng = random.Random(1)
        for _ in range(200):
            self.assertNotEqual(C.sha(C.corrupt(msg, rng.random)), C.sha(msg))
        got, k = C.send_back(msg, lambda t: .9, 0, rng.random)
        self.assertEqual(got, msg)
        with self.assertRaises(RuntimeError): C.send_back(msg, lambda t: 1.0, 0, rng.random, limit=50)   # a dead channel never delivers a bad copy
    def test_shuffled_is_not_the_wave_field(self):
        ws = [dict(k=[1, 0, 0], om=1.0, phi=0.0, A=1.0)]; rng = random.Random(2)
        self.assertEqual(len({round(W.local(W.fresh(ws, rng.random), [1, 1, 1], 3)[0], 6) for _ in range(20)}), 20)
    def test_same_seed_same_log(self):
        a = [json.loads(x) for x in open(self.go("polar", "feed"))]; b = [json.loads(x) for x in open(self.go("polar", "feed"))]
        self.assertEqual(a[1:-1], b[1:-1])
    def test_off_never_mutates(self):
        for x in open(self.go("off", "01")):
            e = json.loads(x)
            if e["type"] == "step": self.assertEqual(e["chans"], [])
    def test_tampered_log_fails(self):
        p = self.go("base", "beef"); rows = open(p).read().splitlines()
        e = json.loads(rows[5]); e["kind"] = "TAMPERED"; rows[5] = json.dumps(e)
        open(p, "w").write("\n".join(rows) + "\n")
        self.assertFalse(W.replay(p))
    def test_logged_timeout_is_reused(self):   # a timeout in the footer forces the same evaluation to UNREACHABLE on replay
        W._forced = {1}
        try:
            W._ev = 0; self.assertEqual(W.timed_eval(dict(base="fib", m=5, ops=[]))["kind"], "UNREACHABLE")
        finally: W._forced = None
if __name__ == "__main__": unittest.main()
