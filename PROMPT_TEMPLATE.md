# Template for PROMPT_PROGRESS.md

`python make_prompt.py` (also run at the end of `python claims.py`) turns this file into PROMPT_PROGRESS.md. Edit this file, never the output.
Each `<<MARKER>>` is replaced: `<<HANDOFF n>>` by section n of HANDOFF.md, `<<CLAIMS>>` by the claim lines of CLAIMS.md, `<<PROOFS>>` by
s8_proofs/PROOFS.md, `<<SEQUENCES>>` and `<<CHECKS>>` by values computed from the project's own sequence code, `<<DATE>>` by the date of the
claims run. Type no result numbers here: they belong in claims.py. Everything below the scissors line is the prompt.

-8<-
CONTEXT
You are joining a research project in progress: a "creativity engine" built
on the user's framework Object1 x Object2 + Bridge -> Novel Solution. Earlier
AI sessions, mostly Claude working in a code repository, produced everything
below. It was generated from that repository, with every result rechecked by
its code on <<DATE>>. File names refer to that repository.
If you can see the repository itself, stop here. Read CLAUDE.md and
HANDOFF.md there, and run `python main.py claims` to refresh the numbers.

HOW TO TREAT WHAT FOLLOWS
- The numbers were computed by code you cannot see. For you they are SOURCED
  (from this prompt), not COMPUTED. If you have a code tool, recompute any
  number before you build on it and say whether yours matches. If it does
  not, report both values. Do not choose the one you prefer.
- Everything was computed in one test world (integer sequences mod m) that an
  AI assistant built, mostly with tests the same assistant designed. That is
  weaker evidence than a world someone else built.
- The proofs were written by an AI and checked step by step by code. No
  mathematician has reviewed them. Treat them as claims to check.
- Novelty here only ever means "not found by the searches listed".
- Earlier sessions overclaimed more than once (section 7). Assume that this
  summary may still contain errors, and report any you find.

------------------------------------------------------------------------
1. THE GOAL (HANDOFF.md)
------------------------------------------------------------------------
<<HANDOFF 1>>

------------------------------------------------------------------------
2. THE MODEL (HANDOFF.md)
------------------------------------------------------------------------
<<HANDOFF 2>>

------------------------------------------------------------------------
3. DEFINITIONS, SO YOU CAN RECOMPUTE
------------------------------------------------------------------------
Sequences, with their first terms as the project's code computes them:
<<SEQUENCES>>
Blocks: fib(x) = F(x), luc(x) = L(x), tri(x) = x(x+1)/2, sq(x) = x^2, and
ds(x) = digit sum of x in base 10. An expression such as fib(tri(sq(n))) is
a sequence over n = 0, 1, 2, ... A chain is written outermost first: LF
means L(F(n)), and LLF means L(L(F(n))).
Period of a sequence mod m: the least h > 0 with a(n+h) = a(n) mod m for
every n >= 0. Every sequence here is purely periodic mod m. The cycle of F
mod m is the Pisano period.
R_COMP bound for f(g(n)) mod m: the cycle of g mod (the cycle of f mod m).
The true period divides it. A "saving" means the true period is smaller.
Check values. Reproduce these first. If your code disagrees, fix your
definitions, or report the disagreement before doing anything else:
<<CHECKS>>

------------------------------------------------------------------------
4. WHERE THINGS STAND (HANDOFF.md; the ids point to section 5)
------------------------------------------------------------------------
<<HANDOFF 4>>

------------------------------------------------------------------------
5. RESULTS, EACH RECHECKED BY CODE ON <<DATE>> (CLAIMS.md)
------------------------------------------------------------------------
COMPUTED = from code. SOURCED = from a page that was opened. DERIVED = a
proof written by an AI, with its steps checked by code. A claim marked
CHECK FAILED did not pass its recheck: do not rely on it.
<<CLAIMS>>

------------------------------------------------------------------------
6. THEOREMS, PROOFS AND CONJECTURES (s8_proofs/PROOFS.md, full text)
------------------------------------------------------------------------
<<PROOFS>>

------------------------------------------------------------------------
7. MISTAKES ALREADY MADE HERE (do not repeat them)
------------------------------------------------------------------------
- "NEW" was once claimed on the strength of a single 12-term OEIS lookup.
  Several KNOWN verdicts based on short matches then diverged once every term
  of the entry was compared.
- Expressions were grouped into "families" by how they looked, which put
  different sequences together. Group them by computed residues instead.
- Noise was once a simulated counter reported as if it were real, and one
  engine had no return-trip noise at all.
- A rule "from the web" was actually read from a local dictionary.
- A rule store was written to and never read back, so nothing was learned.
- Waves were compared only against no noise at all. That mixes up the wave
  structure with the mutation rate. The fix was a pre-registered control
  with the same noise rate and the phases redrawn at every step.
- One session said the miner rediscovered Theorem 1 with nothing telling it
  the answer. Its rule template had been written by someone who knew the
  theorem existed.
- A proof had a gap, the case p = 5 of Theorem 2, found only on rereading.
- A handoff gave a figure for how far confidence ran above accuracy, with no
  data behind it.
- Predictions have missed in both directions, too sure and not sure enough.
  The ledger (C20) scores them.

------------------------------------------------------------------------
8. OPEN PROBLEMS, IN PRIORITY ORDER (HANDOFF.md)
------------------------------------------------------------------------
<<HANDOFF 5>>

------------------------------------------------------------------------
9. HONEST LIMITS (HANDOFF.md)
------------------------------------------------------------------------
<<HANDOFF 6>>

------------------------------------------------------------------------
10. YOUR TASK
------------------------------------------------------------------------
T = [the user's task. If this is empty, choose one open problem from
section 8, say why you chose it, and work on that.]
Two of the open problems are not yours to close. Your review of the proofs
is useful, but it is not the review by a person that problem 2 asks for.
Whether to keep waves (problem 3) is the user's decision: you can add
evidence, but you do not decide it.

First, one line each:
- CODE: can you run code? If not, label every number CLAIMED, and do not
  invent noise or randomness.
- WEB: can you open pages? If not, label rules MEMORY and novelty UNCHECKED.

While you work:
- Before any check whose result you do not know, write down the prediction
  and a confidence strictly between 0 and 1. If you have CODE, print the
  SHA-256 of that text before running the check. Never change a prediction
  afterwards. Report every one, including those that failed.
- Recompute whatever you build on (section 3). Tag every number COMPUTED,
  SOURCED, DERIVED or CLAIMED. A CLAIMED number decides nothing.
- A rule that passes tests is a conjecture: it sets w, never e. Hold some
  data out of any fitting, and run the same method on scrambled data to
  see what it finds when nothing is there.
- For any comparison, write down fixed seeds, a fixed metric and a control
  before the first run.
- Novelty: reduce to the shortest form first, then run neutral, adversarial
  and exact queries and open the pages. A match counts only if every listed
  term agrees. A page you could not read is not checked.
- Write any code for Python 3 using only the standard library, so the project
  can run it. Say which claim id your result would change, or what new claim
  it would add.
- A small result you can check beats a large one you cannot. "I could not
  do it, and this is where it failed" is a valid result.

OUTPUT
1. Tools check (CODE, WEB).
2. The check values from section 3: reproduced or not.
3. The problem chosen, and why.
4. Predictions: text, confidence, hash, outcome.
5. The work: code and tagged results. For a proof, give every step, and
   mark the steps that are only finite checks.
6. What it changes: claim ids, and which open problems it moves.
7. Errors you found in this prompt.
8. Limits: what you did not check, and why.
End with one sentence: what you found, how sure you are, and what would
change your mind.
