# PHASE 13 — Animal Servicing Fix: Diagnosis and Targeted Repair

Submission C (Phase 3.8) and Submission D (Phase 7's fix) are unmodified
throughout this phase. No submission is created.
`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py` for
this phase's own changes is clean (a concurrent, unrelated session's
in-progress "Phase 12" work on `agents/phase3_7/` and
`agents/phase3_8/adapters/competitive_v3_agent.py` was observed but not
touched, inspected further, or acted on by this phase — see the Git
section at the end). All new code lives under `scripts/phase13/` and
`results/phase13/`.

## 1. Executive Summary

**[VERIFIED] This gap is LIVE in Submission C/D's actual tactical layer —
not confined to Phase 11's research code.** Reproduced directly using
`agents/phase2_4/common.py::make_agent`, imported unmodified (the real
function Submission C/D's live path runs), on a clean animal+crop config:
every one of the 30 in-game days shows at least one animal missing feed,
with daily fed-fraction ranging 0.0-0.86 (Section 2). Direct code
comparison (Section 2) confirms Phase 11's research agent copied this
exact logic verbatim from `agents/phase2_3/common.py` — it did not
introduce a new bug.

**[VERIFIED, by direct turn-by-turn trace] The real mechanism is NOT the
"FETCH-then-DELIVER chaining fails" hypothesis Phase 11 §5 proposed.**
That hypothesis is **refuted**: the trace (Section 3) shows the single
worker who does end up fetching WHEAT chains PICKUP→FEED→CARE→move
correctly, turn after turn, without difficulty. The real, verified
mechanism is a **throughput bottleneck, not a sequencing failure**:
`agents/phase2_3/common.py`'s (and `agents/phase2_4/common.py`'s
identical re-implementation's) fetch-task construction builds exactly
**ONE** fetch entry per distinct item type per turn — sized to the total
deficit across every task needing it — rather than one entry per worker
or per task instance. Since only the worker who ends up carrying an item
is eligible for any task requiring it, this permanently funnels **every**
animal-feeding delivery through a single worker all episode, regardless
of how many other hands are free. That one worker can complete roughly one
FEED+CARE pair every ~2 turns — capping animal servicing at ~6 pairs/day
no matter the total hand count, while an 11-14-animal portfolio needs
11-14/day. This exactly explains Phase 11's finding that idle-time was
flat and uncorrelated with hand count (Phase 11 §5) — more hands were
never being given the chance to help.

**[VERIFIED] The fix (`scripts/phase13/fixed_agent.py`, a targeted,
one-block change — split the aggregate fetch deficit into multiple
per-worker-sized entries instead of one batch entry) closes most of the
gap and, critically, makes servicing scale WITH hand count again**, which
it did not before: mean fed-fraction improves from a roughly flat
60-71% (before, uncorrelated with hands) to a clearly hand-count-
increasing 66.5%→93.3% (after, hands 4→13) — an improvement that *grows*
with hand count (+6.6 points at hand 4, up to +26.6 points at hand 12),
exactly the signature expected from removing a single-worker bottleneck
that more hands previously could not help with.

**This phase does not re-test money or marginal animal value** — per its
explicit scope, that is the next phase's job, on top of now-correct
servicing.

## 2. Step 1/2 — Where Does the Gap Live?

**Direct code comparison** (read in full before writing anything):
`scripts/phase11/multi_resource_agent.py`'s animal-task-generation block
(HARVEST_ANIMAL/FEED/CARE priority assignment, lines matching
`agents/phase2_3/common.py`'s own 361-371) and its fetch-entry
construction block (matching lines 390-409) are copied **verbatim** from
`agents/phase2_3/common.py` — confirmed by direct side-by-side reading,
not assumed. `agents/phase2_4/common.py` (Submission C/D's actual
tactical-layer ancestor) imports `tile_pool_assignment` and
`structure_type_assignment` directly from `agents/phase2_3/common.py` and
re-implements the identical task-scheduling/fetch/greedy-assignment
structure in its own lines ~268-425, including the same single-fetch-
entry-per-item construction verified at its line 336
(`fetch_entries.append((req_min_priority[item], home, "FETCH", "PICKUP",
item, take))`, one entry per item, `take` sized to total deficit).

**Conclusion: case (a).** This is a property of `agents/phase2_3/
common.py`'s own task-assignment design, inherited unchanged by
`agents/phase2_4/common.py` (Submission C/D's live path) and by every
research agent built on top of it in Phases 9-11. Phase 11's own code did
not introduce this.

**Live-path reproduction** (`scripts/phase13/live_path_reproduction.py`,
using `agents/phase2_4/common.py::make_agent` imported unmodified — not
any research agent): `crops="STRAWBERRY"` (unbounded, fills ~84 tiles),
`n_hands=8` (deliberately below 10 to avoid Phase 9's separately-diagnosed
HIRE-before-SELL ordering bug, keeping this test isolated to the
animal-feeding question), `land_quadrants=3`, `animals={"COW":6,
"SHEEP":6}`, `feed_source="market"`, `sell_policy={"mode":"passive"}`,
`startingMoney=$30,000`, seed 700000, 30-day episode.

| Day | Animals present | Fed | Fed fraction |
|---|---|---|---|
| 0 | 8 | 6 | 0.75 |
| 2 | 11 | 6 | 0.55 |
| 10 | 9 | 3 | **0.33** |
| 14 | 6 | 2 | **0.33** |
| 28 | 6 | 0 | **0.00** |
| 29 | 7 | 4 | 0.57 |

**Every single day (30/30) shows at least one animal missing feed.**
Animal count fluctuates 5-11 despite a target of 12 (COW6+SHEEP6),
consistent with animals repeatedly escaping (2 consecutive unfed days,
VERIFIED_MECHANIC) and being repurchased. This is with the FROZEN
`agents/phase2_4/common.py::make_agent`, confirming the gap is live-path
relevant, not a research-code artifact. Full data:
`results/phase13/phase13_live_path_reproduction.csv`.

## 3. Step 3 — Verified Mechanism (Turn-by-Turn Trace)

Traced the raw recorded actions (`replay["steps"][t][0]["action"]`, the
actual per-turn action chosen by the frozen agent — not inferred) across
day 2 (turns 48-71) of the same live-path-reproduction episode. Farmer's
action sequence: `PICKUP WHEAT 8` (turn 50) → `FEED` (52) → `CARE` (53) →
move → `FEED` (55) → `CARE` (56) → move → `FEED` (58) → `CARE` (59) →
move/PLANT/WATER → `FEED` (64) → `CARE` (65) → move → `FEED` (67) →
`CARE` (68) → move → `FEED` (70) → `CARE` (71). **The chaining works
correctly** — the farmer reliably alternates FEED/CARE/travel across the
whole day, exactly as the FETCH-then-DELIVER hypothesis would predict if
it were only about sequencing.

**But across the SAME 24 turns, none of the other 8 hired hands ever
performs a single FEED or CARE action** — every one of them spends the
entire day on `WATER`/`PLANT`/movement (crop tasks) or `PASS`. This is not
because they're doing something more urgent — it's because they are
structurally **ineligible**: `entry_eligible` for a FEED task requires
`w["inv"].get("WHEAT", 0) > 0`, and since exactly ONE fetch entry was
generated that turn (`PICKUP WHEAT 8`), exactly one worker (the farmer)
ever carries WHEAT. The other 8 hands are never even offered the chance.

**Verified mechanism: a single-server queue, not a chaining failure.**
One worker completes roughly 1 FEED + 1 CARE pair every ~2 turns (turns
52-53, 55-56, 58-59, 64-65, 67-68, 70-71 — 6 pairs across this day's 24
turns, with several turns spent traveling between animal tiles). With 24
turns/day, a single dedicated worker tops out at roughly 6-8 FEED+CARE
pairs/day even under ideal conditions — but the portfolio has 11-12
animals needing service EVERY day. **This directly explains Phase 11's
finding that idle-time was flat and uncorrelated with hand count**: hiring
more hands never increased the number of WORKERS ABLE TO FEED, because
the fetch-entry count (and therefore the number of eligible feeders) is
determined by distinct item types needing fetching (always 1, "WHEAT"),
never by hand count or animal count.

## 4. Step 4 — The Fix

`scripts/phase13/fixed_agent.py::make_multi_resource_agent_fixed` — an
exact copy of `scripts/phase11/multi_resource_agent.py::
make_multi_resource_agent` (itself already validated in Phase 11) with
**one block changed**: the fetch-entry construction now splits each
item's available (deficit-capped, shed-availability-capped) quantity into
up to `min(available, n_workers)` separate entries (as evenly sized as
possible) instead of one batch entry:

```python
n_entries = min(available, n_workers)
base = available // n_entries
remainder = available % n_entries
for i in range(n_entries):
    qty = base + (1 if i < remainder else 0)
    if qty > 0:
        fetch_entries.append((req_min_priority[item], home, "FETCH", "PICKUP", item, qty))
```

Every other line — buying, selling, land, the tiered task-priority scheme,
and the greedy nearest-worker-to-nearest-entry matching loop itself
(confirmed near-optimal for available tile-work by Phase 10, and
deliberately left untouched here per this phase's brief) — is byte-for-
byte identical to Phase 11's own agent. This is the targeted,
one-mechanism fix the brief asked for, not a rewrite of the assignment
algorithm: the existing greedy matcher, once given MULTIPLE independent
fetch entries in the same priority tier, already knows how to assign each
to a different nearest free worker — it just was never given more than
one to work with.

## 5. Step 5 — Servicing-Rate Validation (Before vs. After)

`scripts/phase13/servicing_rate_experiment.py`: Phase 11's exact config
(STRAWBERRY x24 tiles, COW6/SHEEP6, 3 extra land quadrants, $30,000
starting cushion), hands 4-13, seeds 700000-700003. Metric: mean fraction
of animal-days with `fed_today=True` across the 30-day episode. (Every
seed produces an identical result at a given hand count — this metric
depends only on hand count and the deterministic feeding/escape mechanic,
not on the episode's one stochastic element, weed-spawn timing on empty
crop tiles, which never touches animal structures.)

| n_hands | Before (Phase 11's agent) | After (this phase's fix) | Improvement |
|---|---|---|---|
| 4 | 59.9% | 66.5% | +6.6 pts |
| 5 | 62.9% | 64.7% | +1.8 pts |
| 6 | 62.7% | 70.8% | +8.2 pts |
| 7 | 67.0% | 75.4% | +8.4 pts |
| 8 | 67.9% | 78.7% | +10.8 pts |
| 9 | 67.4% | 79.4% | +12.0 pts |
| 10 | 67.5% | 86.9% | +19.5 pts |
| 11 | 70.6% | 91.0% | +20.4 pts |
| 12 | 65.4% | 92.0% | +26.6 pts |
| 13 | 67.2% | 93.3% | +26.1 pts |

Full data: `results/phase13/phase13_servicing_rate_results.csv` /
`phase13_servicing_rate_summary.json`.

**Confirms the diagnosis precisely.** Before the fix, servicing rate is
roughly flat/noisy around 60-71% regardless of hand count (matching Phase
11 §5's original observation) — more hands did not help, because they were
never eligible to. After the fix, servicing rate **rises cleanly and
substantially with hand count** (66.5%→93.3% from hand 4 to hand 13),
because the fix directly removes the single-worker cap that was
preventing hand count from mattering. **The improvement itself grows with
hand count** (+6.6 points at hand 4 up to +26.6 points at hand 12) — the
correct signature for a fix that specifically unblocks parallelism: with
few hands there's little slack to parallelize into, so the gain is small;
with many hands (previously all excluded but one), the gain is large.

## 6. Recommendation

**Is a separate phase warranted to wire a fix into the actual submission
path?** Yes, worth scoping — but with real caveats, not a rubber stamp:

- This phase's evidence is strong that the gap is real and live
  (Sections 2-3), and the fix (Section 4) closes most of it cleanly in
  isolation (Section 5). That's a legitimate case for a follow-up phase.
- **But**: Submission C/D's actual live configuration never runs anywhere
  near this many simultaneous animals in practice today — Phase 6 §14.A.2
  already documented that Submission C's animal-response ceiling tops out
  at 6 (`agents/phase3_8/animal_response.py`'s `HIGH_RESPONSE_ANIMALS =
  {"COW": 3, "SHEEP": 3}`), and this phase's own before-column shows the
  gap exists even at low hand counts (59.9% at hand 4) but is proportionally
  smaller in absolute animal-days lost when there are only 6 animals
  rather than 12-14. A future phase should first re-measure this exact
  gap at Submission C's OWN actual animal target (6, not 12) before
  assuming the live-path benefit is as large as the 12-animal numbers
  here suggest — this phase deliberately did not do that re-scoped
  measurement (kept identical to Phase 11's config for a clean
  before/after comparison, per the brief).
- Per this phase's own constraints and the project's established pattern
  (Phase 7, and the concurrently-observed "Phase 12" work, Section header
  note): wiring any fix into `agents/phase3_8/` or a new adapter layer
  should be its own deliberate, narrowly-scoped phase with its own
  regression suite and non-target archetype sweep — not appended here.
  This phase's job (diagnose, fix in isolation, validate servicing) is
  complete; a follow-up should (a) re-measure the gap's size at
  Submission C's actual animal scale, (b) confirm the fix is genuinely
  inert when animal count is low enough that the single-fetch-entry cap
  was never binding, and (c) only then consider a live-path integration.

## 7. Limitations

- **This phase validates servicing rate only, not final money or marginal
  animal value** — explicitly out of scope per the brief. The Section 5
  smoke-test in `scripts/phase13/fixed_agent.py`'s development (not a
  formal result of this phase, mentioned here only for transparency) did
  show final money also rising substantially at hand 13 with the fix
  ($60,755 → $86,130 on the seed-700000 cell), but this phase makes no
  claim from that single, informal data point — a proper re-run of Phase
  11 Experiment 4's animal sweep on top of the fix is the next phase's job.
- **The fix was validated at Phase 11's 12-animal, 24-crop-tile
  configuration only** — Section 6 already flags that Submission C's own
  actual animal scale (6) should be separately re-measured before treating
  this as a live-path priority.
- **The turn-by-turn trace (Section 3) is from one representative episode
  (hand=8, seed=700000)** — the servicing-rate sweep (Section 5, 40
  episodes across 10 hand counts × 4 seeds) is what establishes the
  general pattern; the trace establishes the mechanism.
- **A concurrent, unrelated session's changes to `agents/phase3_7/
  f005_liquidity_guard.py` and `agents/phase3_8/adapters/
  competitive_v3_agent.py` were present in the working tree during this
  phase** (apparent "Phase 12" F-005 integration work, with an untracked
  `scripts/phase12/` directory). This phase did not read, modify, revert,
  or otherwise interact with that work — noted here only so a reader of
  `git status` during this phase's development isn't confused about its
  origin.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase13/live_path_reproduction.py`
- `scripts/phase13/fixed_agent.py`
- `scripts/phase13/servicing_rate_experiment.py`
- `results/phase13/phase13_live_path_reproduction.csv`
- `results/phase13/phase13_live_path_summary.json`
- `results/phase13/phase13_servicing_rate_results.csv`
- `results/phase13/phase13_servicing_rate_summary.json`
- `results/phase13/PHASE13_ANIMAL_SERVICING_FIX_REPORT.md` (this file)

No existing file was modified by this phase. `main.py` still builds
Submission C. No `.tar.gz` is created or staged — there is no new
submission from this phase, and no frozen file was touched even though
Section 2 confirmed a live-path-relevant finding (per this phase's
explicit constraint: diagnosis and an isolated fix only, no live-path
wiring).

## Validation Performed

- Case (a)/(b) determination made by direct, side-by-side code reading
  (Section 2) before writing any new code, per the brief's explicit
  "before doing anything else" instruction.
- Live-path reproduction used `agents/phase2_4/common.py::make_agent`
  imported unmodified — never edited, never wrapped in a way that changes
  its behavior — to confirm the finding is not an artifact of any research
  agent.
- Mechanism (Section 3) confirmed by reading the actual recorded
  per-turn actions from the raw replay, not inferred from the aggregate
  idle-fraction number alone.
- Fix (Section 4) changes exactly one block; a diff-equivalent comparison
  against `scripts/phase11/multi_resource_agent.py` confirms every other
  line is unchanged.
- `git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
  agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py`:
  clean for this phase's own changes (see Section header note on the
  concurrent, unrelated session's changes observed but not acted upon).
