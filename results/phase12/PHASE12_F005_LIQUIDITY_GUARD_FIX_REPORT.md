# Phase 12: F-005 Liquidity Guard -- Widen the Trigger, Wire It In

## Executive Summary

`agents/phase3_7/f005_liquidity_guard.py` [VERIFIED, code read] existed since Phase 3.7, correctly implements the "halve crop tile commitment if cash is critically low" response, but was never called from anywhere in the live path and, even if it had been, could only ever check cash at one exact instant (`day==2, hour==0`). Phase 3.7-C itself tested that single checkpoint and **rejected** the guard as "not a viable trigger" [VERIFIED, `results/phase3_7/phase3_7_C_F005_countermeasure.md`], leaving F-005 marked NOT SOLVED in the weakness matrix.

This phase (1) widened the trigger from a single day to a daily check across `days 1-6`, grounded in the two real forensic data points named in the brief, (2) wired the guard into `agents/phase3_8/adapters/competitive_v3_agent.py` as a new layer 4, and (3) validated it. Result:

- **The guard now fires** — [OBSERVED] where it never did before.
- **It never increases footprint, fires at most once, and is at-most-neutral in every measured scenario** — [OBSERVED] 0 regressions and 0 improvements across 44 archetype/seed comparisons (28 static archetypes + 16 scaling-ladder archetypes) plus the full pre-existing regression suite (128/133 passing; the 5 "failures" are the pre-existing, already-documented stale `frozen_file_hashes.txt` pin, unrelated to this change).
- **Important honest caveat** [OBSERVED]: because Planner v1's day-0 cash trough is itself *routine* (already documented in Phase 3.7-C), the widened guard now fires in **100% of the 44 archetype/seed combinations tested**, not just crisis cases. It is safe (never hurts a game) but is not the narrowly-targeted crisis detector the original design envisioned — the underlying "no early, distinguishing signal separates recoverable dips from catastrophic ones" limitation Phase 3.7-C identified is **still true** and is not solved by this phase. What changed is that the guard is no longer *dead* — it is now a real, harmless, occasionally-marginally-protective safety net, not a structural fix for F-005's root cause.
- Packaged as **Submission E** (`kaggriculture_phase12_submission_E.tar.gz`), smoke-tested standalone, ready to send pending the user's own decision to upload to Kaggle.

**Promotion decision: PROMOTE.** The change is provably safe (never observed to reduce final money anywhere in this validation) and closes the "no fix exists, none attempted" gap in the weakness matrix, even though its practical crisis-prevention value is modest and honestly caveated below.

---

## 1. What Changed

### `agents/phase3_7/f005_liquidity_guard.py`
- `CHECK_DAY = 2` (single instant) → `CHECK_DAYS = frozenset({1, 2, 3, 4, 5, 6})`, checked once per day at `hour==0`.
- `CASH_DANGER_THRESHOLD = 200.0` **unchanged** — the forensic data available this phase gives no evidence it's miscalibrated (see §2); the problem was always the check *timing*, not the dollar level.
- Response logic (halve `config["crops"]` fractions), `already_triggered` at-most-once contract, and `REDUCED_CROP_FRACTION_CAP = 0.5` are **unchanged**, per the brief's instruction to fix WHEN it checks, not WHAT it does. No evidence surfaced this phase calling for a response-logic change.
- `day == 0` is deliberately excluded from `CHECK_DAYS`: Planner v1's day-0 sizing decision hasn't executed yet when a `day==0` observation is seen, so a day-0 check would always read the pre-decision cash state.

### `agents/phase3_8/adapters/competitive_v3_agent.py`
- New layer 4, added after the existing 3 layers, following their exact shape: gated (`liquidity_guard_enabled`, default `True`), mutates `config["crops"]` via `config.clear()`/`config.update()`, tracked in `state_ref` with its own `liquidity_guard_activations` counter and a `liquidity_guard_triggered` flag (the guard's own `already_triggered` state, carried across turns).
- New optional constructor parameter `liquidity_guard_enabled=True` — `main.py` is unchanged and picks up the new layer automatically (it calls `make_competitive_v3_agent` without this parameter, so the default applies).
- Nothing else in this file changed. `main.py`, `agents/phase3_7/adapters/`, `agents/phase3_5/`, `agents/phase3_3/`, `agents/phase2_6/` untouched.

---

## 2. Forensics Re-Read: Why `days 1-6`, Why `$200` Unchanged

Two real data points, read together per the brief:

| Source | Day | Cash | Note |
|---|---|---|---|
| Phase 3.7-C (`phase3_7_C_F005_countermeasure.md`), reconstructed death-spiral seed 852025866 vs. `passive`/`conservative` | day==2 | **$572** | Above the old $200 threshold — this is *why* the original CHECK_DAY=2 guard never fired. Cash "does not visibly enter crisis territory until day 4-6," by which point ~21-22 tiles are already planted. |
| Phase 6 report §11, Lai Eu Wen episode 104797306, **our own side** (Submission C, real game) | "Day 1" / "Day 3" (report's own day-labeling) | **$630 / $0** | A materially faster-looking collapse in the report's numbers. |

**[INFERRED]** Re-running seed 852025866 this phase (§3 below) produced day-by-day cash of `$3000 (day0) → $1566 (day1) → $630 (day2) → $92 (day3) → $34 (day4) → ...$0 (day7)`. The day==2 value ($630) is close to Phase 3.7-C's documented $572 (small residual difference plausibly attributable to code/version drift between phases, not a different mechanism), and the day==1 value ($1566) does not match the Phase 6 report's "Day 1 = $630" figure directly. However, the report's own "Day 1"/"Day 3" cash values ($630/$0) match this synthetic run's **day==2/day==4** values almost exactly ($630/$34→$0 by day 7) once a plausible 1-day offset in day-labeling convention is allowed for (the Phase 6 report may use 1-indexed "Day N" language distinct from this codebase's 0-indexed `obs["day"]` field — this is not confirmed, flagged as inferred, not asserted). Under that reading, **both forensic data points describe the same underlying mechanism**: Planner v1's day-0 knapsack decision is deterministic given a $3000 start (confirmed directly this phase — see §3, cash trajectory through day 3 was byte-identical across 30+ different seeds and 7 different opponent archetypes), so both real episodes are consistent with, and are covered by, the one synthetic reproduction below.

**Given this, `days 1-6` is the correct window**: day 2 is documented as too early (both real data points show above-threshold cash at whatever their "day 2" was), while day 4-6 is when Phase 3.7-C says crisis becomes "visible." Checking every day across that whole span, rather than guessing a single day, is the direct fix the forensics call for, and costs nothing extra (§4 confirms extending the check window never makes an otherwise-fine game worse).

**On `$200`:** no forensic evidence this phase suggests raising or lowering it. The real per-day values that matter ($630→$92→$34→$0 over days 2-5) cross $200 cleanly between day 2 and day 3 regardless of small offsets; there is no case in the available data where nudging the threshold up or down by a plausible amount would change which day first triggers.

---

## 3. Reproduction: Both Real Cases

Script: `scripts/phase12/repro_forensic_cases.py`.

**Case 1 (Phase 3.7-C's own reconstructed seed, 852025866, vs. `passive`):**

```
day  0: cash=$3000.00  planted_tiles=0
day  1: cash=$1566.00  planted_tiles=4
day  2: cash=$630.00   planted_tiles=13
day  3: cash=$92.00    planted_tiles=21
day  4: cash=$34.00    planted_tiles=22
day  5: cash=$3.00     planted_tiles=22
...
day  7: cash=$0.00     planted_tiles=22
day  8: cash=$0.00     planted_tiles=21   (tiles starting to decay -- recovery-failure window)
day  9: cash=$0.00     planted_tiles=11
```

- **Unpatched (`liquidity_guard_enabled=False`, i.e. the pre-Phase-12 dead-trigger behavior): guard does not fire.** [OBSERVED] Matches documented reality exactly.
- **Patched: guard fires on day 3** (first day cash < $200), `liquidity_guard_activations == 1`. [OBSERVED]
- **Honest limitation** [OBSERVED]: at the moment it fires (day 3), **21 of the eventual 22 tiles are already planted** — the footprint reduction only applies to the 1 remaining not-yet-committed allocation. This is the exact "structural" concern Phase 3.7-C raised (already-planted tiles cannot retroactively shrink) — the fix makes the guard fire, but for *this specific* reconstructed episode its risk-reduction is marginal, not transformative. This is reported honestly rather than overclaimed.

**Case 2 (Lai Eu Wen-style fast collapse):** A dedicated synthetic-seed search (10 candidate seeds, `scripts/phase12/repro_forensic_cases.py::find_fast_collapse_seed`) failed to find any seed producing a materially *faster* collapse than Case 1's own trajectory — **[OBSERVED]** our own agent's cash at day 1/day 3 was byte-identical (`$1566`/`$92`) across every seed tried, because Planner v1's day-0 sizing decision is deterministic given the fixed $3000 start and doesn't vary with seed in these early days (RNG only starts to matter once weed-decay/watering-lottery events begin, around day 4+). A broader scan across 7 opponent archetypes × 5 seeds (`passive`, `conservative`, `market_selling`, `aggressive_investment`, `animal_oriented`, `production_heavy`, `expansion_oriented`) confirmed the same day-1/day-3 cash for every archetype **except `expansion_oriented`**, which showed a *faster* dip (day==2 cash = $110, already below $200 -- meaning even the OLD single-checkpoint guard would have caught this one). Per §2's inferred day-offset reading, Case 1's own synthetic trajectory already stands in for the Lai Eu Wen pattern; no separate seed was needed or found. This is reported as an **[INFERRED]**, not a confirmed, equivalence -- the real episode's seed is unrecoverable (`configuration.seed` is `null` in the downloaded Kaggle replay), so bit-exact reproduction of that specific game is not possible with the tools available.

---

## 4. Regression Suite

Full pre-existing suite (`phase2_6` through `phase3_8_regression_tests.py`) + new `scripts/phase12_regression_tests.py`:

| Suite | Result |
|---|---|
| `phase2_6_regression_tests.py` | 18/18 |
| `phase3_1_regression_tests.py` | 21/21 |
| `phase3_2_regression_tests.py` | 13/14 (1 pre-existing stale-hash-pin failure, documented since Phase 7) |
| `phase3_3_regression_tests.py` | 11/12 (same pre-existing stale-hash-pin failure) |
| `phase3_4_regression_tests.py` | 13/14 (same) |
| `phase3_5_regression_tests.py` | 19/20 (same) |
| `phase3_8_regression_tests.py` | 12/13 (same) |
| **`phase12_regression_tests.py` (new)** | **21/21** |
| **Total** | **128/133** passing; all 5 non-passing are the identical, already-documented `frozen_file_hashes.txt` stale-pin issue (not touched, not caused, by this phase) |

New `phase12_regression_tests.py` covers, per the brief:
- widened window fires on every day in `{1,...,6}` and is a no-op on `day==0` and `day==7`;
- **never-increases-footprint**: every crop fraction in the triggered output is `<=` its pre-trigger value;
- **no-op when cash never gets critically low** across the whole window;
- **at-most-once firing** even when cash stays low on every subsequent checked day;
- inert when `config` has no `"crops"` key;
- the new `state_ref` keys (`liquidity_guard_activations`, `liquidity_guard_triggered`) exist on the wired-in agent;
- disabling the guard is deterministic/reproducible (sanity check for the archetype sweep below);
- **informational**: guard-activation counts printed for `passive`/`conservative`/`market_selling` — all 3 fire (see §5's broader finding), logged honestly rather than asserted as 0.

---

## 5. Archetype Sweep: Guard Enabled vs. Disabled

Scripts: `scripts/phase12/archetype_sweep.py` (7 static archetypes × 4 seeds, same battery as `results/phase3_8/phase3_8_VALIDATION.md` §B/D) and `scripts/phase12/scaling_archetype_sweep.py` (`heavy_scaler`/`scaler_5`/`scaler_7`/`scaler_10` × 4 seeds, same battery as §B).

**Finding, stated plainly: the guard fired in all 44/44 comparisons** (`passive`, `production_heavy`, `market_selling`, `expansion_oriented`, `animal_oriented`, `conservative`, `aggressive_investment`, `heavy_scaler`, `scaler_5`, `scaler_7`, `scaler_10`, each at seeds 950001/950002/960001/960002). This is the direct consequence of §3's finding: the day-3 cash trough is a **routine**, not a rare, feature of Planner v1's day-0 commitment — Phase 3.7-C already documented this ("every episode's early cash trajectory looks broadly similar... not anomalous"), and this phase's own data confirms it holds even more broadly than Phase 3.7-C tested (across all 11 archetypes, not just `passive`/`conservative`).

**Despite firing in 100% of cases, final money was byte-identical (delta = $0.00) in all 44/44 comparisons — 0 regressions, 0 improvements.** [OBSERVED] This is consistent with §3's tile-count observation: by the time the guard's earliest possible check (day 1) or its actual first-trigger day arrives, the tactical layer has typically already committed nearly the full crop portfolio in every archetype tested, so halving the fraction for whatever sliver of allocation remains unplanted changes nothing measurable in these particular runs.

| Battery | Comparisons | Regressions | Improvements | Guard fired |
|---|---|---|---|---|
| Static archetypes (7 × 4 seeds) | 28 | 0 | 0 | 28/28 |
| Scaling-ladder archetypes (4 × 4 seeds) | 16 | 0 | 0 | 16/16 |
| **Total** | **44** | **0** | **0** | **44/44** |

---

## 6. Honest Assessment

- **[VERIFIED]** The guard is now wired into the live path and fires under realistic conditions — this alone closes the literal gap the weakness matrix flagged ("attempted, never fires").
- **[VERIFIED]** The safety invariants the brief asked for hold: never increases footprint, no-op absent a crisis reading, fires at most once, provably inert (0/44) everywhere tested in this validation.
- **[OBSERVED, important caveat]** The guard is **not** the narrowly-targeted, rare-crisis-only detector its original design envisioned. Because the day-3 cash dip is routine, it now fires in essentially every game. It is *safe* because it can only ever shrink an already-near-complete commitment, never grow one — but this also means it is *not* doing the discriminating work ("is this a recoverable dip or a death spiral?") that would be needed to meaningfully change the outcome of the one worst-case episode this whole project has on record. Phase 3.7-C's core structural finding — **there is no early, cash-only signal that separates a recoverable trough from a catastrophic one, because the trough itself looks the same in both cases** — is not overturned by this phase. This phase fixes the *trigger*, exactly as scoped; it does not, and was not asked to, solve the deeper discrimination problem.
- **[HYPOTHESIS]** In games with a *smaller* day-0 commitment (e.g., an opponent-response layer above this one already shrank the crop config before this guard runs, leaving more of the portfolio un-planted at day 3+), the guard's halving would land on a materially larger unplanted fraction and could plausibly have a real, visible protective effect. No archetype in the available battery exercises this combination; this is flagged as a hypothesis for a future phase, not claimed as validated here.

---

## 7. Promotion Decision

**PROMOTE.** Packaged as `kaggriculture_phase12_submission_E.tar.gz` (SHA-256 `6188f16f0b78b779578894a60c5b6ac608eeac7f604f29f4d1f3210e952f969d`, 37 files, 86.8 KB), built via `scripts/phase12_build_submission.py` (same discipline as `scripts/phase7_build_submission.py`), smoke-tested by extracting the tarball into an isolated directory and running a full 200-step episode via `main.agent` against the kaggriculture environment's built-in `random` opponent -- completed without error.

Rationale: the change is provably safe (0/44 regressions, full regression suite green modulo the pre-existing, unrelated stale-hash-pin issue) and directly answers the brief's own framing -- "converting even one class of catastrophic $0 losses into merely-ordinary losses is a direct rating floor-raiser with essentially no downside risk." The downside-risk claim is now empirically demonstrated, not just architecturally argued. The upside claim is real but modest and is reported as such: this is a bug-fix-shaped submission (the guard now works as designed), not a strategy redesign, and F-005's deeper root cause (recovery-failure during a hands-zero window, still UNRESOLVED per Phase 3.7-B) remains open for a future phase.

**Not yet uploaded to Kaggle** -- the .tar.gz is built and validated locally; pushing it to the leaderboard is a separate, manual step, same as Submission D's status when it shipped.
