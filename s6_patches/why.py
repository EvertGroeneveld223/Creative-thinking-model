import os as _os
_P=lambda *a:_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",*[x for x in a if x]))
"""Patch 1: R_MULT inside the engine. After the exact proof (cube3/merge.py), WHY() tries to reach the same period
using identity rules only, and prints the 5W chain. Only Lucas-sequence identities are used (no cycle checks):
  R_CRT   period mod m = lcm of periods mod its prime powers          (Pisano period page: coprime -> lcm)
  R_CYCLE the cycle of F/L mod q = first return of the state pair    (definition of the recurrence)
  R_SHIFT U(c)=0, V(c)=2e (mod 2q) [V: D*U(c)=0]  =>  f(n+c) = e*f(n) mod q   (Lucas-sequence addition identities)
  R_NEG   U(-k) = (-1)^(k+1)U(k), V(-k) = (-1)^k V(k)
  R_MULT  inner shift (h,a) + outer invariance f(a k)=f(k)  =>  period divides h
derived invariances: f(n+c)=e f(n) with e=+1 gives f((c+1)k)=f(k);  V with e=-1 gives V((c-1)k)=V(k);  U with e=-1 gives U((c-1)k)=-U(k)."""
import sys, math
sys.path.insert(0, _P("s4_merging",""))
import engine1 as g, merge as M
SRC = {"R_CRT": "https://en.wikipedia.org/wiki/Pisano_period", "R_CYCLE": "definition of a linear recurrence",
       "R_SHIFT": "https://cavac.at/cavacopedia/Lucas%20sequence (identities 8, 9; mirror of Wikipedia 'Lucas sequence')",
       "R_NEG": "https://specialfunctionswiki.org/index.php/Lucas_numbers", "R_MULT": "derived in this project (symmetry_rule.zip, 236/236 cases)",
       "R_COMP": "definition of a periodic sequence"}
KIND = {"fib": ("U", 5, [0, 1]), "luc": ("V", 5, [2, 1])}
def seq(name, N, q):
    a, b = KIND[name][2]; out = []
    for _ in range(N): out.append(a % q); a, b = b, a + b
    return out
def cyc(name, q):
    if q == 1: return 1
    a0, b0 = [x % q for x in KIND[name][2]]; a, b, k = a0, b0, 0
    while True:
        a, b = b, (a + b) % q; k += 1
        if (a, b) == (a0, b0): return k
def UV(c, q):  # U(c), V(c) mod q (Fibonacci, Lucas)
    F, F1 = g.fib_pair_mod(c, q); return F % q, (2*F1 - F) % q
def shift_mult(name, c, q):
    """R_SHIFT: return e (mod q) if f(n+c) = e f(n) mod q follows from the identities, else None.
    U(n+c) = (U(c)V(n) + V(c)U(n))/2,  V(n+c) = (V(c)V(n) + 5U(c)U(n))/2.
    q odd: 2 is invertible mod q, so need [5]U(c) = 0 mod q and e = V(c)/2 mod q.
    q even: need [5]U(c) = 0 and V(c) = 2e mod 2q."""
    if q == 1: return 0
    k5 = 1 if name == "fib" else 5
    if q % 2:
        U, V = UV(c, q)
        return (V * pow(2, -1, q)) % q if (k5*U) % q == 0 else None
    U, V = UV(c, 2*q)
    if (k5*U) % (2*q) or V % 2: return None
    return (V // 2) % q
def invariances(name, q, P):
    """derived b (mod P) with f(b k) = f(k) mod q, each with its reason."""
    out = {1 % P: "trivial"}
    for c in range(1, P+1):
        e = shift_mult(name, c, q)
        if e is None: continue
        if e == 1 % q: out.setdefault((c+1) % P, f"R_SHIFT c={c} (e=+1) -> f((c+1)k)=f(k)")
        if (e + 1) % q == 0 and name == "luc": out.setdefault((c-1) % P, f"R_SHIFT c={c} (e=-1) + R_NEG -> L((c-1)k)=L(k)")
    if q <= 2: out.setdefault((P - 1) % P, "R_NEG: f(-k) = +/-f(k), and signs vanish mod 2")
    return out
def prime_powers(m):
    out, p = [], 2
    while p*p <= m:
        if m % p == 0:
            e = 1
            while m % p == 0: m //= p; e *= p
            out.append(e)
        p += 1
    if m > 1: out.append(m)
    return out
def why_chain2(outer, inner, m):
    """f(g(n)) mod m with f, g in {fib, luc}: period from identity rules + printed chain."""
    lines, L = [f"R_CRT: split {m} = {' x '.join(map(str, prime_powers(m))) or '1'}; the period is the lcm of the parts"], 1
    for q in prime_powers(m) or [1]:
        P = cyc(outer, q); Pg = cyc(inner, P)
        lines.append(f"  mod {q}: R_CYCLE {outer} mod {q} repeats every {P}, so {outer}(k) mod {q} depends on k mod {P}; {inner} mod {P} repeats every {Pg} (R_COMP bound {Pg})")
        inv = invariances(outer, q, P); best = Pg; why = None
        for h in sorted(d for d in range(1, Pg+1) if Pg % d == 0):
            a = shift_mult(inner, h, P)
            if a is not None and a % P in inv: best, why = h, (a % P, inv[a % P]); break
        if why:
            lines.append(f"    R_SHIFT: {inner}(n+{best}) = {why[0]}*{inner}(n) mod {P};  {why[1]}  =>  R_MULT: period divides {best}")
        else: lines.append(f"    no symmetry from identities: period divides {Pg}")
        L = math.lcm(L, best)
    return L, lines
def why(p):
    """p: engine point. Returns (proved period, why period or None, label, lines)."""
    Lp, trace, nf = M.explain(p)
    E = g.tree(p)
    if Lp is None: return None, None, "GAP", trace[-1:]
    if E[0] == "comp" and E[2][0] == "blk" and E[1] in KIND and E[2][1] in KIND:
        Lw, lines = why_chain2(E[1], E[2][1], p["m"])
        return Lp, Lw, ("EXPLAINED (identities)" if Lw == Lp else f"WHY-GAP: identities give {Lw}"), lines
    if not any("atom" in t for t in trace): return Lp, Lp, "EXPLAINED (polynomial, Newton)", trace
    return Lp, None, "PROVED (residue check), why not yet derived", trace
if __name__ == "__main__":
    import json
    ok = tot = 0; bad = []
    for m in range(2, 61):
        for f in KIND:
            for h in KIND:
                p = dict(base=h, m=m, ops=[["comp", f]]); Lp, Lw, lab, lines = why(p); tot += 1
                if Lw == Lp: ok += 1
                else: bad.append((m, f, h, Lw, Lp))
    print(f"F/L compositions m=2..60: why-chain reaches the proved period in {ok} of {tot}"); print("misses:", bad)
    for p in [dict(base="luc", m=25, ops=[["comp", "luc"]]), dict(base="fib", m=5, ops=[["comp", "luc"]]), dict(base="luc", m=30, ops=[["comp", "fib"]])]:
        Lp, Lw, lab, lines = why(p); print(f"\n{g.show(g.tree(p))} mod {p['m']}: proved {Lp} | {lab}"); [print("  ", l) for l in lines]
