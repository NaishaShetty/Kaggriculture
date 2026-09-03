"""
Phase 11 Step 5: idle-time cross-check on the multi-resource portfolio.

Same measurement approach as scripts/phase10/idle_time_probe.py (reused,
not modified -- new script here because that module is hard-wired to
Phase 9's single-crop MELON agent/config), applied to this phase's
combined STRAWBERRY+COW+SHEEP portfolio (the LABOR sweep configuration:
animals fixed at COW=6/SHEEP=6, STRAWBERRY tile target 24, hands 4-13) --
directly testing Phase 10 §6.2's hypothesis that task-assignment quality
might matter MORE on a heterogeneous, multi-task-type portfolio than it
did on the homogeneous single-crop one.

Tile idle fraction is computed only over CROP tiles (the bounded
STRAWBERRY footprint) using the identical definition Phase 10 used
(watered_today / _needs_harvest_crop, read directly from the raw replay).
Animal-side idle time (unfed/uncared animals) is tracked separately as a
second, analogous metric, since animals are a structurally different
resource with their own daily-maintenance cycle.

New code only.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase2_3.common import _owned_tiles, _shed_tiles, _needs_harvest_crop  # reuse -- noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402
from scripts.phase9.common import DEVELOPMENT_SEEDS, HIGH_SCALE_STARTING_MONEY  # noqa: E402
from scripts.phase11.multi_resource_agent import make_multi_resource_agent
from scripts.phase11.multi_resource_experiment import CROP, CROP_TILE_TARGET, LABOR_SWEEP_ANIMALS, LAND_QUADRANTS  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
VARIABLE_HANDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
OUT_ROOT = "results/phase11"


def daily_idle_metrics(replay, board_size):
    """Returns per-day (n_crop_tiles, n_crop_idle, n_animals_alive, n_animal_idle)."""
    out = []
    n_steps = len(replay["steps"])
    shed_tiles = set(_shed_tiles(board_size))
    for day in range(TOTAL_DAYS):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= n_steps:
            break
        obs = replay["steps"][t][0]["observation"]
        farm = obs["farms"][0]
        tiles = farm["tiles"]
        owned = _owned_tiles(tiles, board_size)
        n_crop, n_crop_idle, n_animal, n_animal_idle = 0, 0, 0, 0
        for (x, y) in owned:
            if (x, y) in shed_tiles:
                continue
            tile = tiles[y][x]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                n_crop += 1
                needs_water = not tile.get("watered_today", False)
                needs_harvest = _needs_harvest_crop(tile, tile["crop"], day)
                if needs_water or needs_harvest:
                    n_crop_idle += 1
            elif isinstance(tile, dict) and "animal" in tile:
                n_animal += 1
                needs_feed = not tile.get("fed_today", False)
                needs_care = not tile.get("cared_today", False)
                has_product = tile.get("yield_units", 0) > 0
                if needs_feed or needs_care or has_product:
                    n_animal_idle += 1
        out.append((day, n_crop, n_crop_idle, n_animal, n_animal_idle))
    return out


def run_one(n_hands, seed):
    agent = make_multi_resource_agent(
        crop=CROP, crop_tile_target=CROP_TILE_TARGET, n_hands=n_hands,
        land_quadrants=LAND_QUADRANTS, land_buy_day=0,
        animals=LABOR_SWEEP_ANIMALS, animal_buy_day=0, feed_source="market",
    )
    replay, meta = run_episode(agent, "pass", STEPS, seed, extra_config={"startingMoney": HIGH_SCALE_STARTING_MONEY})
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))

    daily = daily_idle_metrics(replay, board_size)
    crop_days = [(n, i) for d, n, i, na, nai in daily if n > 0]
    animal_days = [(na, nai) for d, n, i, na, nai in daily if na > 0]
    mean_crop_idle = sum(i / n for n, i in crop_days) / len(crop_days) if crop_days else None
    mean_animal_idle = sum(nai / na for na, nai in animal_days) / len(animal_days) if animal_days else None

    record, extracted = analyze_replay(replay, meta, "phase11_idle_check", f"h{n_hands}_seed{seed}")
    ae = record["players"][0]["action_efficiency"]
    final_money = record["outcome"]["final_money"][0]

    return {
        "n_hands": n_hands,
        "seed": seed,
        "final_money": final_money,
        "mean_crop_tile_idle_fraction": round(mean_crop_idle, 4) if mean_crop_idle is not None else None,
        "mean_animal_idle_fraction": round(mean_animal_idle, 4) if mean_animal_idle is not None else None,
        "idle_action_fraction": ae["idle_fraction"],
        "productive_action_rate": ae["productive_action_rate"],
    }


def main():
    rows = []
    for h in VARIABLE_HANDS:
        for seed in DEVELOPMENT_SEEDS:
            row = run_one(h, seed)
            rows.append(row)
            print(f"  [h={h}] seed={seed} final_money=${row['final_money']} "
                  f"crop_idle={row['mean_crop_tile_idle_fraction']} "
                  f"animal_idle={row['mean_animal_idle_fraction']} "
                  f"action_idle={row['idle_action_fraction']}", flush=True)

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase11_idle_time_results.csv")
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
            "mean_crop_tile_idle_fraction": round(sum(g["mean_crop_tile_idle_fraction"] for g in group) / len(group), 4),
            "mean_animal_idle_fraction": round(sum(g["mean_animal_idle_fraction"] for g in group) / len(group), 4),
            "mean_action_idle_fraction": round(sum(g["idle_action_fraction"] for g in group) / len(group), 4),
            "mean_final_money": round(sum(g["final_money"] for g in group) / len(group), 2),
        }
    out_json = os.path.join(OUT_ROOT, "phase11_idle_time_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")
    for h, s in summary.items():
        print(f"  h={h}: crop_idle={s['mean_crop_tile_idle_fraction']} animal_idle={s['mean_animal_idle_fraction']} "
              f"action_idle={s['mean_action_idle_fraction']} final_money=${s['mean_final_money']}")


if __name__ == "__main__":
    main()
