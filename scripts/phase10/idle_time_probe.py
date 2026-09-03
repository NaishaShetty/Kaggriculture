"""
Phase 10 Step 2: idle-time / wasted-hand-turn baseline measurement.

Per the brief: instrument FIRST, before building anything. This module adds
a measurement layer around Phase 9's own high-scale agent
(scripts/phase9/common.py::make_high_scale_agent) -- NOT a new agent, NOT a
change to any frozen file. Phase 9's high-scale agent already isolates away
the HIRE-before-SELL/unconditional-HIRE-queuing bug (its own documented
fix), so re-measuring on top of it lets this phase ask specifically: is the
task-ASSIGNMENT logic underneath (the same tiered-priority greedy
bipartite matcher `agents/phase2_3/common.py::make_agent` uses, which
Phase 9's agent reuses unchanged for everything except SELL/HIRE ordering)
leaving productive capacity on the table at high hand counts? That is a
DIFFERENT question from the ordering bug Phase 9 already fixed.

Two independent metrics, computed by directly reading the raw replay
(env.toJSON(), read-only) -- never by modifying or re-deriving the
simulator's own logic:

1. TILE IDLE FRACTION: at the LAST turn of each day (hour=23), for every
   owned, non-shed tile that is currently a PLANT (i.e. a crop is
   standing on it), was it watered at some point that day
   (`tile["watered_today"]`, which only resets at the next day-refresh --
   VERIFIED via vendor_kaggriculture/kaggriculture.py's
   `_daily_refresh_plants`) OR does it still have ripe, unharvested yield
   (`_needs_harvest_crop`, reused unchanged from
   agents/phase2_3/common.py)? A tile in either state went a whole day
   without the attention it needed -- a directly observable measure of
   "tiles left idle", independent of final money.
2. WASTED HAND-TURNS: reuses the EXISTING, unmodified instrumentation
   pipeline's `action_efficiency` metric (instrumentation/metrics.py,
   already computes idle_fraction = PASS-action rate and
   productive_action_rate from the SAME replay) -- not reimplemented here,
   just read from `record["players"][0]["action_efficiency"]`.

Same configuration as Phase 9 Experiment 2's variable arm: MELON solo, 4
land quadrants total (land_quadrants=3 extra), $30,000 starting cushion,
hands 4-13, the same 4 development seeds. New code only; no frozen file
touched.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase2_3.common import _owned_tiles, _shed_tiles, _needs_harvest_crop  # reuse, not duplicate -- noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402
from scripts.phase9.common import DEVELOPMENT_SEEDS, HIGH_SCALE_STARTING_MONEY, make_high_scale_agent  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
VARIABLE_HANDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
LAND_QUADRANTS = 3
OUT_ROOT = "results/phase10"


def tile_idle_fraction_by_day(replay, board_size):
    """Returns a list of (day, n_plant_tiles, n_idle_tiles) for player 0,
    read directly from the raw replay -- independent of, and cross-checked
    against, nothing the agent itself reports."""
    out = []
    n_steps = len(replay["steps"])
    for day in range(TOTAL_DAYS):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= n_steps:
            break
        obs = replay["steps"][t][0]["observation"]
        farm = obs["farms"][0]
        tiles = farm["tiles"]
        shed_tiles = set(_shed_tiles(board_size))
        owned = _owned_tiles(tiles, board_size)
        n_plant, n_idle = 0, 0
        for (x, y) in owned:
            if (x, y) in shed_tiles:
                continue
            tile = tiles[y][x]
            if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                continue
            n_plant += 1
            needs_water = not tile.get("watered_today", False)
            needs_harvest = _needs_harvest_crop(tile, tile["crop"], day)
            if needs_water or needs_harvest:
                n_idle += 1
        out.append((day, n_plant, n_idle))
    return out


def run_one(n_hands, seed):
    agent = make_high_scale_agent(crops="MELON", n_hands=n_hands, land_quadrants=LAND_QUADRANTS, land_buy_day=0)
    replay, meta = run_episode(agent, "pass", STEPS, seed, extra_config={"startingMoney": HIGH_SCALE_STARTING_MONEY})
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))

    daily = tile_idle_fraction_by_day(replay, board_size)
    days_with_crops = [(d, n, i) for d, n, i in daily if n > 0]
    if days_with_crops:
        mean_idle_frac = sum(i / n for d, n, i in days_with_crops) / len(days_with_crops)
    else:
        mean_idle_frac = None

    record, extracted = analyze_replay(replay, meta, "phase10_idle_probe", f"h{n_hands}_seed{seed}")
    ae = record["players"][0]["action_efficiency"]
    final_money = record["outcome"]["final_money"][0]

    return {
        "n_hands": n_hands,
        "seed": seed,
        "final_money": final_money,
        "mean_tile_idle_fraction": round(mean_idle_frac, 4) if mean_idle_frac is not None else None,
        "n_days_with_crops": len(days_with_crops),
        "idle_action_fraction": ae["idle_fraction"],
        "productive_action_rate": ae["productive_action_rate"],
        "movement_fraction": ae["movement_fraction"],
        "crop_fraction": ae["crop_fraction"],
        "n_farmer_actions": ae["n_farmer_actions"],
        "n_hand_actions": ae["n_hand_actions"],
    }


def main():
    rows = []
    for h in VARIABLE_HANDS:
        for seed in DEVELOPMENT_SEEDS:
            row = run_one(h, seed)
            rows.append(row)
            print(f"  [h={h}] seed={seed} final_money=${row['final_money']} "
                  f"tile_idle_frac={row['mean_tile_idle_fraction']} "
                  f"action_idle_frac={row['idle_action_fraction']} "
                  f"productive_rate={row['productive_action_rate']}", flush=True)

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase10_idle_time_results.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows to {out_csv}")

    by_hand = {}
    for r in rows:
        by_hand.setdefault(r["n_hands"], []).append(r)
    summary = {}
    for h, group in sorted(by_hand.items()):
        summary[h] = {
            "mean_tile_idle_fraction": round(sum(g["mean_tile_idle_fraction"] for g in group) / len(group), 4),
            "mean_action_idle_fraction": round(sum(g["idle_action_fraction"] for g in group) / len(group), 4),
            "mean_productive_action_rate": round(sum(g["productive_action_rate"] for g in group) / len(group), 4),
            "mean_final_money": round(sum(g["final_money"] for g in group) / len(group), 2),
        }
    out_json = os.path.join(OUT_ROOT, "phase10_idle_time_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")
    for h, s in summary.items():
        print(f"  h={h}: tile_idle={s['mean_tile_idle_fraction']} action_idle={s['mean_action_idle_fraction']} "
              f"productive={s['mean_productive_action_rate']} final_money=${s['mean_final_money']}")


if __name__ == "__main__":
    main()
