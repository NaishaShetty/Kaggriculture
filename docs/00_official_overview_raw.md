# Kaggriculture — Official Overview Page (verbatim capture)

Source: https://www.kaggle.com/competitions/kaggriculture (Overview tab)
Captured: 2026-08-15, via in-app browser rendering of the live page.
Status: DOCUMENTED (official source of truth). Copied near-verbatim for offline reference;
this is our own working notes file, not a redistribution product.

## Competition summary
- Featured Simulation Competition. Start: 2026-07-29 (per timeline). Entry deadline: 2026-09-23.
- Team merger deadline: 2026-09-23. Final submission deadline: 2026-09-30.
- Post-deadline games run ~2026-10-01 to ~2026-10-15 (or until leaderboard convergence).
- All deadlines 11:59 PM UTC.
- Prize pool: $50,000 total — 1st through 10th place each win $5,000 (flat, not tiered).
- Host: Kaggle (with Google). Citation: Bovard Doerschuk-Tiberi, Domino Weir, María Cruz. Kaggriculture. 2026.
- At capture time: 12,530 entrants / 4,796 participants / 4,503 teams / 8,474 submissions.

## Description
Turn-based farming game. Two players compete on separate farms to maximize profit by the
end of a 30-day season (720 turns). Agent controls a main Farmer and can hire Farm Hands to
scale up. Must plant/water/fertilize/harvest crops; buy/feed/care for animals (eggs, milk, wool);
collect/use fertilizer; buy neighboring land quadrants; trade on a dynamic market that reacts to
player sales and town demand.

## Evaluation
- Up to 5 agent submissions per day per team. Each plays Episodes against similarly-rated bots.
- Only the latest 2 submissions are tracked/matchmade and used for final leaderboard evaluation.
- Skill rating: standard Elo-like system. Win -> rating up, loss -> rating down, ties pull ratings closer.
  Rating delta scales with opponent rating gap. Coin margin does NOT affect rating change — only W/L/T.
- On upload: a Validation Episode (agent vs copy of itself) checks it runs without errors before
  it's marked Error or joins the matchmaking pool with a default rating.
- Final evaluation: after the 2026-09-30 deadline, games continue ~2 weeks to reduce uncertainty;
  a final Bradley-Terry tournament on those episodes produces the final leaderboard.

## How to Play — Object Types (crops & animals)

| Type | Yield Type | Seed Cost | Base Market Price | Time to First Yield | Time to Max Yield | Subsequent Yields | Max Yield | Action Cost | Yield/tile/day |
|---|---|---|---|---|---|---|---|---|---|
| Wheat | One-time | 10 | 25 | 2 days | 4 days | none | 6 (4 unfertilized) | 1 | 0.80 |
| Carrot | One-time | 20 | 35 | 2 days | 3 days | none | 4 (3 unfertilized) | 1 | 0.75 |
| Tomato | Ongoing | 50 | 60 | 8 days | 11 days | every day x4 | 4 | 1 | 0.33 |
| Strawberry | Ongoing | 100 | 120 | 10 days | 16 days | every other day x4 | 4 | 1 | 0.24 |
| Melon | One-time | 80 | 250 | 10 days | 10 days | none | 6 | 1 | 0.55 |
| Goose/Egg | Ongoing | 300 | 50 | 4 days | NA | every day, indefinitely | 4 held | 1 + 1 (build coop) | 1.00 |
| Cow/Milk | Ongoing | 400 | 160 | 8 days | NA | every two days, indefinitely | 6 held | 1 + 1 (build pasture) | 0.50 |
| Sheep/Wool | Ongoing | 500 | 200 | 6 days | NA | every three days, indefinitely | 6 held | 1 + 1 (build pasture) | 0.33 |
| Fertilizer | NA | 100 | X | — | X | X | — | 1 | — |

Notes (documented):
- "Yield/tile/day" for crops = total harvested / days tile occupied, watering daily, harvesting at peak.
- For animals it's steady-state production rate (1/interval) once first yield lands.
- "Max Yield" for animals = max_held, cap on unharvested product on the tile (not lifetime total).
- Crop "Time to Max Yield" = age at which yield stops increasing under daily watering (not always end
  of bonus window):
  - Melon bonus window ages 6-12; base 1 + 1/watered day caps at 6 by age 10 (ages 11-12 add nothing).
    Fertilizing reaches cap at age 8.
  - Wheat/Carrot reach listed Max Yield (6 / 4) only WITH fertilizer; watering alone peaks at 4 / 3.
  - Tomato/Strawberry ongoing but capped at 4 scheduled yields (tomato ages 8-11; strawberry ages
    10,12,14,16), then decays into a weed.
- All plants must be watered every day (grace: 1 missed day). 2 consecutive missed days -> weed.
- All animals must be fed daily using wheat. 2 consecutive missed days -> escape (unrecoverable).
- Wheat can also be bought at market at current price (for feeding).

## Actions (1 action/turn per Farmer/Farm Hand; 24 turns/day, 30 days, 720 turns total)

Units (Farmer/Farm Hands) CAN occupy the same space.

### Movement
- NORTH/SOUTH/EAST/WEST — move 1 cell. Off-board moves are no-ops. Locked tiles are passable
  (can move onto/across unbought quadrants), but tile actions (PLANT, WATER, BUILD_*, etc.) no-op
  on a locked tile and consume nothing. Exception: shed actions (PICKUP, DROP, PLACE-into-shed) work
  from any shed-access tile even if locked — they only use the tile as a standing position.

### Shed
- PICKUP <item> [n] — move up to n (default 1) of <item> from shed into active unit's inventory.
  Must be orthogonally adjacent to shed. Any shed item valid (animals, fertilizer, harvested produce).
  Seeds are a separate slot, never picked up — PLANT consumes them directly.
- DROP — orthogonally adjacent to shed, dump entire inventory into shed. Overflow past shedCapacity
  discarded. No-op if not shed-adjacent.

### Plants
- PLANT <crop> — plant a seed from the seed slot. If too many units try to plant more seeds than
  available in a turn, NONE are planted (e.g. 1 melon seed but 2 units PLANT MELON -> neither plants).
- WATER — water a plant; once/day, subsequent same-day waterings are no-ops.
- HARVEST — gather produce. Plant removed from map if no subsequent yields. Each harvest yields >=1
  unit, formula differs by crop (see Harvest Yields). Harvested items added to inventory.
- FERTILIZE — doubles per-day yield bonus for next 3 days; bonus only applies on days also watered.

### Animals
- PLACE <item> [n] — from inventory: onto a matching unoccupied structure (GOOSE->coop, SHEEP/COW->
  pasture) places 1 animal (n ignored); OR if standing shed-adjacent, moves up to n of <item> into
  shed (capped by shedCapacity, excess stays in inventory).
- FEED — feed animal using wheat, once/day.
- HARVEST — collect eggs/milk/wool.
- COLLECT_FERTILIZER — collect 1 fertilizer from an animal. Every surviving animal makes 1 available
  at end of each day regardless of feed/care status. Does NOT accumulate — uncollected for 5 days
  still yields only 1 unit.
- CARE — care for an animal, once/day, no-op if already cared.

### Animal Care mechanics (documented precisely)
- End of day: if animal fed AND cared for that day, pending_care_bonus += 1. Unfed days do not bank.
- On a scheduled production day: if fed, entire banked bonus added to that yield (plus base 1), bank
  resets to 0. If unfed on production day, base 1 still produced but bonus not applied, bank resets.
- pending_care_bonus indirectly capped by per-animal max_held on yield_units.

### Terrain
- BUILD_COOP — add coop to unoccupied tile.
- BUILD_PASTURE — add pasture to unoccupied tile.
- DIG — remove a plant (no yield) OR remove a weed OR remove an empty coop/pasture. Occupied
  coop/pasture (has animal) cannot be dug — no-op.

### Other
- PASS — default/no-op action (optional; used when nothing to do).

### Market actions (separate action list from farmer/hand actions)
- Up to maxMarketOrdersPerTurn (default 10) market orders per turn per player; extras silently dropped.
  Ordered list, processed in order, simultaneously across players (both players' Nth orders together).
- BUY_SEED <item> <n> — buy N seeds of one item.
- BUY_ANIMAL <item> <n> — buy N animals.
- BUY_PRODUCT <item> <n> — buy N units of WHEAT or FERTILIZER only (other products not buyable).
- SELL <item> <n> — sell N units to market. Unrestricted — any product incl. animal fertilizer.
- HIRE — hire 1 farm hand for the day. Cost increases per additional hire same day (fib sequence,
  see Farmer/Farm Hand section).
- BUY_LAND — unlock a new 5x5 quadrant. Costs (in order): $1k, $2k, $4k.

## Watering / Feeding grace period details
- consecutive_unwatered starts at 1 for a newly planted seed (planting day counts as first missed
  day). If left unwatered same day, reaches 2 at end-of-day refresh -> becomes weed that night before
  growing. NO grace period for fresh plantings.
- consecutive_unfed starts at 0 for a newly placed animal -> survives its first day unfed.
- Watering one-time-yield plants during their yield bonus window increases yield. NOT true for
  ongoing-yield plants/animals.

## Harvest Yield formulas (documented)
- One-time crops (wheat, carrot, melon): starting at ceil(max_yield_day / 2), watering during the
  bonus window adds +1 unit/day to total harvestable yield. Fertilized adds +2/day instead.
- Ongoing crops (tomato, strawberry): scheduled production at fixed intervals, base yield 1/scheduled
  production. If fertilized AND watered that day, yield doubled to 2.
- Once a plant hits max lifespan, total yield on the plant reduces by 1 every OTHER turn until 0, then
  becomes a weed.
  - One-time crops reach max lifespan 1 day after max_yield_day.
  - Ongoing crops start decay 1 day after cumulative production count reaches max_yield (based on
    scheduled firings, regardless of whether harvested).

## Map / Farm

- boardSize x boardSize grid (default 10x10) split into four 5x5 quadrants (NW/NE/SW/SE).
- Start: only NW quadrant unlocked (25% of squares). Buy neighbors for increasing fee.
- 1 plant/animal per square. No per-type placement limits.
- Weeds can spawn randomly on empty unlocked cells (weedSpawnChance per tile per end-of-day refresh,
  default 0.005); must be DIG'd before reuse.
- Tile states: None (empty, unlocked) | "LOCKED" | plant dict | weed dict | structure dict (coop/pasture).
- Players CANNOT see opponent's shed (private); CAN see opponent's farm (tiles/positions - public).

## Shed (inventory)
- Central inventory. Capacity 100 items (excludes seeds). Overflow (via mid-day PLACE or end-of-day
  auto-drop) is discarded, no overflow holding area.
- Farmer/hands spawn at shed at start of each day; drop entire inventory into shed at end of day
  (if room; overflow lost).
- Shed sits at board center, is NOT a tile (never in tiles array; tiles array values are only
  None / "LOCKED" / structure dicts). "Orthogonally adjacent to shed" = one of the 4 center tiles:
  (half-1,half-1), (half,half-1), (half-1,half), (half,half) where half = boardSize//2. Default
  boardSize=10 -> (4,4),(5,4),(4,5),(5,5), one per quadrant. Only NW starts unlocked, so 3 of these
  4 tiles start locked — but shed is reachable from all 4 regardless (shed itself never locked).

## Farmer / Farm Hand
- HIRE is a market order. Cost = farmHandCostMult * fib(n), n = hires already made today, fib
  sequence starts 1,1,2,3,5,8,13,... Default farmHandCostMult=1 -> costs 1,1,2,3,5,8,13,21,...
  Resets each day. Hands disappear at end of day (drop inventory first); must rehire daily.
- New hand spawns orthogonally adjacent to shed, first free space in NWSE order; if none free, the
  least-occupied tile (ties broken NWSE). Spawn placement ignores lock status. First hire of the day
  typically lands on (5,4) which is locked until NE quadrant bought (locked tiles are passable, so
  the hand can walk back to unlocked land).
- Inventory: harvesting/pickup adds to inventory; can DROP to shed; end of day all inventory dumps
  to shed (overflow lost if shed full).

## Town Buildings
- New shop unlocks every townShopUnlockInterval days (default 3), drawn uniformly at random WITH
  replacement from the full shop table (duplicates possible). Stops after 8 total instances. Once
  unlocked, stays active rest of game. Total demand grows monotonically.
- Each unlocked shop instance consumes 1 of every demanded product every townShopSellInterval turns
  (default 4) -> e.g. wheat-demanding shop removes 6 wheat/day; two copies remove 12/day.
  Single-product shops consume 2x.
- Town center consumes 1 of every product (excluding fertilizer) every townCenterSellInterval turns
  (default 24 = once/day). Flat rate all season, does not ramp.

| Shop Type | Demand |
|---|---|
| Bakery | eggs, wheat |
| Pizza Shop | milk, tomatoes, wheat |
| Brunch Spot | eggs, wheat, strawberries |
| Yarn Store | wool (2x) |
| Ice Cream Shop | strawberries, milk, wheat |
| Pet Cafe | carrots (2x) |
| Smoothie Shop | strawberries, milk |
| Farmers Market | wheat, carrots, tomatoes, strawberries |

## Market Mechanics
- Unlimited seed/animal supply at fixed prices. Sell prices move dynamically per-resource, persist
  across days.
- Every product (+ fertilizer) starts with market inventory I0 = 10,000 units (far above realistic
  single-game production so inventory stays positive).
- Price rises as inventory falls (buys/consumption), falls as inventory grows (sells).
- SELL/BUY_PRODUCT orders processed concurrently across players, ONE UNIT AT A TIME, in lockstep:
  e.g. both players SELL CARROT 10 -> take current price, pay both for their 1st carrot, add 2 to
  market inventory (which may shift price), repeat.
- Price floor $1: unit still purchased at floor but NOT added to market inventory (keeps floor
  responsive to subsequent buys).
- Only WHEAT and FERTILIZER are buyable via BUY_PRODUCT. All products (incl. animal-collected
  fertilizer) are sellable via SELL, unrestricted.
- Market inventory drained by: town consumption (free) + player BUY_PRODUCT orders (same 1-unit-at-
  a-time concurrent procedure). If a player runs out of money mid-order, order stops.
- Buy price quoted at POST-buy inventory; sell price quoted at PRE-sell inventory -> an immediate
  buy then sell of the same item nets exactly zero (given otherwise-unchanged market).

### Price function (documented formula)
```
price(inv) = base + sign * amp * f(|inv - I0|)
  sign = +1 if inv < I0 (scarcity -> price up)
  sign = -1 if inv > I0 (glut -> price down)
  amp  = target * base / f(T)      # derived, not stored
  f in {linear, sq, sqrt, log, log10}   # log uses ln(1+x), f(0)=0
```
Floored at $1, rounded to nearest dollar. T = production capacity of a single 5x5 field over a
24-day calibration window at optimal watering, no fertilizer (animal totals pre-discounted 30% for
feed overhead, +1 day to build coop/pasture). 24-day window is a calibration horizon only (season is
30 days) — chosen short because opening days are setup-heavy/low-yield.
"target" = moving T units past I0 shifts price by target * base.

| Resource | Base | I0 | T | Below func | Below target | Above func | Above target | P(I0-T) | P(I0+T) | P(I0+2T) |
|---|---|---|---|---|---|---|---|---|---|---|
| Wheat | 25 | 10000 | 400 | sqrt | 0.80 | log | 0.20 | $45 | $20 | $19 |
| Carrot | 35 | 10000 | 450 | log | 0.20 | sqrt | 0.70 | $42 | $10 | $1 |
| Tomato | 60 | 10000 | 200 | linear | 0.40 | sqrt | 0.60 | $84 | $24 | $9 |
| Strawberry | 120 | 10000 | 100 | sqrt | 0.70 | linear | 1.60 | $204 | $1 | $1 |
| Melon | 250 | 10000 | 300 | log | 0.20 | sq | 3.60 | $300 | $1 | $1 |
| Egg | 50 | 10000 | 332 | linear | 0.40 | log | 0.20 | $70 | $40 | $39 |
| Milk | 160 | 10000 | 122 | sqrt | 0.60 | linear | 1.60 | $256 | $1 | $1 |
| Wool | 200 | 10000 | 105 | log | 0.20 | sq | 3.20 | $240 | $1 | $1 |
| Fertilizer | 100 | 10000 | 200 | linear | 0.40 | linear | 0.40 | $140 | $60 | $20 |

Defaults live in `MARKET_PARAMS` in `kaggriculture.py`. Overridable per-resource (sparse) via
`env.configuration["marketParams"]`, e.g. `{"WOOL": {"above_target": 0.95}}`.

## Turn Processing Order (documented, per turn)
1. Action validation — verify action legality.
2. Player actions — record actions taken by each player (simultaneous).
3. Market actions — process market queue in order, by player (1-unit-at-a-time concurrent as above).
4. Town buy actions — town center and shops reduce inventory.
5. Update observations.

Then, on day boundaries additionally:
6. Day refresh — update plant/animal condition for new day; reset fed/watered flags to False.
7. Market refresh — modify prices based on prior day's sells.
8. Income update — update bank based on buys/sells.
9. Farm update — clear harvested-out plants, consumed/sold inventory items, add new plants/animals.

(Note: exact day-boundary sub-order relative to items 6-9 needs confirmation by source inspection —
marked HYPOTHESIS ORDER pending verification.)

## Win Condition / Reward
- Winner = most coins in bank at end of season (720 turns). Ties possible.
- Reward = money in bank at game end. Unsold inventory items do NOT count.

## Observation format (documented schema) — see docs/01_mechanics_reference.md for the full typed copy

## Configuration defaults

| Parameter | Default | Description |
|---|---|---|
| episodeSteps | 720 | Total turns (24 x 30) |
| boardSize | 10 | Each side's square farm width/height; 4x 5x5 quadrants |
| startingMoney | 3000 | Starting coins per player |
| maxMarketOrdersPerTurn | 10 | Max market orders/turn/player; extras dropped |
| turnsPerDay | 24 | Turns per in-game day |
| shedCapacity | 100 | Max non-seed shed items; overflow discarded |
| weedSpawnChance | 0.005 | Per-tile weed spawn probability per end-of-day refresh |
| townShopUnlockInterval | 3 | Days between shop unlocks |
| townShopSellInterval | 4 | Turns between shop consumption ticks |
| townCenterSellInterval | 24 | Turns between town center consumption ticks (flat) |
| seed | null | Optional deterministic seed; cleared from config after read (kept out of obs) |

Per-crop seed costs / per-product base prices are NOT configurable (fixed, per tables above).

## Getting Started (official)
- `pip install -U kaggle-environments` (any recent release incl. Kaggriculture).
- `from kaggle_environments import make; env = make("kaggriculture", configuration={"episodeSteps":720}, debug=True); env.run([agent, "random"])`
- Built-in named agents: "pass", "random", "starter" (deterministic baseline).
- `env.render(mode="ipython", ...)`, `env.toJSON()` for replay dump.
- Kaggle CLI: `pip install kaggle`; auth via `~/.kaggle/access_token` token file, `kaggle auth login`
  (OAuth), or `KAGGLE_API_TOKEN` env var.
- Submission: `main.py` at tar.gz root (or single file). Max 100 MiB. 5 submissions/day, only latest
  2 active/tracked.
- Submission runtime resources: HDD 8 GiB, RAM 6.5 GiB, vCPUs 1.6.

## Official Quick Start Agent (starter-style wheat loop) — copied verbatim
```python
def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]

    market = []

    # Buy a wheat seed if we have none and have enough money
    if private["seeds"].get("WHEAT", 0) == 0 and me["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    # Sell any wheat sitting in the shed
    wheat_in_shed = private["shed"].get("WHEAT", 0)
    if wheat_in_shed > 0:
        market.append(["SELL", "WHEAT", wheat_in_shed])

    # If standing on an empty tile, plant wheat
    if tile is None and private["seeds"].get("WHEAT", 0) > 0:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}

    # If standing on a plant, manage watering and harvesting
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if crop_age >= 2:  # Wheat first_yield_day = 2
            return {"farmer": ["HARVEST"], "hands": [], "market": market}
        if not tile["watered_today"]:
            return {"farmer": ["WATER"], "hands": [], "market": market}

    return {"farmer": ["PASS"], "hands": [], "market": market}
```

## FAQ (documented)
- Submissions <= 100 MiB. Daily submission limit 5. Only most recent 2 active.
- Submission files land in `/kaggle_simulations/agent/` — imports must account for this.
- Submission runtime: HDD 8 GiB, RAM 6.5 GiB, vCPUs 1.6, size limit 100 MiB.
