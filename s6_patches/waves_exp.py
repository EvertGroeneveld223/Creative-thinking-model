"""The experiment in PREREG_waves.md.
    python waves_exp.py run [WORKERS]     resumable: a run with a footer is not repeated
    python waves_exp.py status            counts files only, looks at no outcome
    python waves_exp.py analyze           writes waves_exp.json. Refuses until all runs have finished.
    python waves_exp.py replay [WORKERS]  re-runs every log from its seed and compares every step"""
import hashlib, json, os, random, statistics as st, sys
import multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "runs_v2")
MODES = ["off", "base", "shuffled", "polar", "polar_shuffled"]
N, T, LABEL = 50, 150, "waves-exp-1"
def seed(mode, i): return hashlib.sha256(f"{LABEL}|{mode}|{i}".encode()).hexdigest()[:16]
def plan():
    P = [(m, seed(m, i)) for m in MODES for i in range(N)]
    random.Random(LABEL).shuffle(P)
    return P
def path(m, s): return os.path.join(OUT, f"{m}_{s}.jsonl")
def finished(m, s):
    if not os.path.exists(path(m, s)): return False
    with open(path(m, s), "rb") as f:
        rows = f.read().splitlines()
    return bool(rows) and b'"type": "footer"' in rows[-1]
def one(job):
    import waves4 as W
    m, s = job
    W.logged_run(T, m, s, OUT, ret=True)
    return job
def replay_one(job):
    import contextlib, io, waves4 as W
    with contextlib.redirect_stdout(io.StringIO()):
        return job, W.replay(path(*job))
def replay_all(workers):
    bad = []; n = 0
    with mp.Pool(workers, maxtasksperchild=1) as pool:
        for job, ok in pool.imap_unordered(replay_one, plan(), chunksize=1):
            n += 1; bad += [] if ok else [job]
    print("replayed", n, "failed", len(bad), bad[:10])
    json.dump(dict(replayed=n, failed=bad), open(os.path.join(HERE, "waves_exp_replay.json"), "w"), indent=1)
    return not bad
def run(workers):
    todo = [j for j in plan() if not finished(*j)]
    print(len(todo), "runs to do", flush=True)
    with mp.Pool(workers, maxtasksperchild=1) as pool:
        for k, j in enumerate(pool.imap_unordered(one, todo, chunksize=1)):
            print(k+1, "of", len(todo), j, flush=True)
def perm(a, b, shuffles, rng):
    obs = abs(st.mean(a) - st.mean(b)); pool = a + b; n = len(a); c = 0
    for _ in range(shuffles):
        rng.shuffle(pool)
        c += abs(sum(pool[:n])/n - sum(pool[n:])/len(b)) >= obs - 1e-12
    return (c + 1) / (shuffles + 1)
def boot(a, b, rng, reps=20000):
    D = sorted(st.mean(rng.choices(a, k=len(a))) - st.mean(rng.choices(b, k=len(b))) for _ in range(reps))
    return D[int(.025*reps)], D[int(.975*reps)]
def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0]*len(ps); top = 0
    for r, i in enumerate(order):
        top = max(top, min(1, (len(ps) - r)*ps[i])); adj[i] = top
    return adj
def load():
    D = {m: [] for m in MODES}
    for m, s in plan():
        rows = [json.loads(x) for x in open(path(m, s))]
        D[m].append((rows[0], [r for r in rows if r["type"] == "step"], rows[-1]))
    return D
def secondary(D):
    """Descriptive only, as pre-registered: distinct finds by (modulus, sequence) instead of by string."""
    import signal, waves4 as W
    g = W.g; memo = {}
    class TO(Exception): pass
    def h(*a): raise TO()
    signal.signal(signal.SIGALRM, h)
    def seq(e):
        k = (e["m"], e["sexpr"])
        if k not in memo:
            signal.alarm(4)
            try:
                s, _ = g.world(g.tree(e["point"]), e["m"], N=240); memo[k] = tuple(s) if len(s) >= 60 else k
            except TO: memo[k] = k
            finally: signal.alarm(0)
        return memo[k]
    out = {}
    for m in MODES:
        counts = [len({(e["m"], seq(e)) for e in r[1] if e.get("worth", 0) > 0}) for r in D[m]]
        out[m] = dict(mean=st.mean(counts), sd=st.stdev(counts))
    return out
def analyze(shuffles=200000):
    missing = [j for j in plan() if not finished(*j)]
    if missing: sys.exit(f"{len(missing)} runs have not finished; the pre-registration forbids looking")
    D = load(); rng = random.Random(LABEL + "|analysis")
    F = {m: [r[2]["finds_all"] for r in D[m]] for m in MODES}
    tests = [("base vs shuffled", F["base"], F["shuffled"]), ("polar vs polar_shuffled", F["polar"], F["polar_shuffled"]),
             ("pooled mutation vs off", F["base"] + F["shuffled"] + F["polar"] + F["polar_shuffled"], F["off"])]
    ps = [perm(a, b, shuffles, rng) for _, a, b in tests]; adj = holm(ps); out = dict(primary=[], per_mode={})
    for (name, a, b), p, q in zip(tests, ps, adj):
        lo, hi = boot(a, b, rng)
        out["primary"].append(dict(test=name, mean_a=st.mean(a), mean_b=st.mean(b), diff=st.mean(a) - st.mean(b), ci95=[lo, hi], p=p, p_holm=q, significant=q < .05))
        print(f"{name}: {st.mean(a):.2f} vs {st.mean(b):.2f}, diff {st.mean(a)-st.mean(b):+.2f}, 95% CI [{lo:+.2f}, {hi:+.2f}], p {p:.4f}, Holm p {q:.4f}")
    for m in MODES:
        R = D[m]; K = lambda k: st.mean(r[2]["kinds"][k] for r in R)
        out["per_mode"][m] = dict(n=len(R), finds_mean=st.mean(F[m]), finds_sd=st.stdev(F[m]), finds_mutated=st.mean(r[2]["finds_mutated"] for r in R), mutations=st.mean(sum(r[2]["muts"].values()) for r in R),
                                  resends=st.mean(sum(e.get("resends", 0) for e in r[1]) for r in R), timeouts=st.mean(len(r[2]["timeouts"]) for r in R), explained=K("EXPLAINED"), false=K("FALSE"), unreachable=K("UNREACHABLE"), out_of_grid=K("OUT-OF-GRID"))
        print(m, {k: round(v, 2) for k, v in out["per_mode"][m].items()})
    out["secondary_by_sequence"] = secondary(D); print("secondary, distinct by (modulus, sequence):", {k: round(v["mean"], 2) for k, v in out["secondary_by_sequence"].items()})
    a, b = F["polar"], F["base"]; out["secondary_polar_vs_base"] = dict(diff=st.mean(a) - st.mean(b), ci95=list(boot(a, b, rng)))
    json.dump(out, open(os.path.join(HERE, "waves_exp.json"), "w"), indent=1)
    return out
if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    if a[0] == "run": run(int(a[1]) if len(a) > 1 else 3)
    elif a[0] == "status": print(sum(finished(*j) for j in plan()), "of", len(plan()), "finished")
    elif a[0] == "analyze": analyze()
    elif a[0] == "replay": sys.exit(0 if replay_all(int(a[1]) if len(a) > 1 else 4) else 1)
