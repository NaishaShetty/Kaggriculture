# Phase 3.6-G: Submission C Packaging

## Decision: No Submission C

Per the brief's explicit rule (section 11): *"If no candidate satisfies this: DO NOT FORCE A PROMOTION. Keep Submission B as champion."* and (section 3.6-G): *"Only if the challenger passes the evidence gate: Create Submission C... If the candidate fails promotion, DO NOT package it as the new champion."*

No candidate passed the evidence gate:
- All 5 adaptive scaling-response candidates (B1-B5) underperformed Submission B's existing fixed response in every tested scenario (Stage B/C).
- The F-003 mechanism was identified and precisely evidenced, but no countermeasure was designed, let alone validated (Stage D) — explicitly deferred per the brief's own instruction not to build a fix before the mechanism is sufficiently supported.

**Submission B remains the champion.** No new `main.py`, no new submission archive was built or packaged this phase — not even as an "experimental artifact," since none of the Phase 3.6 candidates demonstrated behavior worth shipping even experimentally (the brief's allowance for packaging a failed candidate "as an experimental artifact" was considered and declined: shipping a candidate that measurably loses money relative to the control, purely to have a Submission C, would not be scientifically honest and was not requested by any evidence found this phase).

## What Exists Instead

- `agents/phase3_6/` — the full, tested, documented experimental codebase (detector reuse, 5 response candidates, 4 test archetypes, 1 adapter), retained as a research artifact for Phase 3.7, not wired into `main.py`.
- `kaggriculture_phase3_5_competitive_v2_submission_B.tar.gz` (repo root, from Phase 3.5) remains the current, valid, submittable package — unchanged by this phase.

## If Phase 3.7 Produces a Validated Candidate

The packaging process is already proven (Phase 3.5's `scripts/phase3_5_build_submission.py` pattern: enumerate required files, `tar.gz` with `main.py` at the root, cold-process fresh-directory smoke test, extract-and-run validation of the actual built artifact) and can be reused directly once a genuinely validated Submission C candidate exists.
