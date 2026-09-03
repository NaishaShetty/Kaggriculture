"""
Phase 17 Step 1: confirm the WHEAT cross-crop-starvation mechanism directly,
before fixing anything. Two competing hypotheses (per the brief):
  (a) priority-ordering: another crop's task always wins ties in the same
      priority tier (WATER for every crop sits at priority tier 1 in
      agents/phase15/execution.py -- so this would require the greedy
      matcher's tie-break, not the tier number itself, to systematically
      favor one crop).
  (b) geometric: WHEAT tiles happen to sit farther from home / from wherever
      workers are than other crops' tiles, so the pure nearest-distance
      greedy matcher services them last or not at all.

This script measures, at each day 15-20 (Phase 16's flagged window), the
mean manhattan distance from home of WHEAT tiles vs. STRAWBERRY/MELON tiles,
alongside each crop's idle fraction that day -- a direct, cheap test of
hypothesis (b) without needing a full interactive turn-by-turn trace.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase2_3.common import _owned_tiles, _shed_tiles, _needs_harvest_crop, _home_tile, _manhattan  # noqa: E402
from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
SEEDS = [700000, 700001, 700002, 700003]


def analyze_day(replay, board_size, day):
    t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
    if t >= len(replay["steps"]):
        return None
    obs = replay["steps"][t][0]["observation"]
    farm = obs["farms"][0]
    tiles = farm["tiles"]
    home = _home_tile(board_size)
    shed_tiles = set(_shed_tiles(board_size))
    owned = _owned_tiles(tiles, board_size)

    per_crop_dist = {}
    per_crop_idle = {}
    for (x, y) in owned:
        if (x, y) in shed_tiles:
            continue
        tile = tiles[y][x]
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            continue
        crop = tile["crop"]
        dist = _manhattan((x, y), home)
        per_crop_dist.setdefault(crop, []).append(dist)
        needs_water = not tile.get("watered_today", False)
        needs_harvest = _needs_harvest_crop(tile, crop, day)
        bucket = per_crop_idle.setdefault(crop, [0, 0])
        bucket[0] += 1
        if needs_water or needs_harvest:
            bucket[1] += 1

    # also: hand/farmer positions this turn, to see how far workers actually are
    worker_positions = [tuple(farm["farmer"])] + [tuple(h) for h in farm.get("hands", [])]

    return {
        "day": day,
        "mean_dist_by_crop": {c: round(sum(ds) / len(ds), 2) for c, ds in per_crop_dist.items()},
        "n_tiles_by_crop": {c: len(ds) for c, ds in per_crop_dist.items()},
        "idle_frac_by_crop": {c: round(i / n, 4) if n else None for c, (n, i) in per_crop_idle.items()},
        "worker_positions": worker_positions,
        "mean_worker_dist_from_home": round(sum(_manhattan(p, home) for p in worker_positions) / len(worker_positions), 2),
    }


def main():
    for seed in SEEDS:
        print(f"\n=== seed {seed} ===")
        agent = make_macro_agent()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        board_size = int(replay.get("configuration", {}).get("boardSize", 10))
        for day in range(15, 21):
            info = analyze_day(replay, board_size, day)
            if info is None:
                continue
            print(f"  day {day}: mean_dist_by_crop={info['mean_dist_by_crop']} "
                  f"n_tiles={info['n_tiles_by_crop']} idle_frac={info['idle_frac_by_crop']} "
                  f"mean_worker_dist_from_home={info['mean_worker_dist_from_home']}")


if __name__ == "__main__":
    main()
