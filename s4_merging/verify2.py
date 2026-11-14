import json, random, merge as M, engine1 as g
random.seed(20261107)
BLK=["fib","luc","tri","sq","ds"]
def rand_point():
    p=dict(base=random.choice(BLK), m=random.randint(2,16), ops=[])
    for _ in range(random.randint(0,4)):
        p["ops"].append([random.choice(["add","mul","comp"]), random.choice(BLK)])
    return p
pts=[rand_point() for _ in range(600)]
fixed=0; still=[]; gaps=[]
for p in pts:
    s,W=g.world(g.tree(p),p["m"],N=600)
    if len(s)<200: continue
    L,trace,nf=M.explain(p)
    if L is not None and W!=L:
        s2,W2=g.world(g.tree(p),p["m"],N=max(3*L+10,600))
        if W2==L: fixed+=1
        else: still.append((g.show(g.tree(p)),p["m"],L,W2,len(s2)))
    if L is None and W: gaps.append((g.show(g.tree(p)),p["m"],W,trace[-1]))
print("recheck with longer world: confirmed",fixed,"still disagree",still)
print("periodic in world but GAP in rulebook:",len(gaps))
for x in gaps: print("  ",x)
