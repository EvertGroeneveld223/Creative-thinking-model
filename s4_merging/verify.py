import os as _os
_P=lambda *a:_os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",*[x for x in a if x]))
import json, random, time, merge as M, engine1 as g
random.seed(20261107)
BLK=["fib","luc","tri","sq","ds"]
def rand_point():
    p=dict(base=random.choice(BLK), m=random.randint(2,16), ops=[])
    for _ in range(random.randint(0,4)):
        p["ops"].append([random.choice(["add","mul","comp"]), random.choice(BLK)])
    return p
pts=[]
for f in [_P("s3_waves_v2","state.json")]:
    S=json.load(open(f))
pts += [rand_point() for _ in range(600)]
res=dict(n=0, unreachable=0, agree=0, disagree=[], gap_world_periodic=0, gap_world_not=0, old_exact=0, merged_exact=0, old_any=0, timeouts=0, structural=0)
t0=time.time()
for p in pts:
    s,W=g.world(g.tree(p),p["m"],N=600)
    if len(s)<200: res["unreachable"]+=1; continue
    res["n"]+=1
    tr=[]; B=g.bound(g.tree(p),p["m"],tr)
    L,trace,nf=M.explain(p)
    if L is None:
        if W: res["gap_world_periodic"]+=1
        else: res["gap_world_not"]+=1
        continue
    if W==L: res["agree"]+=1
    else: res["disagree"].append((g.show(g.tree(p)),p["m"],L,W))
    if W and B==W: res["old_exact"]+=1
    if W and B: res["old_any"]+=1
    res["merged_exact"]+= (W==L)
    res["structural"]+= (not any("atom" in t for t in trace))
res["secs"]=round(time.time()-t0,1)
print(json.dumps({k:(v if k!="disagree" else v[:10]) for k,v in res.items()}, indent=1)); print("disagreements:",len(res["disagree"]))
json.dump(res,open("verify.json","w"),indent=1,default=str)
