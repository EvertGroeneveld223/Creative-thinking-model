"""R_PARITY: the shift map may differ for even and odd n (the (-1)^n factors of Lucas-sequence identities).
Same layered quotient + affine engine as sym4, run separately on n even and n odd; both must reach the top unchanged."""
import json, math, sys
from sym2 import cycle, vals, divisors
from sym3 import solve_tau
from sym4 import tower, quotient
from why import prime_powers
def period_parity(chain, m, classes=2):
    T = tower(chain, m)
    if T is None: return None
    mods, comp, seqs = T; t, maps = quotient(chain, m, mods, comp, seqs); red = t[-1]; k = len(chain)
    for h in divisors(red):
        good = True
        for cl in range(classes):
            ns = [n for n in range(comp) if n % classes == cl]
            if not ns: continue
            s = [seqs[k-1][n] % t[k-1] for n in ns]; s2 = [seqs[k-1][(n+h) % comp] % t[k-1] for n in ns]
            tau = solve_tau(s, s2, t[k-1], True); ok = tau is not None; j = k - 2
            img = lambda j: sorted(set(seqs[j+1][n] % t[j+1] for n in ns))
            while ok and j >= 0:
                g = maps[j]; a, b = tau
                try: xs = [g[x] for x in img(j)]; ys = [g[(a*x + b) % t[j+1]] for x in img(j)]
                except KeyError: ok = False; break
                if j == 0: ok = xs == ys; break
                tau = solve_tau(xs, ys, t[j], True); ok = tau is not None; j -= 1
            if not ok: good = False; break
        if good: return h
    return red
def crt(chain, m):
    L = 1
    for q in prime_powers(m):
        r = period_parity(chain, q)
        if r is None: return None
        L = math.lcm(L, r)
    return L
if __name__ == "__main__":
    for k in ("depth2", "depth3"):
        rows = json.load(open(f"sym5_{k}.json")); best = lambda r: min(x for x in (r["quot"], r["crt"]) if x is not None)
        for r in rows:
            r["par"] = best(r) if best(r) == r["true"] else min(x for x in (period_parity(list(r["chain"]), r["m"]), crt(list(r["chain"]), r["m"])) if x is not None)
        fin = lambda r: min(best(r), r["par"])
        miss = [r for r in rows if fin(r) != r["true"]]
        print(f"{k}: {len(rows)} | R_COMP {sum(r['comp']==r['true'] for r in rows)} | MUL-GLOBAL {sum(r['eq']==r['true'] for r in rows)} | +QUOT+AFF+CRT {sum(best(r)==r['true'] for r in rows)} | +PARITY {sum(fin(r)==r['true'] for r in rows)} | below true {sum(fin(r)<r['true'] for r in rows)}")
        print("   misses:", len(miss), [(r["m"], r["chain"], fin(r), r["true"]) for r in miss[:15]])
        json.dump(rows, open(f"sym6_{k}.json", "w"))
