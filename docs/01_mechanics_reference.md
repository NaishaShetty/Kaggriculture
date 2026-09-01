# Kaggriculture Mechanics Reference (Phase 1 Deliverable B)

Status legend: **[DOCUMENTED]** = stated on the official Kaggle Overview page.
**[VERIFIED]** = confirmed by running/inspecting the installed `kaggle_environments` package.
**[HYPOTHESIS]** = suspected but not yet confirmed by either of the above.

This file is being built incrementally during Phase 1. See
[00_official_overview_raw.md](00_official_overview_raw.md) for the verbatim source capture.

## 1. Observation schema [DOCUMENTED, pending VERIFIED cross-check against source]

Top-level per-agent observation:
```
{
  "player": int,            # 0 or 1 — which player this agent controls
  "day":    int,             # 0-indexed in-game day
  "hour":   int,             # 0-indexed turn within the day (0..turnsPerDay-1)
  "farms":  [farm, farm],    # public per-player state, indexed by player id (both visible)
  "market": {
    "inventory": {ITEM: int, ...},
    "prices":    {ITEM: int, ...},
  },
  "town": {
    "unlocked_shops": [str, ...],   # may repeat
  },
  "private": {                # only this player's own private state
    "shed":        {ITEM: int, ...},
    "seeds":       {CROP: int, ...},
    "inventories": [farmer_inv, hand_inv, ...],  # index 0 = main farmer
  },
}
```

`farm` dict (PUBLIC — both players see both farms' tiles/positions, but NOT sheds):
```
{
  "money":              float,
  "tiles":              [[tile, ...], ...],  # tiles[y][x], boardSize x boardSize
  "farmer":             [x, y],
  "hands":              [[x, y], ...],
  "unlocked_quadrants": ["NW", ...],
  "hires_today":        int,
}
```

`tile` union type:
- `None` — empty, unlocked
- `"LOCKED"` — not-yet-purchased quadrant
- plant dict: `{kind:"PLANT", crop, planted_day, watered_today, consecutive_unwatered, yield_units, max_lifespan_step, fertilized_until_day}`
- weed dict: `{"kind":"WEED"}`
- structure dict: `{kind:"COOP"|"PASTURE", animal, placed_day, yield_units, fed_today, consecutive_unfed, cared_today, fertilizer_available, pending_care_bonus}`

Observable vs private, per [DOCUMENTED] statements:
- Observable to both players: market inventory/prices, town shop list, both farms' tiles/positions/money/unlocked quadrants/hires_today.
- Private (opponent cannot see): shed contents, seed counts, farmer/hand carried inventory contents.
- NOT stated whether opponent's exact inventory *counts* (e.g. number of items in each hand's carried inventory) are visible at all, even as aggregate — treat as HYPOTHESIS: opponent inventory contents are fully private and not observable in any form, since spec says "private" block only appears for "this player".

## 2. Action schema [DOCUMENTED]

Each turn, an agent returns a dict roughly of shape:
```
{"farmer": [ACTION, ...args], "hands": [[ACTION, ...args], ...], "market": [[ORDER, item, n], ...]}
```
(Exact key names/structure to be confirmed against source — the official Quick Start and starter
agent snippets consistently use `"farmer"`, `"hands"`, `"market"` keys; this is our working
assumption, marked [DOCUMENTED] because it's drawn directly from official example code, but the
precise validation rules are [HYPOTHESIS] until read from source.)

### Action Table

| Action | Preconditions | Effects | Cost | Failure/no-op conditions |
|---|---|---|---|---|
| NORTH/SOUTH/EAST/WEST | unit exists | move 1 cell in direction | 1 turn | off-board move = no-op; locked tiles are passable |
| PICKUP <item> [n] | orthogonally adjacent to shed | moves up to n of item from shed to unit inventory | 1 turn | seeds never pickup-able (separate slot) |
| DROP | orthogonally adjacent to shed | dumps unit's entire inventory into shed | 1 turn | no-op if not shed-adjacent; overflow past shedCapacity discarded |
| PLANT <crop> | unit holds seed of that crop (from seed slot); standing on empty unlocked tile presumably | consumes 1 seed, creates plant tile | 1 turn | no-op on locked tile; if N units try to plant more seeds than available that turn, NONE are planted |
| WATER | standing on a PLANT tile | sets watered_today=True, resets consecutive_unwatered | 1 turn | no-op if already watered today; no-op on locked tile |
| HARVEST (plant) | standing on a PLANT tile with yield_units > 0 (assumed) | adds yield to inventory; removes plant if no subsequent yields | 1 turn | no-op on locked tile |
| FERTILIZE | standing on a PLANT tile; holds fertilizer (assumed) | doubles per-day yield bonus for next 3 days (only applies on watered days) | 1 turn | no-op on locked tile |
| PLACE <item> [n] | animal: standing on matching unoccupied COOP/PASTURE, holds animal in inventory. shed-drop: standing shed-adjacent | animal: places 1 animal onto tile (n ignored). shed: moves up to n of item to shed (capped by shedCapacity) | 1 turn | — |
| FEED | standing on occupied COOP/PASTURE; holds wheat (assumed) | sets fed_today=True, resets consecutive_unfed | 1 turn | no-op if already fed today |
| HARVEST (animal) | standing on occupied COOP/PASTURE with yield_units > 0 | collects eggs/milk/wool to inventory | 1 turn | — |
| COLLECT_FERTILIZER | standing on occupied COOP/PASTURE with fertilizer_available=True | adds 1 fertilizer to inventory, clears fertilizer_available | 1 turn | no accumulation beyond 1 |
| CARE | standing on occupied COOP/PASTURE | sets cared_today=True; banks pending_care_bonus at end of day if also fed | 1 turn | no-op if already cared today |
| BUILD_COOP | standing on unoccupied unlocked tile | converts tile to empty COOP structure | 1 turn (+ cost, unconfirmed) | no-op on locked tile |
| BUILD_PASTURE | standing on unoccupied unlocked tile | converts tile to empty PASTURE structure | 1 turn (+ cost, unconfirmed) | no-op on locked tile |
| DIG | standing on PLANT, WEED, or empty (unoccupied) COOP/PASTURE tile | clears tile to empty (no yield) | 1 turn | no-op on occupied COOP/PASTURE (has animal); no-op on locked tile |
| PASS | always | no-op | 1 turn (optional even) | — |
| BUY_SEED <item> <n> | market order; sufficient money | buys n seeds of item at market price (fixed), adds to seed slot | money -= n*seed_cost | — |
| BUY_ANIMAL <item> <n> | market order; sufficient money | buys n animals at fixed price, adds to unit inventory (assumed) | money -= n*animal_cost | — |
| BUY_PRODUCT <item> <n> | market order; item in {WHEAT, FERTILIZER} only | buys n units at current dynamic market price | money -= dynamic price, processed 1 unit at a time | order stops if money runs out mid-order |
| SELL <item> <n> | market order; unit(s) hold n of item (in shed, presumably) | sells n units at current dynamic market price | money += dynamic price per unit, 1 at a time | price floors at $1 |
| HIRE | market order | hires 1 farm hand for the rest of the day | fib(hires_today)*farmHandCostMult | cost increases each same-day hire; resets daily |
| BUY_LAND | market order | unlocks next 5x5 quadrant | $1k / $2k / $4k (sequential) | — |

Costs marked "(unconfirmed)" for BUILD_COOP/BUILD_PASTURE: the Object Types table lists animal
"Action Cost" as "1 + 1 (build coop/pasture)" meaning build likely costs 1 turn-action plus some
coin cost not explicitly given a dollar figure on the Overview page — needs source confirmation.

## 3. Crops — full parameter table [DOCUMENTED]
See table in 00_official_overview_raw.md §"Object Types". Reproduced key derived facts:
- Wheat: seed $10, sells ~$25 base, first yield day 2, max-yield day 4, max 6 (fert) / 4 (unfert).
- Carrot: seed $20, sells ~$35 base, first yield day 2, max-yield day 3, max 4 (fert) / 3 (unfert).
- Tomato: seed $50, sells ~$60 base, first yield day 8, ongoing every day x4 (days 8-11), max 4.
- Strawberry: seed $100, sells ~$120 base, first yield day 10, ongoing every other day x4 (days 10,12,14,16), max 4.
- Melon: seed $80, sells ~$250 base, first yield day 10 = max-yield day, one-time, max 6.

## 4. Animals — full parameter table [DOCUMENTED]
- Goose/Egg: cost $300, sells ~$50/egg, first yield day 4, daily production indefinitely, max_held 4, requires COOP.
- Cow/Milk: cost $400, sells ~$160/milk, first yield day 8, every-2-days production indefinitely, max_held 6, requires PASTURE.
- Sheep/Wool: cost $500, sells ~$200/wool, first yield day 6, every-3-days production indefinitely, max_held 6, requires PASTURE.

## 5. Fertilizer [DOCUMENTED]
- Buy price $100 via BUY_PRODUCT (market-buyable, unlike other products).
- Also obtainable free via COLLECT_FERTILIZER from any surviving animal (1/day available, non-accumulating).
- Use: FERTILIZE action on a plant tile — doubles per-day yield bonus for 3 days, contingent on watering.
- Sellable via SELL like any other product (dynamic price, see market table).

## 6. Land / Farm structure [DOCUMENTED]
- boardSize default 10x10, split into 4x 5x5 quadrants NW/NE/SW/SE.
- Start: NW unlocked only. BUY_LAND unlocks next quadrant, cost $1k/$2k/$4k sequential.
- Shed at board center, occupies the 4 center tiles' adjacency (not itself a tile).

## 7. Market [DOCUMENTED] — see price function and per-resource table in 00_official_overview_raw.md.

## 8. Time system [DOCUMENTED]
- turnsPerDay=24, 30 days, episodeSteps=720 total.
- Turn processing order and day-boundary refresh order: see 00_official_overview_raw.md §"Turn Processing Order".

## 9. Scoring [DOCUMENTED]
- Winner = highest `money` (bank) at step 720. Unsold shed/inventory items do NOT count.
- Ladder uses Elo-like skill rating (W/L/T only, not margin) for ongoing matchmaking; final leaderboard
  uses a Bradley-Terry tournament fit over the accumulated post-deadline episodes.

## 10. Resolved from source inspection [VERIFIED]

Source: `kaggle_environments/envs/kaggriculture/kaggriculture.py` (v1.32.7, vendored copy at
[../vendor_kaggriculture/kaggriculture.py](../vendor_kaggriculture/kaggriculture.py)). All items
below are VERIFIED by direct code reading (not just running), citing line-level behavior.

- **Action dict schema** — confirmed exact: `{"farmer": [op, ...args], "hands": [[op,...],...],
  "market": [[op,...],...]}`. `interpreter()` reads `action.get("farmer", ["PASS"])` and
  `action.get("hands", [])`; missing/malformed keys default to PASS / empty list (no crash).
- **`hands` list ordering** — `hands_actions[h_idx]` maps to `farm["hands"][h_idx]` by index
  (`_apply_unit_action(..., h_idx+1, ...)`). Fewer actions than hands ⇒ extra hands get no action
  this turn (implicitly idle, not even PASS-processed, but with no ill effect). Extra actions past
  the hand count are ignored (`_farmer_position` returns None → `_apply_unit_action` returns early).
- **BUILD_COOP / BUILD_PASTURE cost** — **$0 monetary cost.** Only precondition is `tile is None`
  (empty, unlocked). The Object Types table's "Action Cost: 1 + 1 (build coop)" refers to **turn-actions**
  (1 turn to BUILD, 1 more turn to PLACE the animal), not a dollar cost — confirmed by code: `BUILD_COOP`
  just checks `tile is not None: return` then sets `farm["tiles"][fy][fx] = {"kind": "COOP"}`, no money
  touched anywhere in that branch.
- **BUY_ANIMAL delivery target** — animals purchased via `BUY_ANIMAL` are deposited **directly into the
  shed** (`private["shed"][item] += 1`), NOT into the buying unit's field inventory. To place an animal
  on a coop/pasture you must first `PICKUP <animal>` from the shed (shed-adjacent) into a unit's
  inventory, then walk to the structure and `PLACE <animal>`. This is a materially important detail for
  agent design that is not stated explicitly on the Overview page (it only implies "standing on a
  matching unoccupied structure ... places one animal from inventory").
- **Observation indexing** — `farms` is always `[farm0, farm1]` in stable player-id order for *both*
  agents; `obs["player"]` tells the agent which index is "me". Confirmed: `_initialize` sets
  `state[i].observation.player = i` while `farms`/`market`/`town` are the *same shared objects* assigned
  to every player's observation (`state[i].observation.farms = farms` for i>0) — i.e. not re-indexed to
  "me"/"opponent", always absolute player-id order.
- **Turn processing order — exact, per `interpreter()`:**
  1. For each player: compute PLANT demand across farmer+hands this turn; if demand for a crop exceeds
     available seed count, ALL PLANT actions for that crop this turn are replaced with PASS (atomic
     all-or-nothing, confirmed exactly matches "if you try to plant too many, none are planted").
  2. Apply farmer action, then each hand's action, via `_apply_unit_action` (movement, shed ops, plant
     ops, animal ops, terrain ops — all in the Action Table above).
  3. `_process_market`: HIRE and BUY_LAND resolved first (atomic, once, in player order for this queue
     slot); then SELL/BUY_SEED/BUY_PRODUCT/BUY_ANIMAL resolved in a per-unit lockstep loop across both
     players' same-index order simultaneously, one unit at a time, re-quoting price after each unit,
     looping until both players' orders for that slot are exhausted; repeated for each order-list index
     up to `maxMarketOrdersPerTurn`. Prices refreshed (`_refresh_prices`) after each order-slot's lockstep
     loop completes.
  4. `_town_consume`: on turns where `step % townShopSellInterval == 0`, every unlocked shop instance
     decrements market inventory for its demanded products (2x if single-product shop); on turns where
     `step % townCenterSellInterval == 0`, town center decrements 1 of every non-fertilizer product.
     Prices refreshed again afterward.
  5. `_decay_plants`: for every plant tile past `max_lifespan_step`, on every-other-**turn** (not day) —
     `(step - max_lifespan_step) % 2 == 0` — reduce `yield_units` by 1; hits 0 → becomes a WEED. This
     runs **every turn** (not just end of day), confirming "reduce by 1 every other turn" literally.
  6. If this is the last turn of the day (`(step+1) % turnsPerDay == 0`): run `_end_of_day`, which for
     each player: refreshes plant watered/unwatered state and applies scheduled ongoing-crop production
     (`_daily_refresh_plants`), refreshes animal fed/unfed state and applies scheduled animal production
     + care-bonus banking (`_daily_refresh_animals`), spawns weeds on empty tiles (`_spawn_weeds`, RNG
     seeded from `(seed*1_000_003) ^ day`), drops all unit inventories into the shed
     (`_drop_inventories_to_shed`), resets farmer position to the default spawn tile, clears hands and
     `hires_today` and per-unit inventories. Then, if `(day+1) % townShopUnlockInterval == 0` and fewer
     than 8 shop instances exist, one new shop is drawn (with replacement) and appended.
  7. Advance `step`/`day`/`hour` counters on the shared observation object.
  8. If `step >= episodeSteps - 2`: mark every agent `status = "DONE"` and set `reward = farm["money"]`
     for that agent's own farm. (This 2-step-early trigger is a framework/off-by-one quirk of how
     kaggle_environments records the *next* state; functionally the final recorded step's reward is each
     player's final bank balance.)
- **Reward / status** — `reward` is a plain float equal to that player's `farm["money"]` at game end;
  `status` is `"DONE"` for a normally completed episode (or an error status string if the agent crashed /
  timed out, per the general kaggle_environments framework, not kaggriculture-specific code).
- **Determinism** — `resolve_episode_seed(env)` is called once at `_initialize`; the actual per-day RNG
  used for weed spawning and shop-unlock draws is `random.Random((env.info["seed"] * 1_000_003) ^ day)`,
  i.e. **deterministic given the episode seed**, independently reproducible per day. `env.configuration
  ["seed"]` is documented as "cleared from config after read" so agents cannot see or infer it from
  their observation. This predicts that two runs with the same `seed` config and same agent action
  sequences will be bit-for-bit identical — to be spot-checked experimentally in Task #6/#7 (empirical
  determinism check), since `resolve_episode_seed`'s exact behavior when no seed is passed is framework
  code we have not read.
- **Built-in reference agents** — `pass_agent`, `random_agent`, `starter_agent` are defined directly in
  `kaggriculture.py` (registered as `agents = {"pass": ..., "random": ..., "starter": ...}`), reachable
  by name string in `env.run(["random", "starter"])`. **Important correction vs. the Overview page's own
  "Quick Start Agent" sample:** the *actual* built-in `"starter"` agent implements a **carrot loop**, not
  a wheat loop — the wheat-loop snippet on the Overview/AGENTS page is a separate illustrative example,
  not the code backing the `"starter"` name. `random_agent`'s policy: 10% chance to queue a `BUY_SEED`
  for a random affordable crop, 30% chance to `PLANT` a random already-owned seed if any, else pick a
  uniformly random op from `{NORTH,SOUTH,EAST,WEST,WATER,HARVEST,PASS}`; every hand gets an independent
  random op from that same movement/water/harvest/pass set (hands never buy/plant/sell). `pass_agent`
  always returns `{"farmer": ["PASS"], "hands": [], "market": []}`.

## 11. Remaining unknowns (HYPOTHESIS, need empirical/further-source confirmation)
- [x] **Determinism — CONFIRMED VERIFIED** (2026-08-15, `scripts/determinism_check.py`): ran
      `make("kaggriculture", configuration={"episodeSteps":200,"seed":42})` with `["starter","starter"]`
      twice. Every recorded step's observation/reward/status was byte-identical between runs (diffed all
      200 steps via sorted-key JSON comparison); the only differing field in the full `env.toJSON()` dump
      was the top-level `id` (a fresh run UUID, not game state). Confirms: same `seed` config + same
      (deterministic) agents ⇒ fully reproducible episode, exactly as `_end_of_day`'s
      `random.Random((seed*1_000_003)^day)` construction predicts.
- [ ] Whether `env.configuration.actTimeout` / `runTimeout` (seen in the printed config: `actTimeout: 1`,
      `runTimeout: 1200`) cause real submissions to fail if an agent is slow — relevant for baseline agent
      performance budget, not yet stress-tested.
- [ ] Kaggle competition Data tab's README.md/AGENTS.md (viewed while signed out) are confirmed byte-for-byte
      consistent with the vendored package copy — not yet diffed programmatically, only spot-checked.
