import os as _os
_P=lambda *a:_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",*[x for x in a if x]))
"""Rulebook + return to sender. Rules are assumed always right.
Every answer must be a chain of rule applications; every rule carries Who/What/Where/Why.
How is produced per step (which rule, which part, which substitution)."""
import json, hashlib, re, sys, urllib.request

W = "https://en.wikipedia.org/wiki/"
RULES_ALL = {
 "N0":  dict(lhs=None, rhs=None, kind="type", what="0 is a natural number",
             who=W+"Peano_axioms", where="natural numbers", why="axiom: gives a starting value"),
 "D1":  dict(lhs=("1",), rhs=("S",("0",)), kind="rewrite", what="1 = S(0)",
             who=W+"Proofs_involving_the_addition_of_natural_numbers", where="natural numbers", why="definition of the name 1"),
 "D2":  dict(lhs=("2",), rhs=("S",("S",("0",))), kind="rewrite", what="2 = S(S(0))",
             who=W+"Peano_axioms", where="natural numbers", why="definition of the name 2"),
 "A1":  dict(lhs=("+","?a",("0",)), rhs="?a", kind="rewrite", what="a + 0 = a",
             who=W+"Proofs_involving_the_addition_of_natural_numbers", where="any natural a", why="addition, base case"),
 "A2":  dict(lhs=("+","?a",("S","?b")), rhs=("S",("+","?a","?b")), kind="rewrite", what="a + S(b) = S(a + b)",
             who=W+"Proofs_involving_the_addition_of_natural_numbers", where="any naturals a, b", why="addition, step case"),
}

def show(t):
    if isinstance(t, str): return t[1:]
    if len(t) == 1: return t[0]
    if t[0] == "S": return f"S({show(t[1])})"
    return f"({show(t[1])} {t[0]} {show(t[2])})"

def match(p, t, s):
    if isinstance(p, str):
        if p in s: return s if s[p] == t else None
        return {**s, p: t}
    if isinstance(t, str) or len(p) != len(t) or p[0] != t[0]: return None
    for a, b in zip(p[1:], t[1:]):
        s = match(a, b, s)
        if s is None: return None
    return s

def subst(t, s):
    if isinstance(t, str): return s[t]
    return (t[0],) + tuple(subst(x, s) for x in t[1:])

def step(t, rules, path="whole"):
    """One rewrite, outermost first. Returns (new_term, record) or None."""
    for rid, r in rules.items():
        if r["kind"] != "rewrite": continue
        s = match(r["lhs"], t, {})
        if s is not None:
            new = subst(r["rhs"], s)
            how = f"apply {rid} to {path} [{show(t)}]" + (f" with " + ", ".join(f"{k[1:]}={show(v)}" for k, v in s.items()) if s else "")
            return new, dict(rule=rid, before=show(t), after=show(new), what=r["what"], how=how,
                             why=r["why"], who=r["who"], where=r["where"])
    for i, sub in enumerate(t[1:], 1):
        res = step(sub, rules, f"part {i} of {path}" if path != "whole" else f"part {i}")
        if res:
            new_sub, rec = res
            return t[:i] + (new_sub,) + t[i+1:], rec
    return None

def normalize(t, rules, limit=50):
    chain = []
    while len(chain) < limit:
        res = step(t, rules)
        if not res: break
        t, rec = res; chain.append(rec)
    return t, chain

def gaps(t):
    """Parts still containing an operator after no rule applies: these need a rule."""
    if isinstance(t, str) or len(t) == 1: return []
    out = [show(t)] if t[0] != "S" else []
    for x in t[1:]: out += gaps(x)
    return out

def prove_equal(lhs, rhs, rules):
    nl, cl = normalize(lhs, rules); nr, cr = normalize(rhs, rules)
    ok = nl == nr
    return dict(explained=ok, left_chain=cl, right_chain=cr, left_end=show(nl), right_end=show(nr),
                gaps=[] if ok else sorted(set(gaps(nl) + gaps(nr))))

def value(t):  # the world: just computes. It can say THAT, never WHY.
    if t[0] == "0": return 0
    if t[0] in ("1", "2"): return int(t[0])
    if t[0] == "S": return value(t[1]) + 1
    if t[0] == "+": return value(t[1]) + value(t[2])

def send(sender, lhs, rhs, rules):
    """Return to sender: the claim goes out, the reply comes back to the sender with
    (a) does it work (world check) and (b) can it be explained (rulebook derivation)."""
    works = value(lhs) == value(rhs)
    proof = prove_equal(lhs, rhs, rules)
    status = ("EXPLAINED" if proof["explained"] else "WORKS-BUT-UNEXPLAINED") if works else \
             ("CONTRADICTION: rulebook vs world" if proof["explained"] else "FALSE")
    reply = dict(to=sender, claim=f"{show(lhs)} = {show(rhs)}", works=works, status=status, **proof,
                 ask_web=[f"rule for '{g}' (definition of the operation in this form)" for g in proof["gaps"]])
    reply["hash"] = hashlib.sha256(json.dumps(reply, sort_keys=True).encode()).hexdigest()[:12]
    return reply

# ---------- a gap asks the web, for real ----------
PAGES = [W+"Proofs_involving_the_addition_of_natural_numbers", W+"Peano_axioms"]
def raw_url(u): return "https://en.wikipedia.org/w/index.php?title=" + u.rsplit("/", 1)[1] + "&action=raw"
def http_fetch(u):
    req = urllib.request.Request(u, headers={"User-Agent": "creativity-engine-novelty/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")
def parse_term(txt):
    """A term over 0, the variables a and b, S(...) and +. Returns the term, with variables as ?a, or None."""
    if re.sub(r"[ab0S()+\s]", "", txt): return None
    toks = re.findall(r"[ab0S()+]", txt); i = [0]
    def atom():
        if i[0] >= len(toks): raise ValueError
        t = toks[i[0]]; i[0] += 1
        if t in "ab": return "?" + t
        if t == "0": return ("0",)
        if t == "S":
            if i[0] >= len(toks) or toks[i[0]] != "(": raise ValueError
            i[0] += 1
        elif t != "(": raise ValueError
        e = expr()
        if i[0] >= len(toks) or toks[i[0]] != ")": raise ValueError
        i[0] += 1
        return ("S", e) if t == "S" else e
    def expr():
        e = atom()
        while i[0] < len(toks) and toks[i[0]] == "+":
            i[0] += 1; e = ("+", e, atom())
        return e
    try:
        e = expr()
    except ValueError: return None
    return e if i[0] == len(toks) else None
def equations(page):
    """Every line of a page that reads as one equation over the small grammar, left side an addition: (line, left term, right term)."""
    out = []
    for line in page.splitlines():
        t = line.replace("''", "").replace("&", "")
        t = re.sub(r"\\(textrm|mbox)\{.*?\}|<[^>]*>|\\\\|\|+|[,.:]|A[0-9]\b", " ", t)
        for m in re.finditer(r"([ab0S()+\s]+)=([ab0S()+\s]+)", t):
            l, r = parse_term(m.group(1)), parse_term(m.group(2))
            if l and r and l[0] == "+": out.append((line.strip(), l, r))
    return out
def inst(t, a, b):
    """The value of a term with numbers put in for a and b."""
    if t == "?a": return a
    if t == "?b": return b
    if t[0] == "0": return 0
    if t[0] == "S": return inst(t[1], a, b) + 1
    return inst(t[1], a, b) + inst(t[2], a, b)
def stuck_terms(t):
    """All subterms that still hold an operator."""
    if isinstance(t, str) or len(t) == 1: return []
    return ([t] if t[0] != "S" else []) + [x for y in t[1:] for x in stuck_terms(y)]
def ask_the_web(lhs, rhs, rules, fetch=http_fetch):
    """The gap goes to the pages. A found equation becomes a rule only if its left side fits a stuck term and the world agrees on a, b = 0..20.
    A page that cannot be reached leaves the gap open. Returns (rule id or None, report).
    This grammar covers Peano addition only; reading rules from a page in general is not solved."""
    stuck = stuck_terms(normalize(lhs, rules)[0]) + stuck_terms(normalize(rhs, rules)[0]); report = []
    for page in PAGES:
        try:
            body = fetch(raw_url(page))
        except OSError as e:
            report.append(dict(page=page, status="UNCHECKED", why=repr(e))); continue
        eqs = equations(body); report.append(dict(page=page, status="READ", equations=len(eqs)))
        for line, l, r in eqs:
            if not any(match(l, t, {}) is not None for t in stuck): continue
            if any(inst(l, a, b) != inst(r, a, b) for a in range(21) for b in range(21)):
                report.append(dict(page=page, rejected=line, why="the world disagrees")); continue
            rid = "W" + str(sum(k.startswith("W") for k in rules) + 1)
            rules[rid] = dict(lhs=l, rhs=r, kind="rewrite", what=line[:120], who=page, where="any naturals; checked on a, b = 0..20", why="found for the gap " + ", ".join(show(t) for t in stuck))
            report.append(dict(page=page, adopted=rid, line=line[:120]))
            return rid, report
    return None, report

def print_reply(r):
    print(f"\n=== reply to {r['to']}: {r['claim']} -> {r['status']} (works={r['works']})  #{r['hash']}")
    for side, ch in (("left", r["left_chain"]), ("right", r["right_chain"])):
        for i, c in enumerate(ch, 1):
            print(f"  {side} step {i}: {c['before']}  =>  {c['after']}")
            print(f"     WHAT:  {c['what']}\n     HOW:   {c['how']}\n     WHY:   {c['why']}\n     WHERE: {c['where']}\n     WHO:   {c['who']}")
    print(f"  ends: left {r['left_end']} | right {r['right_end']}")
    if r["gaps"]: print(f"  GAPS (no rule applies): {r['gaps']}\n  ask the web: {r['ask_web']}")

if __name__ == "__main__":
    one_plus_one, two = ("+", ("1",), ("1",)), ("2",)
    runs = {}
    # Case 1: full rulebook
    runs["full"] = send("generator", one_plus_one, two, RULES_ALL)
    # Case 2: step rule A2 missing
    no_a2 = {k: v for k, v in RULES_ALL.items() if k != "A2"}
    runs["missing_A2"] = send("generator", one_plus_one, two, no_a2)
    # Case 3: the gap really goes to the web pages. The rule it comes back with is the one used, so with no network the gap stays open
    if "--offline" in sys.argv:
        def down(u): raise OSError("offline")
        rid, report = ask_the_web(one_plus_one, two, no_a2, down)
    else:
        rid, report = ask_the_web(one_plus_one, two, no_a2)
    runs["rule_from_web"] = send("generator", one_plus_one, two, no_a2); runs["rule_from_web"]["web"] = report; runs["rule_from_web"]["rule_found"] = no_a2[rid]["what"] if rid else None
    print("web:", report)
    # Case 4: a false claim, 1+1 = 1
    runs["false_claim"] = send("generator", one_plus_one, ("1",), RULES_ALL)
    for r in runs.values(): print_reply(r)
    json.dump(runs, open(_P("s1_rulebook","replies.json"), "w"), indent=1)
