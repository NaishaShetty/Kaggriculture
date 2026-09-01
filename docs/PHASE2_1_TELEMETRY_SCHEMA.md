# Kaggriculture Phase 2.1 — Telemetry Schema

## Changelog

- **2.3.0** (Phase 2.2, discovered while validating a WHEAT+MELON combination episode): fixed the
  HARVEST-vs-DIG disambiguation in `extractor.py`'s `_diff_tile()`. The corroborating-evidence check
  (`crop_gain`) previously summed shed **and** carried-inventory deltas together; since a HARVEST only
  ever adds to carried inventory (never the shed directly) while a same-turn SELL of the same item only
  ever removes from the shed, a turn that both harvests and sells the same crop (the normal case under
  Phase 2.2's "sell everything in shed every turn" policy, once a crop has any older shed balance) nets
  to zero and was silently misclassified as a `DIG` instead of a `HARVEST` — undercounting
  `total_harvested_units` and causing a real money-conservation discrepancy ($25 on the episode that
  surfaced it). Fixed by checking the carried-inventory delta alone, which is unconfounded by shed-side
  SELL activity. This is a materially different bug from the 2.2.0 fixes (which were about *pricing*
  attribution, not event *classification*) and was caught the same way: a failing accounting-validation
  check on real experiment data, not a code read. All Phase 2.2 experiment episodes generated before
  this fix were regenerated; none were reported on until this fix landed. Old Phase 2.1 telemetry under
  `results/phase2_1/` predates any multi-crop or same-turn harvest+sell-of-older-stock pattern common
  enough to trigger this at scale in that phase's benchmarks and is preserved unchanged.
- **2.2.0** (Phase 2.2, discovered while building multi-crop experiment agents): fixed a sign-convention
  bug in `ledger.py`'s single-item SELL/BUY_PRODUCT reconciliation (`BUY_PRODUCT`'s `total` was being
  stored as the raw signed money delta — negative — instead of a positive expenditure magnitude,
  breaking `total_expenditure`/money-conservation whenever an agent bought a market product such as
  fertilizer). Also replaced the old "multiple items moved the same turn → both left `total: None`,
  unresolved" fallback with a real estimate: each item's dollar share is now approximated from that
  turn's already-recorded pre-transaction public market price, then rescaled by a single common factor
  so the estimates always sum EXACTLY to the true pooled money delta (conservation is never broken by
  the estimate; `exact: False` and a `note` still flag it as an estimate, not a measurement). This
  matters materially for Phase 2.2's multi-crop combination experiments, where an agent commonly sells
  two different products in the same turn — previously such turns contributed `None`/unattributed
  revenue to every crop's ledger. Old Phase 2.1 telemetry under `results/phase2_1/` was generated under
  schema 2.1.0 and is preserved unchanged, not regenerated; it predates multi-crop agents so it was not
  affected by either bug in practice (verified: every Phase 2.1 benchmark episode passed money
  conservation before this fix too, since baseline/pass/starter never buy a market product or move two
  items' shed contents in the same turn).
- **2.1.0** (Phase 2.1): initial schema.

**`telemetry_schema_version = "2.2.0"`** (`instrumentation/schema.py::TELEMETRY_SCHEMA_VERSION`). Any
change to the shape or meaning of a field increments this version; older telemetry is never silently
reinterpreted under a new version — a schema bump means new output directories/tags, not an in-place
rewrite of `results/phase2_1/`.

Every field below is labeled:
- **raw** — copied or trivially reshaped directly from `env.toJSON()`, no computation.
- **derived** — computed from raw fields (arithmetic, aggregation, or diff-based event classification).
- **public** — legitimately visible to both agents in the live game (confirmed: `observation.farms` /
  `market` / `town` / `day` / `hour` are the *same shared object* handed to every player each step).
- **private** — visible only to the player it belongs to (`observation.private`); never copied into
  the other player's telemetry record.
- **diagnostic** — simulator-internal information that exists only for our own accounting/validation
  and is never presented to, or usable by, any agent's decision logic (e.g. the reconstructed
  per-transaction price, or an `UNCLASSIFIED` event needing manual review).

## Top-level per-episode record (`results/phase2_1/raw/<tag>/epNNN.json`)

| Field | Layer | Notes |
|---|---|---|
| `schema_version` | derived/diagnostic | this document's version |
| `experiment_id`, `episode_id` | diagnostic | caller-supplied labels |
| `meta.seed`, `meta.p0`, `meta.p1`, `meta.episode_steps_requested`, `meta.n_steps_recorded`, `meta.configuration` | raw | from `collector.run_episode` / `env.toJSON()` |
| `meta.instrumentation_schema_version` | diagnostic | duplicated at top level too |
| `meta.simulator_version`, `meta.environment_name` | raw | from `env.toJSON()["version"|"name"]` |
| `meta.runtime_s` | diagnostic | wall-clock of `env.run()` only, not analysis time |
| `outcome.final_money`, `outcome.statuses`, `outcome.winner`, `outcome.margin` | raw/derived | winner/margin computed from raw rewards, same logic as `harness/run_episodes.py` |
| `market_history[]` | **public**, raw | per-turn `{turn, day, hour, inventory, prices}` — visible to both agents |
| `town_history[]` | **public**, raw | per-turn `{turn, day, hour, unlocked_shops}` |
| `market_price_stats` | **public**, derived | per-item min/max/mean/volatility across the episode |
| `players.<0\|1>` | mixed, see below | one block per player |
| `non_interference_self_check.replay_unmutated_by_pipeline` | diagnostic | deep-equality of the replay object before/after analysis |

## `players.<id>` block

### `financial_transactions[]` — derived, **diagnostic** (reconstructed dollar amounts are never fed to any agent)
`{turn, day, hour, player, category (INCOME|EXPENDITURE), type (SELL|BUY_SEED|BUY_PRODUCT|BUY_ANIMAL|BUY_LAND|HIRE), item, quantity, unit_price, total, exact}`.
`exact=False` transactions additionally carry a `note` explaining the ambiguity (see architecture doc §4).

### `financial_summary` — derived, diagnostic
`starting_money` (raw), `final_money` (raw), `total_income`/`total_expenditure` (derived sums),
`reconstructed_final_money` = starting + income − expenditure, `discrepancy` = reconstructed − actual
(should be 0; validated in §validation), `n_unresolved_transactions`, `by_type` (per-category rollup).

### `crop_instances[]` / `animal_instances[]` — derived, diagnostic
Per-instance lifecycle records keyed by `(x, y, planted_day)` / `(x, y, placed_day)` pseudo-identity
(see architecture doc §5 for why no stronger identity is available). Fields: crop/animal, position,
planted/placed turn+day, watering/fertilize/feed/care event counts, `harvests[]` (turn, day, units),
`removed_turn`/`removed_reason` (`HARVEST`|`DIG`|`WEED_CONVERSION`) or `escaped_turn`,
`total_harvested_units`/`total_product_units`.

### `fertilizer_ledger` — derived, diagnostic
`starting_inventory`, `purchased`, `collected_from_animals`, `total_acquired`, `used_on_fertilize`,
`sold`, `ending_inventory`, `reconstructed_ending_inventory`, `discrepancy`. Aggregate across shed +
all carried inventories (per-unit/per-hand attribution not preserved — see architecture doc §5).

### `land_ledger` — derived, diagnostic
`starting_unlocked_quadrants`, `purchases[]` (turn, day, cost), `ending_unlocked_quadrants`,
`reconstructed_ending_unlocked_quadrants`, `discrepancy`.

### `action_efficiency` — derived, diagnostic
Per brief §9: `total_unit_actions`, counts by category (`movement`, `crop`, `animal`, `farm`, `idle`,
`unknown`; farmer vs hand split), `total_market_orders` by category, and rates:
`productive_action_rate`, `idle_fraction`, `movement_fraction`, `crop_fraction`, `animal_fraction`,
`market_action_fraction`. Movement is reported, not judged inherently wasteful (brief §9).
"Productive" for MOVEMENT means the move was not blocked by a board edge; for CROP/ANIMAL means a
production event was observed at the targeted tile that turn; for FARM ops (`BUILD_*`) means the
board-diff confirms the structure was built. `PICKUP`/`DROP` are counted but not judged (best-effort
only at the aggregate private-state level, not per-unit — see architecture doc §5).

### `crop_metrics` / `animal_metrics` — derived, diagnostic, **measurement only, no ranking claim**
Per crop/animal: counts (planted/harvested/weeded/dug, purchased/escaped), totals (harvested/product
units, watering/fertilize/feed/care events), `seeds_purchased`/`purchased`, `revenue`,
`revenue_per_harvested_unit`, `revenue_per_seed_purchased`, `revenue_per_action`. No field ranks crops
or animals against each other — that comparison is explicitly Phase 2.2 scope.

### `market_transaction_summary` — derived, diagnostic
Per `(op, item)`: order count, total quantity, total value, avg/min/max realized price, and
`n_exact`/`n_total` (how many of the underlying transactions were `exact: True`).

### `town_telemetry` — **public**, derived
`shop_unlock_events[]` (turn, day, shop, instance_index, total_shops_unlocked — duplicate shop
instances tracked distinctly per brief §18), `final_shop_instance_counts`, `total_shop_instances`,
`expected_consumption_events[]` (deterministic, computed from `SHOPS`/`TOWN_CENTER_PRODUCTS` and the
configured sell intervals — see architecture doc "town" note), `shop_sell_interval`,
`center_sell_interval`.

### `validation` — derived, diagnostic
`overall` (PASS/PARTIAL/FAIL) plus `money`, `land`, `fertilizer`, and `inventory[]` (one per PRODUCT)
checks, each with its own `verdict`. See `instrumentation/validation.py` docstring for the
PASS/PARTIAL/FAIL rubric.

### `daily_summary[]` — derived, mixed public/diagnostic
One record per day: starting/ending money (raw), revenue/expenditure (derived), counts of seeds
purchased / crops planted / crops harvested / products sold / animals purchased / animal products
harvested / fertilizer purchased-used-sold / workers hired / land purchased (all derived from this
player's own transactions and events — never the opponent's private data), and
`land_utilization` (**public** — `land_utilization_rate`, `productive_tile_rate`, `idle_tile_rate`,
`weed_rate`, all derived from the shared board state).

### `episode_summary` — derived, diagnostic
Rolled-up financial/production/efficiency/market/town/outcome metrics for the whole episode,
including `opponent_final_money` (**public** — the opponent's final money/reward is itself a public
outcome field the harness already reports, not a private field).

## Raw per-turn records (internal to the pipeline; NOT written to `raw/` verbatim — see architecture
doc §3 storage-efficiency rationale). Available via `instrumentation.extractor.extract_episode()`
directly for ad-hoc analysis: `turns[player][]` — `{turn, day, hour, player, reward, status,
money_before/after, unlocked_quadrants_before/after, hires_today_before, n_hands_before/after,
private_before/after (private), unit_actions[] (public position/tile + own action), market_orders[]
(own action)}`. `production_events[player][]` — `{turn, day, player, x, y, event, ...}`.
`land_daily[player][day]` — board-kind counts (public).

## Info-boundary enforcement

Enforced structurally, not by a filter step: `instrumentation.extractor.extract_episode()` only ever
reads `replay["steps"][t][player]["observation"]["private"]` for that *same* `player` index — there is
no code path that reads player 0's `private` into player 1's record or vice versa. `farms`/`market`/
`town`/`day`/`hour` are read from either player's observation interchangeably because they are
verified-identical shared objects (see architecture doc §1). `instrumentation/schema.py` documents
`PUBLIC_OBSERVATION_KEYS`/`PRIVATE_OBSERVATION_KEYS` as the explicit, checkable policy.
