# Project: Creativity engine ("Formula of Understanding and Creativity")

Read HANDOFF.md first. It has the goal, the state of every stage, the key results and the open problems.

## Rules for working here
- Python 3.14 (the project's .venv), standard library only (no installs needed). Run each script from inside its own folder; paths are relative to the file.
- Never claim a period/explanation that was not computed. Tag numbers COMPUTED / SOURCED / CLAIMED.
- The test world (integer sequences mod m) was built by the assistant, so say so when reporting results.
- waves4.py writes a replayable log to s6_patches/runs/ and no longer touches waves_base.json / waves_polar.json. Those two files are the older 2-run results.
- Novelty comes from s7_novelty/novelty.py, not from memory. n = 1 means "not found by the searches listed", and an unreachable source is UNCHECKED, never novel.
- A proof in s8_proofs/PROOFS.md has not been reviewed by a mathematician; say so when citing it.
- Tests: `python -m unittest discover -s tests` from the project root. Proof checks: `python prove.py` in s8_proofs.
- Next work is listed under "Open problems" in HANDOFF.md. Start from there unless the user says otherwise.
