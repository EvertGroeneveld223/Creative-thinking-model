import os as _os
_P=lambda *a:_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",*[x for x in a if x]))
"""3D rulebook engine. Domain: integer sequences taken modulo m.
X = breadth (sum/product with more blocks), Y = areas used, Z = depth (composition).
Returns per pattern: w works (exact computation), e explained (rulebook derives it), n novel (web, recorded by hand).
Noise: os.urandom only."""
import os, sys, json, math, hashlib
sys.set_int_max_str_digits(0)
ST = _P("s2_cube_v1","state.json")

def u():  return int.from_bytes(os.urandom(8), "big") / 2**64
def pick(xs, w=None):
    w = w or [1]*len(xs); r = u()*sum(w)
    for x, wi in zip(xs, w):
        r -= wi
        if r <= 0: return x
    return xs[-1]

# ---------------- rulebook (always right) ----------------
RULES = {
 "R_FIB": dict(what="F(n) mod m is periodic; its period is pi(m)", who="https://en.wikipedia.org/wiki/Pisano_period",
               where="any integer m >= 1", why="Fibonacci values mod m depend only on n mod pi(m)"),
 "R_LUC": dict(what="any sequence with the Fibonacci recurrence (e.g. Lucas) mod m has period dividing pi(m)",
               who="https://en.wikipedia.org/wiki/Pisano_period", where="any integer m >= 1", why="Lucas values mod m depend only on n mod pi(m)"),
 "R_TRI": dict(what="T(n) = n(n+1)/2", who="https://proofwiki.org/wiki/1%2B2%2B...%2Bn_%3D_n(n%2B1)/2",
               where="natural n", why="lets T be written as a polynomial so R_MOD applies (n(n+1) mod 2m depends on n mod 2m, so T mod m depends on n mod 2m)"),
 "R_MOD": dict(what="if a=c and b=d (mod n) then a+b=c+d and ab=cd (mod n)", who="https://math.gordon.edu/ntic/ntic/section-cong-props.html",
               where="any modulus n", why="sums, products and polynomials respect congruence; gives n^2 mod m depends on n mod m, and sum/product periods combine by lcm"),
 "R_DS":  dict(what="a number and its digit sum differ by a multiple of 9 (casting out nines)", who="https://en.wikipedia.org/wiki/Casting_out_nines",
               where="only moduli m that divide 9 (1, 3, 9)", why="digit sum mod m depends only on the number mod m"),
 "R_COMP":dict(what="if f(k) mod m depends only on k mod L, and g(n) mod L has period P, then f(g(n)) mod m has period dividing P",
               who="definition of a periodic sequence (logic, no web page)", where="any f, g, m", why="chains one block into another"),
 "R_ID":  dict(what="n mod m has period m", who="definition of congruence (logic)", where="any m", why="base block"),
}
AREA = {"fib": "fibonacci", "luc": "fibonacci", "tri": "figurate", "sq": "figurate", "ds": "digits"}
BLOCKS = list(AREA)

def pisano(m):
    if m == 1: return 1
    a, b, k = 0, 1, 0
    while True:
        a, b = b, (a+b) % m; k += 1
        if (a, b) == (0, 1): return k

def dep(f, m, trace, where):
    """L such that f(k) mod m depends only on k mod L, with the rule that licenses it."""
    if m == 1: trace.append(dict(step=f"anything mod 1 is 0", rule="R_ID", how=where)); return 1
    if f == "id":  L, r = m, "R_ID"
    elif f == "sq": L, r = m, "R_MOD"
    elif f == "tri": L, r = 2*m, "R_TRI"
    elif f == "fib": L, r = pisano(m), "R_FIB"
    elif f == "luc": L, r = pisano(m), "R_LUC"
    elif f == "ds":
        if 9 % m: trace.append(dict(step=f"ds(k) mod {m}: NO RULE (casting out nines only covers m | 9)", rule=None, how=where)); return None
        L, r = m, "R_DS"
    trace.append(dict(step=f"{f}(k) mod {m} depends only on k mod {L}", rule=r, how=where)); return L

def bound(E, m, trace, where="whole"):
    if E[0] == "blk": return dep(E[1], m, trace, where)
    if E[0] in ("add", "mul"):
        a = bound(E[1], m, trace, where+"/left"); b = bound(E[2], m, trace, where+"/right")
        if a is None or b is None: return None
        L = a*b//math.gcd(a, b); trace.append(dict(step=f"{'sum' if E[0]=='add' else 'product'} mod {m}: period divides lcm({a},{b}) = {L}", rule="R_MOD", how=where)); return L
    if E[0] == "comp":
        Lf = dep(E[1], m, trace, where+"/outer")
        if Lf is None: return None
        P = bound(E[2], Lf, trace, where+"/inner")
        if P is None: return None
        trace.append(dict(step=f"{E[1]}(inner) mod {m}: period divides {P}", rule="R_COMP", how=where)); return P

# ---------------- the world: exact computation, no rules used ----------------
CAP = 40000  # bits
def fib_pair_mod(k, m):
    def fd(k):
        if k == 0: return (0, 1)
        a, b = fd(k >> 1); c = (a*((2*b - a) % m)) % m; d = (a*a + b*b) % m
        return (d, (c+d) % m) if k & 1 else (c, d)
    sys.setrecursionlimit(100000); return fd(k)
def fib_exact(k):
    if k*0.7 > CAP: raise OverflowError
    a, b = 0, 1
    for _ in range(k): a, b = b, a+b
    return a
def apply(f, k, m=None):
    if f == "id": v = k
    elif f == "sq": v = k*k
    elif f == "tri": v = k*(k+1)//2
    elif f == "ds": v = sum(map(int, str(k)))
    elif f in ("fib", "luc"):
        if m is not None:
            F, F1 = fib_pair_mod(k, m); return F % m if f == "fib" else (2*F1 - F) % m
        F = fib_exact(k + 1); Fk = fib_exact(k) if f == "fib" else None
        v = Fk if f == "fib" else 2*F - fib_exact(k)
    if m is None and v.bit_length() > CAP: raise OverflowError
    return v % m if m is not None else v
def ev(E, n, m=None):
    if E[0] == "blk": return apply(E[1], n, m)
    if E[0] in ("add", "mul"):
        a, b = ev(E[1], n, m), ev(E[2], n, m); v = a+b if E[0] == "add" else a*b
        return v % m if m is not None else v
    if E[0] == "comp": return apply(E[1], ev(E[2], n, None), m)
def world(E, m, N=900):
    s = []
    for n in range(N):
        try: s.append(ev(E, n, m))
        except OverflowError: break
    for L in range(1, len(s)//3 + 1):
        if all(s[i] == s[i+L] for i in range(len(s)-L)): return s, L
    return s, None

# ---------------- points in 3D ----------------
def tree(p):
    E = ("blk", p["base"])
    for kind, b in p["ops"]:
        E = ("comp", b, E) if kind == "comp" else (kind, E, ("blk", b))
    return E
def show(E):
    if E[0] == "blk": return f"{E[1]}(n)"
    if E[0] == "comp": return f"{E[1]}({show(E[2])})"
    return f"[{show(E[1])} {'+' if E[0]=='add' else '*'} {show(E[2])}]"
def coords(p):
    blocks = [p["base"]] + [b for _, b in p["ops"]]
    return (sum(k in ("add", "mul") for k, _ in p["ops"]), len({AREA[b] for b in blocks}), sum(k == "comp" for k, _ in p["ops"]))
def areas(p): return {AREA[b] for b in [p["base"]] + [b for _, b in p["ops"]]}

def move(p, axis, sign):
    q = json.loads(json.dumps(p)); cur = areas(q)
    if sign > 0:
        if axis == "X": q["ops"].append([pick(["add", "mul"]), pick([b for b in BLOCKS if AREA[b] in cur])])
        if axis == "Y":
            new = [b for b in BLOCKS if AREA[b] not in cur]
            if not new: return None
            q["ops"].append([pick(["add", "mul", "comp"]), pick(new)])
        if axis == "Z": q["ops"].append(["comp", pick([b for b in BLOCKS if AREA[b] in cur])])
    else:
        idx = [i for i, (k, b) in enumerate(q["ops"]) if (axis == "X" and k in ("add", "mul")) or (axis == "Z" and k == "comp")
               or (axis == "Y" and AREA[b] != AREA[q["base"]])]
        if not idx: return None
        q["ops"].pop(idx[-1])
    return q

def evaluate(p):
    E = tree(p); m = p["m"]; trace = []
    LB = bound(E, m, trace); s, L = world(E, m)
    w = L is not None; e = LB is not None
    contra = w and e and LB % L != 0
    if e and not w and len(s) >= 3*LB: contra = True
    return dict(expr=show(E), m=m, coords=coords(p), period=L, derived_bound=LB, w=int(w), e=int(e),
                contradiction=contra, terms=s[:24], n_computed=len(s), trace=trace)

def corner(w, e, n):
    if w and e: return "NEW" if n else "KNOWN"
    if w and not e: return "DISCOVERY" if n else "GAP"
    return "CONTRADICTION" if e else "FALSE"

# ---------------- loop state ----------------
def load():
    if os.path.exists(ST): return json.load(open(ST))
    return dict(sigma={"X": .5, "Y": .5, "Z": .5}, eta=.25, K=3, cur=None, last_new=None, expanding=False, fails=0,
                last_axes=[], pending=None, log=[], ideas=[], known_rules=[], count=0)
def save(S): json.dump(S, open(ST, "w"), indent=1)
def fresh(): return dict(base=pick(BLOCKS), m=pick(list(range(5, 13))), ops=[])

def propose(S):
    if S["expanding"]:
        ax = pick(["X", "Y", "Z"], [S["sigma"][a] for a in "XYZ"]); q = move(S["last_new"], ax, +1)
        return (q, [ax]) if q else (None, [ax])
    base = S["cur"] or fresh()
    for _ in range(20):
        q, moved = base, []
        for ax in "XYZ":
            if u() < S["sigma"][ax]:
                r = move(q, ax, +1 if u() < .6 else -1)
                if r: q, moved = r, moved + [ax]
        if not moved:
            ax = pick(["X", "Y", "Z"]); r = move(q, ax, +1)
            if r: q, moved = r, [ax]
        if moved: return q, moved
    return fresh(), []

def adapt(S, kind):
    for ax in S["last_axes"]:
        if kind == "KNOWN": S["sigma"][ax] = min(.9, S["sigma"][ax]*(1+S["eta"]))
        if kind == "FALSE": S["sigma"][ax] = max(.1, S["sigma"][ax]*(1-S["eta"]))

def resolve(S, p, res, kind, src=None):
    S["count"] += 1
    entry = dict(i=S["count"], expr=res["expr"], m=res["m"], coords=res["coords"], period=res["period"], bound=res["derived_bound"],
                 w=res["w"], e=res["e"], corner=kind, axes=S["last_axes"], sigma=dict(S["sigma"]), source=src, expanding=S["expanding"])
    S["log"].append(entry); adapt(S, kind)
    if kind == "KNOWN":
        S["known_rules"].append(dict(what=f"{res['expr']} mod {res['m']} has period {res['period']}", who=src))
    if S["expanding"]:
        if kind == "NEW":
            S["last_new"], S["fails"] = p, 0; S["last_new_res"] = res; S["grow"] = S.get("grow", 0) + 1
            if S["grow"] >= S.get("B", 6):
                S["ideas"].append(dict(point=p, result=res, stop="budget")); S["expanding"] = False; S["cur"] = None; S["grow"] = 0
        else:
            S["fails"] += 1
            if S["fails"] >= S["K"]:
                S["ideas"].append(dict(point=S["last_new"], result=S["last_new_res"])); S["expanding"] = False; S["cur"] = None; S["fails"] = 0
    else:
        if kind == "NEW": S["expanding"], S["last_new"], S["last_new_res"], S["fails"], S["grow"] = True, p, res, 0, 1
        S["cur"] = p if kind in ("KNOWN", "GAP", "DISCOVERY") else S["cur"]
    return entry

def cmd_next(S):
    if S["pending"]: return S["pending"]
    while True:
        p, axes = propose(S); S["last_axes"] = axes
        if p is None:
            S["fails"] += 1
            if S["fails"] >= S["K"]:
                S["ideas"].append(dict(point=S["last_new"], result=S["last_new_res"])); S["expanding"] = False; S["cur"] = None; S["fails"] = 0
            continue
        res = evaluate(p)
        if res["n_computed"] < 60: kind = "UNREACHABLE"
        elif res["contradiction"]: kind = "CONTRADICTION"
        elif not res["w"]: kind = "FALSE"
        elif S["expanding"] and res["terms"] == S["last_new_res"]["terms"] and res["period"] == S["last_new_res"]["period"]: kind = "SAME"
        else:
            S["pending"] = dict(point=p, res=res, axes=axes); save(S); return S["pending"]
        e = resolve(S, p, res, kind); print("auto:", e["i"], kind, e["expr"], "mod", e["m"], e["coords"], "axes", axes)

def cmd_record(S, n, src):
    P = S["pending"]; S["last_axes"] = P["axes"]
    kind = corner(P["res"]["w"], P["res"]["e"], n); e = resolve(S, P["point"], P["res"], kind, src); S["pending"] = None
    print("recorded:", e["i"], kind, e["expr"], "mod", e["m"], "sigma", S["sigma"], "expanding", S["expanding"], "ideas", len(S["ideas"]))

if __name__ == "__main__":
    S = load()
    if sys.argv[1] == "next":
        P = cmd_next(S); r = P["res"]; save(S)
        print(f"CANDIDATE {r['expr']} mod {r['m']}  coords(X,Y,Z)={r['coords']}  w={r['w']} e={r['e']} period={r['period']} bound={r['derived_bound']}")
        print("terms:", ", ".join(map(str, r["terms"])))
    elif sys.argv[1] == "record":
        cmd_record(S, int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None); save(S)
    elif sys.argv[1] == "status":
        print(json.dumps(dict(sigma=S["sigma"], expanding=S["expanding"], n=S["count"], ideas=len(S["ideas"])), indent=1))
