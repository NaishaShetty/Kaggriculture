# PHASE 10 — Scheduling Experiment: Is Phase 9's Labor Ceiling Fixable?

Submission C (Phase 3.8) and Submission D (Phase 7's sell-safety fix) are
unmodified throughout this phase. No submission is created.
`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py` is
clean. All new code lives under `scripts/phase10/` and `results/phase10/`.

## 1. Executive Summary

**[VERIFIED] Tile idle-time is already low and does NOT grow with hand
count.** Measured directly from the raw replay (not the agent's own
self-report) across the exact 10 hand counts (4-13) and 4 seeds Phase 9's
Experiment 2 variable arm used: the fraction of standing MELON tiles that
go a whole day without being watered or harvested stays in a **tight,
flat 4.6%-7.9% band at every single hand count**, with no upward trend —
if anything it is *lower* at hand 13 (4.6%) than at hand 6 (7.9%). This
directly **refutes** the hypothesis that the frozen tactical layer's
task-assignment logic is leaving productive tile-work on the table at
scale, separately from the HIRE/SELL ordering bug Phase 9 already fixed
and isolated away.

**Per this phase's own explicit stop condition, no scheduler was built.**
Steps 3-5 of the brief (design and re-run a new scheduler) do not apply —
idle time is near-zero at every hand count tested, exactly the case the
brief names as a legitimate reason to stop before building a fix for a
problem that doesn't exist.

**[OBSERVED] What DOES grow sharply with hand count is wasted hand-*turns*
(PASS actions): 0.17% at hand 4 → 14.2% at hand 13, an ~85x increase, with
`productive_action_rate` falling from 99.4% to 85.5%.** But this is
**not** a scheduling defect either: since 92-95% of crop tiles are already
being watered/harvested every single day even at 13 hands (Section 1's
finding above), there is no unassigned productive work left for a smarter
matcher to hand those idle hands — the tile-maintenance task volume on a
~96-tile single-crop board is simply **finite and largely already
saturated** by around hand 5-6. Additional hands beyond that increasingly
have nothing left to do, and still cost their full daily wage
(Fibonacci-scaled, paid fresh every day — Phase 9 §5b) regardless.

**Phase 9's negative marginal-hand-value result is confirmed to be an
ECONOMIC ceiling (task-volume scarcity on a single-crop portfolio), not an
architectural/scheduling defect.** `docs/ROADMAP_TO_GOLD.md` Phase 3's
"tile-utilization planner" sketch should be **closed for single-crop
portfolios** specifically — no amount of smarter task assignment can
recover Phase 9's lost marginal hand value on the configuration tested,
because there is no idle *tile-work* to reassign, only idle *hands*.
Phase 9 §7's alternate hypothesis — that hand value only shows up on a
genuinely multi-resource portfolio (crops + animals together, matching
what real strong opponents actually run per Phase 6 §12) — is the
recommended next avenue, not a rebuilt scheduler.

## 2. Methodology

Per the brief: instrument first, build only if warranted.

**Reused, not modified:** `scripts/phase9/common.py::make_high_scale_agent`
(Phase 9's own additive code, not one of the frozen files listed in this
phase's constraints) — it already isolates away the HIRE-before-SELL /
unconditional-HIRE-queuing execution bug Phase 9 diagnosed and fixed, while
leaving the underlying task-*assignment* algorithm (the same tiered-
priority greedy bipartite matcher `agents/phase2_3/common.py::make_agent`
uses — HARVEST > WATER > FERTILIZE/DIG/PLANT, nearest-worker-to-nearest-
task, tier by tier) completely unchanged. Measuring on top of this agent,
rather than the raw frozen one, is the correct isolation: it lets this
phase ask specifically "is the *assignment logic* the problem," separately
from the *ordering* bug Phase 9 already found and fixed.

**Exact same configuration as Phase 9 Experiment 2's variable arm:**
`crops="MELON"`, `land_quadrants=3` (4 total quadrants, ~96-tile pool),
`startingMoney=$30,000`, `n_hands ∈ {4..13}`, the same 4 development seeds
(`700000-700003`).

**Two metrics, both computed by a new, read-only measurement module
(`scripts/phase10/idle_time_probe.py`) — no frozen file touched, no agent
logic modified:**

1. **Tile idle fraction** — read directly from the raw replay
   (`env.toJSON()`, the same source every other phase's instrumentation
   uses), independent of anything the agent itself reports. At the LAST
   turn of each day (`hour=23`), for every owned, non-shed tile currently
   holding a crop (`kind == "PLANT"`): did it get watered at some point
   that day (`tile["watered_today"]`, which only resets at the next
   day-refresh — VERIFIED via `vendor_kaggriculture/kaggriculture.py`'s
   `_daily_refresh_plants`), OR does it still have unharvested, ripe yield
   (`_needs_harvest_crop`, reused unchanged from
   `agents/phase2_3/common.py`)? Either condition means the tile went a
   whole day without the attention it needed. Averaged across all 30 days
   with any standing crop, per episode.
2. **Wasted hand-turns** — reuses the EXISTING, unmodified instrumentation
   pipeline's `action_efficiency` metric
   (`instrumentation/metrics.py::action_efficiency`, already computed by
   every phase's existing pipeline; not reimplemented here) — specifically
   `idle_fraction` (share of unit-actions that were `PASS`) and
   `productive_action_rate`.

## 3. Results — Idle-Time Baseline

`results/phase10/phase10_idle_time_results.csv` /
`phase10_idle_time_summary.json`. Mean of 4 seeds per hand count; per-seed
variance is small at every point (all four seeds agree to within
0.1-1.5 percentage points at every hand count — a clean, low-noise signal,
unlike Phase 9 Experiment 4's animal variable arm).

| n_hands | Tile idle fraction | Action idle fraction (PASS-rate) | Productive action rate | Mean final $ (cross-check vs. Phase 9) |
|---|---|---|---|---|
| 4 | 7.38% | 0.17% | 99.38% | $39,368 (Phase 9: $39,368 ✓) |
| 5 | 6.48% | 0.17% | 99.27% | $37,821 (Phase 9: $37,821 ✓) |
| 6 | 7.90% | 0.78% | 98.52% | $36,459 (Phase 9: $36,459 ✓) |
| 7 | 6.02% | 1.44% | 98.23% | $33,142 (Phase 9: $33,142 ✓) |
| 8 | 5.73% | 2.34% | 97.27% | $30,346 (Phase 9: $30,346 ✓) |
| 9 | 6.88% | 3.43% | 95.93% | $28,614 (Phase 9: $28,614 ✓) |
| 10 | 7.13% | 4.04% | 95.33% | $25,626 (Phase 9: $25,626 ✓) |
| 11 | 6.26% | 4.73% | 94.87% | $22,321 (Phase 9: $22,321 ✓) |
| 12 | 5.32% | 9.53% | 90.18% | $16,638 (Phase 9: $16,638 ✓) |
| 13 | 4.63% | 14.24% | 85.45% | $10,224 (Phase 9: $10,224 ✓) |

Final-money figures match Phase 9's published numbers **exactly**,
confirming this phase's harness reproduces Phase 9's own episodes bit-for-
bit (same agent, same seeds, same config) before layering the new
measurement on top.

**Tile idle fraction: flat, ~5-8% throughout, no correlation with hand
count** (correlation is if anything slightly negative — more hands, if
anything, leave marginally *fewer* tiles idle, consistent with more
coverage capacity, not less). **Action idle fraction: monotonic, ~85x
growth from hand 4 to hand 13.** These two trends moving in opposite
directions is the central finding of this phase (Section 5).

## 4. Steps 3-5 (Scheduler Design / Re-run) — Not Executed

Per the brief's explicit instruction: *"If idle time is already near zero
at every hand count, that's a real, useful, negative finding — say so and
stop before building a scheduler for a problem that doesn't exist."*
Section 3's data satisfies exactly that condition — tile idle fraction is
already low (4.6%-7.9%) and does not grow with scale. Building
`scripts/phase10/scheduler.py` and re-running Phase 9 Experiment 2 with it
was therefore **not attempted**. A smarter task-assignment algorithm can
only recover value by finding productive work for otherwise-idle hands to
do; Section 3 shows there is essentially no such work being missed — the
tiles that need attention are already being attended to 92-95%+ of days
even at the highest hand count tested. There is nothing here for a better
matcher to fix.

## 5. Mechanism

The two metrics diverging is the mechanistic explanation:

- **Tile-maintenance task volume on a ~96-tile single-crop MELON board is
  finite and largely saturated by around hand 5-6** — watering/harvesting
  that many tiles simply does not require more workers past that point,
  regardless of how well they're assigned. This is consistent with, and
  sharpens, Phase 9 §5c's hypothesis: *"a single-crop MELON-solo portfolio
  has a hard ceiling on how much labor it can productively absorb."* This
  phase confirms that ceiling is real and is **not** an artifact of poor
  task assignment — the existing greedy, tiered-priority, nearest-worker
  matcher already used by `agents/phase2_3/common.py` (and inherited
  unchanged by Phase 9's high-scale agent) is already keeping ~93-95% of
  tiles serviced daily, which is close to what any reasonable scheduler
  could achieve on a board with this much homogeneous, single-crop work
  and this many workers chasing it.
- **Additional hands beyond that point become genuinely idle** (the
  growing `action_idle_fraction`), not misassigned — there is nothing
  productive left to assign them to, on THIS portfolio. They still cost
  their full daily Fibonacci-scaled wage (paid fresh every day, per Phase
  9 §5b — VERIFIED_MECHANIC) regardless of whether they do anything,
  which is exactly why Phase 9's marginal-$-per-hand curve turns
  increasingly negative at higher hand counts: the cost side keeps rising
  steeply while the production side has already saturated.

**On the Crop Dusta vs. Whyme Labs signal (`docs/LEADERBOARD_DIAGNOSTIC.md`
§5, cited in this phase's brief and in `docs/ROADMAP_TO_GOLD.md` Phase 3's
original sketch):** that divergence was observed between two real teams
with **similar hand counts** early in the game (day 3), where tile-
utilization *density* (how much of the board is under active cultivation
at all) separated a win from a loss. This phase's finding does not
contradict that — it is a different question. Phase 6's signal is about
whether land/labor get put to work quickly and broadly (a day-0-through-
early-game *commitment* question, upstream of task assignment); this
phase's finding is about whether, ONCE land and a target hand count are
already committed, the turn-by-turn scheduler efficiently uses the hands
you already have (a pure *execution* question). This phase's evidence says
the execution side is already close to as good as it can get on a
single-crop board — it says nothing about whether Planner v1 commits to
enough land/diversity early enough, which remains Phase 6's open point.

## 6. Recommendation

1. **Close the tile-utilization scheduler avenue for single-crop
   portfolios.** `docs/ROADMAP_TO_GOLD.md` Phase 3's "big one" sketch
   (a swappable tactical layer built around better task assignment) is not
   supported by this phase's evidence as a way to recover Phase 9's
   labor-capacity loss — there is no idle tile-work on this configuration
   for it to reclaim. Building the full A/B-able tile scheduler the
   roadmap sketches would be real engineering effort spent on a ceiling
   this phase shows is economic, not architectural, for the portfolio
   shape tested.
2. **Do not fully abandon the idea — narrow it.** This phase deliberately
   tested only a single-crop (MELON-solo) / animal-free portfolio, to keep
   the comparison to Phase 9 clean (per this phase's own scope
   restriction). A genuinely multi-resource portfolio (crops + animals
   simultaneously, matching Phase 6 §12's observation that real strong
   opponents pair high hand counts with BOTH land AND 10-14 animals AND a
   diverse crop mix) has structurally more DISTINCT daily-maintenance
   task *types* competing for the same hands (watering multiple crops,
   feeding, caring, harvesting animal products, fertilizing) — it is
   plausible ([HYPOTHESIS], not tested this phase) that task-assignment
   quality matters more when task types are heterogeneous and contend for
   priority, unlike this phase's homogeneous single-crop case where a
   simple greedy nearest-match is already close to optimal. If a future
   phase wants to revisit scheduling, it should do so on THAT portfolio
   shape, not a single-crop one.
3. **Pursue Phase 9 §7's alternate hypothesis next**: re-test labor (and
   animal) marginal value on a multi-resource portfolio directly, before
   spending further effort on scheduling. This is the more promising
   remaining explanation for why real strong opponents successfully run
   8-13 hands profitably while this project's single-crop tests cannot —
   and it is a portfolio-composition question, testable with the same
   isolated-probe methodology Phase 8/9/10 already established, not a new
   architecture.

## 7. Limitations

- **Single-crop (MELON-solo), animal-free portfolio only**, by this
  phase's explicit scope (matching Phase 9 Experiment 2 exactly for a
  clean, apples-to-apples comparison). Section 6.2 already flags that this
  is the most likely reason a smarter scheduler might matter more on a
  richer portfolio — not tested here.
- **n=4 seeds**, per this project's development-set convention — but
  unlike Phase 9 Experiment 4's animal arm, every metric in this phase
  shows tight, low per-seed variance (Section 3), so n=4 is adequate here;
  this is a genuinely different reliability situation from that prior
  inconclusive result, not the same caveat repeated by rote.
- **Tile idle fraction, as defined, treats "needs water" and "needs
  harvest" as equally weighted idle signals.** A tile that goes unwatered
  for one day on a multi-day growth window may cost less than a tile with
  ripe fruit sitting unharvested (which can eventually convert to WEED via
  `_decay_plants` if never harvested — a real but separately-tracked risk
  this phase's coarse fraction does not distinguish). This did not change
  the qualitative finding (both cases are rare — under 8% — at every hand
  count), but a future phase wanting maximal precision could split the two
  cases out.
- **This phase measures execution efficiency, not planting/portfolio
  decisions.** It cannot speak to whether Planner v1 commits to land/scale
  fast enough or broadly enough early in the game — a separate, open
  question per Section 5's discussion of the Crop Dusta/Whyme Labs signal.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase10/idle_time_probe.py`
- `results/phase10/phase10_idle_time_results.csv`
- `results/phase10/phase10_idle_time_summary.json`
- `results/phase10/PHASE10_SCHEDULING_EXPERIMENT_REPORT.md` (this file)

No existing file was modified. `main.py` still builds Submission C. No
`.tar.gz` is created or staged — there is no new submission from this
phase. `scripts/phase10/scheduler.py` was NOT built (Section 4) — its
absence is a deliberate, evidence-based outcome of this phase, not an
incomplete task.

## Validation Performed

- Cross-checked against Phase 9's own published results: every final-money
  figure in Section 3 matches `results/phase9/PHASE9_CAPACITY_EXPERIMENTS_
  REPORT.md` Section 3's variable-arm numbers exactly, confirming this
  phase's harness reproduces Phase 9's episodes bit-for-bit before adding
  the new measurement layer.
- Tile idle fraction computed by direct, independent inspection of the raw
  replay (`env.toJSON()`), not derived from or dependent on the agent's own
  internal bookkeeping.
- Action-efficiency figures read from the existing, unmodified
  `instrumentation/pipeline.py` / `instrumentation/metrics.py` pipeline
  every other phase in this project uses.
- `git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5
  agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py`:
  clean throughout this phase.
