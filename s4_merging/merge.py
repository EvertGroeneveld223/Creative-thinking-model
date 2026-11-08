"""Block merging. Every expression is rewritten into one normal form:
     s(n) = sum_j c_j * n^a_j * prod(atom^p)      (c_j rational, atoms = Fib(arg), Luc(arg), Ds(arg))
Merge rules (all assumed right; Where is checked):
  M_SQ   sq(x)  -> x*x                         (definition of square)
  M_TRI  tri(x) -> (x*x + x)/2                 (ProofWiki closed form)
  M_DS   Ds(x)  -> x   ONLY when the working modulus divides 9   (casting out nines)
  M_MOD  expand sums/products                  (congruence respects + and x, Gordon 4.3.2)
Exact period proof:
  R_IVP    integer-valued polynomials are integer combinations of C(t,k)      (Wikipedia, Integer-valued polynomial)
  R_NEWTON Q(t) = sum_k Delta^k Q(0) C(t,k)                                   (Newton forward differences)
  => Q(t) = 0 mod m for all t  iff  Delta^k Q(0) = 0 mod m for k = 0..deg     (no sequence values needed beyond deg+1 points)
  atoms Fib/Luc mod q depend on arg mod pisano(q) (R_FIB, R_LUC); arg period found recursively."""
import math
from fractions import Fraction as Fr
import engine1 as g

ATOMS = {}                         # id -> (kind, argNF)
def key(nf): return tuple(sorted((k, (v.numerator, v.denominator)) for k, v in nf.items() if v))
def atom(kind, arg):
    k = (kind, key(arg))
    for i, (kk, a) in ATOMS.items():
        if (kk, key(a)) == k: return i
    i = len(ATOMS); ATOMS[i] = (kind, arg); return i

N = {(1, ()): Fr(1)}
def add(a, b):
    r = dict(a)
    for k, v in b.items(): r[k] = r.get(k, 0) + v
    return {k: v for k, v in r.items() if v}
def scale(a, c): return {k: v*c for k, v in a.items() if v*c}
def mulmono(x, y):
    d = dict(x[1])
    for i, p in y[1]: d[i] = d.get(i, 0) + p
    return (x[0]+y[0], tuple(sorted(d.items())))
def mul(a, b):
    r = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            k = mulmono(ka, kb); r[k] = r.get(k, 0) + va*vb
    return {k: v for k, v in r.items() if v}

def compose(f, x, trace):
    if f == "sq":  trace.append("M_SQ: sq(x) -> x*x"); return mul(x, x)
    if f == "tri": trace.append("M_TRI: tri(x) -> (x*x + x)/2"); return scale(add(mul(x, x), x), Fr(1, 2))
    kind = {"fib": "F", "luc": "L", "ds": "D"}[f]
    return {(0, ((atom(kind, x), 1),)): Fr(1)}

def to_nf(E, trace):
    if E[0] == "blk": return compose(E[1], N, trace)
    if E[0] == "add": trace.append("M_MOD: expand sum"); return add(to_nf(E[1], trace), to_nf(E[2], trace))
    if E[0] == "mul": trace.append("M_MOD: expand product"); return mul(to_nf(E[1], trace), to_nf(E[2], trace))
    if E[0] == "comp": return compose(E[1], to_nf(E[2], trace), trace)

def subst(nf, aid, rep):
    r = {}
    for (a, ats), c in nf.items():
        term = {(a, tuple((i, p) for i, p in ats if i != aid)): c}
        for i, p in ats:
            if i == aid:
                for _ in range(p): term = mul(term, rep)
        r = add(r, term)
    return r

def denom(nf): return math.lcm(*[v.denominator for v in nf.values()]) if nf else 1
def top_atoms(nf): return sorted({i for (_, ats) in nf for i, _ in ats})

def split_den(D, m):
    """D1 = part of D sharing primes with m (must inflate modulus), D2 = part coprime to m (invertible, R_MOD)."""
    D1 = 1; g0 = math.gcd(D, m)
    while g0 > 1:
        D1 *= g0; D //= g0; g0 = math.gcd(D, m)
    return D1

def prep(nf, m, trace):
    """Merge digit sums where Where holds, drop terms that vanish mod m'. Returns (nf, D1, m', int_coefs)."""
    while True:
        D = denom(nf); D1 = split_den(D, m); mp = m*D1
        ic = {}
        for k, v in nf.items():
            c = v*D1; c = (c.numerator * pow(c.denominator, -1, mp)) % mp
            if c: ic[k] = c
        if len(ic) < len(nf): trace.append(f"R_MOD: drop {len(nf)-len(ic)} term(s) whose coefficient is 0 mod {mp}")
        nf = {k: v for k, v in nf.items() if k in ic}
        ds = [i for i in top_atoms(nf) if ATOMS[i][0] == "D"]
        if not ds: return nf, D1, mp, ic
        if 9 % mp: raise Gap(f"Ds(.) mod {mp}: M_DS needs the modulus to divide 9")
        trace.append(f"M_DS: Ds(x) -> x  (Where holds: {mp} divides 9)")
        nf = subst(nf, ds[0], ATOMS[ds[0]][1])

class Gap(Exception): pass

def fib_mod(k, q):
    F, F1 = g.fib_pair_mod(k, q); return F % q
def luc_mod(k, q):
    F, F1 = g.fib_pair_mod(k, q); return (2*F1 - F) % q

def atom_val(i, n, q, cache):
    kk = (i, n, q)
    if kk in cache: return cache[kk]
    kind, arg = ATOMS[i]
    if kind == "D": raise Gap("unmerged digit sum")
    pq = g.pisano(q); k = eval_nf(arg, n, pq, cache)
    v = fib_mod(k, q) if kind == "F" else luc_mod(k, q); cache[kk] = v; return v

def eval_nf(nf, n, q, cache):
    nf, D, qp, ic = prep(nf, q, [])
    x = 0
    for (a, ats), c in ic.items():
        t = c * pow(n, a, qp)
        for i, p in ats: t *= pow(atom_val(i, n, qp, cache), p, qp)
        x += t
    x %= qp; assert x % D == 0
    return (x // D) % q

def divisors(B): return sorted(d for d in range(1, B+1) if B % d == 0)

def period(nf, m, trace, depth=0, cache=None):
    """Exact minimal period of nf mod m, proved by R_NEWTON per residue class. Raises Gap."""
    cache = {} if cache is None else cache
    if m == 1: return 1
    nf, D, mp, Ei = prep(nf, m, trace)
    M = 1
    for i in top_atoms(nf):
        kind, arg = ATOMS[i]; q = g.pisano(mp)
        p = period(arg, q, trace, depth+1, cache)
        trace.append(f"{'  '*depth}atom {kind}(arg) mod {mp}: R_{'FIB' if kind=='F' else 'LUC'} -> depends on arg mod pi({mp})={q}; arg has period {p}")
        M = math.lcm(M, p)
    if not Ei: trace.append(f"{'  '*depth}all terms vanish mod {mp}: constant"); return 1
    deg = max(a for (a, _) in Ei)
    B = math.lcm(M, mp)
    ats = top_atoms(nf)
    def val(nn, avals):
        x = 0
        for (a, at), c in Ei.items():
            t = c * nn**a
            for i, p in at: t *= avals[i]**p
            x += t
        return x
    for h in divisors(B):
        ok = True
        for r in range(M):
            A0 = {i: atom_val(i, r, mp, cache) for i in ats}; A1 = {i: atom_val(i, r+h, mp, cache) for i in ats}
            Q = [val(r+h+M*t, A1) - val(r+M*t, A0) for t in range(deg+1)]
            for k in range(deg+1):                      # Delta^k Q(0)
                if Q[0] % mp: ok = False; break
                Q = [Q[j+1]-Q[j] for j in range(len(Q)-1)]
            if not ok: break
        if ok:
            trace.append(f"{'  '*depth}R_NEWTON: {D}*s(n) mod {mp}: bound {B}, smallest passing shift h={h} over {M} residue classes, degree {deg}")
            return h
    raise AssertionError("B itself must pass")

def explain(p):
    """Merged explanation of a point from the engine. Returns (L or None, trace, nf)."""
    ATOMS_before = len(ATOMS); trace = []
    nf = to_nf(g.tree(p), trace)
    try: L = period(nf, p["m"], trace)
    except Gap as e: return None, trace + [f"GAP: {e}"], nf
    return L, trace, nf

def show_nf(nf):
    def at(i):
        k, a = ATOMS[i]; return f"{ {'F':'Fib','L':'Luc','D':'Ds'}[k] }({show_nf(a)})"
    parts = []
    for (a, ats), c in sorted(nf.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
        mono = ([f"n^{a}" if a > 1 else "n"] if a else []) + [at(i) + (f"^{p}" if p > 1 else "") for i, p in ats]
        parts.append(("" if c == 1 and mono else str(c) + ("*" if mono else "")) + "*".join(mono))
    return " + ".join(parts) if parts else "0"
