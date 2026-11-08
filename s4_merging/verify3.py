import json, random, time, merge as M, engine1 as g
random.seed(20261107)
BLK=["fib","luc","tri","sq","ds"]
def rand_point():
    p=dict(base=random.choice(BLK), m=random.randint(2,16), ops=[])
    for _ in range(random.randint(0,4)):
        p["ops"].append([random.choice(["add","mul","comp"]), random.choice(BLK)])
    return p
pts=[rand_point() for _ in range(600)]
R=dict(tested=0, unreachable=0, proof_eq_world=0, proof_ne_world=[], world_too_short=[], gap_world_periodic=[], gap_world_not=0,
       old_exact=0, merged_exact=0, structural=0, residue=0)
t0=time.time()
for p in pts:
    E=g.tree(p); L,trace,nf=M.explain(p)
    N=max(900, 3*L+20) if L else 900
    s,W=g.world(E,p["m"],N=N)
    if len(s)<200: R["unreachable"]+=1; continue
    R["tested"]+=1
    tr=[]; B=g.bound(E,p["m"],tr)
    if L is None:
        if W: R["gap_world_periodic"].append((g.show(E),p["m"],W,trace[-1]))
        else: R["gap_world_not"]+=1
        continue
    if len(s) < 3*L: R["world_too_short"].append((g.show(E),p["m"],L,len(s))); continue
    if W==L: R["proof_eq_world"]+=1
    else: R["proof_ne_world"].append((g.show(E),p["m"],L,W))
    if B==W: R["old_exact"]+=1
    R["merged_exact"]+=(W==L)
    if any("atom" in t for t in trace): R["residue"]+=1
    else: R["structural"]+=1
R["secs"]=round(time.time()-t0,1)
json.dump(R,open("verify.json","w"),indent=1)
print({k:(len(v) if isinstance(v,list) else v) for k,v in R.items()})
for x in R["proof_ne_world"]+R["gap_world_periodic"]+R["world_too_short"]: print("  ",x)
