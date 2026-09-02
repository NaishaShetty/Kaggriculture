# Phase 3.7-C: F-005 Countermeasure

## Candidate: Early Cash-Trajectory Guard

Derived directly from Stage B's root-cause finding: if our own cash falls below a threshold by day 2, halve the crop portfolio's committed tile fraction for subsequent (not-yet-planted) tiles, reducing the future watering burden if a hands-zero window later occurs. Implemented at `agents/phase3_7/f005_liquidity_guard.py`, tested via `agents/phase3_7/adapters/f005_test_agent.py`.

## Result: Rejected — Not a Viable Trigger

Tested against the reconstructed death-spiral seed (852025866) against `passive` and `conservative` synthetic opponents: **the guard never fired** in either case. Cash at day 2 was $572 — above the $200 threshold — because cash does not visibly enter crisis territory until day 4-6, by which point roughly 21-22 tiles are already planted (the intervention window has already closed).

This is not a parameter-tuning problem to iterate past. It is structural: **every episode's early cash trajectory looks broadly similar** (a $0-30 trough around days 3-10 is documented as routine, not anomalous, across this entire project's prior forensics), so there is no early, distinguishing signal that separates "this will recover" from "this will not" before the crop commitment is already locked in. A viable countermeasure would need either a different, earlier-discriminating signal (not identified this session), or the ability to act on already-planted tiles — which the external config-mutation architecture used throughout Phase 3.3-3.6 does not provide (already-planted, still-viable tiles do not retroactively vanish if the crop config later changes).

## Conclusion

**No viable countermeasure was found this phase. F-005 remains NOT SOLVED, honestly.** This was not forced into a false "partial fix" — the brief's own standard ("do not invent a solution" when the cause/lever isn't sufficiently supported) is applied here to the *countermeasure*, not just the diagnosis: a countermeasure that never fires under realistic conditions is not a fix, and is not claimed as one.
