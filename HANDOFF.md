# HANDOFF: continue in PyCharm (new chat)

Date of handoff: 2026-11-08, corrected the same day after an audit in Claude Code. Sections 3 to 5 describe the current state.

## 1. Goal (user's words, condensed)
Develop the framework **Object1 x Object2 + Bridge -> Novel Solution** into an AI creativity engine that must:
1. produce patterns **not found on the web** (novelty),
2. **explain** them with a **sourced rulebook** (explanation = understanding; "it just works" is not an explanation),
3. check every idea with a **return-to-sender** loop.
The user wants the idea space in **3D** (X, Y, Z) with **noise as waves** that disturb data cells while they travel. Rules are assumed always right (no human-error handling for now). The AI asks Who / What / Where / Why / How.
The user dropped the "memory box" idea and kept return to sender.

## 2. Core model (math)
- **Rule** r = (L -> R, WHAT, WHERE, WHY, WHO). HOW is produced per use (which rule, which part, which substitution).
- **Explained(a = b)** iff both sides reach the same normal form using rules only. Stuck parts are **gaps**; each gap is the next web search.
- **Return to sender** gives reply (w, e, n): works (computed by the world), explained (rulebook), novel (web). Cube corners: NEW (1,1,1), KNOWN (1,1,0), DISCOVERY (1,0,1), GAP (1,0,0), CONTRADICTION (0,1,*), FALSE (0,0,*).
- **Idea space**: X = breadth/rules, Y = areas (Y>=2 is a bridge), Z = depth.
- **Wave noise**: eta(r,t) = sum_i A_i sin(k_i.r - w_i t + phi_i) (3 waves), d = |eta|/sum A. Outbound transit mutates with prob d; corrupted replies are caught by SHA-256 and resent (costs time, never changes truth). Randomness from os.urandom. Sigma per axis: x1.25 on safe, x0.75 on FALSE.
- **Polarized waves** (stage 6): four channels RULE, AREA, DEPTH, MOD, one wave each; amplitude x1.25 if useful, x0.8 if bad, clamp [0.3, 2].
- **worth** = log2(naive bound / observed period) / size. Shortest-form canonical check before any novelty search. Exact vs partial explanation: a looser bound is a DISCOVERY signal, not a pass.
- **Test domain**: integer sequences mod m built from blocks fib, luc, tri, sq, ds (digit sum). Merge rules: M_SQ, M_TRI, M_DS (only if modulus divides 9), M_MOD. Exact period via Newton forward differences per residue class.
- **Symmetry ladder** (explains the exact period of compositions like F(L(n)) mod m): R_COMP, **R_MULT** (g(n+h) = a*g(n) mod P and f(a*k) = f(k) mod m => period divides h; per prime-power factor, a = c +/- 1 where F(c)=0, L(c)=+/-2; on composite m directly this accounts for only 12 of the 42 tightened cases, so split by R_CRT first), R_QUOT (quotient tower), affine maps, R_CRT (lcm over prime powers), R_PARITY, R_ZERO (rank of apparition, chained), R_CLASS (residue class).
- Identities used: Lucas U,V (Q=-1, D=P^2-4Q); Pisano period lcm for coprime moduli; L(-n) = (-1)^n L(n); F(10) | F(10k); L(n+6) = 20F(n)+9L(n); L(9k) = L(k) mod 25.

## 3. Folder map (PyCharm project root = this folder; run each script from inside its own folder)
| Folder | What it is | Entry points |
|---|---|---|
| s1_rulebook | Peano-rule rewriting engine: rules N0, D1, D2, A1, A2 with WHO URLs; send() returns EXPLAINED / WORKS-BUT-UNEXPLAINED / FALSE + gap list | `python rulebook.py` |
| s2_cube_v1 | 3D cube engine v1 (rulebook R_FIB, R_LUC, R_TRI, R_MOD, R_DS, R_COMP, R_ID; bound(), world(), move(), corner()) | `python engine.py next`, `record`, `status` (needs an argument) |
| s3_waves_v2 | v2: wave-noise transit, worth >= 0.3, NO-GAIN skip, shortest(), transfer(), decide(); R_TRI_ODD | `python v2.py next`, `record`, `log` (needs an argument) |
| s4_merging | Merging blocks (merge.py: ATOMS, to_nf, prep, period, explain, show_nf), v3.py run, verify*.py (326/326 agree) | `python v3.py` (overwrites run3.json), `python verify3.py` |
| s5_symmetry | R_MULT test: 236/236 exact; derive.py verifies S1, S3, S4 | `python mult.py`, `python derive.py` |
| s6_patches | Patch work: why.py (identity-only why-chain, 236/236), sym2..sym8 (ladder), waves4.py (waves: base, polar, off; logs and replay) | see order below |
| s7_novelty | novelty.py: code-based check (OEIS, arXiv, Crossref; general web is attempted); hunt.py: runs logged finds through the (w, e, n) cube; results in hunt_results.json | `python hunt.py` |
| s8_proofs | PROOFS.md: theorem for mod 5^k; prove.py: checks its steps, plus exact-period certificates with lower bounds | `python prove.py` |
| tests | Novelty and wave-replay tests, no network used | `python -m unittest discover -s tests` from the root |

Dependencies between folders are by relative path (`_P(...)` helper at the top of each file). Standard library only.

### Run order in s6_patches
```
python sym2.py                    # builds sym2.json (cycles/shift pairs)
python sym3.py depth2 ; python sym3.py depth3
python sym4.py depth2 ; ... sym5 ... sym6 ... sym7 ... sym8   # each reads the previous stage's json, writes its own
python waves4.py base 150 10 ; python waves4.py polar 150 10 ; python waves4.py off 150 10   # logs to runs/<mode>_<seed>.jsonl; each eval has a 5 s alarm
python waves4.py replay runs/<file>.jsonl    # reruns from the seed and compares every step
```
The `*_depth2.json` / `*_depth3.json` files are already included, so you only need to rerun if code changes. `waves4.py` no longer writes `waves_<mode>.json`; those two files hold the older 2-run results.

## 4. Key results (all COMPUTED in a world the assistant built)
- Rulebook loop: 1+1=2 EXPLAINED with sourced rules; removing the step rule -> WORKS-BUT-UNEXPLAINED with the gap `S(0)+S(0)`; adding it back -> EXPLAINED; 1+1=1 -> FALSE.
- Merging engine: exact periods proven, 326/326 agreement with brute force. 246 of the 572 tested expressions got no proof, mostly because of digit sums. (`verify3.py` compares 325; the last one's world is too short, and period 182 was confirmed separately.)
- **R_MULT: 236/236 exact**, 42 of them beyond R_COMP. Printed why-chain (why.py) is identity-only: 236/236, and 960/960 on new moduli m = 61..300. Covers Fibonacci/Lucas only. It proves that the period divides a value; exactness came from comparison with the computed period, and `prove.py` certificates add a lower bound where run.
- Symmetry ladder: **969/969 two-deep**, **2,324/2,367 (98.2%) three-deep**. R_COMP alone gets 831 and 1,786, so on the harder cases that is 138/138 and 538/581 (92.6%). It never went below the truth, even with every rule run on every case. These rules search computed tables rather than deriving from identities. 6 two-deep and 8 three-deep tribonacci cases were skipped (cycle over 20,000).
- Waves, 150 transfers x 10 logged runs per mode (`s6_patches/runs/`; 30/30 replay exactly): mean distinct finds off 18.0, base 25.0, polar 27.4. No difference is clear (permutation p = 0.23 off vs base, 0.11 off vs polar, 0.71 base vs polar). Polar makes more mutations (122 vs 73). Unreachable counts are equal (12.2 vs 12.0). The earlier 2-run result (33 vs 27, DEPTH best, double UNREACHABLE) did not reproduce. An earlier unlogged 10-run comparison also found no advantage (26.0 polar vs 29.1 base, all steps).
- Novelty (s7_novelty, OEIS checked 2026-11-08): the F(F(n)) period table is **OEIS A356550**, 59/59 values match, so it is not new; that entry gives only an upper bound. No OEIS match for the L(L(n)) or L(F(n)) or F(L(n)) period tables, L(L(n)) mod 25, or F(Q(n)) mod 27.
- Hunt over the logged finds: 439 expressions; the 164 of size <= 3 form 107 families: 14 KNOWN, 87 NEW, 6 TRIVIAL (no proved table: digit sums); none UNCHECKED. KNOWN means the first 12 period terms match an entry, which can be a coincidence (tri(n^2) matches a coresilience denominator). NEW means not found by those searches, and most are probably novel only by absence. General web search from code was blocked (DuckDuckGo HTTP 202), so that source is not part of the hunt.
- **Theorem (s8_proofs/PROOFS.md; not reviewed by a mathematician):** for k >= 2, L(L(n)) mod 5^k has exact period 6*5^(k-2) and L(F(n)) mod 5^k has exact period 6*5^(k-1). Identities are checked symbolically, steps on concrete k, the theorem computed to k = 6. Claude derived it from the engine's L(L(n)) mod 25 find; the engine did not produce it. Novelty: not found by OEIS, arXiv, Crossref or general web searches on 2026-11-08. Incomplete: the MDPI paper "Period Lengths of the Incomplete Fibonacci and Incomplete Lucas Sequences Modulo m" returned 403, the Lengyel PDF was unreadable, and four Crossref titles on Lucas periods were not opened. It is elementary and may be known.
- Open pattern, not proved: for odd m and g in {F, L}, F(g(n)) mod m never fell below the R_COMP bound, for all odd m <= 19,999.
- The 43 unexplained three-deep cases are all off by exactly a factor of 2; 34 are twin pairs differing only in an innermost F or L, and 9 involve tribonacci.

## 5. Open problems (priority order)
1. **43 three-deep cases** have a proven period but no complete why-chain (need mixed-rule chains). Start from the factor-of-2 pattern in section 4.
2. **Do waves help at all?** Off vs on is not clear at 10 runs, and finds vary widely. Run more seeds (logged) before tuning. Then stabilise amplitudes (fix the total, normalise).
3. **Extend the printed why-chain** to Pell, tribonacci and polynomial-argument atoms (R_MULT is proven only for Fibonacci/Lucas). Add `prove.py` lower-bound certificates to the engine's own output.
4. **Finish the novelty check.** OEIS, arXiv and Crossref work from code. Still needed: a general-web source code can use, opening the REVIEW candidates, and a way to tell a coincidental OEIS match from a real one. Have a person review PROOFS.md and search for the theorem in the literature.
5. **Fuzzier domain** (simple mechanics, scheduling): the hard step is matching plain-language problems to rule patterns. Untested.
6. The test world is built by the assistant; use an external world if possible.
7. Bookkeeping: `mbox.py` in the old memory-box folder still has the failed noisy-OR (superseded; ignore).

## 6. Honest limits
Self-graded scores did not track quality in earlier runs; stated confidence ran 0.2-0.4 above accuracy. Evidence only counts if it comes from code or opened pages.

## 7. Links
- Progress doc (Claude Doc, latest): https://claude.ai/artifact/Co4kSJbPUwtdnN2iZRXA9c
- Earlier progress doc (v1-v5): https://claude.ai/artifact/GtD4aqW3m8feEzghjCJ7Fo
- Rulebook sources: https://en.wikipedia.org/wiki/Proofs_involving_the_addition_of_natural_numbers , https://en.wikipedia.org/wiki/Peano_axioms
- LLM prompt: PROMPT_FOR_LLMS.md in this folder.

## 8. How to start the new chat in PyCharm
Open this folder as the project, start Claude Code there (it reads CLAUDE.md), and say: "Read HANDOFF.md and continue with open problem 1" (or whichever you choose).
