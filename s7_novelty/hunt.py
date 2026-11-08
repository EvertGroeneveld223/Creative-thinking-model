"""Run the logged wave finds through the whole return-to-sender cube, with novelty decided by code.

    python hunt.py [--offline]          reads s6_patches/runs/*.jsonl, writes hunt_results.json

For each distinct expression with worth > 0 in any logged run:
  w, e  the engine's own world check and exact proof, already in the log (kind EXPLAINED)
  family  the proved period for each modulus m = 2..24: the object that can be new, since one (expression, m) is just an instance
  n     novelty.check on the family's period table, and on the residue terms of the best instance

Corner: NEW (1,1,1) only when the period table is not found. KNOWN when it is.
n = 1 still means only "not found by these searches". Long arbitrary expressions are novel by absence, so
only expressions up to MAX_SIZE blocks are searched; longer ones are counted and reported as not searched.
Expressions with the same period table are one family (a*b and b*a, sq(x) and x*x): one search, the smallest as its name.
The table is searched by its first TERMS terms: an entry listing fewer terms than the query would otherwise be missed,
and novelty.py still checks that the terms really occur in the entry's data."""
import glob, json, math, os, signal, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "s4_merging"))
sys.path.insert(0, HERE)
sys.set_int_max_str_digits(0)
import engine1 as g, merge as M, v3
import novelty as N

MODS = range(2, 25)
SECS = 3
MAX_SIZE = 3
TERMS = 12


class _TO(Exception):
    pass


def _h(*a):
    raise _TO()


def finds():
    """{(ops/base shape): best logged instance}. An expression with different m is one family."""
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "s6_patches", "runs", "*.jsonl"))):
        for line in open(f):
            e = json.loads(line)
            if e.get("type") != "step" or e.get("worth", 0) <= 0:
                continue
            p = e["point"]
            key = json.dumps([p["base"], p["ops"]])
            if key not in out or e["worth"] > out[key]["worth"]:
                out[key] = dict(worth=e["worth"], m=e["m"], L=e["L"], naive=e["naive"], expr=e["sexpr"], point=p, run=os.path.basename(f), t=e["t"])
    return list(out.values())


def family(p):
    """Proved period and naive bound per m. Stops at the first modulus with no proof, so the table has no holes."""
    table, naive = [], []
    for m in MODS:
        q = dict(p, m=m)
        signal.alarm(SECS)
        try:
            L, _, _ = M.explain(q)
            B = v3.naive(q)
        except _TO:
            L = None
        except Exception:      # a rule's WHERE failing mid-proof counts as no proof, never as a result
            L = None
        finally:
            signal.alarm(0)
        if L is None:
            break
        table.append(L)
        naive.append(B)
    return table, naive


def residues(p, L, cap=24):
    """One period repeated, enough terms to search. Computed by the world, modulo m."""
    s, W = g.world(g.tree(p), p["m"], N=max(300, 3*L + 20))
    if W != L:
        return None
    return [s[i % L] for i in range(max(cap, min(2*L, cap)))]


def main():
    offline = "--offline" in sys.argv
    signal.signal(signal.SIGALRM, _h)
    cache = N.Cache()
    def fetch(url):
        if offline:
            raise N.Unavailable("offline")
        return N.http_get(url)
    F = finds()
    short = [x for x in F if 1 + len(x["point"]["ops"]) <= MAX_SIZE]
    print(len(F), "distinct expressions with worth > 0;", len(short), f"of size <= {MAX_SIZE} searched", flush=True)
    groups = {}
    for x in sorted(short, key=lambda r: (len(r["point"]["ops"]), -r["worth"])):
        table, naive = family(x["point"])
        k = json.dumps(table) if len(table) >= 6 else "short:" + x["expr"]
        g_ = groups.setdefault(k, dict(table=table, naive=naive, members=[]))
        g_["members"].append(x)
    print(len(groups), "distinct families", flush=True)
    results = []
    for i, gr in enumerate(groups.values()):
        table, naive, x = gr["table"], gr["naive"], gr["members"][0]
        saved = sum(a < b for a, b in zip(table, naive))
        fam = N.check(table[:TERMS], cache=cache, fetch=fetch) if len(table) >= 6 else dict(verdict="TRIVIAL", n=None, why="fewer than 6 proved moduli")
        res = residues(x["point"], x["L"])
        inst = N.check(res, cache=cache, fetch=fetch) if res else dict(verdict="TRIVIAL", n=None)
        corner = {0: "KNOWN", 1: "NEW"}.get(fam["n"], fam["verdict"])
        results.append(dict(expr=x["expr"], aliases=[m["expr"] for m in gr["members"][1:]], size=1 + len(x["point"]["ops"]), best_m=x["m"], best_L=x["L"], best_naive=x["naive"], worth=x["worth"],
                            source=[x["run"], x["t"]], periods_m2=table, naive_m2=naive, moduli_saved=saved, corner=corner, family=fam, instance=inst, instance_terms=res))
        print(i, corner, x["expr"], "| saved at", saved, "moduli |", table[:10], "| inst:", inst["verdict"], flush=True)
        json.dump(dict(date=time.strftime("%Y-%m-%d"), expressions=len(F), searched_expressions=len(short), families=results), open(os.path.join(HERE, "hunt_results.json"), "w"), indent=1)
    from collections import Counter
    print(Counter(r["corner"] for r in results))


if __name__ == "__main__":
    main()
