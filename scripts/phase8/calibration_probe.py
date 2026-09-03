"""
Phase 8 calibration probe (Phase 5 sec.16 / Phase 6 Experiment 3).

Standalone, isolated-play (single protagonist vs the built-in "pass" no-op
opponent) experiment. For each candidate crop in Variant D's substitution
list (agents/phase3_3/interventions.py::NON_MELON_CANDIDATES, plus MELON
itself -- the full candidate set that logic considers), commits exactly
n_tiles in {5, 10, 15, 20, 25} tiles to that single crop from day 0, plays a
full 30-day season with correct watering/harvesting/replanting discipline,
and records the ACTUAL harvested-and-sold revenue (gross SELL proceeds,
read from the existing instrumentation pipeline's crop_metrics, never
self-computed) for that crop.

This is compared against economic_model.model.crop_production_value's
REVENUE estimate (its net_profit + seed_cost, i.e. the
`rev_per_tile_day * tile_days` term before subtracting seed cost -- land/
hire cost in this harness is a probe-only artifact, not part of what the
calibration constant claims to predict, so it is excluded from the
comparison on both sides) at the same n_tiles.

Reuses, unmodified:
  - agents/phase2_3/common.py's tile/worker helpers (_home_tile, _shed_tiles,
    _owned_tiles, _manhattan, _step_toward, _fib, _is_plant,
    _needs_harvest_crop, _needs_water) -- the SAME primitives Phase 2.4's
    frozen tactical layer is built from.
  - instrumentation/pipeline.py::run_and_analyze -- the same measurement
    pipeline every other phase in this project uses (no bespoke parsing).
  - agents/phase4/market_model.py::simulate_sell -- for the market-impact-
    adjusted comparison (step 6 of the brief), reusing the Phase 4/5
    live-validated exact pricer rather than building a new one.

New code only. Does not modify, import for mutation, or otherwise touch
agents/phase2_6/, agents/phase3_3/, agents/phase3_5/, agents/phase3_8/, or
main.py. No submission is produced.

WHY A CUSTOM AGENT INSTEAD OF agents/phase2_4/common.py DIRECTLY:
Phase 2.4's make_agent (via agents/phase2_3/common.py::tile_pool_assignment)
always assigns 100% of a single crop's *entire* owned tile pool to that
crop -- there is no parameter to cap it at an exact tile count, and pool
size is quantized by land-quadrant boundaries (24 tiles at 1 quadrant, 48 at
2), which cannot hit 5/10/15/20/25 exactly. The agent below is a faithful,
minimal re-composition of the SAME primitives (identical task-priority
order: HARVEST > WATER > PLANT; identical hire/land/sell/buy-seed logic),
with only the tile *pool selection* changed to a fixed-size slice -- so the
execution discipline is the same quality Phase 2.4 already validated, just
scoped to an exact tile count instead of "everything owned."
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS, MARKET_PARAMS, LAND_PRICES  # noqa: E402
from agents.phase2_3.common import (  # reuse, not duplicate -- noqa: E402
    _home_tile, _shed_tiles, _owned_tiles, _manhattan, _step_toward, _fib,
    _is_plant, _needs_harvest_crop, _needs_water,
)
from economic_model.model import EconomicState, crop_production_value, CALIBRATION  # noqa: E402
from agents.phase4.market_model import simulate_sell, market_depth  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

OUT_ROOT = "results/phase8"
STEPS = 720
TOTAL_DAYS = 30
SEED = 700000  # a Phase 3 "development" seed, per this project's existing seed convention

CANDIDATE_CROPS = ["WHEAT", "STRAWBERRY", "CARROT", "TOMATO", "MELON"]  # Variant D's full candidate set (incl. MELON itself)
N_TILES_VALUES = [5, 10, 15, 20, 25]

LAND_QUADRANTS = 2  # 2 quadrants -> 50 owned tiles - 2 shed tiles = 48 pool tiles, enough for n_tiles up to 25
N_HANDS = 4          # generous, fixed labor -- isolates the PRODUCTION/SALE measurement from a labor-scarcity confound
SEED_BUFFER_CAP = 6


def make_probe_agent(crop, n_tiles, n_hands=N_HANDS, land_quadrants=LAND_QUADRANTS, seed_buffer_cap=SEED_BUFFER_CAP):
    """A single-crop, exact-tile-count agent. Task priority (HARVEST > WATER >
    PLANT), hire logic, land-purchase logic, and passive (sell-every-turn)
    selling are all identical in spirit to agents/phase2_4/common.py's
    make_agent -- passive selling is used deliberately so the measured
    number reflects raw production/sale economics, not a selling-timing
    strategy (which would introduce exactly the confound this probe is
    designed to avoid)."""

    def agent(obs):
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        board_size = len(me["tiles"])
        tiles = me["tiles"]
        day = obs["day"]
        money = me["money"]
        shed = private.get("shed", {})
        seeds = private.get("seeds", {})
        invs = private.get("inventories", [{}])

        home = _home_tile(board_size)
        shed_tiles = _shed_tiles(board_size)
        owned = _owned_tiles(tiles, board_size)
        pool = sorted(
            (t for t in owned if t not in shed_tiles),
            key=lambda t: (_manhattan(t, home), t[1], t[0]),
        )
        crop_tiles = pool[:n_tiles]

        positions = [tuple(me["farmer"])] + [tuple(h) for h in me.get("hands", [])]
        workers = []
        for i, pos in enumerate(positions):
            inv = invs[i] if i < len(invs) else {}
            workers.append({"pos": pos, "inv": inv, "claimed": False, "action": None})

        market = []

        # --- HIRE (hands reset daily, identical logic to Phase 2.4) ---
        current_hands = len(me.get("hands", []))
        need_hire = max(0, n_hands - current_hands)
        hire_cost_est = sum(_fib(current_hands + i) for i in range(need_hire))
        for _ in range(need_hire):
            market.append(["HIRE"])
        money -= hire_cost_est

        # --- BUY_LAND: only enough to make room for n_tiles, bought once on day 0 ---
        n_extra_owned = len(me.get("unlocked_quadrants", [])) - 1
        if n_extra_owned < land_quadrants and n_extra_owned < len(LAND_PRICES):
            next_cost = LAND_PRICES[n_extra_owned]
            if money >= next_cost:
                market.append(["BUY_LAND"])
                money -= next_cost

        # --- SELL: passive -- sell everything harvested this turn, no timing strategy ---
        held = shed.get(crop, 0)
        if held > 0:
            market.append(["SELL", crop, held])

        # --- BUY_SEED: keep exactly enough seed buffer for currently-empty crop_tiles ---
        empty_needed = sum(1 for t in crop_tiles if tiles[t[1]][t[0]] is None)
        if empty_needed > 0:
            target = min(seed_buffer_cap, len(workers), empty_needed)
            held_seeds = seeds.get(crop, 0)
            need = max(0, target - held_seeds)
            if need > 0 and money >= CROPS[crop]["seed"]:
                buy_n = min(need, int(money // CROPS[crop]["seed"]))
                if buy_n > 0:
                    market.append(["BUY_SEED", crop, buy_n])
                    money -= buy_n * CROPS[crop]["seed"]

        market = market[:10]

        # --- Task scheduling: identical priority order to Phase 2.4 (HARVEST > WATER > PLANT) ---
        tasks = []
        for t in crop_tiles:
            x, y = t
            tt = tiles[y][x]
            if _needs_harvest_crop(tt, crop, day):
                tasks.append((0, t, "HARVEST", None))
            elif _needs_water(tt, crop):
                tasks.append((1, t, "WATER", None))
            elif tt is None and seeds.get(crop, 0) > 0:
                tasks.append((2, t, "PLANT", crop))

        def nearest_free_worker(pos):
            best, best_d = None, None
            for w in workers:
                if w["claimed"]:
                    continue
                d = _manhattan(w["pos"], pos)
                if best is None or d < best_d:
                    best, best_d = w, d
            return best

        for pr, t, kind, extra in sorted(tasks, key=lambda e: e[0]):
            w = nearest_free_worker(t)
            if w is None:
                continue
            w["claimed"] = True
            if w["pos"] != t:
                w["action"] = [_step_toward(w["pos"][0], w["pos"][1], t[0], t[1])]
            elif kind == "PLANT":
                w["action"] = ["PLANT", extra]
            else:
                w["action"] = [kind]

        # Any worker carrying harvested inventory heads to the shed to DROP it.
        for w in workers:
            if w["claimed"]:
                continue
            if w["inv"]:
                target = min(shed_tiles, key=lambda s: _manhattan(w["pos"], s))
                w["claimed"] = True
                w["action"] = ["DROP"] if w["pos"] == target else [_step_toward(w["pos"][0], w["pos"][1], target[0], target[1])]

        for w in workers:
            if w["action"] is None:
                w["action"] = ["PASS"]

        return {"farmer": workers[0]["action"], "hands": [w["action"] for w in workers[1:]], "market": market}

    return agent


def calibration_estimated_revenue(crop, n_tiles, day=0):
    """The REVENUE component of crop_production_value (its net_profit is
    revenue - seed_cost; we add seed_cost back so this comparison is
    apples-to-apples with the probe's gross SELL revenue, which also does
    not net out seed/land/hire cost)."""
    state = EconomicState(day=day, cash=10 ** 9)  # cash unconstrained: calibration_error probe, not affordability
    est = crop_production_value(crop, state, n_tiles=n_tiles)
    seed_cost = CROPS[crop]["seed"] * n_tiles
    return round(est.value + seed_cost, 2)


def market_impact_adjusted_revenue(crop, n_tiles, day=0):
    """Reprices the SAME implied unit count the calibration estimate stands
    on (estimated $ / current base price) through the Phase 4/5 verified
    unit-by-unit simulator, starting from the market's documented reference
    inventory (I0) -- i.e. 'if this many units were dumped on a fresh
    market, in one batch, what would they actually fetch'. This is the
    step-6 market-impact-adjusted view requested by the brief; it is NOT
    the primary calibration-error comparison (that is gross measured
    revenue vs. calibration_estimated_revenue above), only a secondary
    lens on whether market-impact pricing reorders the crops."""
    est_revenue = calibration_estimated_revenue(crop, n_tiles, day=day)
    base_price = MARKET_PARAMS[crop]["base"]
    implied_units = max(0, round(est_revenue / base_price))
    revenue, _, _ = simulate_sell(crop, implied_units, MARKET_PARAMS[crop]["I0"])
    return round(revenue, 2), implied_units


def run_one(crop, n_tiles):
    agent = make_probe_agent(crop, n_tiles)
    record, replay, extracted = run_and_analyze(
        agent, "pass", STEPS, SEED, f"phase8_calibration_probe_{crop}", f"n{n_tiles}",
    )
    crop_metrics = record["players"][0]["crop_metrics"].get(crop, {})
    actual_revenue = crop_metrics.get("revenue", 0.0)
    actual_units = crop_metrics.get("total_harvested_units", 0)

    estimated_revenue = calibration_estimated_revenue(crop, n_tiles)
    abs_error = round(actual_revenue - estimated_revenue, 2)
    rel_error = round(abs_error / estimated_revenue, 4) if estimated_revenue else None

    mi_revenue, implied_units = market_impact_adjusted_revenue(crop, n_tiles)

    # Market-impact-adjusted revenue for the ACTUAL harvested/sold volume (not the
    # calibration-implied volume above) -- the apples-to-apples figure needed to
    # resolve Phase 6 Experiment 3: "if these actual units were dumped on a fresh
    # market in one batch, what would they fetch", isolating market-depth effects
    # from the (separately diagnosed) replanting-undercount issue.
    actual_mi_revenue, _, _ = simulate_sell(crop, actual_units, MARKET_PARAMS[crop]["I0"])

    return {
        "crop": crop,
        "n_tiles": n_tiles,
        "T_market_depth": market_depth(crop),
        "ongoing_crop": CROPS[crop]["ongoing"],
        "actual_revenue": round(actual_revenue, 2),
        "actual_units_harvested": actual_units,
        "calibration_estimated_revenue": estimated_revenue,
        "abs_error_actual_minus_estimated": abs_error,
        "rel_error": rel_error,
        "revenue_per_tile_day_calibration_constant": CALIBRATION["revenue_per_tile_day"][crop],
        "actual_revenue_per_tile_day": round(actual_revenue / (n_tiles * TOTAL_DAYS), 4) if n_tiles else None,
        "market_impact_implied_units": implied_units,
        "market_impact_adjusted_revenue": mi_revenue,
        "actual_market_impact_adjusted_revenue": round(actual_mi_revenue, 2),
    }


def main():
    rows = []
    for crop in CANDIDATE_CROPS:
        for n_tiles in N_TILES_VALUES:
            row = run_one(crop, n_tiles)
            rows.append(row)
            print(
                f"[{crop} n_tiles={n_tiles}] actual=${row['actual_revenue']} "
                f"estimated=${row['calibration_estimated_revenue']} "
                f"rel_error={row['rel_error']} mi_adjusted=${row['market_impact_adjusted_revenue']}",
                flush=True,
            )

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase8_calibration_probe_results.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows to {out_csv}")

    out_json = os.path.join(OUT_ROOT, "phase8_calibration_probe_results.json")
    with open(out_json, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Wrote raw results to {out_json}")


if __name__ == "__main__":
    main()
