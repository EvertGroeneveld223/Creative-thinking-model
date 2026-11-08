# Proofs

Status: written by Claude and checked step by step by `prove.py`. **No mathematician has reviewed it.** `prove.py` checks the identities symbolically and the lemmas on concrete values. It does not check the induction argument, so read that part critically.

Notation: F(n) and L(n) are the Fibonacci and Lucas numbers, extended to all integers n. v5(x) is the exponent of 5 in x.

## Theorem

For every k >= 2:

- **(a)** L(L(n)) mod 5^k has exact period 6·5^(k-2).
- **(b)** L(F(n)) mod 5^k has exact period 6·5^(k-1). This also holds for k = 1.

The composition rule R_COMP gives twice these values, so the theorem is the rule R_MULT made exact for one infinite family. The engine's "best find", L(L(n)) mod 25 = 6, is case (a) with k = 2.

## Identities (for all integers; checked symbolically by `prove.py`, part 1)

- I1: 2L(n+c) = L(n)L(c) + 5F(n)F(c)
- I2: 2F(n+c) = F(n)L(c) + L(n)F(c)
- I3: L(u+v) - (-1)^v L(u-v) = 5F(u)F(v)
- I4: L(n)^2 = 5F(n)^2 + 4(-1)^n
- I5: L(2n) = L(n)^2 - 2(-1)^n
- I6: F(2n) = F(n)L(n)
- I7: F(5n) = 5F(n)(5F(n)^4 + 5(-1)^n F(n)^2 + 1)
- Also L(-n) = (-1)^n L(n), directly from the Binet formula.

## Lemmas

**V. v5(F(n)) = v5(n) for n >= 1, and 5 never divides L(n).**
F mod 5 has cycle length 20 with zeros exactly at multiples of 5, so 5 divides F(n) iff 5 divides n. L mod 5 cycles through 2, 1, 3, 4, so it is never 0. The bracket in I7 is always 1 mod 5, so v5(F(5n)) = v5(F(n)) + 1 for every n. Write n = 5^a·b with 5 not dividing b. Applying this a times gives v5(F(n)) = a + v5(F(b)) = a.

**A. For j >= 1: L(n + 2·5^(j-1)) = -L(n) mod 5^j.**
Let x = 5^(j-1) and c = 2x. Since x is odd, I5 and I4 give L(c) = L(x)^2 + 2 = 5F(x)^2 - 2. By V, v5(5F(x)^2) = 2j - 1 >= j, so L(c) = -2 mod 5^j. By I6 and V, v5(5F(c)) >= j. Then I1 gives 2L(n+c) = -2L(n) mod 5^j, and 2 is invertible.

**B. For j >= 1: F(n + 2·5^j) = -F(n) mod 5^j.**
Let x = 5^j and c = 2x. As in A, L(c) = -2 mod 5^j and v5(F(c)) >= j. Then I2 gives 2F(n+c) = -2F(n) mod 5^j.

**M. If L(n+c) = -L(n) mod m for all integers n, then L((c-1)x) = L(x) mod m for all x >= 0.**
Shift x times, starting from index -x: L(-x + cx) = (-1)^x L(-x) = (-1)^x (-1)^x L(x) = L(x).

**Mod 4.** F and L mod 4 both have period 6 (finite check).

## Upper bound

Fix k >= 2. Let P = 4·5^(k-1) and a = 2·5^(k-1) - 1. Then:

- A applied twice gives L(n + P) = L(n) mod 5^k, so L(x) mod 5^k depends only on x mod P.
- M with c = 2·5^(k-1) (allowed by A with j = k) gives L(a·x) = L(x) mod 5^k.
- a = 1 mod 4, because 2·(odd) - 1 = 1 mod 4. And a = -1 mod 5^(k-1).

**(a)** Let h = 6·5^(k-2) = 3·(2·5^(k-2)). Mod 4, L(n+h) = L(n) = a·L(n), because 6 divides h. Mod 5^(k-1), A with j = k-1 applied three times gives L(n+h) = -L(n) = a·L(n). So L(n+h) = a·L(n) mod P by CRT. Therefore L(L(n+h)) = L(a·L(n)) = L(L(n)) mod 5^k.

**(b)** Let h = 6·5^(k-1) = 3·(2·5^(k-1)). Mod 4, F(n+h) = F(n) = a·F(n). Mod 5^(k-1), B with j = k-1 applied three times gives F(n+h) = -F(n) = a·F(n). The rest is the same as (a).

## Exactness (lower bound)

If T is a period mod 5^k, it is also a period mod 5^(k-1). So by induction on k, the exact period T contains the previous exact period as a divisor and divides the upper bound. These differ by a factor of 5, so T is one of those two values. It is enough to show that the smaller one fails, using n = 1.

**Valuation tool.** Suppose x, y are positive, y = x mod 4, y != x. Let u = (x+y)/2 and v = (y-x)/2. Then v is even, so I3 gives L(y) - L(x) = 5F(u)F(v), and by V, v5(L(y) - L(x)) = 1 + v5(u) + v5(v).

**(a), k >= 3.** Base: k = 2 has period exactly 6, since 3,1,4,7,4,24 rules out 2 and 3. Let j = k-3, w = 3·5^j, c = 2w = 6·5^j (the smaller candidate), and y = L(1+c). Take x = L(1) = 1.
- From I1, y = (L(c) + 5F(c))/2. From I4 to I6 and w odd, L(c) = 5F(w)^2 - 2 and F(c) = F(w)L(w).
- So y + 1 = 5F(w)(F(w) + L(w))/2 = 5F(w)F(w+1), using 2F(w+1) = F(w) + L(w) from I2.
- By V, v5(y+1) = 1 + j, because 5 does not divide w+1.
- So y = -1 mod 5, hence 5 does not divide y-1. Also y = L(1) = 1 mod 4, because 6 divides c.
- The tool gives v5(L(y) - L(1)) = 1 + (1+j) + 0 = k-1 < k.

So L(L(1+c)) != L(L(1)) mod 5^k.

**(b), k >= 2.** Base: k = 1 has period exactly 6 (finite check). Let j = k-2, w = 3·5^j, c = 2w = 6·5^j, and y = F(1+c). Take x = F(1) = 1.
- From I2, y = (L(c) + F(c))/2. So y + 1 = F(w)(5F(w) + L(w))/2 = F(w)L(w+1), using 2L(w+1) = L(w) + 5F(w) from I1.
- By V, v5(y+1) = j. Also 5 does not divide y-1: for j >= 1 because y = -1 mod 5, and for j = 0 because y = F(7) = 13.
- y = F(1) = 1 mod 4.
- The tool gives v5(L(y) - L(1)) = 1 + j + 0 = k-1 < k.

So L(F(1+c)) != L(F(1)) mod 5^k. QED.

## Not proved

**Odd-modulus pattern (conjecture).** For odd m and g in {F, L}, the period of F(g(n)) mod m seems to equal the R_COMP bound. No exception was computed for odd m up to 19,999. The sign argument only explains why R_MULT does not apply: F((c-1)k) = -F(k) rather than F(k). It does not rule out every other way of shortening the period.

## Novelty

Status of the theorem and the search record are in HANDOFF.md, section 4. Being absent from these searches does not make it new, and it is elementary enough that it may well be known.
