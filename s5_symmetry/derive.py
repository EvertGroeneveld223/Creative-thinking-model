import json
from mult import seq, cycle, mults, shift_ok
F=[0,1]; L=[2,1]
for i in range(3000): F.append(F[-1]+F[-2]); L.append(L[-1]+L[-2])
# Step-by-step check of the L(L(n)) mod 25 derivation
print("S1 L(n+6) = 20F(n) + 9L(n):", all(L[n+6]==20*F[n]+9*L[n] for n in range(400)))
print("S2 Lucas cycle mod 25:", cycle("L",25), "| Fibonacci cycle mod 25:", cycle("F",25))
print("S3a F(10)=55 divides F(10k):", all(F[10*k]%55==0 for k in range(1,45)))
print("S3b L(10k) = 2(-1)^k mod 25:", all((L[10*k]-2*(-1)**k)%25==0 for k in range(45)))
print("S3  L(9k) = L(k) mod 25:", all((L[9*k]-L[k])%25==0 for k in range(55)))
v=[L[L[n]]%25 for n in range(7)]; print("S4 values", v[:6], "shift 2 fails:", v[0]!=v[2], "shift 3 fails:", v[0]!=v[3])
# Does the mechanism 'a = c +/- 1 where F(c)=0 and L(c)=+/-2 (mod m)' produce the multiplier every time R_MULT needed a != 1?
rows=json.load(open("mult_rows.json")); hit=miss=0; misses=[]
for r in rows:
    if r["mult"]==r["comp"]: continue
    m,P=r["m"],r["P"]; Pg=cycle(r["g"],P)
    cand={ (c+s)%P for c in range(P*2) if F[c]%m==0 and ((L[c]-2)%m==0 or (L[c]+2)%m==0) for s in (-1,1)}
    A=set(mults(r["f"],m,P)) & cand
    if any(shift_ok(r["g"],P,r["mult"],a,Pg) for a in A): hit+=1
    else: miss+=1; misses.append((m,r["f"]+"("+r["g"]+")"))
print(f"mechanism c+/-1 explains the multiplier in {hit} of {hit+miss} tightened cases; misses: {misses}")
