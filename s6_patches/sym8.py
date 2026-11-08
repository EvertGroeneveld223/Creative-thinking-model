"""R_CLASS: generalises R_ZERO. The question passed down is 'is x = r (mod d)?'. If the solutions of f_j(y) = r (mod d)
form one residue class r' (mod z), the question passes down as 'is y = r' (mod z)?'. At the bottom the period divides z."""
import json, math
from sym2 import cycle, vals, divisors
from sym4 import tower
from why import prime_powers
def as_class(sol, P):
    """sol: sorted list of y in [0,P) -> (r, z) if sol is exactly one residue class mod z (z | P)."""
    if not sol: return None
    for z in divisors(P):
        r = sol[0] % z
        if sol == list(range(r, P, z)): return (r, z)
    return None
def class_tower(chain, m):
    T = tower(chain, m)
    if T is None: return None
    mods, comp, seqs = T
    img = sorted(set(seqs[1])); v = vals(chain[0], m); P = len(v); base = mods[1] if len(mods) > 1 else comp
    q = None
    for d in divisors(base):
        for r in range(d):
            a = {v[x % P] for x in img if x % d == r}; b = {v[x % P] for x in img if x % d != r}
            if len(a) <= 1 and len(b) <= 1: q = (r, d); break
        if q: break
    if q is None: return None
    steps = [(chain[0], q)]
    for j in range(1, len(chain)):
        Q = mods[j] if j < len(mods) else comp; vv = vals(chain[j], Q); Pj = len(vv); r, d = q
        c = as_class([y for y in range(Pj) if vv[y] % d == r], Pj)
        if c is None: return None
        steps.append((chain[j], c)); q = c
    return q[1], steps
def crt_class(chain, m):
    L = 1
    for qq in prime_powers(m):
        r = class_tower(chain, qq)
        if r is None: return None
        L = math.lcm(L, r[0])
    return (L,)
if __name__ == "__main__":
    tot = {}
    for k in ("depth2", "depth3"):
        rows = json.load(open(f"sym7_{k}.json"))
        prev = lambda r: min(x for x in (r["quot"], r["crt"], r["par"], r["zero"]) if x is not None)
        for r in rows:
            r["cls"] = None
            if prev(r) != r["true"]:
                cands = [x[0] for x in (class_tower(list(r["chain"]), r["m"]), crt_class(list(r["chain"]), r["m"])) if x]
                r["cls"] = min(cands) if cands else None
        fin = lambda r: min(x for x in (prev(r), r["cls"]) if x is not None)
        miss = [r for r in rows if fin(r) != r["true"]]
        lv = dict(R_COMP=sum(r['comp']==r['true'] for r in rows), MUL=sum(r['eq']==r['true'] for r in rows),
                  QUOT_AFF_CRT=sum(min(r['quot'], r['crt'] or 10**9)==r['true'] for r in rows), PARITY=sum(min(r['quot'], r['crt'] or 10**9, r['par'])==r['true'] for r in rows),
                  ZERO=sum(prev(r)==r['true'] for r in rows), CLASS=sum(fin(r)==r['true'] for r in rows))
        print(f"{k}: {len(rows)} cases | cumulative exact: {lv} | below true {sum(fin(r)<r['true'] for r in rows)} | misses {len(miss)} {[(r['m'], r['chain'], fin(r), r['true']) for r in miss[:20]]}")
        tot[k] = dict(n=len(rows), levels=lv, misses=[(r['m'], r['chain'], fin(r), r['true']) for r in miss])
        json.dump(rows, open(f"sym8_{k}.json", "w"))
    json.dump(tot, open("symmetry_levels.json", "w"), indent=1)
    print(class_tower(list("FFL"), 2))
