"""General period formula for f(g(n)) mod m, f and g in {F, L}. Generalises the 5^k theorem in PROOFS.md to every odd prime power.
Status of each part (see PROOFS.md, Theorem 2):
  L outer, shift exists  -> the period DIVIDES h: proved.
  exact value, and "no saving" when the shift does not exist -> tested by this file, NOT proved.
  F outer at odd q, no saving -> tested, NOT proved (the odd-modulus pattern).
  q = 2: factor 2 -> finite check. q = 2^k, k >= 2: no saving -> tested, NOT proved.

The criterion, q an odd prime power, P the cycle of L mod q, B the cycle of g mod P (the R_COMP bound):
  a saving needs P = 4 mod 8. Then z = P/4 is odd, and L(n + 2z) = -L(n) mod q gives L((2z-1)x) = L(x), with 2z-1 = 1 mod 4 and = -1 mod z.
  So any h with 6 | h and g(n+h) = -g(n) mod z makes h a period. For each prime power t of z the shift must be C/2, C the cycle of g mod t.
  The saving exists iff these congruences on h can all hold at once and their solution is smaller than B.
    python general.py [PMAX] [MMAX]    writes general.json. Exits non-zero on any disagreement."""
import json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
START = {"F": (0, 1), "L": (2, 1)}
_tab = {}
def table(s, q):
    """One full cycle of s mod q, found by the state returning to its start."""
    if q == 1: return [0]
    if (s, q) in _tab: return _tab[(s, q)]
    a, b = START[s]; a %= q; b %= q; st = (a, b); x, y = st; out = []
    while True:
        out.append(x); x, y = y, (x+y) % q
        if (x, y) == st: break
    if len(_tab) > 4000: _tab.clear()       # memory is limited; a cycle can be recomputed
    _tab[(s, q)] = out
    return out
def factor(n):
    out, p = {}, 2
    while p*p <= n:
        while n % p == 0: out[p] = out.get(p, 0) + 1; n //= p
        p += 1
    if n > 1: out[n] = out.get(n, 0) + 1
    return out
def prime_powers(n): return [p**e for p, e in factor(n).items()]
def minimal(v):
    n = len(v); T = n
    for p in factor(n):
        while T % p == 0 and all(v[i] == v[(i + T//p) % n] for i in range(n)): T //= p
    return T
def true_period(f, g, m):
    o = table(f, m); it = table(g, len(o))
    return minimal([o[x] for x in it])
def bound(f, g, m): return len(table(g, len(table(f, m))))
def neg_shift(g, t):
    """h with g(n+h) = -g(n) mod t for all n, t odd > 1. If it exists, 2h is a period, so h can only be half the cycle."""
    v = table(g, t); C = len(v)
    if C % 2: return None
    h = C//2
    return h if all((v[(i+h) % C] + v[i]) % t == 0 for i in range(C)) else None
def crt(r1, m1, r2, m2):
    d = math.gcd(m1, m2)
    if (r2 - r1) % d: return None
    l = m1//d*m2
    return (r1 + m1*(((r2 - r1)//d * pow(m1//d, -1, m2//d)) % (m2//d))) % l, l
def shift_solution(g, z):
    """Smallest h > 0 with 6 | h and g(n+h) = -g(n) mod z, or None."""
    r, M = 0, 6
    for t in prime_powers(z):
        h = neg_shift(g, t)
        if h is None: return None
        s = crt(r, M, h, 2*h)
        if s is None: return None
        r, M = s
    return r or M
def predict_q(f, g, q):
    """Predicted period at one prime power, and which rule gave it."""
    B = bound(f, g, q)
    if q == 2: return B//2, "q=2"
    if q % 2 == 0: return B, "2^k: none"
    if f == "F": return B, "F outer: none"
    P = len(table("L", q))
    if P % 8 != 4: return B, "P != 4 mod 8"
    z = P//4
    if z == 1: return B, "z = 1"
    h = shift_solution(g, z)
    if h is None: return B, "no common shift"
    return (h, "shift") if h < B else (B, "shift, no gain")
def predict(f, g, m):
    L = 1
    for q in prime_powers(m): L = math.lcm(L, predict_q(f, g, q)[0])
    return L
def primes(n):
    s = bytearray([1])*(n+1); s[:2] = b"\0\0"
    for i in range(2, int(n**.5)+1):
        if s[i]: s[i*i::i] = bytes(len(s[i*i::i]))
    return [i for i in range(n+1) if s[i]]
def main(pmax=10000, mmax=1200, cap=600000):
    t0 = time.time(); errs = []; n = sav = extra = skipped = blind = blind_sav = 0; saves = {}; reasons = {}
    for p in primes(pmax):
        q = p
        while q <= pmax:
            for f in "FL":
                for g in "FL":
                    if bound(f, g, q) > cap: skipped += 1; continue
                    T = true_period(f, g, q); P_, why = predict_q(f, g, q); n += 1; reasons[why] = reasons.get(why, 0) + 1
                    if p > 300: blind += 1
                    if why in ("shift", "q=2"):
                        sav += 1; saves.setdefault(f+g, []).append(q)
                        if p > 300: blind_sav += 1
                        if T < P_: extra += 1
                    if T != P_: errs.append((f, g, q, P_, T, why))
            q *= p
        _tab.clear()
    print(f"prime powers <= {pmax}: {n} cases, {skipped} too large and skipped, errors {len(errs)} {errs[:12]}", flush=True)
    print(f"  cases at primes > 300 (unseen when the rule was written): {blind}, predicted savings among them: {blind_sav}; true period below a predicted saving: {extra}", flush=True)
    print("  rule used:", reasons, flush=True)
    bad = []; k = 0
    for m in range(2, mmax+1):
        for f in "FL":
            for g in "FL":
                k += 1
                if predict(f, g, m) != true_period(f, g, m): bad.append((f, g, m))
        if m % 200 == 0: _tab.clear()
    print(f"all m = 2..{mmax}: {k} cases, errors {len(bad)} {bad[:12]}, secs {round(time.time()-t0, 1)}", flush=True)
    json.dump(dict(pmax=pmax, mmax=mmax, cases=n, skipped=skipped, errors=errs, blind_cases=blind, blind_savings=blind_sav, hidden_extra=extra, rules=reasons, savings={k: v[:400] for k, v in saves.items()}, m_cases=k, m_errors=bad), open(os.path.join(HERE, "general.json"), "w"), indent=1)
    return len(errs) + len(bad)
if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(*(int(x) for x in a)) else 0)
