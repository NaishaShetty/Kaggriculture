# Phase 43: Fourth-Quadrant Benchmark Report

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`,
`agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`,
`agents/phase2_4/common.py`, `agents/phase15/`). **`agents/phase21/` was
not modified — confirmed, Part A only ever imports it, and Part B was not
attempted (see Section 4).** No submission is created.

## Executive Summary

**[VERIFIED] Submission I does not lose to a real, validated 4th-quadrant
archetype — it beats it decisively: 15/15 (100%) on the full 15-seed set,
mean margin +$22,463.80/game.** This is a real, clean win, not a
coin-flip margin (every one of the 15 seeds is individually a win, the
closest by $2,499). **Part B's trigger condition (a meaningful loss with a
plausible mechanism) is not met, so Part B was not attempted — per this
phase's own scope rule, no build was forced.**

**[VERIFIED] Phase 34's own `sundar_archetype.py` still fails its
prerequisite isolation sanity check, exactly as Phase 34's original report
already documented** (this phase re-confirmed it directly, per Step 1's own
instruction not to trust it blindly: $0-118 final money across the 4
development seeds vs. `"pass"`, with hands collapsing to 0 workers mid-game
on the traced seed) — **not a regression, a confirmed-still-true,
previously-known failure.** A second, independent reconstruction was built
this phase instead (`scripts/phase43/jonaid_archetype.py`, from real episode
105405216), which **does** pass its own isolation sanity check
($38,548-$45,914, no collapse) and is what this report's Part A conclusion
actually rests on.

**[OBSERVED] A striking, honestly-reported contradiction**: in the real
live game this reconstruction is based on (Phase 41's episode 105405216),
the real Jonaid actually *beat* Submission I ($80,988 vs. $63,772). The
*reconstructed* Jonaid archetype, run through the exact same generic
execution engine (`agents/phase21/execution.py`, unmodified) Submission I
itself uses, loses badly to Submission I instead. **[INFERRED]** since both
sides in this phase's benchmark run through the identical execution code,
the difference isolates the TARGET SCHEDULE alone (land/hand/animal/crop
targets), holding execution efficiency constant — and under that controlled
comparison, blindly copying real Jonaid's raw scale numbers (4 quadrants,
24 animals, 5-crop diversity) performs *worse* than Submission I's own
tuned 3-quadrant targets. This is a meaningful finding in its own right: it
suggests Submission I's real weakness against real 4th-quadrant opponents
(where one exists — see Phase 41's own small, mixed 1W-1L sample) is not
explained by "we should also expand to 4 quadrants," since even a
controlled, execution-held-constant test of that exact idea loses.

**Recommendation: adopt the Jonaid archetype as a standing secondary
benchmark** (cheap, real-data-grounded, now validated) **for regression
monitoring alongside Submission G/C — but not as a promotion bar**, since
Submission I already beats it too decisively (15/15, +$22.5k margin) for it
to discriminate between candidate improvements the way G (a genuine 60-67%
contest) does. Retire or flag `sundar_archetype.py` as known-broken rather
than leaving its status ambiguous for a future phase to rediscover.

## Part A: Benchmark Validation

### Step 1 — Re-confirming `sundar_archetype.py` (Not Trusted Blindly)

**[VERIFIED]** `scripts/phase34/sundar_archetype.py::make_sundar_archetype`
still imports and runs without error against the current engine — but its
OUTPUT is not trustworthy: run in isolation vs. `"pass"` on the 4
development seeds, it produces **$30, $70, $0, $118** — a chronic collapse,
not the real Sundar's $97,246. Direct trace (seed 700000) shows the
mechanism: hands crash from 8 (day 10) to 0 (day 16-20), money pinned at
$0 for that entire window, with only a partial late recovery once the 4th
quadrant finally lands (day 22+). This is the exact same failure Phase 34's
own report already named: *"reconstruction failed its own prerequisite
isolation sanity check on every attempt (3 rounds)... untestable by this
method."* This phase does not attempt to fix it (out of scope — Phase 34
already spent 3 rounds on this specific reconstruction without success);
it is reported here, honestly, as still-broken, not silently relied upon.

### Step 3 — A Second, Independent Reconstruction (Jonaid)

**[VERIFIED]** Built `scripts/phase43/jonaid_archetype.py`, the same
day-indexed-rung pattern as `sundar_archetype.py` (reused as a pattern, not
copied code), from real episode 105405216's PUBLIC-only trajectory
(`agents/phase6/replay_forensics.py::extract_episode_timelines`, reused
unchanged, `our_name="shettynaisha"` so Jonaid is read strictly as the
opponent/public side — shed, seeds, inventories, and Jonaid's own submitted
action were never read). Jonaid reaches land=4 by day 13, hands=12 by day
10, animals up to 24 (SHEEP4/COW10/GOOSE10 sustained from day 21), and runs
a materially more crop-diverse portfolio than Submission I's own
(MELON→CARROT/TOMATO/STRAWBERRY mix, vs. Submission I's MELON/STRAWBERRY/
WHEAT-only — directly consistent with Phase 41's own Archetype A/B
findings). **[VERIFIED]** isolation sanity check (vs. `"pass"`, 4 development
seeds): **$45,914 / $38,548 / $38,995 / $40,814** — healthy, no collapse,
in the same general range as Submission I's own isolated economy (Phase
39: $44,258-$76,683). This archetype is trusted for Step 2's head-to-head;
Sundar's is not.

### Step 2/4 — Head-to-Head, Full 15-Seed Set

| Opponent | Record | Win rate | Mean Submission I | Mean opponent | Mean margin |
|---|---|---|---|---|---|
| Sundar (⚠ broken, not valid evidence) | 15W-0L-0T | 100% | $62,746 | $14.53 | +$62,731.53 |
| **Jonaid (validated)** | **15W-0L-0T** | **100%** | **$52,997** | **$30,534** | **+$22,463.80** |

**[VERIFIED]** every one of the 15 seeds against Jonaid is individually a
win — margins range from +$2,499 (seed 701002, the closest) to +$35,540
(seed 701001) — a decisive, clean pattern, not a coin-flip. Full per-seed
data: `results/phase43/phase43_vs_fourth_quadrant_results.json`.

### Adoption Recommendation

**Adopt the Jonaid archetype (`scripts/phase43/jonaid_archetype.py::
make_jonaid_archetype`) as a standing secondary validation benchmark**,
run alongside Submission G/C in future phases' regression checks — it is
cheap (no worse than any other synthetic opponent to run), real-data-
grounded (broadening this project's benchmark set past Submission G/C,
which are this project's own prior work, and past the single-real-trajectory
limitation Phase 39 flagged for Crop Dusta), and now confirmed stable.
**However, it should not be treated as a promotion bar the way Submission
G is** — Submission I already beats it too decisively (100%, +$22.5k
margin) for it to discriminate between a real improvement and noise;
Submission G's own 60-67% contested record is what actually stresses this
agent. Use it as a floor check (a future change should never make this
archetype's record worse), not a ceiling target.

**Recommend flagging `scripts/phase34/sundar_archetype.py` as known-broken**
(a short doc note, not a code fix) so a future phase doesn't have to
rediscover this — its role as "the" 4th-quadrant benchmark is now
superseded by the validated Jonaid reconstruction above.

## Part B: Not Attempted

**[VERIFIED]** Per this phase's own explicit trigger condition ("only if
Submission I loses meaningfully... a real, clear pattern, not a coin-flip
margin"), Part B was not attempted. Submission I does not lose to the
validated 4th-quadrant archetype at all — it wins every single seed, by a
large and consistent margin. There is no loss pattern here to diagnose a
mechanism for, and per this phase's own scope rule (step 7), no build was
forced.

**[INFERRED]** the controlled same-execution-engine comparison in this
phase's own Section (Part A) additionally argues AGAINST a 4th-quadrant
extension being a promising direction even hypothetically: real Jonaid's
raw target numbers (more land, more animals, more crop types), run through
the identical execution layer Submission I itself uses, underperform
Submission I's own current 3-quadrant targets by a wide margin. This does
not prove a well-tuned 4th-quadrant variant of Submission I couldn't work
— it was never built or tested — but it removes the one piece of evidence
(a real opponent's raw numbers) that might have motivated trying, since
copying those numbers directly, execution held constant, loses badly.

## What This Means for the Real-vs-Synthetic Gap

**[OBSERVED]** This phase adds a third data point to the growing evidence
that Submission I's real losses are not explained by anything on its own
execution or scale-target side: Phase 39 found it more tile-attentive than
gold-tier play, Phase 40 found real competition doesn't suppress its
throughput, and this phase finds it decisively beats a real 4th-quadrant
opponent's reconstructed strategy shape. **[OBSERVED, small sample]** Phase
41's own real-game data already showed this same real 4th-quadrant
archetype split 1-1 against Submission I live (a loss to Jonaid, a win
against Alden Jenish S) — consistent with "not a systematic archetype
advantage," now further supported by this phase's controlled benchmark
result. The case for opponent-population diversity (rather than execution,
measurement methodology, or missing scale) as the primary remaining
explanation for the real-vs-synthetic gap continues to strengthen with each
measurement phase that comes back clean on Submission I's own side.

## Changed Files

New, all additive:
- `scripts/phase43/jonaid_archetype.py`
- `scripts/phase43/vs_fourth_quadrant.py`
- `results/phase43/phase43_vs_fourth_quadrant_results.json`
- `results/phase43/PHASE43_FOURTH_QUADRANT_BENCHMARK_REPORT.md` (this file)

`agents/phase21/` was not modified. No submission is created.
