# Pre-registration: do waves add anything beyond noise at the same rate?

Written before any run of this experiment. The question comes from HANDOFF open problem 2.

## Why the earlier comparison could not answer it
off vs base vs polar compared mutation with no mutation. Nothing held the noise level fixed while removing the wave, so a gain could not be credited to waves. Polar also mutates more than base, so base vs polar mixes in the rate.

## Design
- Modes: `off`, `base`, `shuffled`, `polar`, `polar_shuffled`. `shuffled` and `polar_shuffled` run the same code with every phase redrawn at every step, so the noise level has the same distribution but no structure over cells or time.
- 50 runs per mode, T = 150 transfers. Return channel on (`ret=True`) in every mode.
- Seeds are fixed in advance: `sha256("waves-exp-1|<mode>|<i>")`, first 16 hex digits. They are not chosen after seeing anything.
- Runs execute in a seeded shuffled order, so machine load is not tied to mode. The 5 s evaluation alarm depends on the clock, so timeouts are logged and reported per mode.
- Logs go to `s6_patches/runs_v2/`. They are separate from `runs/`, so earlier results are unchanged.

## Primary metric
`finds_all` from each run's footer: distinct (modulus, expression) pairs with worth > 0.

## Primary tests
Two-sided permutation test on the difference of means, 200,000 shuffles, seeded. Holm correction over exactly these three, at alpha = 0.05:
1. `base` vs `shuffled`: do waves matter?
2. `polar` vs `polar_shuffled`: do polarized waves matter?
3. `off` vs pooled (`base`, `shuffled`, `polar`, `polar_shuffled`): does mutation matter?

A 95% bootstrap interval is reported for each difference. "Not significant" means no effect was detected, and the interval shows how large an effect is still possible.

## Secondary, descriptive only (no significance claims)
Distinct finds by (modulus, sequence) instead of by string; finds on mutated steps; mutation counts (to confirm the rates match); resends; timeouts and UNREACHABLE per mode; `polar` vs `base`.

## Rules
- No analysis of outcomes until all 250 runs have finished. Progress checks read only which files exist.
- No runs are added or dropped after seeing results. A crashed run is rerun from the same seed and reported.
- Every result is reported, whichever way it goes.
- The test world was built by the assistant. A result here says nothing about any other domain.
