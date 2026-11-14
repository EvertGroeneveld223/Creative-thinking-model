"""The odd-modulus pattern: for odd m and g in {F, L}, F(g(n)) mod m never falls below the R_COMP bound. A finite check, not a proof.
    python odd_pattern.py [MMAX]       default 19999, writes odd_pattern.json"""
import json, os, sys
from general import table, minimal, _tab
def main(mmax=19999):
    cases = 0; exc = []
    for m in range(3, mmax+1, 2):
        Ft = table("F", m); P = len(Ft)
        for g in "FL":
            it = table(g, P); cases += 1
            if minimal([Ft[x] for x in it]) != len(it): exc.append((m, g))
        if m % 1000 == 1: _tab.clear()
    print(f"odd m <= {mmax}: {cases} cases, {len(exc)} exceptions", exc[:10])
    json.dump(dict(mmax=mmax, cases=cases, exceptions=exc), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "odd_pattern.json"), "w"), indent=1)
if __name__ == "__main__":
    main(*(int(x) for x in sys.argv[1:]))
