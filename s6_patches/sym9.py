"""R_BLOCK: the layers need not each carry an affine map. Treat the outer layers as ONE function G = f1(...f_{k-1}) on the cycle of the innermost.
  f_k(n+h) = tau(f_k(n)) with tau affine mod q, and G(tau(x)) = G(x) for every x in the image  =>  period divides h.
The middle layers may scramble values as long as the top cannot tell. sym3 fails on those cases because it wants an affine map at every layer.
CLASSES = d lets tau differ with n mod d. d = 1 is the plain rule. A large d says nothing: with d = cycle length each n has its own map, so the condition is the period itself.
So the result is reported per d, and only d <= 2 is used for the headline.
These are finite checks on computed tables: they prove the period for this m, they do not derive it from an identity.
    python sym9.py        reads sym8_depth2.json, sym8_depth3.json, writes sym9_depth2.json, sym9_depth3.json, symmetry_levels.json"""
import json, math
from sym2 import vals, divisors
from sym4 import tower
from why import prime_powers
def taus(pairs, q):
    """Every affine (a, b) mod q taking x to y on all pairs. Empty if the pairs are not a function."""
    M = {}
    for x, y in pairs:
        if M.setdefault(x, y) != y: return []
    items = list(M.items()); x0, y0 = items[0]; out = []
    for a in range(q):
        b = (y0 - a*x0) % q
        if all((a*x + b - y) % q == 0 for x, y in items): out.append((a, b))
    return out
def outer_table(chain, m, mods):
    """G on Z_q, q = mods[-1]: the composition of every layer except the innermost."""
    q = mods[-1]; s = list(range(q))
    for f, r in zip(reversed(chain[:-1]), reversed(mods[:-1])):
        v = vals(f, r); s = [v[x % len(v)] for x in s]
    return s
def block_period(chain, m, classes=1):
    """Smallest h the rule reaches, with the map used. None if the chain is too large to tabulate."""
    if len(chain) < 2: return None
    T = tower(chain, m)
    if T is None: return None
    mods, comp, seqs = T; q = mods[-1]; inner = seqs[len(chain)-1]; G = outer_table(chain, m, mods)
    for h in divisors(comp):
        maps = []
        for cl in range(classes):
            pairs = [(inner[n], inner[(n+h) % comp]) for n in range(comp) if n % classes == cl]
            if not pairs: continue
            hit = next(((a, b) for a, b in taus(pairs, q) if all(G[(a*x + b) % q] == G[x] for x, _ in pairs)), None)
            if hit is None: break
            maps.append(hit)
        else:
            return h, maps
    return comp, []
def crt_block(chain, m, classes=1):
    L = 1; parts = []
    for q in prime_powers(m) or [1]:
        r = block_period(chain, q, classes)
        if r is None: return None
        L = math.lcm(L, r[0]); parts.append((q, r[0], r[1]))
    return L, parts
if __name__ == "__main__":
    tot = json.load(open("symmetry_levels.json"))
    for k in ("depth2", "depth3"):
        rows = json.load(open(f"sym8_{k}.json")); prev = lambda r: min(x for x in (r["quot"], r["crt"], r["par"], r["zero"], r["cls"]) if x is not None)
        for r in rows:
            ch = list(r["chain"]); a = crt_block(ch, r["m"], 1); b = crt_block(ch, r["m"], 2)
            r["blk"] = a[0] if a else None; r["blk2"] = b[0] if b else None
        fin = lambda r: min(x for x in (prev(r), r["blk"], r["blk2"]) if x is not None); base = lambda r: min(x for x in (prev(r), r["blk"]) if x is not None)
        below = [r for r in rows if r["blk"] is not None and r["blk"] < r["true"] or r["blk2"] is not None and r["blk2"] < r["true"]]
        miss = [r for r in rows if fin(r) != r["true"]]; old = [r for r in rows if prev(r) != r["true"]]
        print(f"{k}: {len(rows)} cases | ladder before {sum(prev(r)==r['true'] for r in rows)} | R_BLOCK alone (all rows) {sum(r['blk']==r['true'] for r in rows)} | ladder+R_BLOCK d=1 {sum(base(r)==r['true'] for r in rows)} | +d=2 {sum(fin(r)==r['true'] for r in rows)} | of the old misses closed by d=1: {sum(r['blk']==r['true'] for r in old)}, by d=2: {sum(r['blk2']==r['true'] for r in old)} of {len(old)} | below true {len(below)}")
        print("   still missed:", [(r["m"], r["chain"], fin(r), r["true"]) for r in miss][:20])
        tot[k]["levels"]["BLOCK"] = sum(base(r)==r["true"] for r in rows); tot[k]["levels"]["BLOCK2"] = sum(fin(r)==r["true"] for r in rows); tot[k]["misses_after_block"] = [(r["m"], r["chain"], fin(r), r["true"]) for r in miss]
        json.dump(rows, open(f"sym9_{k}.json", "w"))
    json.dump(tot, open("symmetry_levels.json", "w"), indent=1)
    print("example:", crt_block(list("LLF"), 3, 1))
