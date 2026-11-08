"""R_MULT (multiplier symmetry): if g(n+h) = a*g(n) (mod P) and f(a*k) = f(k) (mod m) for all k, where f mod m depends only on k mod P,
then f(g(n)) mod m has period dividing h. R_COMP is the special case a = 1."""
import math, json
def seq(kind, n, mod):
    a, b = (0, 1) if kind == "F" else (2, 1)
    out = []
    for _ in range(n): out.append(a % mod); a, b = b, a + b
    return out
def cycle(kind, m):                      # exact cycle length: first return of the state pair (Lucas/Fibonacci are purely periodic)
    if m == 1: return 1
    a0, b0 = (0, 1) if kind == "F" else (2 % m, 1 % m)
    a, b, k = a0, b0, 0
    while True:
        a, b = b, (a + b) % m; k += 1
        if (a, b) == (a0, b0): return k
def mults(f, m, P):
    s = seq(f, P, m)
    return [a for a in range(P) if math.gcd(a, P) >= 1 and all(s[(a*k) % P] == s[k] for k in range(P))]
def shift_ok(g, P, h, a, Pg):
    s = seq(g, Pg + h + 5, P)
    return all((s[n+h] - a*s[n]) % P == 0 for n in range(Pg))
def true_period(f, g, m):
    P = cycle(f, m); Pg = cycle(g, P); fs = seq(f, P, m); gs = seq(g, 3*Pg, P)
    vals = [fs[x] for x in gs]
    for h in range(1, Pg+1):
        if Pg % h == 0 and all(vals[i] == vals[i+h] for i in range(len(vals)-h)): return h
if __name__ == "__main__":
    rows = []
    for m in range(2, 61):
        for f in "FL":
            for g in "FL":
                P = cycle(f, m); Pg = cycle(g, P)            # R_COMP bound: g mod P has period Pg
                A = mults(f, m, P)
                hm = min(h for h in range(1, Pg+1) if Pg % h == 0 and any(shift_ok(g, P, h, a, Pg) for a in A))
                amult = [a for a in A if shift_ok(g, P, hm, a, Pg)]
                T = true_period(f, g, m)
                rows.append(dict(m=m, f=f, g=g, P=P, comp=Pg, mult=hm, a=amult[0], true=T))
    J = lambda k: sum(k(r) for r in rows)
    print("cases", len(rows))
    print("R_COMP alone exact :", J(lambda r: r["comp"] == r["true"]))
    print("R_COMP + R_MULT exact:", J(lambda r: r["mult"] == r["true"]))
    print("R_MULT used a != 1 :", J(lambda r: r["a"] != 1 and r["mult"] < r["comp"]))
    print("still unexplained:", [(r["m"], r["f"]+"("+r["g"]+")", r["mult"], r["true"]) for r in rows if r["mult"] != r["true"]])
    print("examples where R_MULT tightened:", [(r["m"], r["f"]+"("+r["g"]+")", r["comp"], "->", r["mult"], "a=", r["a"]) for r in rows if r["mult"] < r["comp"]][:25])
    json.dump(rows, open("mult_rows.json", "w"), indent=1)
