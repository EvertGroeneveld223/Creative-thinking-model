"""Generalised symmetry rule: EQUIVARIANCE CHAIN (R_MULT generalised).
  S(u, q) = {(h, a) : u(n+h) = a*u(n) mod q for all n}          shift pairs of a sequence
  E(f, q) = {(b, a) : f(b*k) = a*f(k) mod q for all k}            equivariance pairs of an outer function
  S(f(u), q) = {(h, a') : (h, b) in S(u, cycle(f,q)), (b, a') in E(f, q)}
  f1(...(fk(n))) mod m has period = min h with (h, 1) in S(whole, m).
R_MULT (2-deep) is the special case where the outer pair is (a, 1).
Identity-derived pairs (Lucas sequences U, V with Q = -1, source: Lucas sequence addition identities):
  R_SHIFT: U(c) = 0 and V(c) = 2e (mod 2q), [V: D*U(c) = 0]  =>  f(n+c) = e*f(n) mod q
  R_NEG  : U(-k) = (-1)^(k+1) U(k),  V(-k) = (-1)^k V(k)
  => f((c+1)k) = e^k f(k);  V((c-1)k) = (e*(-1))^k ... constant multipliers when the parity factors cancel."""
import math, json, sys, time
SEQ = {"F": ([1, 1], [0, 1]), "L": ([1, 1], [2, 1]), "P": ([2, 1], [0, 1]), "Q": ([2, 1], [2, 2]), "T": ([1, 1, 1], [0, 0, 1])}
LUCAS = {"F": ("U", 1, 5), "L": ("V", 1, 5), "P": ("U", 2, 8), "Q": ("V", 2, 8)}   # kind, p, D  (all with Q=-1)
_cyc = {}
def cycle(s, q):
    if (s, q) in _cyc: return _cyc[(s, q)]
    if q == 1: return 1
    co, init = SEQ[s]; st0 = tuple(x % q for x in init); st = st0; k = 0
    while True:
        nxt = sum(c*x for c, x in zip(co, reversed(st))) % q
        st = st[1:] + (nxt,); k += 1
        if st == st0: _cyc[(s, q)] = k; return k
_val = {}
def vals(s, q):
    if (s, q) in _val: return _val[(s, q)]
    P = cycle(s, q); co, init = SEQ[s]; out = [x % q for x in init]
    while len(out) < P + len(init): out.append(sum(c*x for c, x in zip(co, reversed(out[-len(co):]))) % q)
    _val[(s, q)] = out[:P]; return out[:P]
def divisors(n): return [d for d in range(1, n+1) if n % d == 0]
def shift_pairs(s, q):
    """S(s(n), q): for each h | cycle, the a (if any) with s(n+h) = a s(n)."""
    v = vals(s, q); P = len(v); out = {}
    for h in divisors(P):
        cands = range(q)
        unit = next((n for n in range(P) if math.gcd(v[n], q) == 1), None)
        if unit is not None: cands = [v[(unit+h) % P] * pow(v[unit], -1, q) % q]
        for a in cands:
            if all((v[(n+h) % P] - a*v[n]) % q == 0 for n in range(P)): out.setdefault(h, set()).add(a)
    return out
def equiv_pairs(s, q):
    """E(s, q): pairs (b, a) with s(b k) = a s(k) mod q, b taken mod cycle."""
    v = vals(s, q); P = len(v); out = {}
    unit = next((k for k in range(P) if math.gcd(v[k], q) == 1), None)
    for b in range(P):
        cands = [v[(b*unit) % P] * pow(v[unit], -1, q) % q] if unit is not None else range(q)
        for a in cands:
            if all((v[(b*k) % P] - a*v[k]) % q == 0 for k in range(P)): out.setdefault(b, set()).add(a)
    return out
def chain_period(chain, m):
    """chain = [f1, f2, ..., fk] meaning f1(f2(...fk(n))). Returns (period by equivariance chain, R_COMP bound, true period)."""
    mods = [m]
    for f in chain[:-1]: mods.append(cycle(f, mods[-1]))
    # innermost shift pairs
    S = {h: set(a) for h, a in shift_pairs(chain[-1], mods[-1]).items()}
    for f, q in zip(reversed(chain[:-1]), reversed(mods[:-1])):
        E = equiv_pairs(f, q); P = cycle(f, q); S2 = {}
        for h, bs in S.items():
            for b in bs:
                for a in E.get(b % P, ()): S2.setdefault(h, set()).add(a)
        S = S2
    eq = min((h for h, a in S.items() if 1 % m in a or (m == 1)), default=None)
    comp = cycle(chain[-1], mods[-1])
    # true period: compose value tables
    seqv = list(range(comp))
    for f, q in zip(reversed(chain), reversed(mods)):
        v = vals(f, q); seqv = [v[x % len(v)] for x in seqv]
    true = min(h for h in divisors(comp) if all(seqv[i] == seqv[(i+h) % comp] for i in range(comp)))
    return eq, comp, true
if __name__ == "__main__":
    t0 = time.time(); R = {"depth2": [], "depth3": []}
    names = "FLPQT"
    for m in range(2, 41):
        for f in names:
            for g in names:
                eq, comp, true = chain_period([f, g], m); R["depth2"].append(dict(m=m, chain=f+g, eq=eq, comp=comp, true=true))
    for m in range(2, 21):
        for f in names:
            for g in names:
                for h in names:
                    if cycle(f, m) * 0 == 0:
                        eq, comp, true = chain_period([f, g, h], m); R["depth3"].append(dict(m=m, chain=f+g+h, eq=eq, comp=comp, true=true))
    json.dump(R, open("sym2.json", "w"))
    for k in R:
        rows = R[k]; n = len(rows)
        print(f"{k}: {n} cases | R_COMP exact {sum(r['comp']==r['true'] for r in rows)} | equivariance chain exact {sum(r['eq']==r['true'] for r in rows)} | chain wrong (!= true) {sum(r['eq'] is not None and r['eq']!=r['true'] for r in rows)}")
        for fam in names:
            sub = [r for r in rows if fam in r["chain"]]
            print(f"   containing {fam}: {len(sub)} | chain exact {sum(r['eq']==r['true'] for r in sub)} | R_COMP exact {sum(r['comp']==r['true'] for r in sub)}")
        bad = [r for r in rows if r["eq"] != r["true"]][:8]; print("   misses:", bad)
    print("secs", round(time.time()-t0, 1))
