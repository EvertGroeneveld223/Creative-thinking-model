"""Layer-by-layer symmetry (demand-driven):
  innermost: f_k(n+h) = tau_k(f_k(n))                      tau affine (or multiplicative) mod q_k
  each layer: f_j(tau_{j+1}(x)) = tau_j(f_j(x)) for x in the IMAGE of the inner sequence
  top: tau_1 = identity on its image  =>  period divides h.
Levels: MUL-GLOBAL (sym2), MUL-IMAGE, AFF-IMAGE."""
import math, json, time
from sym2 import SEQ, cycle, vals, divisors, chain_period
def solve_tau(xs, ys, q, affine):
    """find (a,b) with a*x+b = y mod q for all pairs; b = 0 if not affine. None if impossible."""
    pairs = list(dict(zip(xs, ys)).items())
    if any(dict(zip(xs, ys)).get(x) != y for x, y in zip(xs, ys)): return None   # x maps to two values: not a function
    if not affine:
        u = next(((x, y) for x, y in pairs if math.gcd(x, q) == 1), None)
        cands = [u[1]*pow(u[0], -1, q) % q] if u else (range(q) if q <= 100 else [])
        for a in cands:
            if all((a*x - y) % q == 0 for x, y in pairs): return (a, 0)
        return None
    for (x1, y1) in pairs[:1]:
        for (x2, y2) in pairs:
            dx = (x2 - x1) % q
            if math.gcd(dx, q) == 1:
                a = (y2 - y1)*pow(dx, -1, q) % q; b = (y1 - a*x1) % q
                return (a, b) if all((a*x + b - y) % q == 0 for x, y in pairs) else None
    for a in (range(q) if q <= 100 else []):
        b = (pairs[0][1] - a*pairs[0][0]) % q
        if all((a*x + b - y) % q == 0 for x, y in pairs): return (a, b)
    return None
def layered(chain, m, affine):
    if len(chain) == 1: return None
    mods = [m]
    for f in chain[:-1]: mods.append(cycle(f, mods[-1]))
    comp = cycle(chain[-1], mods[-1])
    if comp > 20000: return "too-large"
    # images of each partial composition (inner part) as sequences over n in [0, comp)
    inner_seq = {len(chain): list(range(comp))}
    for j in range(len(chain)-1, -1, -1):
        v = vals(chain[j], mods[j]); inner_seq[j] = [v[x % len(v)] for x in inner_seq[j+1]]
    for h in divisors(comp):
        # innermost layer: f_k(n+h) vs f_k(n)
        k = len(chain) - 1; s = inner_seq[k]
        tau = solve_tau(s, [s[(n+h) % comp] for n in range(comp)], mods[k], affine)
        ok = tau is not None
        j = k - 1
        while ok and j >= 0:
            img = sorted(set(inner_seq[j+1])); v = vals(chain[j], mods[j]); P = len(v); a, b = tau
            xs = [v[x % P] for x in img]; ys = [v[(a*x + b) % mods[j+1] % P] for x in img]
            if j == 0: ok = xs == ys; break                      # top: the outer function must not change
            tau = solve_tau(xs, ys, mods[j], affine); ok = tau is not None; j -= 1
        if ok: return h
    return comp
if __name__ == "__main__":
    t0 = time.time(); R = json.load(open("sym2.json")); out = {}
    import sys
    for k in sys.argv[1:]:
        rows = R[k]
        for r in rows:
            ch = list(r["chain"]); r["mul_img"] = layered(ch, r["m"], False); r["aff_img"] = layered(ch, r["m"], True)
        rows = [r for r in rows if r["aff_img"] != "too-large"]; n = len(rows)
        print(f"{k}: {n} | R_COMP {sum(r['comp']==r['true'] for r in rows)} | MUL-GLOBAL {sum(r['eq']==r['true'] for r in rows)} | MUL-IMAGE {sum(r['mul_img']==r['true'] for r in rows)} | AFF-IMAGE {sum(r['aff_img']==r['true'] for r in rows)} | any level wrong-low {sum(min(x for x in (r['mul_img'],r['aff_img'])) < r['true'] for r in rows)}")
        miss = [r for r in rows if r["aff_img"] != r["true"]]
        print("   AFF-IMAGE misses:", len(miss), [(r["m"], r["chain"], r["aff_img"], r["true"]) for r in miss[:12]])
        out[k] = rows
    json.dump(out, open(f"sym3_{sys.argv[1]}.json", "w")); print("secs", round(time.time()-t0, 1))
