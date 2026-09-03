# Roadmap to Gold

**A phased plan where every submission is expected to move rank, not just churn code.**

> **Update, post-Phase 14 — the animal-servicing thread is CLOSED, no live wiring needed.** `results/phase14/PHASE14_LIVE_SCALE_SERVICING_CHECK_REPORT.md` re-measured Phase 13's fetch-bottleneck fix at Submission C's *actual* live targets (confirmed by direct code read: hands fixed at 5 always, animals capped at 6 total even at the highest competitive-pressure tier — `agents/phase3_5/response_policy.py`, `agents/phase3_8/animal_response.py`). At that real operating point, the fix's effect is **-1.22 points** (i.e. noise, not an improvement) — a stark contrast to Phase 13's clean +6.6-to-+26.6-point gain at 12 animals. Mechanism: one worker already tops out around 6-8 FEED+CARE pairs/day even under the old bug, and Submission C's live animal ceiling of 6/day sits right at that edge — the bottleneck is real but never binding at the scale the agent actually runs at. **Do not scope a Phase 15 live-wiring integration for this** — real integration/regression risk for zero measured benefit. The one remaining open thread from the whole Phase 9-14 capacity investigation is **Phase 11's own labor re-seed recommendation**: the multi-resource labor result (net +$7,690 from hand 4→13, reversing Phase 9's single-crop finding) is directionally strong but too noisy at n=4 seeds to name a specific new hand target — that's the next actionable, potentially submission-worthy item left on this thread.

> **Update, post-Phase 12 — F-005's dead trigger is fixed and packaged as Submission E, not yet uploaded.** `results/phase12/PHASE12_F005_LIQUIDITY_GUARD_FIX_REPORT.md`: widened the check from one exact instant (`day==2,hour==0`) to a daily check across days 1-6, wired into `agents/phase3_8/adapters/competitive_v3_agent.py` as a new gated layer 4. Provably safe: 0/44 regressions across the full archetype/scaling battery, 128/133 regression tests green (5 failures are the pre-existing, unrelated stale-hash-pin issue from Phase 7). **Honest caveat, important**: the guard now fires in 100% of the 44 tested games, not just crisis cases — Planner v1's day-3 cash trough turns out to be routine, not rare (confirmed across all 11 archetypes), so this isn't the narrowly-targeted detector originally envisioned. It's a real, harmless safety net, but Phase 3.7-C's deeper finding — no early cash-only signal distinguishes a recoverable dip from a catastrophic one — is **not** solved by this phase, only the dead-wiring bug is. **This submission is safe to send now** (zero measured downside, closes a real gap in the weakness matrix); a future phase could still target the deeper discrimination problem if F-005 losses keep recurring after this ships.

> **Update, post-Phase 11 — labor's negative result was portfolio-specific; animals reveal a real logistics bug, not an economic ceiling.** `results/phase11/PHASE11_MULTI_RESOURCE_PORTFOLIO_REPORT.md` re-ran Phase 9's labor and animal sweeps on a bounded portfolio matching real opponent moushun_chen's actual shape (STRAWBERRY 24 tiles + 12 animals, from `results/phase6/moushun_chen/days_opponent.csv`) instead of MELON-solo. **Labor reverses direction**: net +$7,690 from hand 4→13 (vs. Phase 9's −$29,144), every hand count 3-6x higher in absolute money — directionally confirms Phase 9 §7's hypothesis, though too noisy at n=4 seeds (one seed runs persistently low) to name a specific new target yet. **Animals still don't show a positive turn** — but the idle-time cross-check found why, and it's not economics: crop-tile idle-time is ~0% (confirming Phase 10 was right to close that), but **animal idle-time sits flat at 34-43% at every hand count, uncorrelated with labor supply** — animals cycle unfed→escape→repurchase even when cash and hands are both abundant. Traced cause: feeding is a two-step FETCH-WHEAT-then-DELIVER task; the frozen scheduler doesn't reliably chain the two steps. **This means Phase 11's "animal cap shouldn't rise" conclusion is confounded by a real execution bug, not a clean economic reading like labor's** — the honest next step is to fix the servicing gap FIRST (mirroring exactly how Phase 10 had to confirm crop scheduling was clean before Phase 9's labor conclusion could be trusted), then re-test animal marginal value on top of correct servicing. **Also worth surfacing: this FETCH-then-DELIVER gap lives in the same frozen tactical layer (`agents/phase2_3/common.py`) that Submission C/D actually run** — meaning C's own animal-response layer (`agents/phase3_8/animal_response.py`) may be raising live animal targets that the tactical layer can't actually service reliably, independent of anything this research thread is testing. Worth a small, targeted diagnostic on the live path specifically, not just the isolated probes.

> **Update, post-Phase 10 — Phase 3 (tile-utilization scheduler) is CLOSED for single-crop portfolios.** `results/phase10/PHASE10_SCHEDULING_EXPERIMENT_REPORT.md` measured tile idle-time directly on Phase 9's exact negative-result configuration (4 quadrants, MELON-solo, hands 4-13) and found it flat at 4.6%-7.9% with no growth trend — the frozen scheduler already keeps 92-95%+ of tiles serviced daily even at 13 hands. What grows instead is wasted hand-*turns* (0.17%→14.2%), because there simply isn't enough distinct task volume on a ~96-tile single-crop board to occupy that many hands, not because they're poorly assigned. **Per the phase's own instruction, no scheduler was built — there was nothing for one to fix.** Phase 9's negative marginal-hand-value result is now confirmed to be a genuine economic ceiling (task-volume scarcity), not an architectural defect. **The original Phase 3 sketch below is superseded** — do not build the swappable tile scheduler on a single-crop portfolio. The live open question is now Phase 9 §7 / Phase 10 §6's shared alternate hypothesis: does labor (and animal) marginal value turn positive on a genuinely multi-resource portfolio (crops + animals together, matching what real strong opponents actually run per Phase 6 §12)? That's next — see the new Phase 11 note below once sent.

> **Update, post-Phase 9:** Phase 9 (`results/phase9/PHASE9_CAPACITY_EXPERIMENTS_REPORT.md`) ran Phase 6's Experiments 2 & 4 — the gating condition for raising hand/animal caps. **Labor: decisive FAIL.** Marginal hand value is negative at every count 5-13 on a large 4-quadrant board with a single-crop (MELON) portfolio, and gets worse with scale (−$1,547 at hand 5 to −$6,415 at hand 13) — the current ~5-hand cap is already close to correct; **do not raise it** on a single-crop portfolio. **Animal: inconclusive**, not a false pass or fail — the high-scale arm's marginal-value curve flips sign 5 times with noise larger than the effect; needs more seeds before Phase 4 acts on it either way. The mechanistic explanation (§5c of that report) matters for Phase 3 below: real strong opponents pair high hand counts with land **+ animals + a diverse crop mix simultaneously** (Phase 6 §12) — this phase's result suggests hands only pay off with genuinely more distinct daily-maintenance work to do, not just a bigger field of the same crop. That's a point in favor of building Phase 3's tile/resource scheduler before revisiting hand capacity again, not against it. **Phase 9 also found a real, disclosed, currently-live property of the shared tactical-layer ancestor** (`agents/phase2_3/common.py` and `agents/phase2_4/common.py`, the latter underlying Submission C/D): HIRE orders are queued before SELL orders with no affordability check, so at high hand counts (`need_hire >= 10`) HIRE fills the entire 10-order/turn cap and silently blocks that turn's SELL. Never triggered by any prior phase (none tested hand counts this high) and not a risk today since the hand target isn't being raised — but worth remembering if that ever changes.

> **Update, post-Phase 8:** Phase 8 (`results/phase8/PHASE8_CALIBRATION_PROBE_REPORT.md`) ran the calibration probe and resolved Phase 6's Experiment 3 — with a result that corrects something this roadmap and the earlier diagnostic report both got wrong. **MELON beats STRAWBERRY in isolated single-player economics at every scale tested (1.6-1.7x, batch-dump-adjusted or not) — the community-sourced advice to favor STRAWBERRY does not hold up under direct measurement, and Planner v1's MELON-first default is reinforced, not overturned.** The real bug Phase 8 found is different and narrower than what Phase 5/6 hypothesized: `crop_production_value` undercounts non-`ongoing` crops (WHEAT/CARROT/MELON) by 3-8x because it never models replanting after a tile clears — `ongoing` crops (STRAWBERRY/TOMATO) are already accurate to within ~2-19%. **Phase 3/Phase 4 below must branch on `CROPS[crop]["ongoing"]` for any future volume estimate, not apply a flat scale correction.** The real 4-opponent STRAWBERRY preference Phase 6 observed remains a genuine open unknown — Phase 8's isolated design can't see two-player market dynamics, which is the leading suspect. Do not act on "prefer STRAWBERRY" anywhere until a two-player experiment actually confirms a mechanism; treat this as unresolved, not settled in either direction beyond "not raw production economics."

> **Update, post-Phase 7:** the sell-safety wiring bug (below, formerly "Phase -1") is fixed and shipped as **Submission D** (`kaggriculture_phase7_submission_D.tar.gz`) — reproduced the exact freeze Phase 6 found, confirmed resolved, full regression suite and archetype sweep clean. This item is done; skip it if reading this roadmap fresh.

> **Update, post-Phase 6:** `results/phase6/PHASE6_COMPETITIVE_META_FORENSICS_REPORT.md` (real-replay forensics across 4 strong opponents plus Submission C's own 2 real games) landed after this roadmap was first written and changes the order below. Its headline finding — a **verified, currently-live bug**: Planner v1 sets `sell_policy["horizon_aware"] = True` believing it activates a force-liquidate safety net, but that net lives only in `agents/phase2_5/common.py`, which Planner v1 never calls (it imports `make_agent` from `agents/phase2_4/common.py` directly — see `agents/phase2_6/common.py:28,139`). This is traced directly to Submission C's single worst real loss (episode 104797306: $0 vs opponent's $104,569 — 59 harvested MELON units sat unsold in the shed from day 12 onward). This fix now sits **ahead of Phase 0** below — it's cheaper, safer, and more urgent than anything else in this roadmap: see the new **Phase -1** section. Phase 6 also found strong, consistent evidence (n=4 opponents, no exceptions) that all real strong opponents abandon MELON for STRAWBERRY by mid-game, and sustain 8-13 hands / 10-14 animals daily — both of which sharpen Phase 0 and Phase 4 below without changing their shape. Full findings: `results/phase6/PHASE6_COMPETITIVE_META_FORENSICS_REPORT.md` §1, §8, §13.

This roadmap is grounded in the actual code (not the phase reports' summaries) and in two things the reports don't yet reflect:

1. **`results/phase5/PHASE5_FINAL_REPORT.md` already tried and rejected one of the two fixes recommended in [`LEADERBOARD_DIAGNOSTIC.md`](LEADERBOARD_DIAGNOSTIC.md).** Wiring the verified market simulator (`agents/phase4/market_model.py`) into the *crop-substitution/portfolio* decision was built, tested on all 15 of Variant D's own founding seeds, and lost every single one (0/15 vs the frozen control's 10/15, mean −$10,371/episode). The root cause is diagnosed precisely (§13 of that report): the calibration constant `CALIBRATION["revenue_per_tile_day"]` is only validated as a *ranking* signal at its reference scale (`n_tiles=10`) — using it to back out a true unit *volume* at the real freed-tile count (~20-25 tiles) inflates STRAWBERRY's implied revenue enough to fool even the exact simulator. **Do not re-attempt this on the portfolio decision.** Phase 5's own recommended next step — confirmed by re-reading its report — is to use the same simulator on **sell-timing** instead, where the quantity is already known (harvested inventory) and there's no volume-estimation step to get wrong. Phase 0 below follows that lead.
2. **A live code inventory of the actual submission path**, so every phase below names exact files and functions rather than re-deriving them.

## What's actually live right now

```
main.py
 └─ agents/phase3_8/adapters/competitive_v3_agent.py :: make_competitive_v3_agent
     1. Planner v1                    agents/phase2_6/common.py            — always runs, day-0 greedy-knapsack sizing
     2. Variant D substitution        agents/phase3_3/interventions.py     — gated by expansion_detector (confidence ≥ 0.5)
     3. Scaling response (B)          agents/phase3_5/response_policy.py   — gated by opponent hands/animals ≥ 5, 3 consecutive days
     4. Animal response (C)           agents/phase3_8/animal_response.py   — same trigger, piecewise on opponent animal count
```

Everything in `agents/phase4/` (market simulator, opponent trajectory model, 5-mode strategy controller) and `agents/phase5/` (market-impact sell substitution) is **built, tested, and not wired into anything live.** Nothing there needs to be built from scratch — it needs to be either connected correctly or explicitly retired.

---

## Phase -1 — Fix the dead sell-safety wiring (submission candidate #4, send first) — ✅ DONE

**Shipped.** Commit `22cca31`, pushed to `origin/main`. Packaged as `kaggriculture_phase7_submission_D.tar.gz` (SHA-256 `14db20c2e34fd2a18375445848ec229f8464dcae91f0be12fd965360e2d25e7c`). Full validation: `results/phase7/PHASE7_SELL_SAFETY_FIX_REPORT.md`.

Key results: reproduced the exact freeze on unpatched code (0/720 turns sold, 50 units stranded), confirmed the fix resolves it (1 SELL order fires at the day-29 terminal deadline, shed empties). Regression suite clean (5 "failures" are all the same expected stale hash-pin, not functional regressions). 32-pair archetype sweep: byte-identical in all 21 pairs with no stranded inventory; in 10 of 11 pairs with stranded inventory, money strictly increases; the 1 exception is a correctly-preserved animal-feed reserve, not a gap.

**Still open, not done in this phase (don't lose track of it):** `results/phase3_1/control_reproduction/frozen_file_hashes.txt` was deliberately left stale (the report explains why — avoiding scope creep). Worth a 1-line follow-up at some point so the regression suites stop reporting an "expected" failure on every future run.

**Not yet submitted to Kaggle** — the .tar.gz is built and validated locally but pushing it to the leaderboard is a separate, manual step. This is now your best candidate for one of the 2 active submission slots.

---

<details>
<summary>Original Phase -1 brief (for reference)</summary>


**Goal:** restore behavior Planner v1 already believes it has. This is not a new strategic bet — it's a bug fix, and per `results/phase6/...` §18 it's "the highest-confidence, lowest-risk improvement identified in this entire project's history."

**Ground truth (verified by direct code read, confirmed by Phase 6's forensics):**
- `agents/phase2_6/common.py:73` sets `sp["horizon_aware"] = True` unconditionally for any non-passive mode, with the comment *"F16 protection is always on... (mandatory, brief section 17)"* — Planner v1 believes this is load-bearing.
- The only code that actually reads `policy.get("horizon_aware")` is `agents/phase2_5/common.py::_sell_quantity_horizon_aware` (lines 19-27), which forces full liquidation once `day >= terminal_liquidation_deadline(...)`.
- `agents/phase2_6/common.py:139` calls `make_agent_24(**...)`, imported at line 28 from `agents.phase2_4.common` **directly** — never through `agents/phase2_5/common.py`'s wrapper. `agents/phase2_4/common.py`'s own `_sell_quantity` never looks at `horizon_aware` at all. The flag is set, checked by nothing, forever.
- Real-world cost: episode 104797306 — 0 SELL orders across all 720 turns, 59 units of harvested MELON stranded in the shed from day 12, final score $0 vs opponent's $104,569 (the largest margin loss in all 34 real episodes on record).

**This is a deliberate, scoped exception to this project's "phase2_6 is frozen" rule** — justified specifically because Phase 6's forensics proved the current behavior is already broken, not because a new strategy is being tried. Nothing else in `agents/phase2_6/` changes.

- **Fix:** swap `agents/phase2_6/common.py`'s import/call from `agents.phase2_4.common.make_agent` to `agents.phase2_5.common.make_agent` (same signature, documented as "identical to phase2_4 except the sell policy is wrapped with the horizon-safety override" — see `agents/phase2_5/common.py`'s own docstring). This is the minimal change: one import line, one call site.
- **Validate exactly per Phase 6's own Experiment 1 (`results/phase6/...` §17.1):** reproduce the Lai Eu Wen episode's conditions synthetically (an opponent that also floods the MELON market early) against the *unpatched* code first to confirm the freeze reproduces deterministically, then confirm the patched code fires SELL orders near the terminal deadline under the same conditions.
- **Regression:** full existing suite must stay green; additionally sweep all synthetic archetypes to confirm final money is **unchanged** in every scenario that never hit the stuck-sell condition (the fix should only change behavior in the specific case it targets) — same non-regression discipline every phase report in this project already uses.
- **This one is allowed to become a real submission** once validated (unlike Phase 6's forensics, which was explicitly barred from producing one) — it's a genuine, evidence-backed correction to the live champion.
- **Why this should move rank:** it doesn't require out-competing anyone — it just stops handing away games we already had the production to win. Converting even one class of $0 losses into ordinary losses or wins is a direct rating floor-raiser with essentially no downside risk, since the fix is provably inert everywhere it isn't needed.

---
</details>

## Phase 0 — Recalibration probe (no submission, ~1 day)

**Goal:** answer the one open question Phase 5 left on the table before spending any more effort on volume-aware decisions anywhere in the codebase.

Phase 5 §16 names this exactly: *"directly measure `crop_production_value`'s calibration error as a function of tile count... at n_tiles = 5, 10, 15, 20, 25 for each candidate crop, isolated, no opponent."* This is cheap (no live-path code touched, no opponent modeling needed) and it de-risks every later phase that wants to reason about production volume at real scale (Phase 2 and Phase 3 below both depend on knowing whether this calibration is trustworthy past n_tiles=10).

**Sharpened by Phase 6:** real-replay forensics (`results/phase6/...` §8, §13) found all 4 strong opponents studied abandon MELON for STRAWBERRY by mid-game, directly contradicting `CALIBRATION["revenue_per_tile_day"]`'s MELON (69.49) > STRAWBERRY (42.88) ranking. Phase 6's own Experiment 3 (§17.3) asks a narrower version of this same question (STRAWBERRY vs. MELON specifically, at 20-30 tiles). Run this phase pointed at both reports — it should resolve Phase 6's Experiment 3 as a byproduct, not as separate work. Use `phase7` for all new paths in this phase (`agents/phase6/` and `results/phase6/` are already claimed by the forensics phase).

- **Build:** a standalone script (`scripts/phase6_calibration_probe.py`) that runs isolated single-player episodes at fixed tile commitments (5/10/15/20/25 tiles) per crop and compares actual harvested-and-sold revenue against `crop_production_value`'s estimate at that same tile count.
- **Output:** a correction curve (or a confirmation that it's scale-invariant, which would be a genuine surprise given Phase 5's evidence).
- **No submission from this phase** — it's pure measurement.

---

## Phase 1 — Fix F-005's dead trigger (submission candidate #4)

**Goal:** close the worst-outcome failure mode. This is the highest-leverage, lowest-risk item on the board — it can only prevent catastrophic losses, never cause new ones, if scoped correctly.

**Ground truth:** `agents/phase3_7/f005_liquidity_guard.py` already exists and is exactly as narrow as the weakness matrix says: it fires **only** at `day == 2, hour == 0`, and only if cash has already fallen below `$200`. Outside that single 1-turn window, it can never trigger — a cash crisis detected at day 3 or with $250 remaining is invisible to it. It is also not imported anywhere in the live adapter chain.

- **Fix the detection window**, not the response: widen `CHECK_DAY` to a range (e.g. days 1–3, checked once per day rather than one exact turn) and reconsider `CASH_DANGER_THRESHOLD` against real observed pre-death-spiral cash trajectories (the moushun chen and other forensic replays already in `results/phase3_5/` and `results/phase3_6/` have the real numbers — use them instead of guessing a new threshold).
- **Wire it in**: add it as a new gated layer in `make_competitive_v3_agent`, following the exact pattern the existing three layers already use (config mutation, `already_triggered` state tracked in `state_ref`, at-most-once-per-episode). This is mechanically identical to how Layer 3 (animal response) was added on top of Layer 2 in Phase 3.8 — same integration shape, new trigger.
- **Validate:** regression suite must stay green (currently ~119+ tests across `scripts/phase3_*_regression_tests.py`); add new unit tests following `phase3_8_regression_tests.py`'s pattern (`test_never_downgrades`-equivalent: confirm it only ever *reduces* footprint, confirm it's a no-op when cash never gets low, confirm at-most-once firing). Then replay it against any real or synthetic trace that previously ended in the catastrophic-$0 pattern to confirm it actually fires this time — the whole point of this phase is fixing the fact that it *currently never does*.
- **Why this should move rank:** it doesn't need to win more games — it needs to stop losing the very worst ones. On the Elo-style live rating, converting a small number of catastrophic 0-point losses into merely-ordinary losses (or wins, if the reduced footprint survives to harvest) is a direct, low-variance rating improvement with no downside risk to the games that were already fine.

---

## Phase 2 — Sell-timing, not portfolio (submission candidate #5)

**Goal:** fix F-003 (`opportunistic_market_exit_timing`) using the lead Phase 5 itself identified as the safer application of the verified market simulator.

**Why this is different from what Phase 5 already killed:** Phase 5's failure was in estimating how many units of a *not-yet-planted* crop to switch to — an unsolved volume-estimation problem. Selling is different: by the time a SELL decision is made, the quantity is **already known** (it's sitting in the shed, harvested). There is no volume-estimation step to get wrong — only a batching/timing decision, which `agents/phase4/market_model.py::simulate_sell` and `market_depth`/`revenue_curve` are already built and verified to answer correctly (re-validated live against the running engine in Phase 5 §5, exact match).

- **Concrete case to fix:** the exact, quantified loss already on record (Phase 3.6 §4) — a 95-unit MELON dump landed at the $4/unit price floor, worth ~$25,650 less than spacing the same units across the day 8–10 price recovery. This is a real episode with real numbers to regression-test against.
- **Build:** a new sell-sizing layer that, given a pending SELL order and the crop's `market_depth`/`revenue_curve`, decides whether to sell the full quantity now or split it across turns/days — using `simulate_sell` to compare total realized revenue for each split against the current single-batch behavior. This plugs in at the SELL-order-construction point, wherever the tactical layer (`agents/phase2_4/common.py`) currently emits `SELL` actions — read that file first to find the exact insertion point before writing any code.
- **Validate the same way Phase 5 did it right:** re-run against the same 15 founding Variant D seeds plus the non-target archetype sweep (6 archetypes × 2 seeds) to confirm zero regression when the feature is inert, exactly like Phase 5 §9–10's methodology — that discipline is what let Phase 5 catch its own failure honestly instead of shipping it.
- **Why this should move rank:** this targets money efficiency in games you already win or nearly win, not new win conditions — expect a smaller, more marginal rank effect than Phase 1, but it's a real, quantified, previously-measured leak being closed, and it's structurally safe (bounded to SELL timing, can't touch what gets planted or when).

---

## Phase 3 — The tile-utilization planner (submission candidate #6 — the big one)

**Goal:** this is the step-change item. Both pieces of live-replay evidence gathered this session point at the same thing: **near-zero idle tiles, sustained across many simultaneous hands, is what separates a win from a loss even between two top-5 teams** (Crop Dusta vs. Whyme Labs, day 3 divergence — see [`LEADERBOARD_DIAGNOSTIC.md`](LEADERBOARD_DIAGNOSTIC.md) §5). Your current architecture doesn't have this: Planner v1 makes a **day-0 sizing decision once** (`agents/phase2_6/decisions.py`'s greedy knapsack) and hands off to the frozen tactical layer (`agents/phase2_4/common.py`) for per-turn execution — there is no rolling re-evaluation of whether every owned tile is actually staying in a water→harvest→replant cycle every single day.

This is also the one explicitly flagged as out-of-scope in *every* phase so far (Phase 4's own report: *"the rolling-horizon per-tile task allocator... out of scope by the brief's own 'do not modify C' and this project's standing discipline against rewriting validated, frozen code"*). That discipline was right for the smaller phases — it is exactly the discipline to break here, deliberately, because the evidence now says the ceiling is architectural, not tunable.

- **Do not modify `agents/phase2_4/common.py` in place.** Given how much validated behavior sits on top of it, build the new tile-scheduling logic as a new, isolated module (`agents/phase6/tile_scheduler.py` or similar) that can be **A/B'd against the frozen tactical layer** behind a flag, the same integration pattern Phase 5 used for its (failed) substitution candidate — additive, swappable, easy to roll back.
- **What it should actually do**, grounded in what the replays showed: each day, for every owned tile the farmer/hands can reach, guarantee it gets watered (or harvested, or replanted) that day rather than relying on whichever unit happens to path through it — i.e. genuine task assignment across however many hands are hired, not fixed per-unit routines. This is a scheduling/assignment problem (something like nearest-idle-hand-to-nearest-needs-attention-tile), not a new economic model — it doesn't need to re-decide *what* to plant, only to stop wasting tile-days on things that are already decided.
- **Benchmark it correctly:** this is the phase where synthetic archetypes stop being sufficient (they cap at ~10 hands; real opponents already exceed that). Before evaluating this candidate, pull a handful of real top-tier replays via the Kaggle API/"Daily Top Episodes Dataset" (or record fresh ones the way this session did manually) and use tile-idle-time as an explicit, measured metric — not just final money — the way this session observed it directly on the board.
- **Why this should move rank:** this is the only item in this roadmap that plausibly changes which *tier* you're competing in, not just your record within your current tier. It's also the highest-risk item — budget real testing time, and be willing to find out it doesn't help (per this project's own standing discipline: report the honest result even if negative).

---

## Phase 4 — Recalibrate the ceilings Planner v1 assumes (submission candidate #7)

**Goal:** once Phase 3's scheduling actually keeps tiles busy, the fixed caps elsewhere in the pipeline become the next binding constraint.

- **`agents/phase2_6/decisions.py`'s hard 2-animals-per-cycle cap** and the Phase 3.8 animal response's own ceiling (max 6 total, `{"COW":3,"SHEEP":3}`) were both validated against synthetic archetypes that bankrupt past ~10 hands — well below what live replays this session showed (Yuan800: 8+ sheep by day 9, expanding). Re-test these specific caps once Phase 0's calibration probe and Phase 3's scheduler are in, using the same real-replay benchmark from Phase 3.
- **`cash_reserve_frac = 0.1`** in the greedy knapsack budget — worth checking against the observed live pattern of spending down to single-digit cash on day 1 (Yuan800 replay: $27 left after day 1's last turn). This may be too conservative, or it may be exactly why the current agent avoids F-005-style crashes better than a more aggressive spender would; this is a question to test, not assume an answer to.
- **Land-purchase timing** — live replays bought the second quadrant by day 7 of 30. Confirm what day your current agent typically buys NE (if at all) and whether accelerating it pays back given the remaining season length.

---

## Phase 5 — Evaluation discipline (ongoing, not a single submission)

**Goal:** make sure every phase above is actually measured the way the live leaderboard measures you, so "validated" claims keep meaning what they say.

- Every promotion decision in this project so far has correctly followed a strong discipline (regression suites, non-target archetype sweeps, honest negative results like Phase 5's own). The one gap: **almost all of it is scored by mean final money, and the live rating is win/loss only.** Add win-rate-against-hardest-available-opponent as a first-class metric alongside mean money for every future phase's promotion decision, per [`LEADERBOARD_DIAGNOSTIC.md`](LEADERBOARD_DIAGNOSTIC.md) §6 P3.
- Build the real-replay benchmark set once (needed by Phase 3 and Phase 4 above anyway) and keep reusing it — it directly answers questions synthetic archetypes structurally cannot.

---

## Submission sequencing

Per the Elo mechanics in `LEADERBOARD_DIAGNOSTIC.md` §1: a new submission needs ~a day to mean anything, and only your 2 most recent submissions matter at the final deadline. Recommended cadence:

| Order | What ships | Expected effect | Confidence |
|---|---|---|---|
| 1 | **Phase -1 (dead sell-safety wiring fix) — ✅ shipped, commit `22cca31`, not yet uploaded to Kaggle** | eliminates a confirmed class of $0 losses | **Highest — verified bug, provably inert elsewhere** |
| 2 | Phase 1 (F-005 fix) | fewer catastrophic losses → modest but real rating floor rise | High — bounded downside |
| 3 | Phase 2 (sell-timing) | closes a specific, quantified leak in already-winnable games | Medium — real but marginal |
| 4 | Phase 3 (tile scheduler) | the actual tier-change candidate | Lower confidence, highest potential payoff — test hard before trusting it |
| 5 | Phase 4 (recalibrated ceilings, now also targeting the 8-13 hand / 10-14 animal range Phase 6 observed in every strong opponent) | compounds on Phase 3 once tiles are no longer idle | Depends entirely on Phase 3 landing first |

Phase 0 (calibration probe) still runs early and produces no submission of its own — slot it wherever convenient before Phase 3/4 need its answer, ideally right after Phase -1 ships.

Hold two submission slots for your two best validated candidates at any time — per the submission-hygiene rule already in the diagnostic report, don't burn a slot re-rolling a near-duplicate; each new entry in the table above is a genuine architectural change, which is exactly what a slot should be spent on.
