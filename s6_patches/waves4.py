import os as _os
_P=lambda *a:_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",*[x for x in a if x]))
"""Patch 3: POLARIZED WAVES. Four waves, each disturbs one channel of the data cell:
   RULE  swap a block for another of the SAME area, or flip + / x          (moves along X)
   AREA  swap a block for one from a DIFFERENT area                         (moves along Y)
   DEPTH wrap the idea in one more composition, or unwrap one              (moves along Z)
   MOD   shift the modulus by +/-1                                           (parameter)
 local disruption of wave i:  d_i(r,t) = |sin(k_i.r - w_i t + phi_i)|
 mutation happens with prob  mean_i(A_i d_i) / max(A),  channel chosen with prob ~ A_i d_i
 amplitude adapts per channel: A_i *= 1.25 when its mutation led to a useful find (explained, worth > 0),
                               A_i *= 0.8 when it led to FALSE / UNREACHABLE; clamp [0.3, 2].
BASELINE = the v2/v3 mutation (one wave field, mutation type fixed by fixed odds).
OFF = control: same moves through the grid, no wave mutation at all.
Every run draws a seed from os.urandom and writes runs/<mode>_<seed>.jsonl: a header, one line per step, a footer.
Replay: python waves4.py replay runs/<file>.jsonl   re-runs from the seed and compares every step.
The 5 s evaluation alarm depends on the clock, so timeouts are logged and replay reuses them instead of re-timing."""
import sys, json, math, hashlib, os, platform
sys.path.insert(0, _P("s4_merging",""))
import engine1 as g, v2, v3
u, pick = g.u, g.pick
CH = ["RULE", "AREA", "DEPTH", "MOD"]
def new_waves():
    W = []
    for _ in CH:
        v = [u()*2-1 for _ in range(3)]; nv = math.sqrt(sum(a*a for a in v)) or 1; lam = 1.5 + 4*u()
        W.append(dict(k=[2*math.pi/lam*a/nv for a in v], om=0.3+1.2*u(), phi=2*math.pi*u(), A=1.0))
    return W
def local(W, r, t): return [abs(math.sin(sum(ki*ri for ki, ri in zip(w["k"], r)) - w["om"]*t + w["phi"])) for w in W]
def mutate_channel(p, ch):
    q = json.loads(json.dumps(p)); blocks = ["base"] + list(range(len(q["ops"])))
    get = lambda s: q["base"] if s == "base" else q["ops"][s][1]
    def put(s, b):
        if s == "base": q["base"] = b
        else: q["ops"][s][1] = b
    if ch == "RULE":
        flips = [i for i, o in enumerate(q["ops"]) if o[0] in ("add", "mul")]
        if flips and u() < .4:
            i = pick(flips); q["ops"][i][0] = "mul" if q["ops"][i][0] == "add" else "add"; return q, "RULE: flip +/x"
        s = pick(blocks); old = get(s); same = [b for b in v2.BLK if g.AREA[b] == g.AREA[old] and b != old]
        if not same: return q, None
        nb = pick(same); put(s, nb); return q, f"RULE: {old}->{nb}"
    if ch == "AREA":
        s = pick(blocks); old = get(s); other = [b for b in v2.BLK if g.AREA[b] != g.AREA[old]]
        nb = pick(other); put(s, nb); return q, f"AREA: {old}->{nb}"
    if ch == "DEPTH":
        comps = [i for i, o in enumerate(q["ops"]) if o[0] == "comp"]
        if comps and u() < .4: q["ops"].pop(comps[-1]); return q, "DEPTH: unwrap"
        q["ops"].append(["comp", pick(v2.BLK)]); return q, f"DEPTH: wrap {q['ops'][-1][1]}"
    nm = min(16, max(4, q["m"] + pick([-1, 1]))); r = f"MOD: {q['m']}->{nm}"; q["m"] = nm; return q, r
def classify_old(notes, p):
    out = []
    for n in notes:
        if n.startswith("m "): out.append("MOD")
        elif n == "op flip": out.append("RULE")
        else:
            a, b = n.split(" ")[-1].split("->"); out.append("RULE" if g.AREA[a] == g.AREA[b] else "AREA")
    return out
import signal
class _TO(Exception): pass
def _h(*a): raise _TO()
signal.signal(signal.SIGALRM, _h)
_ev = 0; _timeouts = []; _forced = None     # evaluation counter; timed-out evaluations; replay's list of them
def timed_eval(q, secs=5):
    global _ev
    _ev += 1
    if _forced is not None:
        return dict(kind="UNREACHABLE") if _ev in _forced else v3.evaluate(q)
    signal.alarm(secs)
    try: return v3.evaluate(q)
    except _TO: _timeouts.append(_ev); return dict(kind="UNREACHABLE")
    finally: signal.alarm(0)
def run(T, mode, emit=None, quiet=False):
    """emit(step) receives each logged step as it happens."""
    global _ev, _timeouts
    _ev = 0; _timeouts = []
    W = new_waves() if mode == "polar" else v2.new_waves()
    waves0 = json.loads(json.dumps(W))
    sigma = {"X": .5, "Y": .5, "Z": .5}; cur = None; best = None; fails = 0; log = []; ideas = []
    def rec(e, q=None):
        if q is not None: e["q"] = q
        e["sigma"] = dict(sigma)
        if mode == "polar": e["amps"] = [w["A"] for w in W]
        e = json.loads(json.dumps(e))               # tuples become lists, so logged and replayed steps compare equal
        log.append(e)
        if emit: emit(e)
    for t in range(1, T+1):
        src = best["p"] if best else (cur or dict(base=pick(v2.BLK), m=pick(list(range(5, 17))), ops=[]))
        ax = pick(["X", "Y", "Z"], [sigma[a] for a in "XYZ"]); sign = 1 if (best or u() < .6) else -1
        q = g.move(src, ax, sign) or g.move(src, ax, 1) or src
        r = list(g.coords(q)); chans = []
        if mode == "polar":
            dl = local(W, r, t); Amax = max(w["A"] for w in W)
            if u() < sum(w["A"]*d for w, d in zip(W, dl)) / len(W) / Amax:
                for _ in range(1 + int(2*max(dl))):
                    ch = pick(CH, [w["A"]*d + 1e-9 for w, d in zip(W, dl)]); q2, note = mutate_channel(q, ch)
                    if note: q = q2; chans.append((ch, note))
        elif mode == "base":
            dist = v2.d(W, r, t)
            if u() < dist:
                q2, notes = v2.mutate(q, 1 + int(2*dist)); q = q2; chans = list(zip(classify_old(notes, q), notes))
        if not v2.within(q): rec(dict(t=t, kind="OUT-OF-GRID", chans=chans, ax=ax), q); continue
        res = timed_eval(q); e = dict(t=t, kind=res["kind"], expr=g.show(g.tree(q)), m=q["m"], chans=chans, ax=ax)
        if res["kind"] == "EXPLAINED":
            short = v2.shortest(q, res["s"])
            if short is not q: q = dict(short, m=q["m"]); res = timed_eval(q)
            if res["kind"] != "EXPLAINED": rec(e, q); continue
            B0 = v3.naive(q); w = math.log2(B0 / res["L"]) / v3.size(q)
            e.update(L=res["L"], naive=B0, worth=round(w, 3), point=q, sexpr=g.show(g.tree(q)))
            if w == 0: sigma[ax] = min(.9, sigma[ax]*1.25)
            if best and w > best["worth"] + 1e-9: best = dict(p=q, worth=w); fails = 0
            elif best: fails += 1
            elif w > 0: best = dict(p=q, worth=w); fails = 0
            else: cur = q
        else:
            if res["kind"] == "FALSE": sigma[ax] = max(.1, sigma[ax]*.75)
            if best: fails += 1
        if mode == "polar":
            useful = e.get("worth", 0) > 0; bad = e["kind"] in ("FALSE", "UNREACHABLE")
            for ch, _ in chans:
                i = CH.index(ch)
                if useful: W[i]["A"] = min(2.0, W[i]["A"]*1.25)
                elif bad: W[i]["A"] = max(0.3, W[i]["A"]*0.8)
        if best and fails >= 3: ideas.append(best); best = None; fails = 0; cur = None
        rec(e, q)
        if t % 25 == 0 and not quiet: print(mode, "t", t, flush=True)
    if best: ideas.append(best)
    return dict(log=log, waves0=waves0, ideas=ideas, amps=[round(w.get("A", 0), 2) for w in W] if mode == "polar" else None)
def summary(R):
    from collections import Counter
    muts = Counter(); useful = Counter(); finds = {}; finds_all = {}
    for e in R["log"]:
        for ch, _ in e["chans"]:
            muts[ch] += 1
            if e.get("worth", 0) > 0: useful[ch] += 1
        if e.get("worth", 0) > 0:
            k = (e["m"], e["sexpr"]); finds_all[k] = max(finds_all.get(k, 0), e["worth"])
            if e["chans"]: finds[k] = max(finds.get(k, 0), e["worth"])
    return muts, useful, finds, finds_all
def code_hash():
    """Which code produced a run. Replay warns when this differs."""
    h = hashlib.sha256()
    for f in (_P("s4_merging", "engine1.py"), _P("s4_merging", "merge.py"), _P("s4_merging", "v2.py"), _P("s4_merging", "v3.py"), os.path.abspath(__file__)):
        h.update(open(f, "rb").read())
    return h.hexdigest()[:16]
def digest(steps):
    h = hashlib.sha256()
    for e in steps: h.update(json.dumps(e, sort_keys=True).encode())
    return h.hexdigest()
def logged_run(T, mode, seed, out):
    os.makedirs(out, exist_ok=True); path = os.path.join(out, f"{mode}_{seed}.jsonl")
    g.set_seed(seed)
    with open(path, "w") as f:
        def put(x): f.write(json.dumps(x, sort_keys=True) + "\n"); f.flush()
        put(dict(type="header", mode=mode, T=T, seed=seed, python=platform.python_version(), code=code_hash()))
        R = run(T, mode, emit=lambda e: put(dict(e, type="step")))
        muts, useful, finds, finds_all = summary(R)
        kinds = {k: sum(1 for e in R["log"] if e["kind"] == k) for k in ("EXPLAINED", "FALSE", "UNREACHABLE", "OUT-OF-GRID")}
        put(dict(type="footer", digest=digest(R["log"]), timeouts=_timeouts, waves0=R["waves0"], amps=R["amps"], kinds=kinds, muts=dict(muts), useful=dict(useful),
                 ideas=[[i["worth"], i["p"]] for i in R["ideas"]], finds_mutated=len(finds), finds_all=len(finds_all)))
    g.set_seed(None)
    return path, R, muts, useful, finds, finds_all, kinds
def replay(path):
    global _forced
    rows = [json.loads(x) for x in open(path)]
    H, steps, F = rows[0], [{k: v for k, v in r.items() if k != "type"} for r in rows if r["type"] == "step"], rows[-1]
    if F["type"] != "footer": print("run has no footer (it was cut off):", path); return False
    if H["code"] != code_hash(): print("WARNING: the code changed since this run; a difference may come from that")
    if H["python"] != platform.python_version(): print("note: run used Python", H["python"], "- this is", platform.python_version())
    g.set_seed(H["seed"]); _forced = set(F["timeouts"])
    try: R = run(H["T"], H["mode"], quiet=True)
    finally: _forced = None; g.set_seed(None)
    for a, b in zip(steps, R["log"]):
        if a != b:
            print("DIVERGED at step", a["t"]); print("  logged  :", json.dumps(a, sort_keys=True)); print("  replayed:", json.dumps(b, sort_keys=True)); return False
    ok = len(steps) == len(R["log"]) and digest(R["log"]) == F["digest"]
    print(("REPLAY OK: " if ok else "REPLAY FAILED: ") + f"{len(R['log'])} of {len(steps)} steps, {len(F['timeouts'])} logged timeouts, digest {digest(R['log'])[:16]}")
    return ok
if __name__ == "__main__":
    if sys.argv[1] == "replay": sys.exit(0 if all([replay(p) for p in sys.argv[2:]]) else 1)
    # python waves4.py base|polar|off T RUNS [SEED]   writes runs/<mode>_<seed>.jsonl
    mode, T, seeds = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if mode not in ("base", "polar", "off"): sys.exit("mode must be base, polar, off or replay")
    if len(sys.argv) > 4 and seeds != 1: sys.exit("a fixed SEED needs RUNS = 1")
    for s in range(seeds):
        seed = sys.argv[4] if len(sys.argv) > 4 else os.urandom(8).hex()
        path, R, muts, useful, finds, finds_all, kinds = logged_run(T, mode, seed, _P("s6_patches", "runs"))
        print(mode, s, "mutations", dict(muts), "useful", dict(useful), "distinct finds: mutated steps", len(finds), "all steps", len(finds_all), "amps", R["amps"], kinds, "log", path, flush=True)
