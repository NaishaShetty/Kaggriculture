# Kaggriculture Phase 2.1 — Economic Instrumentation & Telemetry Foundation

Date: 2026-08-16. Builds directly on the Phase 2.0 freeze
([docs/PHASE2_0_REPORT.md](PHASE2_0_REPORT.md), `phase1_freeze/`). See
[docs/PHASE2_1_ARCHITECTURE.md](PHASE2_1_ARCHITECTURE.md) for the full design rationale and the two
real bugs caught by the validation suite during development, and
[docs/PHASE2_1_TELEMETRY_SCHEMA.md](PHASE2_1_TELEMETRY_SCHEMA.md) for the field-by-field schema.

## 1. Freeze integrity reverified before and after this phase

`sha256sum -c phase1_freeze/hashes.txt` — all 15 entries `OK`, both before any Phase 2.1 code was
written and again after this report was drafted. No file under `vendor_kaggriculture/`,
`agents/baseline_agent.py`, `harness/run_episodes.py`, `kaggriculture-data/`, `docs/00-02` +
`PHASE1_REPORT.md`, or any historical `results/*` directory was touched. All Phase 2.1 code lives
under `instrumentation/` (new); all Phase 2.1 output lives under `results/phase2_1/` (new, distinct
from every Phase 1/2.0 results directory).

## 2. Inventory of existing capabilities (brief §5) — see architecture doc §0 for the full table

Already available: final money/winner/status/runtime/aggregate stats (`harness/run_episodes.py`), and
critically, the **complete per-step observation/action/reward/status trajectory** via
`env.toJSON()` — already produced by the frozen simulator, just never analyzed. Missing (built this
phase): financial/production/land/fertilizer ledgers, action classification, market/town telemetry,
daily/episode summaries, accounting validation. Requires reconstruction (no stable object IDs):
crop/animal instance identity, approximated via `(x, y, planted_day)`. Cannot currently be measured
exactly: individual per-unit market-clearing price within a multi-unit order (see §5 below).

## 3. Instrumentation architecture

Entirely post-hoc and read-only: `Frozen Agent → Frozen Simulator → env.toJSON() →
instrumentation.extractor (raw) → instrumentation.ledger/market_telemetry (derived) →
instrumentation.metrics (derived) → instrumentation.validation → results/phase2_1/`. No agent
wrapping, no simulator patching, no live-loop hook. Full diagram and rationale in the architecture doc.

## 4. Metrics implemented

Financial ledger (income/expenditure by category, per-transaction records, starting/ending money
reconciliation), production ledger (per-instance crop and animal lifecycle: planting, watering,
fertilizing, feeding, caring, harvests, removal/weed/escape), land ledger (unlocked-quadrant tracking,
purchase cost verification), fertilizer ledger (aggregate source/use/sale), action efficiency
(productive/idle/movement/market fractions per brief §9), crop-level and animal-level economics
(revenue per harvested unit / per seed / per action — measurement only, no ranking), market telemetry
(per-turn price/inventory history, realized transaction prices, volatility), town-demand telemetry
(shop unlock events including duplicate instances, deterministic consumption reconstruction), daily
summaries, episode summaries, and a 4-part accounting validation suite (money, land, fertilizer,
per-product inventory conservation).

## 5. Known limitations (stated up front, not buried)

1. **Individual per-unit market-clearing price** within a multi-unit SELL/BUY_PRODUCT order cannot be
   recovered exactly without re-simulating the dual-player, per-unit lockstep pricing loop in
   `_process_market` — deliberately out of scope (re-simulating gameplay to measure it would blur the
   read-only architecture this phase is built on). The **average** realized price per turn *is* exact
   (derived from ground-truth money delta ÷ ground-truth quantity delta) whenever a turn's shed
   activity for that item is unambiguous, which was true for 100% of transactions in every benchmark
   episode run this phase.
2. **Per-unit (which specific hand) attribution** of fertilizer/inventory movement is not preserved
   when multiple hands act on the same item in the same turn — aggregate totals remain exact.
   Immaterial to every benchmark this phase (none of pass/starter/baseline ever hire hands).
3. **Shed-capacity overflow discards** are not independently confirmed as the cause of an inventory
   discrepancy; the validation suite flags a positive discrepancy as `PARTIAL` (plausibly overflow)
   rather than asserting it. Not observed in any benchmark episode this phase (shed never neared
   capacity).
4. Crop/animal instance identity is a reconstructed pseudo-ID (`x, y, planted_day`), not a
   simulator-native object ID — correct as long as a tile never holds two live instances at once,
   which the game rules guarantee.
5. Only agents that exercise hiring, animals, and fertilizer would stress-test limitations 2-3;
   the frozen baseline doesn't, so those code paths are validated by construction/code review (the
   underlying accounting identities are exact by algebra) but not by an empirical accounting-PASS on
   a real episode this phase. Flagged for Phase 2.2 if/when an agent using those mechanics is built.

## 6. Non-interference verification — **PASS**

`python -m instrumentation.cli_noninterference --p0 agents/baseline_agent.py --p1 starter --steps 200 --seed 42`

Compared the actual frozen harness function (`harness.run_episodes.run_one_episode`, imported
unmodified) against `instrumentation.collector.run_episode` + the full telemetry pipeline, same seed:

| | Run A (frozen harness) | Run B (instrumentation) |
|---|---|---|
| Final money | [3387.0, 3062.0] | [3387.0, 3062.0] |
| Statuses | [DONE, DONE] | [DONE, DONE] |
| Full 400-entry action sequence | identical | identical |
| Pipeline mutates the replay it analyzes? | — | No (deep-copy-and-compare self-check) |

**Overall: PASS.** Instrumentation does not alter observations, actions, state trajectory, rewards,
final money, or winner.

## 7. Benchmark against the frozen control (brief §24)

Re-ran the exact Phase 2.0/Phase 1 seed ranges through the instrumented pipeline:

| Matchup | Episodes | Seeds | Money matches historical `results/*` exactly? | Winner | Validation |
|---|---|---|---|---|---|
| baseline vs pass | 5 | 100-104 | **Yes, episode-exact** (verified against `results/baseline_vs_pass/raw_episodes.json`) | baseline, 5/5 | 10/10 checks PASS |
| baseline vs starter | 5 | 300-304 | **Yes, episode-exact** (verified against `results/baseline_vs_starter/raw_episodes.json`) | baseline, 5/5 | 10/10 checks PASS |
| baseline vs random | 3 | 200-202 | Not expected to be episode-exact (documented `random`-agent caveat, Phase 2.0 §7/§13); aggregate behavior consistent (baseline wins all 3, opponent converges to $0 as expected from `random_agent`'s buy-only, never-sell logic) | baseline, 3/3 | 6/6 checks PASS |

**Total: 26/26 accounting-validation checks PASS across 13 benchmark episodes.** Instrumentation does
not alter final money, action sequence, or winner in any run (each episode's own
`non_interference_self_check.replay_unmutated_by_pipeline` is `True`).

## 8. Runtime / storage overhead (brief §25)

`python -m instrumentation.cli_benchmark --p0 agents/baseline_agent.py --p1 starter --steps 720 --episodes 5`

| | Plain (frozen harness) | Instrumented (collector + full pipeline) |
|---|---|---|
| Mean runtime / 720-step episode | 1.71 s | 3.29 s |
| Overhead | — | **+1.58 s (+92.9%)**, i.e. the full extraction+ledger+metrics+validation pipeline roughly doubles wall-clock time |

| Output file | Size (one 720-step episode) |
|---|---|
| `raw/<tag>/epNNN.json` | 882.6 KB |
| `daily/<tag>/epNNN.json` | 42.3 KB |
| `episode/<tag>/epNNN.json` | 7.1 KB |
| `validation/<tag>/epNNN.json` | 7.6 KB |

For context against the Kaggle competition's resource constraints: the raw layer's size is a
deliberate design trade-off (production events + once-per-day land snapshots, not full-board-every-turn
dumps — see architecture doc §3); the `episode`/`daily`/`validation` layers most later Phase 2
experiments will actually consume are two orders of magnitude smaller. Overhead is measured, not
hidden, and is acceptable for offline experimentation (this phase's purpose) but would need
lighter-weight, more selective instrumentation before any of this ran inside a live competition
submission's per-turn time budget — noted for anyone extending this into an in-submission use case,
which is explicitly out of Phase 2.1's scope.

## 9. Raw vs derived data separation (brief §26)

Enforced structurally: `instrumentation/extractor.py` produces only raw/public-or-private-as-received
fields; every subsequent module (`ledger.py`, `market_telemetry.py`, `metrics.py`, `validation.py`)
only ever reads from the raw layer and never writes back into it. The per-episode output record keeps
raw (`meta`, `outcome`, `market_history`, `town_history`) and derived (everything under
`players.<id>.*` except the private/public raw pass-throughs) in clearly separated top-level keys —
see the schema doc's raw/derived/public/private/diagnostic label on every field.

## 10. Opponent information boundary — **PASS**

Verified both by construction and by direct source reading (`vendor_kaggriculture/kaggriculture.py`
`_initialize()`/`interpreter()`): `observation.private` is assigned per-player and never shared;
`observation.farms`/`market`/`town`/`day`/`hour` are the *same shared object* handed to both players
every step, i.e. legitimately public in the live game. `instrumentation/extractor.py` only ever reads
`private` from a player's own recorded observation — there is no code path that could leak the other
player's shed/seeds/carried-inventory into a telemetry record. `instrumentation/schema.py` documents
this policy explicitly as `PUBLIC_OBSERVATION_KEYS`/`PRIVATE_OBSERVATION_KEYS`.

## 11. Two real bugs caught during development (evidence the validation discipline works)

1. **Replay index off-by-one**: the first extractor implementation paired `steps[i]`'s action with
   `steps[i]`/`steps[i+1]` observations, silently producing a locally-"balanced" but wrong ledger.
   Caught by a failing money-conservation check on the first smoke-test episode, before any benchmark
   was trusted. Root-caused by direct inspection (a `BUY_SEED` order's effect was visible in the *same*
   step index it was submitted at) and fixed — see architecture doc §2.
2. **End-of-day auto-drop misattributed as a phantom purchase**: raw shed deltas conflate market
   activity with the daily automatic carried-inventory→shed drop. Caught by a failing
   inventory-conservation check (135-unit WHEAT discrepancy, a spurious 148-unit `BUY_PRODUCT` the
   baseline agent's source code never issues) on the first full 720-step benchmark episode. Fixed by
   subtracting the turn's carried-inventory↔shed movement (computed from the production-event stream)
   from the raw shed delta before attributing the remainder to SELL/BUY_PRODUCT — see architecture doc
   §4. After the fix: 26/26 validation checks PASS across all benchmark episodes.

## 12. Economic optimization introduced this phase

**None.** No crop/fertilizer/hiring/land/animal/market-timing tuning, no economic planner, no RL, no
evolutionary or self-play search, and `agents/baseline_agent.py` was never edited (hash unchanged,
reverified §1). Every metric produced is descriptive.

---

```text
KAGGRICULTURE PHASE 2.1
ECONOMIC INSTRUMENTATION & TELEMETRY FOUNDATION

Status:
PASS WITH ISSUES

Frozen simulator:
kaggle-environments 1.32.7 ("kaggriculture")
Source hash: bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e (reverified unchanged)

Frozen baseline:
Wheat Patroller
Source hash: d007f1ed0c025f6fc90d9914c371e49cf2e49ac4f6183fb6c9554079847ecefd (reverified unchanged)

Telemetry schema:
Version: 2.1.0

Instrumentation architecture:
Entirely post-hoc and read-only: frozen agent(s) -> frozen simulator (unmodified
kaggle_environments.make/env.run) -> env.toJSON() -> raw extraction -> derived
ledgers/metrics -> accounting validation -> results/phase2_1/. No agent wrapping,
no simulator patching, no live-loop hook. Full diagram in
docs/PHASE2_1_ARCHITECTURE.md.

Metrics implemented:
Financial ledger, production ledger (crop + animal lifecycle), land ledger,
fertilizer ledger, action efficiency, crop-level and animal-level economics
(measurement only), market price/transaction telemetry, town-demand telemetry
(with duplicate-shop-instance tracking), daily summaries, episode summaries.

Accounting validation:
PASS  (26/26 checks across 13 benchmark episodes: money, land, fertilizer,
       per-product inventory conservation, all exact after two bugs caught
       during development were fixed -- see section 11)

Market telemetry:
PASS  (public price/inventory history exact every turn; realized transaction
       prices exact whenever unambiguous, which was 100% of transactions in
       every benchmark episode; individual per-unit price within a multi-unit
       order is a documented, deliberate non-goal -- see section 5.1)

Production telemetry:
PASS  (crop and animal lifecycle fully reconstructed via pseudo-identity
       x,y,planted_day / x,y,placed_day; no UNCLASSIFIED events emitted in
       any benchmark episode)

Opponent information boundary:
PASS  (verified by source inspection and by construction -- private state is
       never cross-read between players)

Non-interference:
PASS  (frozen-harness run vs instrumented run: identical 400-action sequence,
       identical final money/statuses; pipeline proven non-mutating)

Runtime overhead:
+92.9% mean wall-clock for a 720-step episode (1.71s -> 3.29s) running the
full extraction+ledger+metrics+validation pipeline. Acceptable for offline
Phase 2 experimentation; would need lighter instrumentation before running
inside a live per-turn competition time budget (out of Phase 2.1 scope).

Storage overhead:
~883 KB raw / ~42 KB daily / ~7 KB episode / ~8 KB validation per 720-step
episode. Raw-layer size is a deliberate design choice (production-event
stream + once-per-day land snapshots, not full-board-every-turn dumps).

Known limitations:
Individual per-unit market-clearing price not independently recoverable
(deliberate non-goal, see section 5.1). Per-unit/per-hand attribution of
fertilizer and inventory movement is aggregate-only when multiple hands act
the same turn (untested by any benchmark this phase -- baseline never hires).
Shed-capacity overflow is inferred, not independently confirmed, when an
inventory discrepancy is positive (not observed this phase). Crop/animal
identity is a reconstructed pseudo-ID, not a simulator-native one.

Historical data preserved:
YES (all 15 phase1_freeze/hashes.txt entries reverified OK before and after
this phase; no file under vendor_kaggriculture/, agents/baseline_agent.py,
harness/run_episodes.py, kaggriculture-data/, docs/00-02+PHASE1_REPORT.md,
or any historical results/* directory was modified)

Economic optimization introduced:
NO

Phase 2.1 conclusion:
The instrumentation PROVES: episode-exact reproduction of Phase 1/2.0's own
historical results when driven through the instrumented pipeline (baseline vs
pass and baseline vs starter, 10/10 episodes bit-identical to
results/baseline_vs_{pass,starter}); exact money/land/fertilizer conservation
on every benchmark episode; a hard, source-verified opponent information
boundary; and non-interference between instrumentation and gameplay. It
RECORDS (derived, not independently re-verified against a second method):
per-transaction category/price/quantity, crop and animal lifecycles, market
and town activity, and daily/episode rollups -- all exact whenever a turn's
activity is unambiguous, degrading gracefully to a flagged, still-conservative
aggregate when it is not (never silently wrong; ambiguity is always visible in
the output, not hidden). It CANNOT currently measure exactly: the individual
per-unit price within a multi-unit market order, or per-hand attribution when
multiple hands act on the same item simultaneously -- both are explicit,
documented non-goals for this phase, not silent gaps. What Phase 2.2 must
still answer experimentally, using this instrument: which crops/animals/
strategies are actually profitable under the dynamic pricing model, what the
opportunity cost of fertilizer and land timing is, and how the agent's
resource allocation compares against the frozen baseline's Phase 1 control --
none of which this phase claims or implies (no crop/animal is ranked "best"
anywhere in this report or its outputs).

Status is PASS WITH ISSUES rather than a clean PASS because of the
documented, non-blocking limitations in section 5 (individual per-unit price
and per-hand attribution are explicit non-goals, not defects, but they are
real boundaries on what "exact" means in this instrument) and because the
+92.9% runtime overhead, while fine for offline Phase 2 experimentation, was
not optimized for and would need further work before any in-submission use.
Neither issue affects the correctness of what is measured, only its
completeness/cost -- consistent with the Phase 2.0 precedent of using
PASS WITH ISSUES for open, documented, non-blocking items rather than a false
clean PASS.

Approved next step:
Phase 2.2 -- Production / Crop Economics
```
