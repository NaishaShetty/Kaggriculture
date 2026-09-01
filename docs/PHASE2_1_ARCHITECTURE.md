# Kaggriculture Phase 2.1 — Instrumentation Architecture

Companion to [PHASE2_1_TELEMETRY_SCHEMA.md](PHASE2_1_TELEMETRY_SCHEMA.md) (field-by-field schema)
and [PHASE2_1_REPORT.md](PHASE2_1_REPORT.md) (results and final report). Code lives entirely under
[`instrumentation/`](../instrumentation/), new outputs under `results/phase2_1/`. Nothing under
`phase1_freeze/`, `agents/baseline_agent.py`, `vendor_kaggriculture/`, `harness/run_episodes.py`, or
any historical `results/*` directory was modified — reverified by hash at the start and end of this
phase (`sha256sum -c phase1_freeze/hashes.txt`, all 15 entries `OK`).

## 0. First task: inventory of what was already available

Before writing anything, `harness/run_episodes.py`, `scripts/smoke_test.py`,
`scripts/determinism_check.py`, and `vendor_kaggriculture/kaggriculture.py` were read in full.

| | Status |
|---|---|
| Final money, winner, status, runtime, per-episode aggregate stats | **Already available** — `harness/run_episodes.py` computes these directly. |
| Full per-step observation/action/reward/status trajectory | **Already available, but unused** — `env.toJSON()` / `env.steps` already contain everything (the harness only invokes `--save-replays` optionally, and even then just dumps the JSON without analyzing it). This is the entire foundation Phase 2.1 builds on. |
| Per-turn action classification, financial ledger, production lifecycle, land/fertilizer/inventory ledgers, market/town telemetry, daily/episode summaries, accounting validation | **Missing** — did not exist before this phase. Built in `instrumentation/`. |
| Exact per-unit market-clearing price for every SELL/BUY_PRODUCT unit | **Cannot be measured exactly without re-simulating** the dual-player, per-unit lockstep pricing loop in `_process_market` (see §4). Deliberately not attempted — see "Known limitations" in the final report. Average realized price per turn *is* exact when reconstructable (see §3). |
| Stable object identity for a specific crop/animal instance across turns | **Requires reconstruction** — the simulator exposes no object IDs. Reconstructed using `(x, y, planted_day)` / `(x, y, placed_day)` as the strongest justified pseudo-identity (a tile can't hold two live crops/animals at once). |
| Opponent's shed contents, seed counts, carried inventory | **Not available, by design** — confirmed by reading `_initialize()`/`interpreter()`: `observation.private` is assigned per-player and never shared; `observation.farms/market/town/day/hour` *are* shared (same object reference handed to both players every step). This is the exact public/private boundary enforced throughout. |

## 1. Why the whole pipeline is post-hoc and read-only

`kaggle_environments`' `env.run()` already records, for every step and every player: the observation
that player acted on, the action they returned, the reward, and the status — all serializable via
`env.toJSON()` (this is exactly what `scripts/determinism_check.py` and the harness's
`--save-replays` flag already rely on). Because `observation.farms` (tiles, money, farmer/hand
positions, unlocked land, hires-today) and `observation.market`/`observation.town`/`day`/`hour` are
the *same shared object* handed to both players each step (confirmed by direct inspection of
`interpreter()`), and only `observation.private` (shed, seeds, per-unit carried inventory) is
genuinely per-player, **the complete economic history of an episode is reconstructable entirely from
data the frozen simulator already produces**, with zero need to touch simulator internals, wrap
agent decision logic, or add any instrumentation hook to the live game loop.

This is why the chosen architecture is a single one-way pipe:

```text
Frozen Agent(s)  →  Frozen Simulator (kaggle_environments.make("kaggriculture").run(...))
                          │
                          ▼
                  env.toJSON()  (already-existing, unmodified public API)
                          │
                          ▼
              instrumentation.extractor   (RAW layer: per-turn action/state
                                            records, production-event stream,
                                            once-per-day land snapshots,
                                            market/town history)
                          │
                          ▼
     instrumentation.ledger / market_telemetry   (DERIVED layer: financial,
                                                    production, land,
                                                    fertilizer ledgers;
                                                    market/town telemetry)
                          │
                          ▼
              instrumentation.metrics   (DERIVED layer: action efficiency,
                                          crop/animal-level economics,
                                          daily/episode summaries)
                          │
                          ▼
             instrumentation.validation   (accounting consistency checks —
                                            money/land/fertilizer/inventory
                                            conservation, PASS/PARTIAL/FAIL)
                          │
                          ▼
   results/phase2_1/{raw,daily,episode,validation}/<tag>/epNNN.json
```

There is no feedback path from any pipeline stage back into the agent or the simulator: the
simulator runs to completion first (`env.run()` returns), and only then is `env.toJSON()` — a
fully-formed, already-serialized copy of the finished episode — handed to `extract_episode()`. No
stage mutates its input; `pipeline.run_and_analyze()` deep-copies the replay before analysis and
asserts byte-for-byte equality afterward as a structural non-interference self-check (recorded in
every episode's `non_interference_self_check` field), in addition to the dedicated non-interference
test in §6.

The only simulator-derived import used anywhere in `instrumentation/` is a set of **pure, fixed
lookup constants and pure functions** from `vendor_kaggriculture.kaggriculture` — `CROPS`, `ANIMALS`,
`PRODUCTS`, `LAND_PRICES`, `FARM_HAND_COST_MULT`, `SHOPS`, `TOWN_CENTER_PRODUCTS`, `_fib`,
`_hire_cost`, and the state constructors `_new_farm`/`_new_private`/`_new_market`/`_new_town` (used
only to build the synthetic pre-game "turn -1" state, guaranteeing it matches the simulator's own
initialization rather than being independently re-derived). None of these execute game logic, consume
randomness, or have any side effect; importing them is read-only usage of the single frozen source of
truth, not a fork or a re-implementation of the simulator (per the change-control policy in
`docs/03_control_contract_and_change_policy.md`, rule 2).

## 2. Replay indexing (a real gotcha, verified empirically)

`replay["steps"][t]` stores the action an agent chose **using the observation at index `t-1`** (or
the true pre-game initial state for `t==0`), together with the **resulting** observation after that
action was applied — i.e. `steps[t].observation` already reflects `steps[t].action`'s effect. This
was verified directly: at `seed=42`, `starter` vs `pass`, `steps[1].action` is `BUY_SEED CARROT` and
`steps[1].observation.private.seeds.CARROT` is already `1` with money already debited by $20 — in the
*same* index. A naive `before = steps[t]`, `after = steps[t+1]` pairing (the first version of
`extractor.py` used exactly this) silently produces a one-step-shifted ledger that still "balances"
locally per turn but attributes every transaction to the wrong turn and, worse, misclassifies
same-turn shed activity (see §3). This was caught by the validation suite itself (money-conservation
discrepancy on the very first test episode) before any benchmark was trusted — exactly the "any
mismatch must be investigated, not silently accepted" discipline the brief requires. The fix: for
turn `t`, before-state = `steps[t-1].observation` (or the synthetic initial state for `t==0`),
action = `steps[t].action`, after-state = `steps[t].observation`.

## 3. Raw event extraction (`instrumentation/extractor.py`)

For every turn *t* and player, records: the action submitted (farmer + each hand, with the tile each
unit stood on before acting and a classification per brief §8), all market/economy orders submitted,
money before/after, unlocked-quadrant list before/after, hires-today, hand count before/after, and
full private state (shed/seeds/carried-inventory) before/after.

**Storage-efficiency decision (brief §25 — "avoid generating enormous unnecessary records"):** the
raw layer does **not** store the full 10×10 board every turn (that would be 720 turns × 2 players ×
100 cells of mostly-redundant data). Instead, a single internal full-board diff pass (still inspecting
every turn's board, "where feasible" is interpreted as *feasible internally*, not *feasible to store
raw at that resolution*) is distilled into a **production-event stream** — named events (`PLANT`,
`WATER`, `FERTILIZE`, `HARVEST`, `GROWTH`, `WEED_CONVERSION`, `WEED_SPAWN`, `DIG`, `BUILD`,
`PLACE_ANIMAL`, `FEED`, `CARE`, `FERTILIZER_READY`, `COLLECT_FERTILIZER`, `ANIMAL_ESCAPE`,
`UNCLASSIFIED` as a safety net for any transition the diff logic doesn't recognize) plus a
**once-per-day land snapshot** (tile-kind counts, per-quadrant breakdown). This is a deliberate
choice, not a limitation — it is far more directly useful for the production/land ledgers than a raw
board dump would have been, and it's the "aggregated summaries, optional high-detail tracing" the
brief explicitly asks for. A benchmark episode (720 steps) produces an ~880 KB raw JSON per episode
(see final report §"Storage overhead") under this design; a naive full-board-every-turn approach was
estimated at roughly 15-20× that.

HARVEST-vs-DIG and other otherwise-ambiguous transitions are disambiguated using **inventory-delta
corroboration**: e.g. a `PLANT → None` transition is classified `HARVEST` only if the crop's item
count in that player's shed+carried-inventory also increased that turn; otherwise it's `DIG`. This is
exact for every episode analyzed in this phase (no `UNCLASSIFIED` events emitted in any benchmark
run) but is documented as best-effort in general, since a `SELL`/`BUY_PRODUCT` of the *same* crop in
the *same* turn as a harvest would confound the corroboration signal (see `extractor.py` docstring).

## 4. Financial ledger reconstruction (`instrumentation/ledger.py`)

Dollar amounts fall into two classes:

- **Exact, fixed-price categories** (`BUY_LAND`, `HIRE`, `BUY_SEED`, `BUY_ANIMAL`): priced from
  public, fixed lookup tables (`LAND_PRICES`, `_hire_cost`/`FARM_HAND_COST_MULT`, `CROPS[x]["seed"]`,
  `ANIMALS[x]["cost"]`), fulfilled quantity cross-checked against the actual state delta (seed count,
  hand count, unlocked-quadrant count, shed count). Flagged `exact: True` when the fulfilled quantity
  exactly matches what was requested.
- **Dynamic-price categories** (`SELL`, `BUY_PRODUCT`): the simulator's per-unit market-clearing price
  formula (`_process_market`) is a **dual-player, per-unit lockstep loop** — both players' orders at
  the same queue index are quoted and committed together, and price refreshes after every single unit,
  so two units of the *same* SELL order can clear at different prices, and one player's orders can
  shift the price the *other* player pays within the same turn. Replicating this exactly would mean
  re-implementing a meaningful fraction of the interpreter and executing it in lockstep with whatever
  the *opponent* did that turn too — explicitly out of scope ("if the game rules must be
  re-simulated to measure something, that is a sign the measurement is not really external"). Instead:
  **realized revenue/expenditure is taken directly from the ground-truth money delta** (exact, no
  approximation — this is literally what happened), and **quantity is taken directly from the
  ground-truth shed delta** (exact). Average realized unit price = revenue ÷ quantity is therefore
  *exact*, not estimated, whenever a turn's shed activity for an item is unambiguous. It becomes
  merely a *pooled aggregate* (still summing to the correct total dollar value, but not separable into
  a clean per-item price) only when multiple order types collide on the *same item* in the *same
  turn* — flagged `exact: False` with a `note`. This never occurred in any of the benchmark episodes
  run in this phase (baseline/pass/starter never combine SELL and BUY_PRODUCT of the same item in one
  turn).
- **Carried-inventory correction (critical, and the second real gotcha found during validation):** raw
  shed deltas are *not* purely market activity — the simulator auto-drops each unit's carried
  inventory into the shed once per day (`_end_of_day` → `_drop_inventories_to_shed`), and a turn that
  both sells a product *and* coincides with that day's auto-drop would otherwise misattribute the
  freshly-harvested (unsold) units as a phantom `BUY_PRODUCT`. This was caught the same way as the
  indexing bug: the very first full-length (720-step) benchmark episode failed inventory-conservation
  validation with a `WHEAT` discrepancy of 135 units and a spurious 148-unit "BUY_PRODUCT" that the
  baseline agent's source code never issues. The fix: subtract the turn's carried-inventory ↔ shed
  movement (`carried_before + harvested_this_turn − carried_after − consumed_by_FEED/FERTILIZE`,
  computed from the production-event stream) from the raw shed delta before attributing the remainder
  to SELL/BUY_PRODUCT. After the fix, all benchmark episodes pass inventory conservation exactly (see
  final report).

## 5. Production, land, fertilizer ledgers

- **Crops/animals**: `(x, y, planted_day)` / `(x, y, placed_day)` pseudo-identity, since the simulator
  exposes no stable object ID and a tile cannot hold two live instances at once. Each instance
  accumulates watering/fertilize/feed/care events and harvests from the production-event stream until
  a `HARVEST` (non-ongoing crop), `DIG`, `WEED_CONVERSION`, or `ANIMAL_ESCAPE` closes it.
- **Land**: unlocked-quadrant count before/after, cross-checked against `BUY_LAND` transaction count.
- **Fertilizer**: aggregate (shed + all carried inventories combined) source/use/sale ledger; per-unit
  (which specific hand) attribution is not preserved when multiple hands act the same turn — documented
  limitation, immaterial to every benchmark run since none of pass/starter/baseline hire hands or use
  fertilizer.

## 6. Non-interference proof (`instrumentation/cli_noninterference.py`)

Two independent code paths are run against the identical seed/agents/step-count: (a) the actual
**frozen harness function** `harness.run_episodes.run_one_episode`, imported unmodified — "normal
frozen environment" — and (b) `instrumentation.collector.run_episode` (architecturally separate code,
but calling the same public `kaggle_environments.make()`/`env.run()` API) followed by the **entire**
telemetry/ledger/metrics/validation pipeline — "instrumentation enabled." The full per-turn,
per-player action sequence (400 entries for a 200-step episode) plus final money and statuses are
compared for exact equality, and the pipeline's structural non-mutation self-check (deep-copy-and-compare
of the replay before/after analysis) is included in the verdict. Result: **PASS** — see final report.
This is a strong proof precisely because of the architecture in §1: since analysis only ever begins
after `env.run()` has already returned a finished, immutable episode, there is no code path through
which instrumentation *could* feed back into gameplay, and the empirical test exists to catch any
accidental violation of that invariant (e.g. an import-time side effect), not to detect a plausible
one.

## 7. What Phase 2.1 does not do

No crop/fertilizer/hiring/land/animal/market-timing optimization, no economic planner, no tuning of
any threshold for profitability, no RL, no evolutionary or self-play search, and no modification to
`agents/baseline_agent.py`'s policy. Every metric in this phase is descriptive; see final report for
the explicit list of what remains open for Phase 2.2.
