"""Prediction ledger: a confidence is written down and hashed BEFORE its check runs, and scored afterwards.

    python ledger.py commit P "claim" "how it will be checked"     P = probability the claim is true, 0 < P < 1
    python ledger.py resolve ID 0|1 "evidence"
    python ledger.py void ID "reason"                              the check could not run; not scored, stays visible
    python ledger.py report
    python ledger.py verify                                        exits non-zero if the chain was edited

Records are append-only. Each one holds the SHA-256 of the record before it, so an edit breaks every later hash.
Limit: the chain is made on this machine, so it shows later edits, not a timestamp anyone else witnessed.
A person can compare it with the chat transcript, where each commit appears before its result.
Brier score: mean (P - outcome)^2. Always saying 0.5 scores 0.25, so anything near or above 0.25 shows no skill."""
import hashlib, json, os, sys, time

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.jsonl")
GENESIS = "0"*64


def _hash(rec):
    body = {k: v for k, v in rec.items() if k != "sha"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def rows(path=PATH):
    return [json.loads(x) for x in open(path)] if os.path.exists(path) else []


def _append(rec, path=PATH):
    R = rows(path)
    rec = dict(rec, seq=len(R), prev=R[-1]["sha"] if R else GENESIS, t=time.strftime("%Y-%m-%dT%H:%M:%S"))
    rec["sha"] = _hash(rec)
    with open(path, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def commit(p, claim, check, path=PATH):
    if not 0 < p < 1:
        raise ValueError("P must be strictly between 0 and 1: nothing here is certain")
    n = sum(r["type"] == "commit" for r in rows(path))
    return _append(dict(type="commit", id=f"P{n+1:03d}", p=p, claim=claim, check=check), path)


def _commit_of(i, path):
    R = rows(path)
    c = next((r for r in R if r["type"] == "commit" and r["id"] == i), None)
    if c is None:
        raise KeyError(i)
    if any(r["type"] in ("resolve", "void") and r["id"] == i for r in R):
        raise ValueError(f"{i} is already closed; a result is never rewritten")
    return c


def resolve(i, outcome, evidence, path=PATH):
    _commit_of(i, path)
    if outcome not in (0, 1):
        raise ValueError("outcome is 0 or 1")
    return _append(dict(type="resolve", id=i, outcome=outcome, evidence=evidence), path)


def void(i, reason, path=PATH):
    _commit_of(i, path)
    return _append(dict(type="void", id=i, reason=reason), path)


def verify(path=PATH):
    prev = GENESIS
    for s, r in enumerate(rows(path)):
        if r["prev"] != prev or r["seq"] != s or _hash(r) != r["sha"]:
            return False, s
        prev = r["sha"]
    return True, None


def score(path=PATH):
    R = rows(path)
    done = {r["id"]: r["outcome"] for r in R if r["type"] == "resolve"}
    voided = {r["id"] for r in R if r["type"] == "void"}
    C = [r for r in R if r["type"] == "commit"]
    pairs = [(r["p"], done[r["id"]]) for r in C if r["id"] in done]
    out = dict(committed=len(C), resolved=len(pairs), voided=len(voided), open=[r["id"] for r in C if r["id"] not in done and r["id"] not in voided])
    if pairs:
        out["brier"] = sum((p - o)**2 for p, o in pairs) / len(pairs)
        out["mean_p"] = sum(p for p, _ in pairs) / len(pairs)
        out["accuracy"] = sum(o for _, o in pairs) / len(pairs)
        # how often the side the prediction leaned to was right, against the mean confidence in that side
        side = [(max(p, 1-p), (p >= .5) == bool(o)) for p, o in pairs]
        out["mean_conf"] = sum(c for c, _ in side) / len(side)
        out["hit_rate"] = sum(h for _, h in side) / len(side)
        bins = {}
        for c, h in side:
            b = min(int(c*5)/5, .8)
            bins.setdefault(b, []).append(h)
        out["bins"] = {f"{b:.1f}-{b+.2:.1f}": (sum(v), len(v)) for b, v in sorted(bins.items())}
    return out


def report(path=PATH):
    s = score(path)
    print(f"committed {s['committed']}, resolved {s['resolved']}, voided {s['voided']}, open {s['open']}")
    if s["resolved"]:
        print(f"Brier {s['brier']:.3f} (0.25 = always saying 0.5). Mean confidence in the chosen side {s['mean_conf']:.2f}, hit rate {s['hit_rate']:.2f}, gap {s['mean_conf'] - s['hit_rate']:+.2f}.")
        print("by confidence (right, total):", s["bins"])
        print(f"few predictions, so this is a weak signal: n = {s['resolved']}")
    done = {r["id"]: r for r in rows(path) if r["type"] in ("resolve", "void")}
    for r in rows(path):
        if r["type"] == "commit":
            d = done.get(r["id"])
            res = "OPEN" if d is None else ("VOID" if d["type"] == "void" else ("TRUE " if d["outcome"] else "FALSE"))
            print(f"  {r['id']} p={r['p']:.2f} {res} {r['claim']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "commit":
        r = commit(float(a[1]), a[2], a[3]); print("committed", r["id"], r["sha"][:16])
    elif a[0] == "resolve":
        r = resolve(a[1], int(a[2]), a[3]); print("resolved", r["id"], r["sha"][:16])
    elif a[0] == "void":
        r = void(a[1], a[2]); print("voided", r["id"], r["sha"][:16])
    elif a[0] == "report":
        report()
    elif a[0] == "verify":
        ok, at = verify(); print("chain intact" if ok else f"CHAIN BROKEN at record {at}"); sys.exit(0 if ok else 1)
    else:
        sys.exit(__doc__)
