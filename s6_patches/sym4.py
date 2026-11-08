"""Adds R_QUOT (quotient tower): on the image of the inner sequence, the outer function depends only on x mod d (smallest d).
The tower of moduli shrinks top-down: t0 = m, t_{j+1} = d_j. Then the layered affine symmetry runs on the reduced tower."""
import math, json, time, sys
from sym2 import cycle, vals, divisors
from sym3 import solve_tau
def tower(chain, m):
    mods = [m]
    for f in chain[:-1]: mods.append(cycle(f, mods[-1]))
    comp = cycle(chain[-1], mods[-1])
    if comp > 20000: return None
    seqs = {len(chain): list(range(comp))}
    for j in range(len(chain)-1, -1, -1):
        v = vals(chain[j], mods[j]); seqs[j] = [v[x % len(v)] for x in seqs[j+1]]
    return mods, comp, seqs
def quotient(chain, m, mods, comp, seqs):
    t = [m]; maps = []
    for j in range(len(chain)):
        xs, ys = seqs[j+1], [y % t[j] for y in seqs[j]]
        base = mods[j+1] if j+1 < len(mods) else comp
        for d in divisors(base):
            g = {}
            if all(g.setdefault(x % d, y) == y for x, y in zip(xs, ys)): break
        t.append(d); maps.append(g)
    return t, maps
def period_quot(chain, m, affine=True):
    T = tower(chain, m)
    if T is None: return None
    mods, comp, seqs = T; t, maps = quotient(chain, m, mods, comp, seqs)
    red_bound = t[-1]                                   # innermost index n only matters mod t_k: period divides it
    k = len(chain)
    for h in divisors(red_bound):
        # innermost: f_k(n+h) vs f_k(n), as reduced values mod t[k-1]... layer index: maps[j] maps x mod t[j+1] -> value mod t[j]
        s = [seqs[k-1][n] % t[k-1] for n in range(comp)]
        if k == 1:
            if all(s[n] == s[(n+h) % comp] for n in range(comp)): return dict(per=h, t=t, red=red_bound)
            continue
        tau = solve_tau(s, [s[(n+h) % comp] for n in range(comp)], t[k-1], affine); ok = tau is not None; j = k - 2
        while ok and j >= 0:
            g = maps[j]; a, b = tau; img = sorted(set(x % t[j+1] for x in seqs[j+1]))
            try: xs = [g[x] for x in img]; ys = [g[(a*x + b) % t[j+1]] for x in img]
            except KeyError: ok = False; break
            if j == 0: ok = xs == ys; break
            tau = solve_tau(xs, ys, t[j], affine); ok = tau is not None; j -= 1
        if ok: return dict(per=h, t=t, red=red_bound)
    return dict(per=red_bound, t=t, red=red_bound)
if __name__ == "__main__":
    k = sys.argv[1]; t0 = time.time()
    R = json.load(open("sym2.json"))[k]; rows = []
    for r in R:
        q = period_quot(list(r["chain"]), r["m"])
        if q is None: continue
        r.update(quot=q["per"], red=q["red"], tower=q["t"]); rows.append(r)
    n = len(rows)
    print(f"{k}: {n} | R_COMP {sum(r['comp']==r['true'] for r in rows)} | MUL-GLOBAL {sum(r['eq']==r['true'] for r in rows)} | QUOT bound alone {sum(r['red']==r['true'] for r in rows)} | QUOT+AFF {sum(r['quot']==r['true'] for r in rows)} | below true (error) {sum(r['quot']<r['true'] for r in rows)}")
    miss = [r for r in rows if r["quot"] != r["true"]]
    print("   misses:", len(miss), [(r["m"], r["chain"], r["quot"], r["true"], r["tower"]) for r in miss[:15]])
    json.dump(rows, open(f"sym4_{k}.json", "w")); print("secs", round(time.time()-t0, 1))
