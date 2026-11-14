import os as _os
_P=lambda *a:_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",*[x for x in a if x]))
"""v2: the idea space is a 3D grid of cells (X breadth, Y areas, Z depth).
Noise = interfering waves eta(r,t) = sum_i A_i sin(k_i . r - w_i t + phi_i), all drawn from os.urandom.
Disruption d(r,t) = |eta| / sum A_i in [0,1].
Outbound transfer to cell r': with prob d(r',t) the data cell is mutated in transit (creative noise).
Return transfer to sender at r: with prob d(r,t+1) the reply is corrupted; SHA-256 mismatch -> resend (error noise).
Checks: w works, e exact (derived period == observed) / partial (rules undershoot) / none, n novel (web).
worth = log2(bound/period) / length.  Novelty checked on the shortest equivalent form only."""
import os, sys, json, math, hashlib, itertools
sys.path.insert(0, _P("s3_waves_v2",""))
import engine1 as g
ST = _P("s3_waves_v2","state.json")
u, pick = g.u, g.pick
BLK = ["fib", "luc", "tri", "sq", "ds"]
LIM = {"X": (0, 4), "Y": (1, 3), "Z": (0, 3)}

# ---------- wave field ----------
def new_waves(n=3):
    W = []
    for _ in range(n):
        v = [u()*2-1 for _ in range(3)]; nv = math.sqrt(sum(a*a for a in v)) or 1
        lam = 1.5 + 4*u()                                # wavelength in cell units
        W.append(dict(k=[2*math.pi/lam*a/nv for a in v], om=0.3+1.2*u(), phi=2*math.pi*u(), A=0.5+u()))
    return W
def d(W, r, t):
    eta = sum(w["A"]*math.sin(sum(ki*ri for ki, ri in zip(w["k"], r)) - w["om"]*t + w["phi"]) for w in W)
    return abs(eta) / sum(w["A"] for w in W)

# ---------- shortest form ----------
SMALL = [dict(base=b, ops=[]) for b in BLK] + \
        [dict(base=a, ops=[["comp", b]]) for a in BLK for b in BLK] + \
        [dict(base=a, ops=[[k, b]]) for k in ("add", "mul") for a, b in itertools.combinations_with_replacement(BLK, 2)]
def size(p): return 1 + len(p["ops"])
_canon = {}
def shortest(p, s):
    m = p["m"]
    if m not in _canon:
        _canon[m] = {}
        for q in sorted(SMALL, key=size):
            q = dict(q, m=m); ss, L = g.world(g.tree(q), m, N=300)
            if L and len(ss) >= 300: _canon[m].setdefault(tuple(ss[:300]), q)
    q = _canon[m].get(tuple(s[:300])) if len(s) >= 300 else None
    return q if q and size(q) < size(p) else p

# ---------- mutation in transit ----------
def mutate(p, k):
    q = json.loads(json.dumps(p)); notes = []
    for _ in range(k):
        r = u()
        if r < .45 and (q["ops"] or True):
            slots = ["base"] + list(range(len(q["ops"]))); s = pick(slots); nb = pick(BLK)
            if s == "base": notes.append(f"base {q['base']}->{nb}"); q["base"] = nb
            else: notes.append(f"block {q['ops'][s][1]}->{nb}"); q["ops"][s][1] = nb
        elif r < .7 and any(o[0] in ("add", "mul") for o in q["ops"]):
            i = pick([i for i, o in enumerate(q["ops"]) if o[0] in ("add", "mul")])
            q["ops"][i][0] = "mul" if q["ops"][i][0] == "add" else "add"; notes.append("op flip")
        else:
            nm = min(16, max(4, q["m"] + pick([-1, 1]))); notes.append(f"m {q['m']}->{nm}"); q["m"] = nm
    return q, notes

def within(p):
    x, y, z = g.coords(p); return LIM["X"][0] <= x <= LIM["X"][1] and LIM["Y"][0] <= y <= LIM["Y"][1] and LIM["Z"][0] <= z <= LIM["Z"][1]

def evaluate(p):
    E = g.tree(p); tr = []; B = g.bound(E, p["m"], tr); s, L = g.world(E, p["m"])
    unreach = len(s) < 60
    if unreach: return dict(kind="UNREACHABLE", s=s, L=None, B=B, tr=tr)
    if L is None: return dict(kind="CONTRADICTION" if (B and len(s) >= 3*B) else "FALSE", s=s, L=None, B=B, tr=tr)
    if B is None: e = "none"
    elif B == L: e = "exact"
    elif B % L == 0: e = "partial"
    else: return dict(kind="CONTRADICTION", s=s, L=L, B=B, tr=tr)
    return dict(kind={"exact": "EXPLAINED", "partial": "UNDERSHOOT", "none": "GAP-candidate"}[e], s=s, L=L, B=B, tr=tr, e=e)

def worth(p, res):
    if res.get("e") != "partial": return 0.0
    return math.log2(res["B"] / res["L"]) / size(p)

def load():
    if os.path.exists(ST): return json.load(open(ST))
    return dict(t=0, waves=new_waves(), sigma={"X": .5, "Y": .5, "Z": .5}, eta=.25, K=3, cur=None, best=None, expanding=False,
                fails=0, log=[], pending=None, checked={}, ideas=[], resends=0)
def save(S): json.dump(S, open(ST, "w"), indent=1)
def key(p, s): return f"m{p['m']}:" + ",".join(map(str, s[:24]))

def transfer(S):
    """One send + return. Returns (point, result, note) or None if nothing needs a web check."""
    src = S["best"]["point"] if S["expanding"] else (S["cur"] or dict(base=pick(BLK), m=pick(list(range(5, 13))), ops=[]))
    ax = pick(["X", "Y", "Z"], [S["sigma"][a] for a in "XYZ"]); sign = +1 if (S["expanding"] or u() < .6) else -1
    q = g.move(src, ax, sign) or g.move(src, ax, +1) or src
    S["t"] += 1; t = S["t"]
    dest = list(g.coords(q)); dist = d(S["waves"], dest, t)
    notes = []
    if u() < dist:                                    # outbound: wave hits the data cell in transit
        q, notes = mutate(q, 1 + int(2*dist))
    if not within(q): return dict(point=q, kind="OUT-OF-GRID", d=round(dist, 3), notes=notes, ax=ax)
    res = evaluate(q)
    # return trip to sender: reply may be corrupted; hash check -> resend until clean
    reply = json.dumps([res["kind"], res["L"], res["B"], res["s"][:24]]); h = hashlib.sha256(reply.encode()).hexdigest()
    back = d(S["waves"], list(g.coords(src)), t+1); tries = 0
    while True:
        tries += 1; got = reply
        if u() < back: got = reply.replace(",", ";", 1)  # corrupted in transit
        if hashlib.sha256(got.encode()).hexdigest() == h: break
        S["resends"] += 1; back = d(S["waves"], list(g.coords(src)), t+1+tries)
    canon = shortest(q, res["s"]) if res["kind"] not in ("FALSE", "UNREACHABLE", "CONTRADICTION") else q
    shorter = canon is not q
    if shorter: q = dict(canon, m=q["m"]); res = evaluate(q)
    return dict(point=q, res=res, kind=res["kind"], d=round(dist, 3), back=round(back, 3), resends=tries-1, notes=notes, ax=ax,
                shorter=shorter, worth=worth(q, res), expr=g.show(g.tree(q)), m=q["m"], coords=g.coords(q))

def adapt(S, ax, kind):
    if kind == "EXPLAINED": S["sigma"][ax] = min(.9, S["sigma"][ax]*(1+S["eta"]))
    if kind == "FALSE":     S["sigma"][ax] = max(.1, S["sigma"][ax]*(1-S["eta"]))

def step_until_pending(S, max_steps=200):
    for _ in range(max_steps):
        T = transfer(S); kind = T["kind"]
        entry = {k: T.get(k) for k in ("kind", "expr", "m", "coords", "d", "back", "resends", "notes", "ax", "shorter", "worth")}
        entry["t"] = S["t"]
        if "res" in T: entry.update(L=T["res"]["L"], B=T["res"]["B"])
        adapt(S, T["ax"], kind)
        if kind == "UNDERSHOOT" and T["worth"] < 0.3: kind = entry["kind"] = "LOW-WORTH"
        if kind == "UNDERSHOOT" and S["expanding"] and T["worth"] <= S["best"]["worth"] + 1e-9: kind = entry["kind"] = "NO-GAIN"
        if kind in ("UNDERSHOOT", "GAP-candidate"):
            k = key(T["point"], T["res"]["s"])
            if k in S["checked"]:
                entry["novel"] = S["checked"][k]; entry["note"] = "already searched"
                S["log"].append(entry); decide(S, T, S["checked"][k]); continue
            S["pending"] = dict(T=dict(point=T["point"], res=dict(L=T["res"]["L"], B=T["res"]["B"], s=T["res"]["s"][:40], e=T["res"].get("e"),
                                      tr=T["res"]["tr"]), kind=kind, worth=T["worth"], expr=T.get("expr"), ax=T["ax"]), entry=entry, key=k)
            return S["pending"]
        S["log"].append(entry)
        if S["expanding"]:
            S["fails"] += 1
            if S["fails"] >= S["K"]: finish(S)
        elif kind == "EXPLAINED": S["cur"] = T["point"]
    return None

def finish(S):
    S["ideas"].append(S["best"]); S["expanding"] = False; S["fails"] = 0; S["cur"] = None; S["best"] = None

def decide(S, T, novel):
    kind = T["kind"]; w = T["worth"]
    corner = ("DISCOVERY" if novel else "KNOWN") if kind == "UNDERSHOOT" else ("DISCOVERY(no rule)" if novel else "GAP")
    if S["expanding"]:
        if novel and w > S["best"]["worth"]: S["best"] = dict(point=T["point"], worth=w, expr=T["expr"], corner=corner, res=T["res"]); S["fails"] = 0
        else:
            S["fails"] += 1
            if S["fails"] >= S["K"]: finish(S)
    elif novel:
        S["expanding"] = True; S["best"] = dict(point=T["point"], worth=w, expr=T["expr"], corner=corner, res=T["res"]); S["fails"] = 0
    else: S["cur"] = T["point"]
    return corner

if __name__ == "__main__":
    S = load()
    if sys.argv[1] == "next":
        P = S["pending"] or step_until_pending(S); save(S)
        if not P: print("no candidate"); sys.exit()
        T = P["T"]; print(f"CANDIDATE {T['expr']} mod {T['point']['m']} | {T['kind']} period {T['res']['L']} bound {T['res']['B']} worth {T['worth']:.3f}")
        print("terms:", ", ".join(map(str, T["res"]["s"][:20])))
    elif sys.argv[1] == "record":
        P = S["pending"]; novel = int(sys.argv[2]); src = sys.argv[3] if len(sys.argv) > 3 else None
        S["checked"][P["key"]] = novel; c = decide(S, P["T"], novel)
        P["entry"].update(novel=novel, corner=c, source=src); S["log"].append(P["entry"]); S["pending"] = None; save(S)
        print("recorded", c, "| expanding", S["expanding"], "| best", S["best"] and (S["best"]["expr"], S["best"]["point"]["m"], round(S["best"]["worth"], 3)), "| ideas", len(S["ideas"]))
    elif sys.argv[1] == "log":
        for e in S["log"]: print(e["t"], e["kind"], e.get("corner", ""), e["expr"], "mod", e["m"], "L", e.get("L"), "B", e.get("B"), "d", e["d"], "mut", e["notes"], "short", e["shorter"])
        print("sigma", S["sigma"], "resends", S["resends"])
