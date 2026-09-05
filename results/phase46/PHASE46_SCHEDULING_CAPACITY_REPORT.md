# Phase 46: Worker-Turn Scheduling Capacity — the Root Cause Behind Four Independent Rejections

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`,
`agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`,
`agents/phase2_4/common.py`, `agents/phase15/`, `agents/phase21/`). All new
code lives in `scripts/phase46/`; all new results in `results/phase46/`.
Per this phase's own three-sequential-parts structure, Part C was attempted
because Part B alone left the escape reduction modest and mixed (see
Section 3) — neither part is forced past what the evidence supports.

## Executive Summary

**[VERIFIED] Part A precisely re-confirms and sharpens Phase 30/45's shared
diagnosis**: at Submission I's real operating scale, FEED's shortfall is
DOMINATED by losing the same-tier nearest-worker race to WATER (62.9%-65.9%
of FEED-relevant turns across two full 30-day trajectories), not by
outright worker exhaustion (24.1%-27.2%) — these are the two distinct
failure modes the brief asked to separate, and they call for different
fixes: a priority-ordering fix for the dominant one, more capacity for the
smaller one. Idle-action fraction reconfirms Phase 30's own ~7% finding at
this later phase's larger animal/crop scale (7.0%-9.3%).

**[VERIFIED] Part B (FEED reprioritized to a new tier strictly ahead of
WATER, tier 0.5) is a real but modest, mixed improvement**: mean escaped
animals on the 4-seed isolated screen dropped 8.25→7.50 (individual seeds
moved in both directions), final owned count barely moved (9.5→9.0), and
the isolated economy was a statistical wash (+0.72%). It does NOT close
most of the gap to the target rung (17). Idle fraction and crop-tile
throughput did not regress (idle 0.0795→0.0747, crop_fraction
0.2273→0.2291) — the self-defeating-feedback-loop failure mode Phase 36
found once was watched for directly and did not recur **in this specific
form**. **[VERIFIED, disclosed honestly] A more aggressive version — merging
FEED into HARVEST's own tier 0 rather than giving it a distinct tier ahead
of WATER — was tried first and IS exactly that self-defeating failure
mode**: -89.5% mean isolated money, idle fraction roughly doubling
(0.0795→0.1684), and escapes going UP, not down (8.25→14.25), because FEED
(and its WHEAT fetch entries) then competed directly with time-sensitive
crop harvests for the same nearest-worker pass. This was reverted before
any further validation; the tier-0.5 design is what proceeded.

**[VERIFIED] Part C (further capacity-aware BUY_ANIMAL throttle, capping
owned+in-flight animals at 0.7× current hand count) reduces escapes
further** (mean 8.25→6.25, a ~24% cut) at an essentially flat isolated
economy (-0.01%), by design trading a SMALLER final animal count (9.5→8.0
mean) for fewer chronic escapes, exactly the goal the brief specified.

**[VERIFIED] Full 15-seed head-to-head validation is a decisive, clean
win for Part B, and a comparable win with one trade-off for Part B+C.**
Part B (`feed_priority`) recovers 4 of baseline's 5 losses against
Submission G (10/15→14/15, mean margin $4,031→$7,345, +82%) while
introducing ZERO new losses on any seed baseline previously won, and
improves margin against both Submission C (+37%) and Jonaid (+24%) while
staying 15/15 against both. Part B+C (`feed_priority_throttled`) reaches
the same 14/15 record against Submission G with an even larger margin
($8,223) and the best margin against Submission C ($38,145), but does so
by fixing all 5 of baseline's original G-losses while introducing one NEW
loss on a seed (700002) baseline had actually won — a different, not
strictly better, trade-off. **Recommendation: Part B alone (FEED
tier-0.5 reprioritization, without the animal-purchase throttle) is the
cleaner, fully non-regressing candidate — ready to package.** Full detail
in Section 4.

**[VERIFIED] Retest of Phase 42's CARROT/TOMATO slice through the new
execution layer is a genuine negative, not a positive** — running Phase
42's exact, unmodified day-15 slice through Part B's FEED-priority
execution layer instead of the original pacer produced -4.42% mean
isolated money (worse than Phase 42's own original +0.08% wash), and 3 of
4 seeds sold ZERO carrot/tomato units at all. Fixing the FEED/WATER
scheduling bottleneck does NOT retroactively rescue this specific rejected
addition — its blocker (a BUY_SEED cash-flow collision, per Phase 42/45)
is a different mechanism than the one this phase fixed. Full detail in
Section 5.

## 1. Part A: Precisely Characterizing the Bottleneck

### Methodology

Extended Phase 30's own idle-action-fraction capacity check
(`results/phase30/PHASE30_FERTILIZER_REPORT.md` Section 2 — a raw
action-idle-fraction measurement, isolated vs. `"pass"`) across two full
30-day/719-turn trajectories at Submission I's actual shipped scale (11
hands, up to 12-13 owned animals, 50+ crop tiles): seed 700000 isolated
(vs. `"pass"`) and seed 701002 vs. Submission G — the same two conditions
Phase 45's own animal-count trace used, for direct continuity.

`scripts/phase46/capacity_probe.py` is a pure-measurement instrumented copy
of `scripts/phase36/paced_execution.py::make_paced_execution_agent`
(Submission I's own shipped execution logic, imported via composition, not
modified — the task list, tier ordering, and greedy nearest-worker matching
are byte-identical). Every turn, before and after the tier-1 (FEED/WATER)
assignment pass, it records: how many workers were free entering tier 1,
how many FEED and WATER task entries existed, how many of each got
assigned, and classifies the turn's FEED outcome into one of four buckets:

- `no_feed_needed` — no animal needed feeding this turn
- `worker_exhaustion` — FEED entries existed, but tier 0 (HARVEST/
  HARVEST_ANIMAL) had already claimed every single worker before tier 1
  was even reached
- `assignment_race_loss` — FEED entries existed, at least one worker was
  still free entering tier 1, but some FEED entries ended the turn
  unassigned anyway (WATER or other FEED entries won the nearest-worker
  comparison)
- `fully_served` — every FEED entry that existed got assigned

### Findings

| Metric | Isolated (seed 700000) | vs. Submission G (seed 701002) |
|---|---|---|
| Idle-action fraction | **[VERIFIED] 7.02%** | **[VERIFIED] 9.28%** |
| FEED-relevant turns (of 719) | 658 | 651 |
| `assignment_race_loss` | **[VERIFIED] 62.92%** of FEED-relevant turns | **[VERIFIED] 65.90%** |
| `worker_exhaustion` | **[VERIFIED] 27.20%** | **[VERIFIED] 24.12%** |
| `fully_served` | 9.88% | 9.98% |
| Turn-level FEED service rate (assigned/entries) | 14.97% | 13.84% |
| Max owned animal count reached | 12 | 10 |

**[VERIFIED]** Phase 30's own ~7% idle-worker-turn finding reproduces
almost exactly at this later phase's actual animal/crop scale (7.0-9.3%,
vs. Phase 30's original 7.0% on a pre-fertilizer, pre-Phase-36-pacer
build) — confirming the capacity ceiling described across Phases 30/33/42/45
is the same one, not four unrelated coincidences.

**[VERIFIED]** The two failure modes are NOT evenly split, and the split
answers the brief's own question about which fix category applies:
**assignment-race loss outweighs worker exhaustion by roughly 2.4-2.7x**.
This means the DOMINANT mechanism is not "there simply aren't enough
worker-turns" (that would show up as high `worker_exhaustion`) but "FEED
and WATER are tied for priority and WATER (or another FEED entry) is
closer often enough to win the nearest-worker comparison." A priority-
ordering fix (Part B) directly targets the dominant mechanism; a pure
capacity increase (more hands) would only address the smaller
`worker_exhaustion` slice.

**Caveat, disclosed honestly**: the turn-level FEED service rate (~14-15%)
looks low in absolute terms, but this is expected and not itself alarming
— `fed_today` only needs to flip true ONCE per day, and a FEED task
persists across every turn of that day until it does, so most FEED entries
in the raw tally are the SAME underlying animal being re-counted across
many turns of an unsuccessful day, not a per-animal per-day failure rate.
The relevant comparison for this phase's purposes is the RELATIVE outcome
mix (race-loss vs. exhaustion), not the raw service-rate percentage, and
that comparison is stable across both trajectories measured (round 63%/65%
race-loss, 27%/24% exhaustion).

### Step 2: Surplus/Deficit at Real Animal Counts

**[INFERRED]** At the 10-13 owned-animal scale Submission I actually
reaches (matching Phase 45's own 13-purchased trace), the idle fraction
staying positive (7-9%, not negative or near-zero) means the agent is NOT
in a state of total worker-turn exhaustion most of the time — exhaustion
only explains roughly a quarter of FEED-relevant turns. **[INFERRED]**
Because the dominant mechanism is a same-tier priority race rather than a
raw shortage, no plausible amount of ADDITIONAL hands would fully close the
gap on its own without also fixing the priority tie — Phase 30/32 already
found that manufacturing capacity via extra hands costs more in Fibonacci
hire premiums than it returns, and Part A's own split here explains WHY: a
large fraction of the shortfall (the race-loss two-thirds) isn't a hands
problem at all. **[HYPOTHESIS]** Closing just the smaller worker-exhaustion
slice (the ~25-27% of FEED-relevant turns where zero workers were free
entering tier 1) would plausibly need on the order of 1-2 additional hands
at this scale (a rough translation from the ~7-9% idle-turn deficit,
not a precisely measured requirement) — but this was not tested directly,
since Part B's priority-ordering fix is cheaper and targets the larger
mechanism first, per this phase's own sequencing.

## 2. Part B: FEED Priority Reordering

### Design

`scripts/phase46/feed_priority_execution.py` starts as an exact copy of
`scripts/phase36/paced_execution.py` (Submission I's shipped, validated
BUY_ANIMAL cash pacer — composed/wrapped, not reimplemented, per this
phase's explicit constraint) and changes exactly one line: FEED's priority
tuple changes from `(1, t, "FEED", "WHEAT", None)` to `(0.5, t, "FEED",
"WHEAT", None)` — a new, distinct tier strictly between HARVEST/
HARVEST_ANIMAL (tier 0) and WATER (tier 1). Every other line — BUY_ANIMAL
pacing, HIRE/BUY_LAND/BUY_SEED, the rest of the priority scheme, the greedy
nearest-worker matching algorithm itself — is byte-identical.

**Why tier 0.5, not literal tier 0** (justified directly against Part A's
own findings, and an honestly-reported failed first attempt): the brief's
letter suggests moving FEED to "priority tier 0 (alongside HARVEST/
HARVEST_ANIMAL)". This was tried first, literally, and is a **decisive
regression**: -89.5% mean isolated money on the 4-seed screen (Section 3),
because merging FEED into HARVEST's own tier means FEED (and its WHEAT
fetch entries, since `req_min_priority` elevates with the task) directly
compete with time-sensitive crop harvests for the exact same nearest-worker
pass — starving HARVEST instead of fixing FEED, the self-defeating
substitution this phase was explicitly told to watch for (the same
category of failure Phase 36 found once when it coupled HIRE to the animal
feed-buffer term). Part A's own diagnosis (Section 1) shows the dominant
FEED failure mode is losing to WATER specifically, not to HARVEST — so the
brief's own alternative phrasing ("or otherwise gives it precedence over
WATER specifically") is the design actually followed: a new tier (0.5)
gives FEED strict precedence over WATER without ever contesting HARVEST's
own tier.

### Validation: 4-Seed Isolated Screen

| Candidate | Mean money | Δ vs. baseline | Mean escaped | Mean final owned | Mean idle_fraction | Mean crop_fraction |
|---|---|---|---|---|---|---|
| Baseline (Submission I shipped) | $59,144.50 | — | 8.25 | 9.50 | 0.0795 | 0.2273 |
| **Part B: FEED tier 0 (literal merge, FAILED attempt)** | $6,195.75 | **-89.52%** | 14.25 | 10.00 | 0.1684 | 0.2146 |
| **Part B: FEED tier 0.5 (final design)** | $59,569.75 | +0.72% | 7.50 | 9.00 | 0.0747 | 0.2291 |
| Part B+C: FEED tier 0.5 + BUY_ANIMAL throttle | $59,140.00 | -0.01% | 6.25 | 8.00 | 0.0792 | 0.2324 |

**[VERIFIED]** The literal tier-0 merge is a clean, decisive negative — not
promoted, not carried into head-to-head validation, reported honestly as a
failed design per this phase's own instruction not to force a positive
spin.

**[VERIFIED]** The tier-0.5 design is a real but modest, MIXED improvement
in escapes (per-seed: 700000 8→9 worse, 700001 9→5 better, 700002 6→10
worse, 700003 10→6 better — mean improves 8.25→7.50 but not uniformly), a
statistical wash economically (+0.72%, well within this project's own
noise band for a 4-seed screen), and — importantly — does NOT regress
idle_fraction or crop_fraction; if anything both moved slightly favorably.
**This does not close most of the gap to the target rung (17)** — final
owned count stays essentially flat (9.5→9.0) — so per this phase's own
brief, Part C was attempted rather than stopping here.

## 3. Part C: Capacity-Aware BUY_ANIMAL Throttle

### Design

`scripts/phase46/feed_priority_throttled_execution.py` is Part B's file
plus one further, additive change to the BUY_ANIMAL section: no further
animal purchase is made once owned+in-flight animal count already meets or
exceeds `ANIMAL_TO_HAND_THROTTLE_RATIO (0.7) * current hand count`. This
directly implements the brief's own suggested proxy ("current owned-animal
count relative to available hands") rather than a live escape-rate
estimator — the engine gives no direct "an animal escaped this turn"
signal inside `obs` for the agent to react to causally in real time; escape
counts can only be reconstructed after the fact from ledger data. The
throttle re-arms every turn (not a one-time cap), so a purchase becomes
possible again once natural escapes bring the owned count back under the
cap.

### Validation: 4-Seed Isolated Screen (see table above)

**[VERIFIED]** Escapes drop further (8.25→6.25 mean, a ~24% reduction from
baseline) at an essentially flat isolated economy (-0.01%) and no
idle/crop-throughput regression. **[OBSERVED, as designed]** Final owned
animal count is intentionally SMALLER (9.5→8.0 mean) — trading count for
reliability, exactly the goal the brief specified ("a smaller,
RELIABLY-FED animal count rather than a larger chronically-escaping one").

**Honest framing**: this is still a modest, not decisive, improvement —
neither Part B nor Part B+C makes a dramatic dent in the underlying
scheduling-capacity ceiling Part A quantified. Both are genuine,
measured, non-regressing changes; neither singlehandedly "solves" the
animal-escape problem at this agent's scale.

### Confirmation at Full 15-Seed Isolated Scale

`scripts/phase46/feed_priority_screen_isolated_full.py` reruns the same
three-way isolated-economy comparison across the full 15-seed set
(development + validation + held-out), closing the "don't promote off a
4-seed screen" gap for the isolated-economy side too (the head-to-head
side is the mandatory one per Phase 17's rule; this is an extra
confirmatory pass, not a substitute for it):

| Candidate | Mean money (15 seeds) | Δ vs. baseline | Mean idle_fraction | Mean crop_fraction | Mean escaped | Mean final owned |
|---|---|---|---|---|---|---|
| Baseline | $62,920.20 | — | 0.0841 | 0.2336 | 8.40 | 9.13 |
| **Part B (feed_priority)** | **$63,286.07** | **+0.58%** | 0.0761 | 0.2315 | 7.13 | 8.60 |
| Part B+C (feed_priority_throttled) | $60,767.00 | -3.42% | 0.0780 | 0.2322 | 6.47 | 8.33 |

**[VERIFIED]** At full 15-seed scale, Part B holds up exactly as the
4-seed screen suggested: a small positive economically (+0.58%), a real
escape reduction (8.40→7.13), and no idle/crop-throughput regression.
**[VERIFIED] Part B+C's economic cost is larger at full scale than the
4-seed screen showed** (-3.42%, vs. the screen's near-zero -0.01%) — the
larger sample reveals the animal-purchase throttle has a real, if modest,
economic cost that the smaller screen understated, even though it does
cut escapes further (6.47, the lowest of the three). This is a second,
independent piece of evidence (beyond the head-to-head margins in Section
4) for preferring Part B alone over Part B+C.

## 4. Full 15-Seed Head-to-Head Validation

Per this project's own standing rule (Phase 17), no promotion
recommendation is made off the 4-seed screen alone. `scripts/phase46/feed_priority_screen_h2h.py`
mirrors `scripts/phase45/opponent_steering_screen.py`'s own structure
exactly, run first on the 4-seed dev set (all three candidates went
12/12 or 11/12 against all three opponents — a clean pass, no reason to
skip the mandatory full run), then on the full 15-seed set (development +
validation + held-out, `scripts/phase3_2_configs.py::SEED_SETS`).

### 4-Seed Dev Screen (cheap pass, run before committing to the full set)

| Candidate | vs. Submission G | vs. Submission C | vs. Jonaid |
|---|---|---|---|
| Baseline | 4/4 ($7,133) | 4/4 ($21,355) | 4/4 ($24,318) |
| Part B (feed_priority) | 4/4 ($6,061) | 4/4 ($35,268) | 4/4 ($28,859) |
| Part B+C (feed_priority_throttled) | 3/4 ($8,314) | 4/4 ($39,054) | 4/4 ($28,548) |

(Part B+C's single dev-seed loss, seed 700002 vs. Submission G, foreshadows
the same trade-off seen at full scale below.)

### Full 15-Seed Set

| Candidate | vs. Submission G | vs. Submission C | vs. Jonaid |
|---|---|---|---|
| Baseline | 10/15, mean margin $4,031.20 (ours $52,272.93 / G $48,241.73) | 15/15, margin $25,939.27 | 15/15, margin $22,463.80 |
| **Part B (feed_priority)** | **14/15, margin $7,345.47** (ours $57,537.07 / G $50,191.60) | **15/15, margin $35,483.40** | **15/15, margin $27,808.07** |
| Part B+C (feed_priority_throttled) | 14/15, margin $8,223.27 | 15/15, margin $38,145.27 | 15/15, margin $27,354.33 |

**[VERIFIED] Per-seed detail on the Submission G matchup (the only one
where baseline had ANY losses)**: baseline's 5 losses were seeds 701000,
701001, 702000, 702001, 702002. **Part B recovers 4 of these 5** (only
702001 remains a loss) **while introducing zero new losses on any seed
baseline previously won** — a strictly dominant improvement in this
sample, not just a better average. Part B+C recovers ALL 5 of baseline's
original losses, but at the cost of introducing one NEW loss on seed
700002 (a seed baseline itself won) — same final win count (14/15), a
different, not strictly better, trade-off.

**[VERIFIED] Both variants improve mean margin against every one of the
three required opponents**, not just the one where baseline had losses —
Submission C's margin rises from $25,939 to $35,483 (Part B, +36.8%) or
$38,145 (Part B+C, +47.0%); Jonaid's margin rises from $22,464 to $27,808
(Part B, +23.8%) or $27,354 (Part B+C, +21.8%). This is consistent with
Part A's diagnosis: FEED reprioritization frees up real economic value
(fed, surviving animals produce revenue) across the board, not only in the
specific games where it was the deciding factor between a win and a loss.

**Verdict: Part B (FEED tier-0.5 reprioritization alone, no throttle) is
the recommended candidate** — it is a clean win with no observed
downside in this validation sample (strictly recovers losses, never creates
new ones), simpler than Part B+C (one less moving part), and achieves
materially better margins than baseline against all three opponents. Part
B+C remains a reasonable, closely comparable alternative if a smaller,
more conservatively-fed animal count is independently valued, but is not
clearly superior on the validation evidence gathered here.

## 5. Retest: Phase 42's CARROT/TOMATO Slice Through the New Execution Layer

Per the brief's step 7, `scripts/phase46/carrot_tomato_retest.py` re-runs
Phase 42's exact, UNCHANGED day-15 CARROT(6)/TOMATO(2) slice
(`scripts/phase42/carrot_tomato_portfolio.py::make_slice_target_fn`,
imported directly, no parameters changed) through Part B's new
FEED-priority execution layer (`scripts/phase46/feed_priority_execution.py`,
swapped in for the original `scripts/phase36/paced_execution.py`), same
4-seed cheap-screen-first discipline Phase 42 itself used.

| Seed | Baseline (shipped) | Slice through FEED-priority layer | CARROT qty/rev | TOMATO qty/rev |
|---|---|---|---|---|
| 700000 | $44,258.00 | $63,627.00 | 13 / $503.61 | 4 / $281.89 |
| 700001 | $76,683.00 | $63,287.00 | 0 / $0.00 | 0 / $0.00 |
| 700002 | $64,197.00 | $47,409.00 | 0 / $0.00 | 0 / $0.00 |
| 700003 | $51,440.00 | $51,789.00 | 0 / $0.00 | 0 / $0.00 |
| **Mean** | **$59,144.50** | **$56,528.00** | | |

**[VERIFIED] Delta: -4.42%** — a genuine net loss, WORSE than Phase 42's
own original day-15 result on the unmodified execution layer (+0.08%,
reported as a statistical wash). **[VERIFIED]** 3 of 4 seeds sold ZERO
carrot/tomato units at all even after the FEED/WATER scheduling fix — the
slice essentially never got planted/harvested/sold in those seeds, the
same "additive slots crowded out" pattern Phase 42 itself found, just
still present after this phase's fix.

**[INFERRED] Fixing the FEED/WATER scheduling-capacity bottleneck does
NOT retroactively rescue Phase 42's CARROT/TOMATO slice**, because the
two rejections have different root causes: Phase 42/45 diagnosed the
slice's blocker as a `BUY_SEED` cash-flow collision (delaying the 3rd land
quadrant purchase by competing for the SAME limited cash the core
hand/land ramp needs, Phase 45's own seed-pacer partially fixed this
specific collision but the slice still lost decisively when retested
through it, -25.4%) — a MONEY competition, not a WORKER-TURN competition.
This phase's fix targets worker-turn scheduling (which task gets a free
hand's attention this turn), a genuinely different resource than cash.
Confirming this negative result directly (rather than assuming it) was
exactly this phase's step-7 instruction, and it is reported honestly as a
closed negative for this specific combination, not spun positive.

**Not tested further** (per the brief's own "go further only if promising"
instruction): Phase 30's fertilizer and Phase 33's opportunistic
fertilizer/CARROT-glut work were not re-run, since neither is a
worker-turn-scheduling-shaped fix candidate distinct from what Part A/B
already characterizes directly (fertilizer's own rejection, Phase 30,
IS the same capacity mechanism this phase fixed for FEED — a natural
follow-on question, flagged below as a real, concrete next-phase
candidate rather than spun into an unearned "this also works" claim).

## 6. Recommendation

**READY TO PACKAGE: Part B (FEED tier-0.5 reprioritization,
`scripts/phase46/feed_priority_execution.py` / `feed_priority_portfolio_agent.py`)
is a validated, non-regressing improvement over Submission I's shipped
baseline.** Full 15-seed validation: 14/15 vs. Submission G (up from
10/15, margin +82%), 15/15 vs. Submission C (margin +36.8%), 15/15 vs.
Jonaid (margin +23.8%) — every required-opponent margin improves, and no
new loss is introduced anywhere in the validation sample relative to
baseline. Packaging itself (a new submission tarball, cold-process test,
dependency-closure check) was not in this phase's scope, mirroring Phase
36's own "ready to package, not yet done" precedent — that would be a
natural, low-risk next step.

**Part B+C (with the capacity-aware BUY_ANIMAL throttle) is a reasonable,
closely comparable alternative**, not clearly superior — it achieves
slightly better margins against Submission G/C but trades one baseline win
for one baseline loss rather than Part B's strictly-recover-only profile,
and its isolated-economy 4-seed screen showed a real reduction in escapes
(8.25→6.25) at the cost of a smaller final animal count (9.5→8.0). If a
smaller, more conservatively-managed animal count is independently valued
(e.g. as a hedge against unsampled seeds), Part B+C remains available and
validated; Part B alone is the recommendation on the evidence gathered
here.

**Retroactive effect on Phases 30/33/42/45's rejected additions**: mixed,
honestly reported. The CARROT/TOMATO slice (Phase 42) retested WORSE
through the new execution layer (-4.42%, Section 5) — its blocker was
cash-flow, not worker-turns, so this phase's fix does not help it and
should not be represented as doing so. Phase 30's fertilizer rejection and
Phase 45's own animal-escape diagnosis are the two prior findings this
phase's Part A most directly explains and partially addresses (Phase 45's
open question — chronic escapes matching purchases — is the exact
mechanism Part A quantified and Part B measurably improved). Phase 30's
fertilizer itself was NOT re-tested this phase (out of scope per the
brief's "go further only if promising" instruction) but is now a
concrete, well-motivated candidate for a FUTURE phase to re-attempt
through this phase's FEED-priority layer, since fertilizer's own
rejection was explicitly the same capacity-ceiling category this phase
targeted — flagged here, not claimed as solved.

## Changed Files

New, additive only (no frozen file touched, `agents/phase21/` untouched):
- `scripts/phase46/capacity_probe.py` (Part A instrumentation)
- `scripts/phase46/feed_priority_execution.py` (Part B)
- `scripts/phase46/feed_priority_portfolio_agent.py`
- `scripts/phase46/feed_priority_throttled_execution.py` (Part C)
- `scripts/phase46/feed_priority_throttled_portfolio_agent.py`
- `scripts/phase46/feed_priority_screen_isolated.py`
- `scripts/phase46/feed_priority_screen_isolated_full.py`
- `scripts/phase46/feed_priority_screen_h2h.py`
- `scripts/phase46/carrot_tomato_retest.py`
- `results/phase46/*.json`, this report
