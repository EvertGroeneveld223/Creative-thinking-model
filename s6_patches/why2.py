"""The identity why-chain, for every Lucas sequence with Q = -1: Fibonacci and Lucas (P = 1, D = 5), Pell and Pell-Lucas (P = 2, D = 8).
Identities, in this general form: 2U(n+c) = U(n)V(c) + V(n)U(c),  2V(n+c) = V(n)V(c) + D U(n)U(c),  U(-k) = (-1)^(k+1) U(k),  V(-k) = (-1)^k V(k).
They give the same R_SHIFT, R_NEG and R_MULT as why.py. Tribonacci has no such identities here, so it stays with the table rules (sym9).
The chain proves that the period DIVIDES a value. Exactness comes from the lower-bound certificate at the end, a finite check by s8_proofs/prove.py.
    python why2.py                 chains F,L,P,Q two-deep on m = 2..60, compared with tables; writes why2.json
    python why2.py report LL 25    the printed chain and certificate for one case"""
import json, math, os, sys
from sym2 import vals, cycle, divisors
from why import prime_powers
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "s8_proofs"))
FAMILY = {"F": ("U", "F", "L", 5), "L": ("V", "F", "L", 5), "P": ("U", "P", "Q", 8), "Q": ("V", "P", "Q", 8)}   # kind, name of U, name of V, D
def uv(name, c, q):
    _, U, V, _ = FAMILY[name]; a, b = vals(U, q), vals(V, q)
    return a[c % len(a)], b[c % len(b)]
def shift_mult(name, c, q):
    """R_SHIFT: e mod q if f(n+c) = e f(n) mod q follows from the identities, else None."""
    if q == 1: return 0
    kind, _, _, D = FAMILY[name]; k = 1 if kind == "U" else D
    if q % 2:
        u, v = uv(name, c, q)
        return v * pow(2, -1, q) % q if k*u % q == 0 else None
    u, v = uv(name, c, 2*q)
    if k*u % (2*q) or v % 2: return None
    return (v//2) % q
def invariances(name, q, P):
    """b mod P with f(b k) = f(k) mod q, each with its reason."""
    kind = FAMILY[name][0]; out = {1 % P: "trivial"}
    for c in range(1, P+1):
        e = shift_mult(name, c, q)
        if e is None: continue
        if e == 1 % q: out.setdefault((c+1) % P, f"R_SHIFT c={c} (e=+1) -> f((c+1)k)=f(k)")
        if (e + 1) % q == 0 and kind == "V": out.setdefault((c-1) % P, f"R_SHIFT c={c} (e=-1) + R_NEG -> V((c-1)k)=V(k)")
    if q <= 2: out.setdefault((P - 1) % P, "R_NEG: f(-k) = +/-f(k), and signs vanish mod 2")
    return out
def why_chain(outer, inner, m):
    lines, L = [f"R_CRT: split {m} = {' x '.join(map(str, prime_powers(m))) or '1'}; the period is the lcm of the parts"], 1
    for q in prime_powers(m) or [1]:
        P = cycle(outer, q); Pg = cycle(inner, P)
        lines.append(f"  mod {q}: R_CYCLE {outer} mod {q} repeats every {P}; {inner} mod {P} repeats every {Pg} (R_COMP bound {Pg})")
        inv = invariances(outer, q, P); best = Pg; why = None
        for h in divisors(Pg):
            a = shift_mult(inner, h, P)
            if a is not None and a % P in inv: best, why = h, (a % P, inv[a % P]); break
        lines.append(f"    R_SHIFT: {inner}(n+{best}) = {why[0]}*{inner}(n) mod {P};  {why[1]}  =>  R_MULT: period divides {best}" if why else f"    no symmetry from identities: period divides {Pg}")
        L = math.lcm(L, best)
    return L, lines
def true_period(f, g, m):
    o = vals(f, m); it = vals(g, len(o)); s = [o[x] for x in it]; n = len(s)
    return next(h for h in divisors(n) if all(s[i] == s[(i+h) % n] for i in range(n)))
def report(chain, m):
    import prove
    L, lines = why_chain(chain[0], chain[1], m); T, cert = prove.certify(chain, m); ok, why = prove.check_certificate(chain, m, T, cert)
    print(f"{chain[0]}({chain[1]}(n)) mod {m}"); print("\n".join(lines))
    print(f"identities give: period divides {L}")
    print(f"certificate: exact period {T} ({why if ok else 'FAILED: ' + why}), witnesses {cert['witnesses']}")
    print("EXACT" if L == T else f"WHY-GAP: identities give {L}, true period {T}")
if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1] == "report": report(sys.argv[2], int(sys.argv[3])); sys.exit()
    rows = []
    for m in range(2, 61):
        for f in "FLPQ":
            for g in "FLPQ":
                L, _ = why_chain(f, g, m); T = true_period(f, g, m); B = cycle(g, cycle(f, m))
                rows.append(dict(m=m, chain=f+g, why=L, true=T, comp=B))
    n = len(rows); ok = sum(r["why"] == r["true"] for r in rows); below = sum(r["why"] < r["true"] for r in rows); hard = [r for r in rows if r["true"] < r["comp"]]
    print(f"F,L,P,Q two-deep, m = 2..60: {n} cases | why-chain exact {ok} ({ok/n:.1%}) | R_COMP exact {sum(r['comp']==r['true'] for r in rows)} | below true {below} | harder cases (true < R_COMP) {len(hard)}, chain exact on {sum(r['why']==r['true'] for r in hard)}")
    by = {}
    for r in rows: by.setdefault(r["chain"], [0, 0]); by[r["chain"]][0] += r["why"] == r["true"]; by[r["chain"]][1] += 1
    print("by chain:", {k: f"{a}/{b}" for k, (a, b) in by.items()})
    print("misses:", [(r["m"], r["chain"], r["why"], r["true"]) for r in rows if r["why"] != r["true"]][:30])
    json.dump(rows, open("why2.json", "w"))
