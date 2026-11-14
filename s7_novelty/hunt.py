"""Run the logged wave finds through the whole return-to-sender cube, with novelty decided by code.

    python hunt.py [--offline]          reads s6_patches/runs/*.jsonl, writes hunt_results.json

For each distinct expression with worth > 0 in any logged run:
  w, e    the engine's own world check and exact proof, already in the log (kind EXPLAINED)
  class   expressions giving the same residues for every m = 2..24 are one class (a*b and b*a). Equal period tables alone do not make a class.
  n       novelty.check on the class's period table and on the residue terms of its best instance, plus text searches

Corners:
  KNOWN    the table matches an OEIS entry on every listed term, at least 30 of them
  NEW      all sources answered and none has a candidate. Still only "not found by these searches".
  REVIEW   a candidate page exists, a table match is too short to judge, or the residues are in OEIS. Code cannot decide; a person must open it.
  UNCHECKED a source could not be asked. An outage never counts as novelty.
  TRIVIAL  no proved table to search for (digit sums).
A 12-term table match that disagrees with the entry on later terms is logged as a coincidence and does not make the class KNOWN.
Long arbitrary expressions are novel by absence, so only expressions up to MAX_SIZE blocks are searched; longer ones are counted as not searched."""
import glob, hashlib, json, os, signal, sys, time
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "s4_merging"))
sys.path.insert(0, HERE)
sys.set_int_max_str_digits(0)
import engine1 as g, merge as M, v3
import novelty as N, tables as TB

CLASS_MODS = range(2, 25)
MODS = range(2, 121)
SECS = 3
MAX_SIZE = 3
TERMS = 12
WORD = {"fib": "Fibonacci", "luc": "Lucas", "tri": "triangular", "sq": "square", "ds": "digit sum"}
PERIOD = ("period", "pisano", "periodic", "periodicity")
NESTED = ("composition", "composite", "nested", "iterated", "iterate", "iteration", "self-composition", "fibonacci of fibonacci", "of fibonacci numbers of", "f_{f_", "f(f(")
REQUIRED = ("oeis-terms", "arxiv", "crossref", "openalex", "zbmath", "stackexchange-math", "stackexchange-mathoverflow")


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


def timed(fn, *a):
    signal.alarm(SECS)
    try:
        return fn(*a)
    except (_TO, TB.NoRule, TB.TooLarge):
        return None
    finally:
        signal.alarm(0)


def proved_table(p):
    """merge.py's proved period per m = 2..24, stopping at the first m with no proof, so the table has no holes."""
    out = []
    for m in CLASS_MODS:
        signal.alarm(SECS)
        try:
            L = M.explain(dict(p, m=m))[0]
        except _TO:
            L = None
        except Exception:      # a rule's WHERE failing mid-proof counts as no proof, never as a result
            L = None
        finally:
            signal.alarm(0)
        if L is None:
            break
        out.append(L)
    return out


def long_table(p):
    """Periods from tables.py for m = 2..120, stopping at the first m it cannot do."""
    E = g.tree(p); out = []
    for m in MODS:
        L = timed(TB.period, E, m)
        if L is None:
            break
        out.append(L)
    return out


def class_key(p):
    """Hash of one minimal period of the residues for every m = 2..24. None if some m cannot be computed."""
    E = g.tree(p); h = hashlib.sha256()
    for m in CLASS_MODS:
        v = timed(TB.series, E, m)
        if v is None:
            return None
        T = TB.minimal(v)
        h.update(repr((m, v[:T])).encode())
    return h.hexdigest()


def words(p):
    return sorted({WORD[b] for b in [p["base"]] + [b for _, b in p["ops"]]})


def queries(p):
    """A neutral and an adversarial query per kind of source. A candidate must name every block and periods, and for a composition also nesting."""
    w = words(p); W = " ".join(w); nested = any(k == "comp" for k, _ in p["ops"])
    must = [x.split()[0] for x in w] + [PERIOD] + ([NESTED] if nested else [])
    neutral = f"period of {W} numbers modulo m"
    adversarial = f"{W} {'composition ' if nested else ''}periodic modulo known result"
    arx = " AND ".join(f'all:"{x}"' for x in w) + ' AND (all:period OR all:periodic OR all:pisano)'
    crossref_must = [x.split()[0] for x in w] + [PERIOD]
    return dict(phrases=[], arxiv_queries=[(arx, must)], crossref_queries=[(neutral, crossref_must), (adversarial, crossref_must)],
                openalex_queries=[(neutral, must), (adversarial, must)], zbmath_queries=[(f"{W} period modulo", must)], stackexchange_queries=[(neutral, must)])


def judge(table_long, fam, cache, fetch):
    """Turns an OEIS term match into KNOWN, or sets it aside as a coincidence after comparing every listed term."""
    t = fam["searched"].get("oeis-terms", {})
    if t.get("status") != "FOUND":
        return fam["verdict"], []
    report = []
    for h in t["hits"]:
        e = N.oeis_entry(h["id"], cache, fetch)
        if e["status"] == "UNCHECKED":
            report.append(dict(h, result="UNCHECKED"))
            continue
        report.append(dict(id=h["id"], name=h["name"], url=h["url"], **N.compare(table_long, e["data"])))
    res = {r["result"] for r in report}
    if "AGREES" in res:
        return "KNOWN", report
    if res & {"SHORT", "UNCHECKED"}:
        return "REVIEW", report
    rest = dict(fam["searched"], **{"oeis-terms": dict(status="CLEAR", hits=[])})   # every match was a coincidence: the other sources decide
    return N.verdict(rest, REQUIRED)[0], report


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
    classes = {}; disagree = []
    for x in sorted(short, key=lambda r: (len(r["point"]["ops"]), -r["worth"])):
        table, longt = proved_table(x["point"]), long_table(x["point"])
        if len(table) >= 6 and longt[:len(table)] != table:      # two independent computations of the same table
            disagree.append((x["expr"], table[:10], longt[:10]))
        k = class_key(x["point"]) if len(table) >= 6 else None
        k = k or "single:" + x["expr"]
        c = classes.setdefault(k, dict(table=table, long=longt, members=[]))
        c["members"].append(x)
    tabs = Counter(json.dumps(c["table"]) for c in classes.values() if len(c["table"]) >= 6)
    print(len(classes), "classes by residues;", len(tabs), "distinct period tables; table disagreements merge vs tables:", len(disagree), flush=True)
    results = []
    for i, c in enumerate(classes.values()):
        table, longt, x = c["table"], c["long"], c["members"][0]
        res = None
        s, W = g.world(g.tree(x["point"]), x["m"], N=max(300, 3*x["L"] + 20))
        if W == x["L"]:
            res = [s[i_ % x["L"]] for i_ in range(24)]
        inst = N.check(res, cache=cache, fetch=fetch) if res else dict(verdict="TRIVIAL", n=None)
        if len(table) >= 6:
            fam = N.check(table[:TERMS], cache=cache, fetch=fetch, required=REQUIRED, **queries(x["point"]))
            corner, oeis = judge(longt if len(longt) >= len(table) else table, fam, cache, fetch)
        else:
            fam = dict(verdict="TRIVIAL", n=None, why="fewer than 6 proved moduli", searched={})
            corner, oeis = "TRIVIAL", []
        if corner == "NOT-FOUND":
            corner = "NEW"
        elif corner == "KNOWN" and not oeis:
            corner = "REVIEW"
        notes = []
        if inst["verdict"] == "KNOWN" and corner == "NEW":
            corner = "REVIEW"; notes.append("residues of the best instance are in OEIS")
        if corner == "UNCHECKED":
            notes.append("unreached: " + ", ".join(fam.get("unreached", [])))
        cand = sorted({(h.get("name", ""), h.get("url", "")) for k, v in fam.get("searched", {}).items() if k != "oeis-terms" for h in v.get("hits", [])})
        results.append(dict(expr=x["expr"], aliases=[m["expr"] for m in c["members"][1:]], size=1 + len(x["point"]["ops"]), best_m=x["m"], best_L=x["L"], best_naive=x["naive"], worth=x["worth"], source=[x["run"], x["t"]],
                            periods_m2=table, periods_long=longt, shared_table=tabs.get(json.dumps(table), 0), moduli_saved=sum(a < v3.naive(dict(x["point"], m=m)) for m, a in zip(CLASS_MODS, table)), corner=corner, oeis_compare=oeis, candidates=cand, notes=notes,
                            sources={k: v["status"] for k, v in fam.get("searched", {}).items()}, instance=dict(verdict=inst["verdict"], hits=(inst.get("searched") or {}).get("oeis-terms", {}).get("hits", [])), instance_terms=res))
        print(i, corner, x["expr"], "|", table[:8], "| oeis", [(r["id"], r["result"], r.get("overlap")) for r in oeis], "| candidates", len(cand), "| inst", inst["verdict"], flush=True)
        json.dump(dict(date=time.strftime("%Y-%m-%d"), expressions=len(F), searched_expressions=len(short), table_disagreements=disagree, required_sources=list(REQUIRED), families=results), open(os.path.join(HERE, "hunt_results.json"), "w"), indent=1)
    print(Counter(r["corner"] for r in results))
    print("distinct candidate pages:", len({u for r in results for _, u in r["candidates"]}))


if __name__ == "__main__":
    main()
