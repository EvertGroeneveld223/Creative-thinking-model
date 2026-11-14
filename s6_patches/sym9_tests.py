"""Does R_BLOCK mean anything, or would it pass on anything?
  null   : the 43 old misses with G scrambled (same multiset of values, random positions). The rule should now rarely find a period below the bound.
  fresh  : three-deep chains on m = 21..40, never used while building the rule.
  deeper : four-deep chains on m = 2..12.
A case (chain, m) gets BUDGET seconds. One over it is reported as timed out, never as a hit or a miss. (A first run spent 20 CPU hours on one chain.)
The true period comes from tables here, independently of the rule. The rule is sound by construction, so `below true` must stay 0.
    python sym9_tests.py     writes sym9_tests.json"""
import itertools, json, math, multiprocessing as mp, random, signal, sym2, sym9, time
from sym2 import cycle, vals, divisors
from sym4 import tower
def true_period(chain, m):
    T = tower(chain, m)
    if T is None: return None
    mods, comp, seqs = T; s = seqs[0]
    return next(h for h in divisors(comp) if all(s[i] == s[(i+h) % comp] for i in range(comp))), comp
def scrambled(chain, m, rng, classes):
    T = tower(chain, m); mods, comp, seqs = T; q = mods[-1]; inner = seqs[len(chain)-1]
    G = sym9.outer_table(chain, m, mods); rng.shuffle(G)
    for h in divisors(comp):
        if h == comp: return False
        ok = True
        for cl in range(classes):
            pairs = [(inner[n], inner[(n+h) % comp]) for n in range(comp) if n % classes == cl]
            if pairs and not any(all(G[(a*x + b) % q] == G[x] for x, _ in pairs) for a, b in sym9.taus(pairs, q)): ok = False; break
        if ok: return True
    return False
BUDGET = 300
class Slow(Exception): pass
def _alarm(*_): raise Slow
def one_chain(job):
    ch, mods = job; tot = hit1 = hit2 = low = skipped = 0; missed = []; slow = []; t0 = time.time()
    signal.signal(signal.SIGALRM, _alarm)
    for m in mods:
        signal.alarm(BUDGET)
        try:
            t = true_period(list(ch), m)
            if t is None: skipped += 1; continue
            a = sym9.crt_block(list(ch), m, 1); b = sym9.crt_block(list(ch), m, 2)
        except Slow:
            slow.append((m, ch)); continue
        finally:
            signal.alarm(0)
        tot += 1; A = a[0] if a else None; B = b[0] if b else None
        low += (A is not None and A < t[0]) or (B is not None and B < t[0])
        hit1 += A == t[0]; hit2 += (A == t[0] or B == t[0])
        if A != t[0] and B != t[0]: missed.append((m, ch, B, t[0]))
    sym2._cyc.clear(); sym2._val.clear()
    return tot, hit1, hit2, low, skipped, missed, slow, (round(time.time() - t0, 1), ch)
def sweep(chains, mods, workers=5):
    tot = hit1 = hit2 = low = skipped = 0; missed = []; slow = []; times = []
    with mp.Pool(workers, maxtasksperchild=25) as pool:
        for a, b, c, d, e, f, g, h in pool.imap_unordered(one_chain, [(ch, list(mods)) for ch in chains], chunksize=1):
            tot += a; hit1 += b; hit2 += c; low += d; skipped += e; missed += f; slow += g; times.append(h)
    missed.sort(); slow.sort(); times.sort()
    return dict(cases=tot, skipped=skipped, d1=hit1, d2=hit2, below=low, missed=len(missed), missed_sample=missed[:12],
                timed_out=len(slow), timed_out_cases=slow, budget_s=BUDGET, slowest_chains_s=times[-5:])
if __name__ == "__main__":
    rng = random.Random("sym9-null"); L = json.load(open("symmetry_levels.json"))["depth3"]["misses"]
    # the misses are split over prime powers by the rule, so the null is run on one prime power per case: the one that decides the period
    from why import prime_powers
    trials = passed1 = passed2 = 0; per = []
    for m, ch, _, tr in L:
        qs = [q for q in prime_powers(m) if true_period(list(ch), q) and true_period(list(ch), q)[0] < true_period(list(ch), q)[1]] or prime_powers(m)
        q = qs[0]; n = 20; a = sum(scrambled(list(ch), q, rng, 1) for _ in range(n)); b = sum(scrambled(list(ch), q, rng, 2) for _ in range(n))
        trials += n; passed1 += a; passed2 += b; per.append((m, ch, q, a, b))
    null = dict(trials=trials, d1_passed=passed1, d2_passed=passed2, rate_d1=passed1/trials, rate_d2=passed2/trials)
    print("null:", null, flush=True)
    names = "FLPQT"
    fresh = sweep(["".join(c) for c in itertools.product(names, repeat=3)], range(21, 41)); print("fresh three-deep m=21..40:", fresh, flush=True)
    json.dump(dict(null=null, null_per_case=per, fresh=fresh), open("sym9_tests_partial.json", "w"), indent=1)
    deep = sweep(["".join(c) for c in itertools.product(names, repeat=4)], range(2, 13)); print("four-deep m=2..12:", deep, flush=True)
    json.dump(dict(null=null, null_per_case=per, fresh=fresh, deeper=deep), open("sym9_tests.json", "w"), indent=1)
