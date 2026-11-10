"""Exact period tables without big integers, independent of merge.py's proof: each block is a table over one cycle of its argument,
and a composition reads the inner values modulo the cycle of the outer block. Used to extend a period table far enough to compare with an OEIS entry.
A digit sum mod m is only defined here when m divides 9 (casting out nines). Otherwise series raises NoRule, as merge.py raises Gap."""
import math
class NoRule(Exception): pass
class TooLarge(Exception): pass
_pi = {}
def pisano(m):
    if m == 1: return 1
    if m not in _pi:
        a, b, k = 0, 1, 0
        while True:
            a, b = b, (a+b) % m; k += 1
            if (a, b) == (0, 1): _pi[m] = k; break
    return _pi[m]
def dep(f, m):
    """L such that f(k) mod m depends only on k mod L."""
    if f in ("fib", "luc"): return pisano(m)
    if f == "sq": return m
    if f == "tri": return m if m % 2 else 2*m
    if f == "ds":
        if 9 % m: raise NoRule(f"ds mod {m}")
        return m
    raise KeyError(f)
def block(f, m):
    L = dep(f, m)
    if f in ("fib", "luc"):
        a, b = (0, 1) if f == "fib" else (2, 1)
        a %= m; b %= m; out = []
        for _ in range(L): out.append(a); a, b = b, (a+b) % m
        return out
    if f == "sq": return [k*k % m for k in range(L)]
    if f == "tri": return [k*(k+1)//2 % m for k in range(L)]
    return [k % m for k in range(L)]
def series(E, m, cap=400000):
    """Values of expression tree E mod m over one (not always minimal) period."""
    if m == 1: return [0]
    if E[0] == "blk": return block(E[1], m)
    if E[0] in ("add", "mul"):
        a, b = series(E[1], m, cap), series(E[2], m, cap); B = math.lcm(len(a), len(b))
        if B > cap: raise TooLarge(B)
        if E[0] == "add": return [(a[i % len(a)] + b[i % len(b)]) % m for i in range(B)]
        return [a[i % len(a)] * b[i % len(b)] % m for i in range(B)]
    t = block(E[1], m); L = len(t)
    return [t[x % L] for x in series(E[2], L, cap)]
def minimal(v):
    """Smallest period of a list that covers whole periods."""
    n = len(v); T = n; t = n; d = 2; ps = []
    while d*d <= t:
        if t % d == 0:
            ps.append(d)
            while t % d == 0: t //= d
        d += 1
    if t > 1: ps.append(t)
    for p in ps:
        while T % p == 0 and all(v[i] == v[(i + T//p) % n] for i in range(n)): T //= p
    return T
def period(E, m, cap=400000):
    return minimal(series(E, m, cap))
