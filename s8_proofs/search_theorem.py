"""Novelty search for the theorems in PROOFS.md. Everything goes through novelty.py and is kept in its cache, so the search can be read back.
    python search_theorem.py          prints the candidates still to open
    python search_theorem.py record   copies opened_pages.json into novelty.py's cache with add_manual
Pages opened by hand are in opened_pages.json with what was read of each."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "s7_novelty"))
import novelty as N
NEST = ("composition", "composite", "nested", "iterated", "subscript", "l_{l", "f_{f", "l_{f", "f_{l", "l(l(", "f(f(", "of lucas numbers", "of fibonacci numbers")
QUERIES = [
    # neutral, adversarial, exact
    ("period of Lucas numbers with Lucas subscripts modulo m", ["lucas", ("period", "periodic", "pisano"), NEST]),
    ("Fibonacci numbers with Fibonacci subscripts period modulo m", ["fibonacci", ("period", "periodic", "pisano"), NEST]),
    ("composition of Fibonacci and Lucas sequences periodic modulo prime powers known theorem", [("fibonacci", "lucas"), ("period", "periodic", "pisano"), NEST]),
    ("iterated Fibonacci sequence F(F(n)) period modulo m", ["fibonacci", ("period", "periodic", "pisano"), NEST]),
    ("L_{L_n} modulo 5^k period Lucas", ["lucas", ("5^k", "powers of 5", "5-adic", "modulo 5"), NEST]),
]
def run():
    cache = N.Cache(); out = {}
    for q, must in QUERIES:
        res = {"crossref": N.crossref(q, must, cache), "openalex": N.openalex(q, must, cache), "zbmath": N.zbmath(q, must, cache),
               "stackexchange-math": N.stackexchange(q, must, cache, site="math"), "stackexchange-mathoverflow": N.stackexchange(q, must, cache, site="mathoverflow"),
               "arxiv": N.arxiv('all:"Lucas" AND all:"Fibonacci" AND (all:composition OR all:subscripts OR all:nested OR all:iterated) AND (all:period OR all:modulo)', cache, must=must)}
        out[q] = {k: dict(status=v["status"], hits=v.get("hits", [])) for k, v in res.items()}
        print(q); print("   ", {k: (v["status"], len(v.get("hits", []))) for k, v in res.items()}, flush=True)
    seen = {}
    for q, r in out.items():
        for k, v in r.items():
            for h in v["hits"]:
                seen.setdefault(h.get("url", ""), h.get("name", ""))
    json.dump(dict(queries=[q for q, _ in QUERIES], results=out, candidates=seen), open(os.path.join(HERE, "search_theorem.json"), "w"), indent=1)
    print(len(seen), "distinct candidates")
    for u, n in sorted(seen.items(), key=lambda x: x[1]):
        print("  ", n[:105], u)
def record():
    """READ means a person or agent read the page as described in the note; NOT-READ pages are not evidence either way."""
    O = json.load(open(os.path.join(HERE, "opened_pages.json"))); cache = N.Cache()
    for p in O["pages"]:
        N.add_manual(p["url"], "READ", [dict(name=p["title"], url=p["url"])], f"read: {p['read']}. states the theorem: {p['states_theorem']}. {p['note']}", cache)
    for p in O["not_read"]:
        N.add_manual(p["url"], "NOT-READ", [dict(name=p["title"], url=p["url"])], p["why"], cache)
    print(len(O["pages"]), "read,", len(O["not_read"]), "not read, stored in the cache")
if __name__ == "__main__":
    record() if sys.argv[1:] == ["record"] else run()
