"""Every result the project reports, recomputed or re-read from its raw data. HANDOFF.md cites these by id and types no numbers of its own.
    python claims.py            checks every claim, writes CLAIMS.md, exits non-zero if one fails
    python claims.py --slow     also replays all logged wave runs and reruns the merge check
Both also rewrite PROMPT_PROGRESS.md (make_prompt.py), so the LLM prompt carries the same numbers.

Tags: COMPUTED came from code here. SOURCED came from a page that was opened. DERIVED is a proof written by Claude, with its steps checked by code and no review by a mathematician.
All computed results are in a test world the assistant built: integer sequences mod m."""
import glob, importlib, json, math, os, random, statistics as st, subprocess, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
for d in ("s4_merging", "s5_symmetry", "s6_patches", "s7_novelty", "s8_proofs", "s9_loop", "calibration", "s1_rulebook"):
    sys.path.insert(0, os.path.join(ROOT, d))
def J(*a): return json.load(open(os.path.join(ROOT, *a)))
CLAIMS = []
def claim(cid, tag, source):
    def deco(fn):
        CLAIMS.append((cid, tag, source, fn)); return fn
    return deco
def perm(a, b, shuffles, rng):
    obs = abs(st.mean(a) - st.mean(b)); pool = a + b; n = len(a); c = 0
    for _ in range(shuffles):
        rng.shuffle(pool)
        c += abs(sum(pool[:n])/n - sum(pool[n:])/len(b)) >= obs - 1e-12
    return (c + 1) / (shuffles + 1)

@claim("C01", "COMPUTED", "s1_rulebook/rulebook.py, replies.json")
def rulebook(slow):
    import rulebook as R
    one, two = ("+", ("1",), ("1",)), ("2",)
    full = R.send("x", one, two, R.RULES_ALL); no = {k: v for k, v in R.RULES_ALL.items() if k != "A2"}; gap = R.send("x", one, two, no); false = R.send("x", one, ("1",), R.RULES_ALL)
    web = J("s1_rulebook", "replies.json")["rule_from_web"]
    ok = full["status"] == "EXPLAINED" and gap["status"] == "WORKS-BUT-UNEXPLAINED" and gap["gaps"] == ["(S(0) + S(0))"] and false["status"] == "FALSE" and web["status"] == "EXPLAINED" and web["rule_found"]
    return ok, f"1+1=2 is explained by sourced rules. Without the step rule it works but is unexplained, with the gap {gap['gaps'][0]}. That gap went to a real web page, which gave the line {web['rule_found']!r}; the world agreed on a, b = 0..20, and the claim is then explained. 1+1=1 is false. With no network the gap stays open."

@claim("C02", "COMPUTED", "s4_merging/verify3.py, verify.json")
def merging(slow):
    v = J("s4_merging", "verify.json")
    no_proof = len(v["gap_world_periodic"]) + v["gap_world_not"]
    if slow:
        r = subprocess.run([sys.executable, "verify3.py"], cwd=os.path.join(ROOT, "s4_merging"), capture_output=True, text=True); v = J("s4_merging", "verify.json")
    return not v["proof_ne_world"] and v["tested"] == 572, f"Merging engine: of {v['tested']} random expressions, {v['proof_eq_world']} proved periods agree with brute force, {len(v['proof_ne_world'])} disagree, {len(v['world_too_short'])} could not be compared because the world was too short, and {no_proof} got no proof."

@claim("C03", "COMPUTED", "s5_symmetry/mult.py, mult_rows.json")
def mult(slow):
    M = J("s5_symmetry", "mult_rows.json"); a = sum(r["mult"] == r["true"] for r in M); b = sum(r["true"] < r["comp"] for r in M)
    return a == len(M), f"R_MULT reaches the exact period on {a} of {len(M)} F/L compositions with m = 2..60; on {b} of them R_COMP alone is too large."

@claim("C04", "COMPUTED", "s6_patches/why.py, checked here against tables")
def why(slow):
    import why as W, general as G
    ok = {}
    for lo, hi in ((2, 60), (61, 300)):
        n = c = 0
        for m in range(lo, hi+1):
            for f, F in (("fib", "F"), ("luc", "L")):
                for g, H in (("fib", "F"), ("luc", "L")):
                    n += 1; c += W.why_chain2(f, g, m)[0] == G.true_period(F, H, m)
        ok[(lo, hi)] = (c, n)
    a, b = ok[(2, 60)], ok[(61, 300)]
    return a[0] == a[1] and b[0] == b[1], f"Identity why-chain, Fibonacci and Lucas: exact on {a[0]} of {a[1]} for m = 2..60 and {b[0]} of {b[1]} for m = 61..300. It proves the period divides a value; exactness is by comparison."

@claim("C05", "COMPUTED", "s6_patches/why2.py, why2.json")
def why2(slow):
    R = J("s6_patches", "why2.json"); n = len(R); e = sum(r["why"] == r["true"] for r in R); low = sum(r["why"] < r["true"] for r in R); hard = [r for r in R if r["true"] < r["comp"]]; he = sum(r["why"] == r["true"] for r in hard)
    innerQ = sum(r["why"] != r["true"] and r["chain"][1] == "Q" for r in R)
    return low == 0, f"Why-chain generalised to Pell and Pell-Lucas: exact on {e} of {n} two-deep chains over F, L, P, Q (m = 2..60), never below the truth. Where R_COMP is too large it is exact on only {he} of {len(hard)}. Of the {n-e} misses, {innerQ} have Pell-Lucas as the inner sequence. Tribonacci is not covered."

@claim("C06", "COMPUTED", "s6_patches/sym2..sym9, sym9_depth2.json, sym9_depth3.json")
def ladder(slow):
    out = []; good = True; L = J("s6_patches", "symmetry_levels.json")
    for k in ("depth2", "depth3"):
        R = J("s6_patches", f"sym9_{k}.json"); prev = lambda r: min(x for x in (r["quot"], r["crt"], r["par"], r["zero"], r["cls"]) if x is not None)
        a = sum(r["comp"] == r["true"] for r in R); b = sum(prev(r) == r["true"] for r in R); base = lambda r: min(x for x in (prev(r), r["blk"]) if x is not None); c = sum(base(r) == r["true"] for r in R)
        fin = lambda r: min(x for x in (prev(r), r["blk"], r["blk2"]) if x is not None); d = sum(fin(r) == r["true"] for r in R); low = sum(fin(r) < r["true"] for r in R)
        good = good and low == 0; out.append(f"{k}: {len(R)} chains, R_COMP alone {a}, old ladder {b}, with R_BLOCK d=1 {c}, with d=2 {d}, below the truth {low}")
    m = L["depth3"]["misses"]; tw = {}
    for x in m:
        if x[1][-1] in "FL": tw[(x[0], x[1][:-1])] = tw.get((x[0], x[1][:-1]), 0) + 1
    pairs = sum(v == 2 for v in tw.values())
    return good, "; ".join(out) + f". These rules search computed tables; they do not derive from identities. Chains with a cycle over 20,000 are skipped. The {len(m)} old misses were all off by a factor of 2: {2*pairs} are twin pairs differing only in an innermost F or L, and {sum('T' in x[1] for x in m)} involve tribonacci."

@claim("C07", "COMPUTED", "s6_patches/sym9_tests.py, sym9_tests.json")
def block_tests(slow):
    T = J("s6_patches", "sym9_tests.json"); n, f, d = T["null"], T["fresh"], T["deeper"]
    return f["below"] == 0 and d["below"] == 0, f"R_BLOCK on scrambled outer functions passes {n['rate_d1']:.1%} of {n['trials']} trials at d=1 and {n['rate_d2']:.1%} at d=2, so it is not passing on anything. On fresh three-deep chains (m = 21..40) it is exact on {f['d2']} of {f['cases']}, and on four-deep chains (m = 2..12) on {d['d2']} of {d['cases']}, with {d['skipped']} too large to tabulate and {d.get('timed_out', 0)} over the time budget of {d.get('budget_s', '?')} s, which count neither way. Never below the truth."

@claim("C08", "COMPUTED", "s6_patches/runs/, the original 30 logs")
def waves_old(slow):
    D = {}
    for f in glob.glob(os.path.join(ROOT, "s6_patches", "runs", "*.jsonl")):
        rows = [json.loads(x) for x in open(f)]; D.setdefault(rows[0]["mode"], []).append(rows[-1]["finds_all"])
    rng = random.Random("claims"); p = perm(D["off"], D["base"], 20000, rng); q = perm(D["off"], D["polar"], 20000, rng)
    ok = all(len(D[m]) == 10 for m in D)
    if slow:
        import waves4 as W, contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            ok = ok and all(W.replay(f) for f in glob.glob(os.path.join(ROOT, "s6_patches", "runs", "*.jsonl")))
    return ok, f"The original 10 runs per mode: mean finds off {st.mean(D['off']):.1f}, base {st.mean(D['base']):.1f}, polar {st.mean(D['polar']):.1f}, with permutation p about {p:.2f} and {q:.2f} against off. Too few runs to decide, and with no control for the waves themselves. Superseded by C09."

@claim("C09", "COMPUTED", "s6_patches/PREREG_waves.md, waves_exp.py, runs_v2/, waves_exp.json")
def waves_new(slow):
    import hashlib, waves_exp as E
    sha = hashlib.sha256(open(os.path.join(ROOT, "s6_patches", "PREREG_waves.md"), "rb").read()).hexdigest()
    W = J("s6_patches", "waves_exp.json"); D = E.load(); F = {m: [r[2]["finds_all"] for r in D[m]] for m in E.MODES}
    same = all(abs(st.mean(F[m]) - W["per_mode"][m]["finds_mean"]) < 1e-9 for m in E.MODES); P = W["primary"]; R = J("s6_patches", "waves_exp_replay.json")
    if slow: R = dict(failed=[] if E.replay_all(4) else ["some"], replayed=250)
    M = W["per_mode"]
    ok = same and sha.startswith("4bdb24ca") and not R["failed"]
    t = lambda x: f"{x['diff']:+.2f} (95% CI {x['ci95'][0]:+.2f} to {x['ci95'][1]:+.2f}, Holm p {x['p_holm']:.3g})"
    return ok, f"Pre-registered, {M['off']['n']} runs per mode, all {R['replayed']} replay exactly. Waves vs the same noise with no wave structure: base {t(P[0])}; polar {t(P[1])}. Mutation vs none: {t(P[2])}. Mutation rates match: base {M['base']['mutations']:.1f} vs shuffled {M['shuffled']['mutations']:.1f}; polar {M['polar']['mutations']:.1f} vs shuffled {M['polar_shuffled']['mutations']:.1f}. So mutation helps, and no benefit from the wave structure was detected; the intervals still allow a gain of up to about 3 to 4 finds out of about 30."

@claim("C10", "COMPUTED", "tests/test_waves.py")
def channel(slow):
    import channel as C
    rng = random.Random(3); msg = '["EXPLAINED", 12]'; n = 2000; good = 0; res = 0
    for _ in range(n):
        got, k = C.send_back(msg, lambda t: .5, 0, rng.random); good += got == msg; res += k
    return good == n and res > 0, f"Return channel: {n} replies at corruption rate 0.5 needed {res} resends and all arrived intact. tests/test_waves.py shows that the same seed with and without return noise gives identical steps."

@claim("C11", "COMPUTED", "s7_novelty/hunt.py, hunt_results.json")
def hunt(slow):
    H = J("s7_novelty", "hunt_results.json"); F = H["families"]; c = {}
    for x in F: c[x["corner"]] = c.get(x["corner"], 0) + 1
    tabs = len({json.dumps(x["periods_m2"]) for x in F if x["periods_m2"]}); srcs = {k.split(":")[0] for x in F for k in x["sources"]}; size = {x["size"] for x in F if x["corner"] == "NEW"}
    un = sum(1 for x in F for v in x["sources"].values() if v == "UNCHECKED")
    return not H["table_disagreements"] and un == 0, f"Hunt: {H['expressions']} logged expressions, {H['searched_expressions']} of size 3 or less, forming {len(F)} classes with identical residues and {tabs} distinct period tables. KNOWN {c.get('KNOWN', 0)}, REVIEW {c.get('REVIEW', 0)}, NEW {c.get('NEW', 0)}, TRIVIAL {c.get('TRIVIAL', 0)}. Sources: {', '.join(sorted(srcs))}. NEW means every source answered with no candidate, so it is only 'not found by these searches'; all NEW classes have size {sorted(size)}, the arbitrary kind that is novel by absence. Most REVIEW candidates look like noise, and only a person can clear them. The proof engine and independent tables agree on every table."

@claim("C12", "COMPUTED", "s7_novelty/hunt_results.json")
def coincidence(slow):
    F = J("s7_novelty", "hunt_results.json")["families"]
    div = sorted(x["expr"] for x in F if x["oeis_compare"] and all(r["result"] == "DIVERGES" for r in x["oeis_compare"])); n = sum(r["result"] == "DIVERGES" for x in F for r in x["oeis_compare"]); a = sum(r["result"] == "AGREES" for x in F for r in x["oeis_compare"])
    return "fib(tri(sq(n)))" in div, f"OEIS term matches compared on every listed term: {a} agree over at least 30 terms and {n} diverge, so a 12-term match alone is weak evidence. Classes where every match diverged: {', '.join(div)}."

@claim("C13", "COMPUTED", "s7_novelty/novelty_cache.json, tables.py")
def a356550(slow):
    import novelty as N, tables as TB
    e = N.Cache().get("oeis-entry:A356550"); E = ("comp", "fib", ("blk", "fib")); table = [TB.period(E, m) for m in range(2, 64)]; r = N.compare(table, e["data"])
    return r["result"] == "AGREES", f"F(F(n)) period table: OEIS A356550 agrees on all {r['overlap']} terms compared, so that table is known. The entry gives only an upper bound, a(n) divides pi(pi(n))."

@claim("C14", "DERIVED", "s8_proofs/PROOFS.md, prove.py")
def proofs(slow):
    r = subprocess.run([sys.executable, "prove.py"], cwd=os.path.join(ROOT, "s8_proofs"), capture_output=True, text=True); last = [x for x in r.stdout.splitlines() if x.startswith("Theorem 2:")]
    return r.returncode == 0, f"Theorem 1 (exact periods of L(L(n)) and L(F(n)) mod 5^k) and Theorem 2 (an upper bound for odd prime powers with P = 4 mod 8) have written proofs. prove.py checks their steps, not the reasoning that joins them. {last[0] if last else ''}. Claude read Theorem 1 line by line and found no error. No mathematician has reviewed either."

@claim("C15", "COMPUTED", "s8_proofs/general.py, general.json")
def formula(slow):
    import general as G
    A = J("s8_proofs", "general.json"); ok = not A["errors"] and not A["m_errors"] and A["hidden_extra"] == 0
    bad = sum(G.predict_q(f, g, q)[0] != G.true_period(f, g, q) for q in range(2, 1000) if len(G.factor(q)) == 1 for f in "FL" for g in "FL")
    return ok and bad == 0, f"Conjecture 2, the exact period formula: 0 errors on {A['cases']} prime-power cases up to {A['pmax']} and {A['m_cases']} cases with m up to {A['mmax']}. The rule was written after seeing primes below 300, so {A['blind_cases']} cases with {A['blind_savings']} predicted savings were blind. A finite check, not a proof."

@claim("C16", "COMPUTED", "s8_proofs/odd_pattern.py, odd_pattern.json")
def odd(slow):
    A = J("s8_proofs", "odd_pattern.json")
    return not A["exceptions"], f"Odd-modulus pattern: {A['cases']} cases with odd m up to {A['mmax']}, {len(A['exceptions'])} exceptions. Not proved."

@claim("C17", "COMPUTED", "s9_loop/loop.py, rules.json, loop_results.json")
def miner(slow):
    R = J("s9_loop", "loop_results.json"); S = J("s9_loop", "rules.json"); c = R["composite"]; rules = S["rules"]
    st_ = rules["LL:5"]["statement"]
    return R["later_survived"] == R["later_tested"] and "6*5^(k-2)" in st_, f"The miner, from tables alone, kept {R['rules']} rules at primes {R['primes_with_rules']}, and all {R['later_survived']} survived values never used; {R['null_rules']} rules on scrambled data. It rediscovered '{st_}'. R_COMP is wrong on {R['rcomp_wrong']} of {R['cases']} prime-power cases. Composite m = 61..200 ({c['cases']} cases, never mined): exact with an empty store {c['empty']}, with rules {c['rules']}, with rules and {R['facts']} finite facts {c['rules_and_facts']}. Rules are conjectures unless a proof is linked. n is small, and it finds nothing at primes above 5. Its template was written by someone who knew Theorem 1 exists, so the rediscovery checks the pipeline and is not independent evidence. The criterion in Theorem 2 came from Claude reading a table, not from the miner."

@claim("C18", "COMPUTED", "s8_proofs/search_theorem.py, search_theorem.json, opened_pages.json")
def search(slow):
    S = J("s8_proofs", "search_theorem.json"); O = J("s8_proofs", "opened_pages.json")
    return not any(p["states_theorem"] for p in O["pages"]), f"Novelty of the theorems: {len(S['queries'])} queries through novelty.py on 6 sources, {len(O['web_searches_by_agent'])} agent web searches, {len(O['pages'])} pages opened at least in part. None states these periods. {len(O['not_read'])} pages could not be read and count as not checked. Not found does not mean new; the results are elementary and may be known."

@claim("C19", "SOURCED", "s8_proofs/opened_pages.json")
def sourced(slow):
    O = J("s8_proofs", "opened_pages.json"); ok = any("lengyel" in p["url"] for p in O["pages"])
    return ok, "Lemma V of PROOFS.md (v5(F(n)) = v5(n), and 5 never divides L(n)) is Lemma 1 of T. Lengyel, Fibonacci Quarterly 33.3 (1995), read in full."

@claim("C20", "COMPUTED", "calibration/ledger.py, ledger.jsonl")
def calibration(slow):
    import ledger as K
    ok, at = K.verify(); s = K.score()
    tail = f"Brier {s['brier']:.3f} (always saying 0.5 scores 0.25); mean confidence {s['mean_conf']:.2f}, hit rate {s['hit_rate']:.2f}" if s["resolved"] else "none resolved"
    return ok, f"Prediction ledger: {s['committed']} predictions hashed before their checks, {s['resolved']} resolved, {len(s['open'])} open, {s['voided']} voided. {tail}. Small sample, all from one session and mostly on checks the same author designed, so this is a weak signal."

def main():
    slow = "--slow" in sys.argv; fails = 0; lines = ["# Claims", "", "Generated by `python claims.py`. Do not edit by hand: change the code or the data, then rerun.", "", f"Checked {time.strftime('%Y-%m-%d')}. All COMPUTED results are in a test world the assistant built (integer sequences mod m).", ""]
    for cid, tag, source, fn in CLAIMS:
        t0 = time.time()
        try:
            ok, text = fn(slow)
        except Exception as e:
            ok, text = False, f"could not check: {e!r}"
        fails += not ok
        print(("PASS " if ok else "FAIL ") + f"{cid} [{tag}] {text[:150]} ({time.time()-t0:.1f}s)", flush=True)
        lines.append(f"- **{cid}** {tag}{'' if ok else ' **CHECK FAILED**'}. {text} Source: `{source}`.")
    open(os.path.join(ROOT, "CLAIMS.md"), "w").write("\n".join(lines) + "\n")
    print("ALL CLAIMS CHECKED" if not fails else f"{fails} CLAIMS FAILED")
    try:
        import make_prompt; make_prompt.write()
    except Exception as e:
        print(f"PROMPT_PROGRESS.md not rewritten: {e!r}"); fails += 1
    return fails
if __name__ == "__main__":
    sys.exit(1 if main() else 0)
