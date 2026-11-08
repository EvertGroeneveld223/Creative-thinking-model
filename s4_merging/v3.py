"""v3 loop: 3D wave noise (from v2) + merged explanations. Novelty is checked by web AFTER the loop for the top finds."""
import json, math, hashlib, sys
import engine1 as g, merge as M, v2
u, pick = g.u, g.pick
def naive(p):
    tr = []; B = g.bound(g.tree(p), p["m"], tr)
    if B: return B
    L = 1
    for b in [p["base"]] + [b for _, b in p["ops"]]:
        L = math.lcm(L, {"fib": g.pisano(p["m"]), "luc": g.pisano(p["m"]), "tri": 2*p["m"], "sq": p["m"], "ds": p["m"]}[b])
    return L
def size(p): return 1 + len(p["ops"])
def evaluate(p):
    L, trace, nf = M.explain(p)
    s, W = g.world(g.tree(p), p["m"], N=max(900, 3*L+20) if L else 900)
    if len(s) < 200: return dict(kind="UNREACHABLE")
    if L is None: return dict(kind="FALSE" if not W else "WORLD-ONLY", W=W)
    if len(s) < 3*L: return dict(kind="UNREACHABLE")
    if W != L: return dict(kind="CONTRADICTION", W=W, L=L)
    return dict(kind="EXPLAINED", L=L, s=s, trace=trace, nf=M.show_nf(nf))
def run(T=300):
    W = v2.new_waves(); sigma = {"X": .5, "Y": .5, "Z": .5}; eta = .25
    cur = None; best = None; fails = 0; ideas = []; log = []; resends = 0
    for t in range(1, T+1):
        src = best["p"] if best else (cur or dict(base=pick(v2.BLK), m=pick(list(range(5, 17))), ops=[]))
        ax = pick(["X", "Y", "Z"], [sigma[a] for a in "XYZ"]); sign = 1 if (best or u() < .6) else -1
        q = g.move(src, ax, sign) or g.move(src, ax, 1) or src
        dist = v2.d(W, list(g.coords(q)), t); notes = []
        if u() < dist: q, notes = v2.mutate(q, 1 + int(2*dist))
        if not v2.within(q): log.append(dict(t=t, kind="OUT-OF-GRID")); continue
        r = evaluate(q)
        reply = json.dumps([r["kind"], r.get("L")]); h = hashlib.sha256(reply.encode()).hexdigest()
        back = v2.d(W, list(g.coords(src)), t+1); k = 0
        while u() < back and k < 20: resends += 1; k += 1          # corrupted replies fail the hash and are resent
        e = dict(t=t, kind=r["kind"], expr=g.show(g.tree(q)), m=q["m"], ax=ax, d=round(dist, 3), notes=notes)
        if r["kind"] == "EXPLAINED":
            short = v2.shortest(q, r["s"])
            if short is not q: e["shorter"] = g.show(g.tree(short)); q = dict(short, m=q["m"]); r = evaluate(q)
            B0 = naive(q); w = math.log2(B0 / r["L"]) / size(q)
            e.update(L=r["L"], naive=B0, worth=round(w, 3), nf=r["nf"], terms=r["s"][:24])
            if w == 0: sigma[ax] = min(.9, sigma[ax]*(1+eta))
            if best and w > best["worth"] + 1e-9: best = dict(p=q, worth=w, e=e); fails = 0
            elif best:
                fails += 1
            elif w > 0: best = dict(p=q, worth=w, e=e); fails = 0
            else: cur = q
        else:
            if r["kind"] == "FALSE": sigma[ax] = max(.1, sigma[ax]*(1-eta))
            if best: fails += 1
        if best and fails >= 3: ideas.append(best); best = None; fails = 0; cur = None
        log.append(e)
    if best: ideas.append(best)
    return dict(log=log, ideas=ideas, sigma=sigma, resends=resends)
if __name__ == "__main__":
    R = run(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
    json.dump(R, open("run3.json", "w"), indent=1, default=str)
    from collections import Counter
    print(Counter(e["kind"] for e in R["log"]), "resends", R["resends"], "sigma", R["sigma"])
    seen = {}
    for e in R["log"]:
        if e.get("worth", 0) > 0:
            k = (e["m"], tuple(e["terms"]))
            if k not in seen or e["worth"] > seen[k]["worth"]: seen[k] = e
    top = sorted(seen.values(), key=lambda e: -e["worth"])[:10]
    print("ideas:", [(i["e"]["expr"], i["p"]["m"], round(i["worth"], 3)) for i in R["ideas"]])
    for e in top: print(f"worth {e['worth']:.3f} | {e['expr']} mod {e['m']} | period {e['L']} vs naive {e['naive']} | merged: {e['nf']} | wave mut {e['notes']}")
