"""
Phase 16 Step 1-2: diagnose WHERE Phase 15's execution efficiency gap
concentrates, on Phase 15's ACTUAL agent (agents/phase15/adapters/
macro_agent.py) at its real, changing operating trajectory -- not a fixed
config. Reuses Phase 10's tile-idle-fraction methodology and Phase 11/13's
animal-servicing (fed-fraction) methodology, and instrumentation's own
action_efficiency metric (wasted-hand-turns), but breaks tile-idle down
PER CROP TYPE (new -- neither Phase 10 nor Phase 13 tested more than one
crop type at once) and reports all three metrics at three day ranges
(early ramp 5-10, mid-game 15-20, late-game 25-29) since the macro
controller's targets change over the game.

Isolated (vs "pass"), same 4 development seeds Phase 15 used
(700000-700003). New code only; does not modify agents/phase15/ (this is
the diagnostic pass BEFORE any fix).
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase2_3.common import _owned_tiles, _shed_tiles, _needs_harvest_crop  # noqa: E402
from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
DEV_SEEDS = [700000, 700001, 700002, 700003]
DAY_RANGES = {"early_ramp_5_10": range(5, 11), "mid_game_15_20": range(15, 21), "late_game_25_29": range(25, 30)}
OUT_ROOT = "results/phase16"


def daily_stats(replay, board_size):
    """Returns list of dicts, one per day: overall + per-crop tile idle
    counts, and animal fed counts -- all read directly from the raw replay
    at the last turn of each day (hour==23), same discipline as Phase 10/13."""
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

        per_crop = {}  # crop -> [n_plant, n_idle]
        n_animal, n_fed = 0, 0
        for (x, y) in owned:
            if (x, y) in shed_tiles:
                continue
            tile = tiles[y][x]
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crop = tile["crop"]
                bucket = per_crop.setdefault(crop, [0, 0])
                bucket[0] += 1
                needs_water = not tile.get("watered_today", False)
                needs_harvest = _needs_harvest_crop(tile, crop, day)
                if needs_water or needs_harvest:
                    bucket[1] += 1
            elif "animal" in tile:
                n_animal += 1
                if tile.get("fed_today"):
                    n_fed += 1

        out.append({"day": day, "per_crop": per_crop, "n_animal": n_animal, "n_fed": n_fed})
    return out


def summarize_range(daily, day_range):
    rows = [d for d in daily if d["day"] in day_range]
    if not rows:
        return None
    # overall crop idle fraction (all crops pooled)
    total_plant, total_idle = 0, 0
    per_crop_totals = {}
    total_animal, total_fed = 0, 0
    for d in rows:
        for crop, (n_plant, n_idle) in d["per_crop"].items():
            total_plant += n_plant
            total_idle += n_idle
            pc = per_crop_totals.setdefault(crop, [0, 0])
            pc[0] += n_plant
            pc[1] += n_idle
        total_animal += d["n_animal"]
        total_fed += d["n_fed"]
    overall_idle_frac = (total_idle / total_plant) if total_plant else None
    per_crop_idle_frac = {c: (i / n if n else None) for c, (n, i) in per_crop_totals.items()}
    animal_fed_frac = (total_fed / total_animal) if total_animal else None
    return {
        "n_days": len(rows),
        "overall_tile_idle_fraction": round(overall_idle_frac, 4) if overall_idle_frac is not None else None,
        "per_crop_tile_idle_fraction": {c: round(v, 4) if v is not None else None for c, v in per_crop_idle_frac.items()},
        "per_crop_tile_counts": {c: n for c, (n, i) in per_crop_totals.items()},
        "animal_fed_fraction": round(animal_fed_frac, 4) if animal_fed_frac is not None else None,
        "mean_animals_present": round(total_animal / len(rows), 2),
    }


def run_one(seed):
    agent = make_macro_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))
    daily = daily_stats(replay, board_size)

    record, extracted = analyze_replay(replay, meta, "phase16_diagnose", f"seed{seed}")
    ae = record["players"][0]["action_efficiency"]
    final_money = record["outcome"]["final_money"][0]

    by_range = {name: summarize_range(daily, rng) for name, rng in DAY_RANGES.items()}
    return {
        "seed": seed,
        "final_money": final_money,
        "action_idle_fraction": ae["idle_fraction"],
        "productive_action_rate": ae["productive_action_rate"],
        "movement_fraction": ae["movement_fraction"],
        "by_range": by_range,
    }


def main():
    rows = []
    for seed in DEV_SEEDS:
        row = run_one(seed)
        rows.append(row)
        print(f"seed={seed} final_money=${row['final_money']} "
              f"action_idle={row['action_idle_fraction']} productive={row['productive_action_rate']}")
        for name, s in row["by_range"].items():
            if s is None:
                continue
            print(f"  [{name}] overall_tile_idle={s['overall_tile_idle_fraction']} "
                  f"per_crop_idle={s['per_crop_tile_idle_fraction']} "
                  f"per_crop_counts={s['per_crop_tile_counts']} "
                  f"animal_fed_frac={s['animal_fed_fraction']} (n_animals~{s['mean_animals_present']})")

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase16_diagnostic_results.json"), "w") as f:
        json.dump(rows, f, indent=2)
    print(f"\nWrote results to {OUT_ROOT}/phase16_diagnostic_results.json")

    # Cross-seed mean summary per range
    summary = {}
    for name in DAY_RANGES:
        vals = [r["by_range"][name] for r in rows if r["by_range"][name] is not None]
        if not vals:
            continue
        mean_overall = sum(v["overall_tile_idle_fraction"] for v in vals if v["overall_tile_idle_fraction"] is not None) / len(vals)
        mean_animal_fed = [v["animal_fed_fraction"] for v in vals if v["animal_fed_fraction"] is not None]
        mean_animal_fed = sum(mean_animal_fed) / len(mean_animal_fed) if mean_animal_fed else None
        all_crops = set()
        for v in vals:
            all_crops.update(v["per_crop_tile_idle_fraction"].keys())
        per_crop_mean = {}
        for c in all_crops:
            cvals = [v["per_crop_tile_idle_fraction"].get(c) for v in vals if v["per_crop_tile_idle_fraction"].get(c) is not None]
            per_crop_mean[c] = round(sum(cvals) / len(cvals), 4) if cvals else None
        summary[name] = {
            "mean_overall_tile_idle_fraction": round(mean_overall, 4),
            "mean_per_crop_tile_idle_fraction": per_crop_mean,
            "mean_animal_fed_fraction": round(mean_animal_fed, 4) if mean_animal_fed is not None else None,
        }
    mean_action_idle = sum(r["action_idle_fraction"] for r in rows) / len(rows)
    mean_productive = sum(r["productive_action_rate"] for r in rows) / len(rows)
    summary["overall_action_efficiency"] = {
        "mean_action_idle_fraction": round(mean_action_idle, 4),
        "mean_productive_action_rate": round(mean_productive, 4),
    }
    with open(os.path.join(OUT_ROOT, "phase16_diagnostic_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {OUT_ROOT}/phase16_diagnostic_summary.json")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
