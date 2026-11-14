"""R_ZERO (rank of apparition, chained): if the outer layer only sees whether its input is 0 mod d,
and the zero set of the next function mod d is exactly the multiples of z, the question passes down as 'is the inner 0 mod z?'.
At the bottom: f_k(n) = 0 mod d  iff  z | n, so the period divides z."""
import json, math
from sym2 import cycle, vals, divisors
from sym4 import tower
from why import prime_powers
def zero_tower(chain, m):
    T = tower(chain, m)
    if T is None: return None
    mods, comp, seqs = T
    # top: f1 value on image must depend only on [x = 0 mod d]
    img = sorted(set(seqs[1])); v = vals(chain[0], m); P = len(v)
    d = next((d for d in divisors(mods[1] if len(mods) > 1 else comp)
              if len({v[x % P] for x in img if x % d == 0}) <= 1 and len({v[x % P] for x in img if x % d}) <= 1), None)
    if d is None: return None
    steps = [(chain[0], m, d)]
    for j in range(1, len(chain)):
        q = mods[j] if j < len(mods) else comp
        vv = vals(chain[j], q); Pj = len(vv)
        zeros = [y for y in range(Pj) if vv[y] % d == 0]
        z = next((z for z in divisors(Pj) if zeros == list(range(0, Pj, z))), None)
        if z is None: return None
        steps.append((chain[j], d, z)); d = z
    return d, steps
def crt_zero(chain, m):
    L = 1; allsteps = []
    for q in prime_powers(m):
        r = zero_tower(chain, q)
        if r is None: return None
        L = math.lcm(L, r[0]); allsteps.append((q, r[1]))
    return L, allsteps
if __name__ == "__main__":
    for k in ("depth2", "depth3"):
        rows = json.load(open(f"sym6_{k}.json"))
        best = lambda r: min(x for x in (r["quot"], r["crt"], r["par"]) if x is not None)
        for r in rows:
            r["zero"] = None
            if best(r) != r["true"]:
                cands = [x[0] for x in (zero_tower(list(r["chain"]), r["m"]), crt_zero(list(r["chain"]), r["m"])) if x]
                r["zero"] = min(cands) if cands else None
        fin = lambda r: min(x for x in (best(r), r["zero"]) if x is not None)
        miss = [r for r in rows if fin(r) != r["true"]]
        print(f"{k}: {len(rows)} | +ZERO {sum(fin(r)==r['true'] for r in rows)} | below true {sum(fin(r)<r['true'] for r in rows)} | misses {len(miss)} {[(r['m'], r['chain'], fin(r), r['true']) for r in miss[:12]]}")
        json.dump(rows, open(f"sym7_{k}.json", "w"))
    print(zero_tower(list("FFF"), 2))
