"""The loop, closed: a gap in the rules makes the engine look for a rule, keep it only if it survives held-out data, and use it next time.

  gap     the rules predict X, the world shows Y (world = exact tables, no rule used)
  mine    template LADDER: for k >= k0, period(chain, p^k) = A * r^(k-k0), r in {1, p}. Fitted on the first values only.
  hold    the next value must match, or the candidate is logged as rejected
  store   rules.json holds rule = (statement, WHAT, WHERE, WHY, WHO, status, evidence). predict() reads it, so the same gap does not reopen.
  refute  a later value that disagrees marks the rule REFUTED, and the data so far can mine a replacement
  later   the last value of each series is never used for mining or hold-out. Survival on it is the honest score.
  null    the same pipeline on scrambled periods, to see how many rules it would keep if nothing were there
  fact    a gap no ladder covers is kept as a finite fact: one chain, one prime power, one period. It is exact but predicts nothing new.

Status of a rule: CONJECTURE until a written proof is linked in PROVED. A mined rule is a pattern that held on the values tested, nothing more.
It covers only primes with enough values, so at large primes the gap stays open. It does not generalise across primes: Theorem 2 in PROOFS.md
was derived by Claude from a table, not by this miner. The LADDER template was also written by someone who knew Theorem 1 exists, so finding
that theorem again checks the pipeline. It is not independent evidence of what the miner can discover.
    python loop.py [--web]       writes rules.json and loop_results.json. --web also asks novelty.py about each gap-closing family."""
import json, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RULES = os.path.join(HERE, "rules.json")
SEQ = {"F": ((1, 1), (0, 1)), "L": ((1, 1), (2, 1)), "P": ((2, 1), (0, 1)), "Q": ((2, 1), (2, 2)), "T": ((1, 1, 1), (0, 0, 1))}
NAME = {"F": "Fibonacci", "L": "Lucas", "P": "Pell", "Q": "Pell-Lucas", "T": "tribonacci"}
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
CAP = 400000
PROVED = {"LL:5": "s8_proofs/PROOFS.md Theorem 1 (not reviewed by a mathematician)", "LF:5": "s8_proofs/PROOFS.md Theorem 1 (not reviewed by a mathematician)"}
_t = {}
def table(s, q):
    """One cycle of s mod q, or None if it is longer than CAP."""
    if q == 1: return [0]
    if (s, q) in _t: return _t[(s, q)]
    co, init = SEQ[s]; st0 = tuple(x % q for x in init); st = st0; out = []
    while True:
        out.append(st[0]); nxt = sum(c*x for c, x in zip(co, reversed(st))) % q; st = st[1:] + (nxt,)
        if st == st0: break
        if len(out) > CAP: out = None; break
    _t[(s, q)] = out
    return out
def factor(n):
    out, p = {}, 2
    while p*p <= n:
        while n % p == 0: out[p] = out.get(p, 0) + 1; n //= p
        p += 1
    if n > 1: out[n] = out.get(n, 0) + 1
    return out
def minimal(v):
    n = len(v); T = n
    for p in factor(n):
        while T % p == 0 and all(v[i] == v[(i + T//p) % n] for i in range(n)): T //= p
    return T
def bound(chain, m):
    """R_COMP: the cycle of the innermost block mod the cycle of the next one out, and so on. None if too large."""
    q = m
    for s in chain:
        t = table(s, q)
        if t is None: return None
        q = len(t)
    return q
def world(chain, m):
    """(exact period, R_COMP bound) from tables, or None."""
    B = bound(chain, m)
    if B is None: return None
    qs = [m]
    for s in chain[:-1]: qs.append(len(table(s, qs[-1])))
    v = table(chain[-1], qs[-1])
    for s, q in zip(reversed(chain[:-1]), reversed(qs[:-1])):
        t = table(s, q); v = [t[x % len(t)] for x in v]
    return minimal(v), B
def series(chain, p, kmax=12):
    out = []
    for k in range(1, kmax+1):
        r = world(chain, p**k)
        if r is None: break
        out.append(dict(k=k, T=r[0], B=r[1]))
    return out
def fit(points, p):
    """Longest tail of the points following T = A r^(k-k0), r in {1, p}, with at least two steps. Returns (k0, A, r) or None."""
    if len(points) < 3: return None
    for i in range(len(points) - 2):
        base = points[i]
        for r in (p, 1):
            if all(x["T"] == base["T"] * r**(x["k"] - base["k"]) for x in points[i:]): return base["k"], base["T"], r
    return None
def value(rule, k): return rule["A"] * rule["r"]**(k - rule["k0"])
def statement(chain, p, k0, A, r):
    expr = "".join(c + "(" for c in chain) + "n" + ")"*len(chain)
    return f"{expr} mod {p}^k has exact period {A}" + (f"*{p}^(k-{k0})" if r != 1 else "") + f" for k >= {k0}"
def mine(data, label="real"):
    """data: {(chain, p): series}. Returns (rules, rejected, tests on the last value)."""
    rules, rejected = {}, []
    for (chain, p), s in data.items():
        if len(s) < 4: continue
        use = s[:-2] if len(s) >= 5 else s[:-1]
        f = fit(use, p)
        if f is None: continue
        k0, A, r = f
        tail = [x for x in use if x["k"] >= k0]
        if all(x["T"] == x["B"] for x in tail): continue       # R_COMP is already right here: no gap, no rule
        cand = dict(id=f"{chain}:{p}", chain=chain, p=p, k0=k0, A=A, r=r)
        hold = s[len(use)]
        if value(cand, hold["k"]) != hold["T"]:
            rejected.append(dict(cand, why=f"hold-out k={hold['k']}: rule says {value(cand, hold['k'])}, world {hold['T']}")); continue
        first = next(x for x in tail if x["T"] != x["B"])
        cand.update(statement=statement(chain, p, k0, A, r), what=f"period of the composition on powers of {p}", where=f"k >= {k0}, tested to k = {s[-1]['k']}",
                    why=f"closes a gap: at k = {first['k']} R_COMP predicts {first['B']}, the world shows {first['T']}", who=f"mined by s9_loop/loop.py ({label}) from tables; proof: {PROVED.get(f'{chain}:{p}', 'none')}",
                    status="PROVED" if f"{chain}:{p}" in PROVED else "CONJECTURE", mined_on=[x["k"] for x in use], holdout=hold["k"])
        rules[cand["id"]] = cand
    return rules, rejected
def reconcile(rules, rule_id, s, p):
    """A later value disagreed: mark the rule REFUTED, then try to mine a replacement from all the values now known. Returns the replacement or None."""
    r = rules[rule_id]; r["status"] = "REFUTED"
    f = fit(s, p)
    if f is None or all(x["T"] == x["B"] for x in s if x["k"] >= f[0]): return None
    k0, A, q = f
    new = dict(r, k0=k0, A=A, r=q, status="CONJECTURE", statement=statement(r["chain"], p, k0, A, q), who=r["who"] + "; re-mined after refutation")
    rules[rule_id] = new
    return new
def facts_from(data, rules):
    """Every gap the ladders leave open, as an exact finite fact."""
    F = {}
    for (chain, p), s in data.items():
        r = rules.get(f"{chain}:{p}")
        for x in s:
            if x["T"] != x["B"] and not (r and r.get("status") != "REFUTED" and x["k"] >= r["k0"]): F[f"{chain}:{p}^{x['k']}"] = x["T"]
    return F
def predict(rules, chain, m, facts=None):
    """Period predicted by the store: per prime power use a fact or a rule if one applies, else R_COMP; R_CRT combines them. None if a bound is too large."""
    L = 1; used = []
    for p, e in factor(m).items():
        r = rules.get(f"{chain}:{p}"); fact = (facts or {}).get(f"{chain}:{p}^{e}")
        if fact is not None:
            L = math.lcm(L, fact); used.append("fact")
        elif r and r.get("status") != "REFUTED" and e >= r["k0"]:
            L = math.lcm(L, value(r, e)); used.append(r["id"])
        else:
            B = bound(chain, p**e)
            if B is None: return None, used
            L = math.lcm(L, B)
    return L, used
def scramble(data, seed="loop-null"):
    """Each period replaced by a random divisor of its bound: the same kind of numbers, with no pattern across k."""
    rng = random.Random(seed); out = {}
    for key, s in data.items():
        out[key] = []
        for x in s:
            ds = [d for d in range(1, min(x["B"], 2000)+1) if x["B"] % d == 0]
            out[key].append(dict(x, T=x["B"] // rng.choice(ds)))
    return out
def learned_worth(rules, chain, m):
    """Surprise left after the rule is known: log2(what the rules predict / what the world shows) per block. 0 means nothing here is news any more."""
    T = world(chain, m)[0]; B = bound(chain, m); pred, _ = predict(rules, chain, m)
    return math.log2(B / T) / len(chain), math.log2(pred / T) / len(chain)
def web_check(rules):
    """Asks novelty.py about each family of gap-closing rules. Candidate pages are for a person to open: code cannot judge them."""
    sys.path.insert(0, os.path.join(ROOT, "s7_novelty"))
    import novelty as N
    cache = N.Cache(); seen = {}
    for r in rules.values():
        names = sorted({NAME[c] for c in r["chain"]})
        key = "+".join(names)
        if key not in seen:
            must = [n.split("-")[0] for n in names] + [("period", "periodic", "pisano"), ("composition", "composite", "nested", "iterated", "subscript")]
            q = f"period of {' '.join(names)} numbers composition modulo prime powers"
            res = {"crossref": N.crossref(q, must, cache), "openalex": N.openalex(q, must, cache), "zbmath": N.zbmath(q, must, cache), "stackexchange": N.stackexchange(q, must, cache)}
            st = {k: v["status"] for k, v in res.items()}
            seen[key] = dict(query=q, sources=st, n=None if "UNCHECKED" in st.values() or "REVIEW" in st.values() else 1, candidates=[h.get("url") for v in res.values() for h in v.get("hits", [])][:10])
        r["novelty"] = seen[key]
    return seen
def cube(rule):
    """The (w, e, n) corner of a rule. e = 1 only with a written proof: passing tests is w, not e."""
    w, e, n = 1, int(rule["status"] == "PROVED"), (rule.get("novelty") or {}).get("n")
    if n is None: return "UNDECIDED (w=1, e=%d, n unknown)" % e
    return {(1, 1): "NEW", (1, 0): "KNOWN", (0, 1): "DISCOVERY", (0, 0): "GAP"}[(e, n)]
def main(web=False):
    t0 = time.time(); chains = [a+b for a in SEQ for b in SEQ]
    data = {}
    for c in chains:
        for p in PRIMES:
            data[(c, p)] = series(c, p)
            _t.clear()
    cases = [(c, p, x) for (c, p), s in data.items() for x in s]
    print(f"{len(cases)} (chain, p^k) cases; R_COMP wrong on {sum(x['T'] != x['B'] for _, _, x in cases)}", flush=True)
    rules, rejected = mine(data)
    null_rules, null_rej = mine(scramble(data), "null")
    print(f"mined {len(rules)} rules, rejected at hold-out {len(rejected)}; on scrambled data: {len(null_rules)} rules, {len(null_rej)} rejected", flush=True)
    # scores on values not used to make the rule
    later = []; gapcases = []
    for r in rules.values():
        s = data[(r["chain"], r["p"])]; unseen = [x for x in s if x["k"] > r["holdout"]]
        if unseen:
            ok = all(value(r, x["k"]) == x["T"] for x in unseen)
            later.append((r["id"], ok, [x["k"] for x in unseen]))
            r["later"] = dict(k=[x["k"] for x in unseen], survived=ok)
            if not ok: r["status"] = "REFUTED"; r["who"] += "; refuted by a later value"
        for x in unseen:
            if x["T"] != x["B"]: gapcases.append((r["id"], x["k"], value(r, x["k"]) == x["T"]))
    print(f"later values (never used): {len(later)} rules tested, survived {sum(o for _, o, _ in later)}; refuted {[i for i, o, _ in later if not o]}", flush=True)
    print(f"later values where R_COMP is wrong: {len(gapcases)}, rule exact on {sum(o for _, _, o in gapcases)}", flush=True)
    # read-back: every case again, and then composite moduli nothing was mined on
    facts = facts_from(data, rules)
    for label, rr, ff in (("empty store", {}, None), ("rules only", rules, None), ("rules and facts", rules, facts)):
        ok = bad = 0
        for c, p, x in cases:
            pred, _ = predict(rr, c, p**x["k"], ff)
            ok += pred == x["T"]; bad += pred != x["T"]
        print(f"  all prime-power cases, {label}: exact {ok}, wrong {bad}", flush=True)
        _t.clear()
    comp = []
    for m in range(61, 201):
        if len(factor(m)) < 2: continue
        for c in chains:
            r = world(c, m)
            if r is None: continue
            comp.append((c, m, r[0], predict({}, c, m)[0], predict(rules, c, m)[0], bool(predict(rules, c, m)[1]), predict(rules, c, m, facts)[0]))
        _t.clear()
    print(f"composite m = 61..200: {len(comp)} cases | exact: empty store {sum(x[3] == x[2] for x in comp)}, rules only {sum(x[4] == x[2] for x in comp)}, rules and facts {sum(x[6] == x[2] for x in comp)} | a rule fired on {sum(x[5] for x in comp)}, exact there: empty {sum(x[3] == x[2] for x in comp if x[5])}, rules {sum(x[4] == x[2] for x in comp if x[5])}", flush=True)
    if web: print("web:", {k: v["sources"] for k, v in web_check(rules).items()}, flush=True)
    for r in rules.values(): r["corner"] = cube(r)
    res = dict(cases=len(cases), rcomp_wrong=sum(x["T"] != x["B"] for _, _, x in cases), rules=len(rules), rejected=rejected, null_rules=len(null_rules), null_rejected=len(null_rej), later_tested=len(later), later_survived=sum(o for _, o, _ in later), refuted=[i for i, o, _ in later if not o],
               later_gap_cases=len(gapcases), later_gap_exact=sum(o for _, _, o in gapcases), facts=len(facts), composite=dict(cases=len(comp), empty=sum(x[3] == x[2] for x in comp), rules=sum(x[4] == x[2] for x in comp), rules_and_facts=sum(x[6] == x[2] for x in comp), fired=sum(x[5] for x in comp), fired_empty=sum(x[3] == x[2] for x in comp if x[5]), fired_rules=sum(x[4] == x[2] for x in comp if x[5])),
               primes_with_rules=sorted({r["p"] for r in rules.values()}), secs=round(time.time()-t0, 1))
    json.dump(dict(rules=rules, facts=facts), open(RULES, "w"), indent=1); json.dump(res, open(os.path.join(HERE, "loop_results.json"), "w"), indent=1)
    print("rules by prime:", {p: sum(r["p"] == p for r in rules.values()) for p in PRIMES}, "secs", res["secs"], flush=True)
    for i in ("LL:5", "LF:5"):
        if i in rules: print(" ", rules[i]["statement"], "|", rules[i]["status"], "|", rules[i]["why"])
    return res
if __name__ == "__main__":
    main("--web" in sys.argv)
