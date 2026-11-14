"""R_CRT on top of R_QUOT + affine layers: period mod m = lcm of periods mod each prime power."""
import json, math, sys
from sym4 import period_quot
from why import prime_powers
def period_crt(chain, m):
    L = 1
    for q in prime_powers(m):
        r = period_quot(chain, q)
        if r is None: return None
        L = math.lcm(L, r["per"])
    return L
if __name__ == "__main__":
    k = sys.argv[1]; rows = json.load(open(f"sym4_{k}.json"))
    for r in rows: r["crt"] = period_crt(list(r["chain"]), r["m"]) if r["quot"] != r["true"] else r["quot"]
    n = len(rows); best = lambda r: min(x for x in (r["quot"], r["crt"]) if x is not None)
    print(f"{k}: {n} | R_COMP {sum(r['comp']==r['true'] for r in rows)} | MUL-GLOBAL {sum(r['eq']==r['true'] for r in rows)} | QUOT+AFF {sum(r['quot']==r['true'] for r in rows)} | +CRT {sum(best(r)==r['true'] for r in rows)} | below true {sum(best(r)<r['true'] for r in rows)}")
    miss = [r for r in rows if best(r) != r["true"]]
    print("   misses:", len(miss), [(r["m"], r["chain"], best(r), r["true"]) for r in miss[:20]])
    json.dump(rows, open(f"sym5_{k}.json", "w"))
