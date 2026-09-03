# Phase 20: A Liquidity Guard for agents/phase15/ — Recovering the Win Rate Phase 19 Lost

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py` — confirmed via `git status --short` below). Per the standing exception, `agents/phase15/`'s own files were modified directly (new `liquidity_guard.py`; `execution.py` wired to use it).

## Executive Summary

**[OBSERVED] Both bars are now cleared together — the isolated-money gain Phase 19 achieved is kept, and the head-to-head win-rate regression it caused is substantially recovered, not traded for the other.** On the same 15-seed wide sample:

- **Isolated final money: mean $56,664.93** (median $55,305, range $49,190-$66,806, **14 of 15 seeds clear $50,000**) — essentially unchanged from Phase 19's $57,659.47 (a $994.54 / 1.7% cost, not a regression back toward Phase 17's $43,735).
- **Head-to-head win rate vs. Submission C and Submission E: 13/15 (86.7%)** — recovered from Phase 19's 53.3%, and close to (though not full parity with) Phase 17's original 100%. Mean margin widened substantially too: ours $48,323.00 vs. theirs $17,478.93 (+176%), vs. Phase 19's +26.6%.

**Root cause diagnosed by direct trace (Section 2), not assumed to match Submission C's F-005 case**: the collapse pattern in `agents/phase15/` is NOT a single early crisis — it recurs 3-4 separate times across the first ~25 days of a game, each time triggered by a big lump expenditure (a land-quadrant purchase, or a large hire batch) that drains cash from a comfortable level to exactly $0 in one step. Once cash is genuinely $0, the daily hands-reset mechanic (hands reset to `[]` every day) means even the CHEAPEST possible re-hire is unaffordable that whole day — a total production standstill, not just slower growth. This is why a single, one-shot, F-005-style "halve the crop config once" guard is the wrong shape here: the guard needed to be a per-turn, re-armable throttle, plus a pre-emptive reserve check before the lump purchases that start each collapse — not a reactive, once-only response.

**Decision: PROMOTE. Packaged as Submission G** (`kaggriculture_phase20_submission_G.tar.gz`), validated with the same discipline as every prior promoted phase (dependency closure, cold-process test, re-confirmed packaged-artifact behavior, SHA-256).

## 1. Reading the Existing F-005 Guard First

`agents/phase3_7/f005_liquidity_guard.py` (Phase 3.7/12, Submission C/E's lineage): checks cash on a day-indexed window (`CHECK_DAYS = {1..6}`), and if it fires — **at most once per episode** — halves the (otherwise-static) crop-portfolio config for the rest of the game. This is well-suited to Submission C's own diagnosed failure mode (Phase 3.7-B: a single early cash trough that either recovers on its own or doesn't, with no second chance needed once past it). `agents/phase15/`'s architecture is different in a way that matters here: `macro_controller.py` produces PROPORTIONAL, day-indexed targets that keep ramping upward throughout the game (not a single day-0 config), so a mechanism that can only intervene once is structurally mismatched to an agent whose commitment keeps growing (and can keep re-triggering a cash crisis) well past day 6.

## 2. Diagnosing the Real Collapse Pattern

Traced 3 of Phase 19's worst head-to-head losses (`results/phase19/phase19_wide_validation_results.json`, sorted by margin: seeds 701002, 700003, 702003, plus the already-traced 702005 from the Phase 19 report) day-by-day, before writing any guard code.

**[VERIFIED, by direct trace] All 4 traced seeds show an IDENTICAL day 0-9 cash trajectory** ($2,098 → $1,238 → $556 → $311 → $198 → $66 → $24 → $12 → $0 → $0), regardless of seed — confirming (again, as Phase 15/16 found before) that the day-0 opening commitment is deterministic given a fixed $3,000 start. **The pattern that matters is what happens AFTER**: cash recovers to $1,905-$3,688 by day 11-14 once hands/land/animals ramp up, but then **collapses to $0 again at day 15** (exactly when land jumps from 2 to 3 quadrants), stays at or near $0 through day 16-20 with hands repeatedly dropping to 0, partially recovers, then **collapses a THIRD time around day 21-25** before finally breaking free from day 26 onward as the endgame liquidation converts standing crops to cash.

**[VERIFIED, root cause] The trigger for each collapse is a lump expenditure, not a slow drain**: at day 14, cash is $2,442-$2,805 (comfortable); the very next sampled day (15), it is $0-$83. A land-quadrant purchase costs a sum large enough to consume nearly all of that comfortable balance in one shot. **[VERIFIED, by reading `vendor_kaggriculture/kaggriculture.py` directly] Once cash reaches exactly $0, the situation is worse than merely "can't grow"**: hands reset to `[]` every single day (a documented engine mechanic), so re-hiring even a single hand the next day costs `fib(0) = 1`. If cash is genuinely $0 that day, even a $1 hire is unaffordable, and the entire day passes with zero hands, zero production, and zero recovery — directly explaining the repeated multi-day stretches of `hands=0`.

**This is the reason a single-shot guard (matching F-005's shape literally) is the wrong tool**: the pattern recurs 2-3 times per game, driven by discrete lump-cost events, not a single early trough.

## 3. The Guard

New module: `agents/phase15/liquidity_guard.py`. Two complementary mechanisms, both re-checked every turn (not "at most once"):

1. **`apply_liquidity_guard(targets, cash, current_hands, current_land_quadrants)`**: if cash falls below `CASH_DANGER_THRESHOLD = $300`, caps this turn's hiring target down to a small operating floor (`MIN_HANDS_WHEN_GUARDED = 3`, never below whatever is already hired) instead of the macro controller's full proposed target, and freezes further land purchases at the current owned count. **[VERIFIED, found and fixed while validating the guard's first draft]**: an initial version capped hands down to the RAW current hand count, which — because hands reset to `[]` daily — meant targeting exactly zero hands on the very day cash was already critical, deepening rather than escaping the drought. The `MIN_HANDS_WHEN_GUARDED` floor fixes this: it keeps the farm minimally staffed (a cheap floor, far below the Fibonacci-cost cliff of the full target) while still suppressing the expensive climb back to 11 hands until cash recovers.
2. **`land_purchase_affordable(money, cost)`**: requires a `$500` reserve to remain AFTER a land purchase, not just that the raw cost is technically covered. **[VERIFIED, found and fixed while validating the guard's second draft]**: mechanism 1 alone reacts only AFTER cash is already critical, but the traced collapses show cash was comfortable ($2,442+) the turn immediately before the triggering land purchase — a purely reactive guard can never prevent the purchase that causes the crash in the first place. Requiring a reserve makes the land-purchase decision itself pre-emptive.

Both mechanisms can only ever REDUCE a turn's commitment relative to what the macro controller proposed, never raise it — the same "can only reduce risk, never add it" safety principle every guard in this project has used (F-005 included).

## 4. Before/After Validation (15-Seed Wide Sample)

Reused `scripts/phase17/wide_validate.py` unchanged, same `scripts/phase3_2_configs.py::SEED_SETS` (n=15).

### Isolated final money

| Statistic | Phase 19 (no guard) | Phase 20 (with guard) |
|---|---|---|
| Mean | $57,659.47 | $56,664.93 |
| Median | $57,797.00 | $55,305.00 |
| Min | $46,697.00 | $49,190.00 |
| Max | $67,435.00 | $66,806.00 |
| Seeds clearing $50,000 | 13/15 | **14/15** |

**Cost of the guard: $994.54 mean (1.7%)** — the bar stays clearly cleared, not eroded back toward Phase 17's $43,734.93.

### Head-to-head vs. Submission C (byte-identical vs. Submission E in every seed)

| Statistic | Phase 17 (original) | Phase 19 (no guard) | Phase 20 (with guard) |
|---|---|---|---|
| Ours: mean | $38,079.80 | $28,937.20 | **$48,323.00** |
| Ours: min | $29,200.00 | $5,298.00 | $20,865.00 |
| Theirs: mean | $21,271.47 | $22,853.87 | $17,478.93 |
| **Win rate** | **15/15 (100%)** | **8/15 (53.3%)** | **13/15 (86.7%)** |

Full per-seed data: `results/phase20/phase20_wide_validation_results.json`. The 2 remaining losses (seeds 701001, 701003) are now ordinary competitive losses (ours $20,865-$24,577 vs. theirs $29,357-$29,382) — no longer the catastrophic sub-$10,000 collapses Phase 19 showed on these and other seeds.

## 5. Direct Trace Confirmation (Not Just an Aggregate Number)

Seed 701002 (a clear Phase-19 loss, $5,298 vs. Submission C's $24,779) was re-traced after the fix:

| Day | Phase 19 (no guard) | Phase 20 (with guard) |
|---|---|---|
| 14 | cash $2,442, hands 11 | cash $2,805, hands 11 |
| 15 | **cash $0** (land 2→3 just bought) | cash $83, hands 11 (land bought, but reserve check held it back until affordable) |
| 16-17 | cash $0, **hands 0 both days** | hands stay at the 3-hand floor, cash low but non-zero |
| 18-20 | cash $0-2, hands oscillating 0-11 | cash recovering, no further hands=0 collapse |
| 29 (final) | **$5,298** | **$30,849** |

**[VERIFIED] The guard fires and directly prevents the specific mechanism diagnosed in Section 2**: the day-15 land purchase no longer drains cash straight to $0, and the multi-day `hands=0` stretches that followed it in the unguarded run do not recur. This seed moved from a clear loss to a clear win (ours $30,849 vs. Submission C's $23,091).

## 6. Regression Check

`git status --short main.py agents/phase2_6 agents/phase3_3 agents/phase3_5 agents/phase3_8 agents/phase2_3/common.py agents/phase2_4/common.py`: only `agents/phase3_8/adapters/competitive_v3_agent.py` (Phase 12's prior, unrelated F-005 wiring, unchanged by this phase) shows as modified. Existing regression suite (`scripts/phase12_regression_tests.py`, representative): 21/21 passing, unchanged.

## 7. Packaging (Submission G)

Same discipline as Phase 18 (Submission F). Letter confirmed by listing every existing `kaggriculture_*.tar.gz` in the repo root: A-F taken, **G** is next.

| Property | Value |
|---|---|
| Filename | `kaggriculture_phase20_submission_G.tar.gz` |
| SHA-256 | `c6cef8e6929ec86eb418dad5646e81c8ebf495cc44631f47230bd5f317344a3a` |
| Size | 42,788 bytes (41.8 KB) |
| File count | 17 |

**Dependency closure**: identical to Submission F's (`agents/phase2_3/common.py`, `agents/phase3/`, `agents/phase4/market_model.py`, `vendor_kaggriculture/`) plus the two new self-contained modules (`agents/phase15/endgame.py`, `agents/phase15/liquidity_guard.py` — neither imports anything outside the standard library, confirmed by direct read).

**Cold-process test**: extracted to `/tmp/phase20_coldtest` (outside the repo), loaded via `exec()` with `__file__` deliberately unset (`sys.path.append`, matching Kaggle's own convention, same technique validated for Submission F), ran a full 720-turn episode against the environment's built-in `random` opponent: `DONE`/`DONE` status, final money $63,433 (ours) vs. $0 (random), 2.66s runtime.

**Re-confirmed packaged-artifact win rate** (`scripts/phase20/reconfirm_packaged_head_to_head.py`, same cross-root technique validated in Phase 18): packaged Submission G vs. in-repo Submission C, 4 development seeds — **4/4 wins**, figures matching the in-repo wide-sample run exactly (seed 700000: $51,739 vs. $28,777, etc.). All dependency files were also SHA-256-verified byte-identical to their repo sources.

## 8. Promotion Decision

**PROMOTE.** Both of this phase's required bars are cleared together, not one at the expense of the other: isolated money stays clearly inside the $50,000-80,000+ range (mean $56,664.93, 14/15 seeds), and head-to-head win rate against both live submissions recovered from Phase 19's disqualifying 53.3% to **86.7%** — short of Phase 17's original 100%, but a clear, large recovery, and the brief's own standard ("full parity is the ideal but not strictly required") is met. `kaggriculture_phase20_submission_G.tar.gz` is ready to upload.

## Changed Files

Modified (Phase 15's own, non-frozen agent — the standing exception for this phase):
- `agents/phase15/execution.py` (wired to the new liquidity guard: per-turn hiring/land-target throttle, pre-emptive land-purchase reserve check)

New, additive:
- `agents/phase15/liquidity_guard.py`
- `scripts/phase20_build_submission.py`
- `scripts/phase20/reconfirm_packaged_head_to_head.py`
- `results/phase20/phase20_wide_validation_results.json`
- `results/phase20/PHASE20_LIQUIDITY_GUARD_REPORT.md` (this file)
- `kaggriculture_phase20_submission_G.tar.gz` (repo root, the built package)

No frozen file was touched. `main.py` still builds Submission C/E. `kaggriculture_phase18_submission_F.tar.gz` (Submission F, already shipped) is completely unaffected.
