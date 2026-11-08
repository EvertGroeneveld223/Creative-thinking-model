"""Logged wave runs replay exactly, and a changed log is caught. Uses a temp folder, not s6_patches/runs."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "s6_patches"))
sys.dont_write_bytecode = True
import waves4 as W
class T(unittest.TestCase):
    def go(self, mode, seed):
        d = tempfile.mkdtemp(); return W.logged_run(25, mode, seed, d)[0]
    def test_replay_all_modes(self):
        for mode in ("base", "polar", "off"):
            self.assertTrue(W.replay(self.go(mode, "abc123")), mode)
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
