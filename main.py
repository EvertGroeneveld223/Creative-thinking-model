"""Entry point for the whole project. Each stage can also be run from its own folder.
    python main.py claims [--slow]   check every reported result, rewrite CLAIMS.md and PROMPT_PROGRESS.md
    python main.py prompt            rewrite PROMPT_PROGRESS.md from the current CLAIMS.md
    python main.py tests             unit tests (no network; a few minutes)
    python main.py proofs            step checks of the theorems
    python main.py ledger            the prediction ledger and its score
    python main.py loop              run the rule miner
    python main.py why CHAIN M       the why-chain and certificate for one case, for example: python main.py why LL 25"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
def run(args, where="."): return subprocess.call([sys.executable] + args, cwd=os.path.join(ROOT, where))
def main(a):
    if not a or a[0] not in ("claims", "prompt", "tests", "proofs", "ledger", "loop", "why"): print(__doc__); return 0
    if a[0] == "claims": return run(["claims.py"] + a[1:])
    if a[0] == "prompt": return run(["make_prompt.py"])
    if a[0] == "tests": return run(["-W", "ignore", "-m", "unittest", "discover", "-s", "tests"])
    if a[0] == "proofs": return run(["prove.py"], "s8_proofs")
    if a[0] == "ledger": return run(["ledger.py", "report"], "calibration")
    if a[0] == "loop": return run(["loop.py"] + a[1:], "s9_loop")
    return run(["why2.py", "report"] + a[1:], "s6_patches")
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
