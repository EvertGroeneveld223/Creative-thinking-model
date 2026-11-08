"""Proof checks. Run: python prove.py     (exits non-zero if any check fails)

Part 1 checks every algebra identity used in PROOFS.md symbolically, for all n: nothing is sampled.
Part 2 checks the finite base facts of the proof by direct computation.
Part 3 tests each step of the induction and the final theorem on concrete k, using code independent of the proof.
Part 4 is a general certificate for one composition and one modulus: it proves "exact period T" by finite checks,
       including the lower bound that the identity-only why-chain (s6_patches/why.py) does not give.

Python checks the steps. It does not check the induction argument itself: that is in PROOFS.md, for a person to read.
Standard library only."""
import itertools, math, sys

# ---------- Part 1: identities as exact Laurent polynomials ----------
# alpha^n = x, beta^n = y, x*y = s = (-1)^n. So y = s/x. Then sqrt5*F(n) = x - y and L(n) = x + y.
# Two independent indices use (x1, s1), (x2, s2). A polynomial is {(e1, e2): integer coefficient}. s = +1 and -1 are both checked.


def padd(a, b, k=1):
    r = dict(a)
    for e, c in b.items():
        r[e] = r.get(e, 0) + k*c
    return {e: c for e, c in r.items() if c}


def pmul(a, b):
    r = {}
    for (i, j), c in a.items():
        for (k, l), d in b.items():
            r[(i+k, j+l)] = r.get((i+k, j+l), 0) + c*d
    return {e: c for e, c in r.items() if c}


def ppow(a, n):
    r = {(0, 0): 1}
    for _ in range(n):
        r = pmul(r, a)
    return r


def pk(k):
    return {(0, 0): k} if k else {}


def lin(i, s, sign):
    """x_i + sign*y_i, where y_i = s/x_i. sign=+1 gives L, sign=-1 gives sqrt5*F."""
    e = (1, 0) if i == 0 else (0, 1)
    ne = (-1, 0) if i == 0 else (0, -1)
    return padd({e: 1}, {ne: s*sign})


def identities():
    """name -> (left, right) for the given signs."""
    out = {}
    for s1, s2 in itertools.product((1, -1), repeat=2):
        L1, D1, L2, D2 = lin(0, s1, 1), lin(0, s1, -1), lin(1, s2, 1), lin(1, s2, -1)
        x1, y1, x2, y2 = {(1, 0): 1}, {(-1, 0): s1}, {(0, 1): 1}, {(0, -1): s2}
        Lsum = padd(pmul(x1, x2), pmul(y1, y2))                 # L(n+c)
        Dsum = padd(pmul(x1, x2), pmul(y1, y2), -1)             # sqrt5*F(n+c)
        # alpha^(-v) = (-1)^v beta^v, so L(u-v) = (-1)^v (x1*y2 + y1*x2)
        Ldiff = pmul(pk(s2), padd(pmul(x1, y2), pmul(y1, x2)))
        sfx = f"[s=({s1},{s2})]"
        out["I1 2L(n+c) = L(n)L(c) + 5F(n)F(c) " + sfx] = (pmul(pk(2), Lsum), padd(pmul(L1, L2), pmul(D1, D2)))
        out["I2 2F(n+c) = F(n)L(c) + L(n)F(c) " + sfx] = (pmul(pk(2), Dsum), padd(pmul(D1, L2), pmul(L1, D2)))
        out["I3 L(u+v) - (-1)^v L(u-v) = 5F(u)F(v) " + sfx] = (padd(Lsum, pmul(pk(s2), Ldiff), -1), pmul(D1, D2))
    for s in (1, -1):
        L, D = lin(0, s, 1), lin(0, s, -1)
        x, y = {(1, 0): 1}, {(-1, 0): s}
        sfx = f"[s={s}]"
        out["I4 L(n)^2 = 5F(n)^2 + 4(-1)^n " + sfx] = (pmul(L, L), padd(pmul(D, D), pk(4*s)))
        out["I5 L(2n) = L(n)^2 - 2(-1)^n " + sfx] = (padd(ppow(x, 2), ppow(y, 2)), padd(pmul(L, L), pk(-2*s)))
        out["I6 F(2n) = F(n)L(n) " + sfx] = (padd(ppow(x, 2), ppow(y, 2), -1), pmul(D, L))
        # sqrt5*F(5n) = D*(D^4 + 5 s D^2 + 5), the sqrt5-free form of F(5n) = 5F(n)(5F(n)^4 + 5(-1)^n F(n)^2 + 1)
        rhs = pmul(D, padd(padd(ppow(D, 4), pmul(pk(5*s), ppow(D, 2))), pk(5)))
        out["I7 F(5n) = 5F(n)(5F(n)^4 + 5(-1)^n F(n)^2 + 1) " + sfx] = (padd(ppow(x, 5), ppow(y, 5), -1), rhs)
    return out


# ---------- exact sequences, any non-negative index ----------


def fl(n):
    """(F(n), L(n)) exactly."""
    a, b = 0, 1
    for bit in bin(n)[2:]:
        a, b = a*(2*b - a), a*a + b*b
        if bit == "1":
            a, b = b, a + b
    return a, 2*b - a


def fl_mod(n, m):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        a, b = a*(2*b - a) % m, (a*a + b*b) % m
        if bit == "1":
            a, b = b, (a + b) % m
    return a, (2*b - a) % m


def F(n, m=None): return fl(n)[0] if m is None else fl_mod(n, m)[0]
def L(n, m=None): return fl(n)[1] if m is None else fl_mod(n, m)[1]


def v5(x):
    x = abs(x)
    if x == 0:
        raise ValueError("v5(0)")
    v = 0
    while x % 5 == 0:
        x //= 5
        v += 1
    return v


# ---------- Part 3: the theorem's steps ----------


def seq_period(values, candidates):
    """Smallest candidate that is a period of a list covering one whole period (index taken cyclically)."""
    n = len(values)
    for h in sorted(candidates):
        if all(values[i] == values[(i+h) % n] for i in range(n)):
            return h
    return None


def composite_values(outer, inner, m):
    """outer(inner(n)) mod m = 5^k over Q values, with the inner value reduced mod P = 4*5^(k-1).
    The reduction is what the proof justifies, so `direct_check` tests it against exact indices.
    Q = 12*5^k is a period of F and L mod P; the assert keeps the cyclic comparison in seq_period honest."""
    k = round(math.log(m, 5))
    P = 4*5**(k-1)
    Q = 12*5**k
    assert all((fl_mod(i, P)) == (fl_mod(i+Q, P)) for i in range(2))
    vals = []
    for n in range(Q):
        vals.append((F if outer == "F" else L)((F if inner == "F" else L)(n, P), m))
    return vals


def step_checks(K):
    """Each lemma of PROOFS.md on concrete values. Returns [(name, passed, detail)]."""
    R = []
    def add(name, ok, detail=""): R.append((name, bool(ok), detail))
    # v5(F(n)) = v5(n)
    add("V  v5(F(n)) = v5(n), n = 1..3000", all(v5(F(n)) == v5(n) for n in range(1, 3001)))
    add("V0 5 never divides L(n), n = 0..3000", all(L(n) % 5 for n in range(3001)))
    for j in range(1, K+1):
        q = 5**j
        add(f"A{j} L(n + 2*5^{j-1}) = -L(n) mod 5^{j}", all((L(n + 2*5**(j-1), q) + L(n, q)) % q == 0 for n in range(4*5**(j-1))))
        add(f"B{j} F(n + 2*5^{j}) = -F(n) mod 5^{j}", all((F(n + 2*5**j, q) + F(n, q)) % q == 0 for n in range(4*5**j)))
    for k in range(1, K+1):
        m = 5**k
        c = 2*5**(k-1)
        add(f"M{k} L((c-1)x) = L(x) mod 5^{k}, c = {c}", all(L((c-1)*x, m) == L(x, m) for x in range(4*5**(k-1))))
    for k in range(2, K+1):
        P, a = 4*5**(k-1), 2*5**(k-1) - 1
        h, hf = 6*5**(k-2), 6*5**(k-1)
        add(f"S{k} L(n+{h}) = {a}*L(n) mod {P}", all((L(n+h, P) - a*L(n, P)) % P == 0 for n in range(12*5**(k-1))))
        add(f"T{k} F(n+{hf}) = {a}*F(n) mod {P}", all((F(n+hf, P) - a*F(n, P)) % P == 0 for n in range(12*5**k)))
    # lower-bound witnesses: exact valuations from the proof's formulas against exact big integers
    for k in range(3, K+1):
        j, w = k-3, 3*5**(k-3)
        y = L(1 + 2*w)
        add(f"W{k} y+1 = 5F(w)F(w+1), L(L(n)) witness", y + 1 == 5*F(w)*F(w+1))
        add(f"W{k} v5(y+1) = {1+j}, 5 does not divide y-1", v5(y+1) == 1+j and (y-1) % 5 != 0)
        add(f"W{k} y = 1 mod 4", y % 4 == 1)
        add(f"W{k} L(y) - L(1) has v5 = {k-1} (below {k})", (L(y, 5**k) - 1) % 5**(k-1) == 0 and (L(y, 5**k) - 1) % 5**k != 0)
    for k in range(2, K+1):
        j, w = k-2, 3*5**(k-2)
        y = F(1 + 2*w)
        add(f"X{k} y+1 = F(w)L(w+1), L(F(n)) witness", y + 1 == F(w)*L(w+1))
        add(f"X{k} v5(y+1) = {j}, 5 does not divide y-1", v5(y+1) == j and (y-1) % 5 != 0)
        add(f"X{k} y = 1 mod 4", y % 4 == 1)
        add(f"X{k} L(y) - L(1) has v5 = {k-1} (below {k})", (L(y, 5**k) - 1) % 5**(k-1) == 0 and (L(y, 5**k) - 1) % 5**k != 0)
    return R


def divisors(n): return [d for d in range(1, n+1) if n % d == 0]


def theorem_checks(K):
    """The theorem, tested by a search over every divisor of a period common to all shifts. No lemma of the proof is used
    except the reduction of the inner index, which direct_check tests against exact big-integer indices."""
    R = []
    for k in range(1, K+1):
        m = 5**k
        LL, LF = composite_values("L", "L", m), composite_values("L", "F", m)
        pLL = seq_period(LL, divisors(len(LL)))
        pLF = seq_period(LF, divisors(len(LF)))
        want_LL = 6*5**(k-2) if k >= 2 else 6
        want_LF = 6*5**(k-1)
        R.append((f"Theorem k={k}: L(L(n)) mod {m} has exact period {want_LL}", pLL == want_LL, f"computed {pLL}"))
        R.append((f"Theorem k={k}: L(F(n)) mod {m} has exact period {want_LF}", pLF == want_LF, f"computed {pLF}"))
    return R


def direct_check(n_max=26):
    """First terms with the exact, unreduced inner index against the reduced values used above."""
    bad = 0
    for k in (1, 2, 3, 4):
        m, P = 5**k, 4*5**(k-1)
        for n in range(n_max):
            bad += L(L(n), m) != L(L(n, P), m)
            bad += L(F(n), m) != L(F(n, P), m)
    return bad


# ---------- Part 4: certificate for one composition and modulus ----------
SEQ = {"F": ((1, 1), (0, 1)), "L": ((1, 1), (2, 1)), "P": ((2, 1), (0, 1)), "Q": ((2, 1), (2, 2)), "T": ((1, 1, 1), (0, 0, 1))}


def _table(s, q):
    """One full cycle of s mod q. The state returning to its start proves it: the recurrence is deterministic."""
    co, init = SEQ[s]
    if q == 1:
        return [0]
    st0 = tuple(x % q for x in init)
    st, out = st0, []
    while True:
        out.append(st[0])
        nxt = sum(c*x for c, x in zip(co, reversed(st))) % q
        st = st[1:] + (nxt,)
        if st == st0:
            return out


def prime_factors(n):
    out, p = [], 2
    while p*p <= n:
        if n % p == 0:
            out.append(p)
            while n % p == 0:
                n //= p
        p += 1
    return out + ([n] if n > 1 else [])


def certify(chain, m):
    """chain = "LL", "FQ", "FTT"...: f1(f2(...fk(n))) mod m. Returns (T, certificate).
    Upper bound: the whole composition is periodic with period B (cycles, R_COMP), and T is checked as a shift over all B values.
    Lower bound: for each prime p dividing T, a witness n with s(n + T/p) != s(n). A period below T would divide T/p for some p."""
    mods = [m]
    for f in chain[:-1]:
        mods.append(len(_table(f, mods[-1])))
    tabs = [_table(f, q) for f, q in zip(chain, mods)]
    B = len(tabs[-1])
    def s(n):
        x = n
        for tab in reversed(tabs):
            x = tab[x % len(tab)]
        return x
    vals = [s(n) for n in range(B)]
    T = B
    for p in prime_factors(B):
        while T % p == 0 and all(vals[i] == vals[(i + T//p) % B] for i in range(B)):
            T //= p
    witnesses = {}
    for p in prime_factors(T):
        witnesses[p] = next(i for i in range(B) if vals[i] != vals[(i + T//p) % B])
    return T, dict(chain=chain, m=m, B=B, cycles=[len(t) for t in tabs], witnesses=witnesses)


def check_certificate(chain, m, T, cert):
    """Re-checks a certificate from its own numbers: T divides B, T is a shift over all B values, and every witness differs."""
    if cert["B"] % T:
        return False, "T does not divide B"
    tabs = [_table(f, q) for f, q in zip(chain, [m] + cert["cycles"][:-1])]
    def s(n):
        x = n
        for tab in reversed(tabs):
            x = tab[x % len(tab)]
        return x
    if any(s(i) != s(i+T) for i in range(cert["B"])):
        return False, "T is not a period"
    if sorted(cert["witnesses"]) != prime_factors(T):
        return False, "a prime factor of T has no witness"
    for p, n in cert["witnesses"].items():
        if s(n) == s(n + T//p):
            return False, f"witness for {p} fails"
    return True, "ok"


def main(K=6):
    fails = 0
    def show(name, ok, detail=""):
        nonlocal fails
        fails += not ok
        print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    print("--- Part 1: identities, symbolic, for all n")
    for name, (a, b) in identities().items():
        show(name, padd(a, b, -1) == {})
    print("--- Part 2: base facts")
    f4 = [F(n, 4) for n in range(12)]
    l4 = [L(n, 4) for n in range(12)]
    show("F mod 4 has period 6", f4[:6] == f4[6:], str(f4[:6]))
    show("L mod 4 has period 6", l4[:6] == l4[6:], str(l4[:6]))
    z = [n for n in range(1, 21) if F(n) % 5 == 0]
    show("5 divides F(n) iff 5 divides n, one full cycle of F mod 5 (length 20)", z == [5, 10, 15, 20] and [F(n, 5) for n in range(2)] == [F(20, 5), F(21, 5)])
    show("5 never divides L(n), one full cycle of L mod 5 (length 4)", sorted(L(n, 5) for n in range(4)) == [1, 2, 3, 4] and (L(4, 5), L(5, 5)) == (2, 1))
    show("L(L(n)) mod 25 = 3,1,4,7,4,24 repeating; shifts 2 and 3 fail", [L(L(n), 25) for n in range(6)] == [3, 1, 4, 7, 4, 24])
    show("L(F(n)) mod 5 has exact period 6", (lambda v: v[:6] == v[6:12] and v[0] != v[2] and v[0] != v[3])([L(F(n), 5) for n in range(12)]), str([L(F(n), 5) for n in range(6)]))
    print("--- Part 3: lemmas and theorem on concrete k")
    results = step_checks(K)
    for name, ok, detail in results:
        if not ok:
            show(name, ok, detail)
    print(f"lemma instances: {sum(r[1] for r in results)} of {len(results)} pass")
    for name, ok, detail in theorem_checks(K):
        show(name, ok, detail)
    bad = direct_check()
    show("reduced inner index agrees with exact big-integer index, k=1..4, n<26", bad == 0, f"{bad} differences")
    print("--- Part 4: certificates (exact period and lower-bound witnesses)")
    for chain, m, want in (("LL", 25, 6), ("LF", 25, 30), ("FQ", 27, 4), ("FF", 25, 300), ("LLF", 3, 12)):
        T, cert = certify(chain, m)
        ok, why = check_certificate(chain, m, T, cert)
        show(f"{chain} mod {m}: exact period {T}, witnesses {cert['witnesses']}", ok and T == want, why)
    print("ALL CHECKS PASSED" if not fails else f"{fails} CHECKS FAILED")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
