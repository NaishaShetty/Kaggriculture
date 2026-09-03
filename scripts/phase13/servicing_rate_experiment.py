"""
Phase 13 Step 5: servicing-rate validation, BEFORE (Phase 11's own
`scripts/phase11/multi_resource_agent.py::make_multi_resource_agent`,
unmodified) vs. AFTER (this phase's `scripts/phase13/fixed_agent.py::
make_multi_resource_agent_fixed`, the PARALLEL FETCH fix and nothing
else), on the EXACT SAME configuration and seeds Phase 11 used: STRAWBERRY
x24 tiles + COW6/SHEEP6, 3 extra land quadrants, $30,000 starting cushion,
hands 4-13, development seeds 700000-700003.

Metric: mean fraction of animal-days with `fed_today=True` (the direct
servicing rate, not final money -- per this phase's explicit scope,
economic re-testing is the NEXT phase's job). Computed identically to
Phase 11's `mean_animal_idle_fraction` methodology but reported as its
complement (fed fraction) for directness, plus the same idle-style number
for continuity with Phase 11's own reporting.

New code only.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase2_3.common import _owned_tiles  # reuse -- noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from scripts.phase9.common import DEVELOPMENT_SEEDS, HIGH_SCALE_STARTING_MONEY  # noqa: E402
from scripts.phase11.multi_resource_agent import make_multi_resource_agent  # noqa: E402
from scripts.phase11.multi_resource_experiment import CROP, CROP_TILE_TARGET, LABOR_SWEEP_ANIMALS, LAND_QUADRANTS  # noqa: E402
from scripts.phase13.fixed_agent import make_multi_resource_agent_fixed  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
VARIABLE_HANDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
OUT_ROOT = "results/phase13"


def daily_fed_fraction(replay, board_size):
    out = []
    n_steps = len(replay["steps"])
    for day in range(TOTAL_DAYS):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= n_steps:
            break
        obs = replay["steps"][t][0]["observation"]
        tiles = obs["farms"][0]["tiles"]
        owned = _owned_tiles(tiles, board_size)
        n_animal, n_fed = 0, 0
        for (x, y) in owned:
            tile = tiles[y][x]
            if isinstance(tile, dict) and "animal" in tile:
                n_animal += 1
                if tile.get("fed_today"):
                    n_fed += 1
        if n_animal > 0:
            out.append(n_fed / n_animal)
    return out


def run_one(agent_factory, n_hands, seed):
    agent = agent_factory(
        crop=CROP, crop_tile_target=CROP_TILE_TARGET, n_hands=n_hands,
        land_quadrants=LAND_QUADRANTS, land_buy_day=0,
        animals=LABOR_SWEEP_ANIMALS, animal_buy_day=0, feed_source="market",
    )
    replay, meta = run_episode(agent, "pass", STEPS, seed, extra_config={"startingMoney": HIGH_SCALE_STARTING_MONEY})
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))
    daily = daily_fed_fraction(replay, board_size)
    mean_fed = sum(daily) / len(daily) if daily else None
    return mean_fed


def main():
    rows = []
    for h in VARIABLE_HANDS:
        for seed in DEVELOPMENT_SEEDS:
            before = run_one(make_multi_resource_agent, h, seed)
            after = run_one(make_multi_resource_agent_fixed, h, seed)
            rows.append({"n_hands": h, "seed": seed, "before_fed_frac": round(before, 4),
                         "after_fed_frac": round(after, 4), "improvement": round(after - before, 4)})
            print(f"  [h={h}] seed={seed} before={round(before,4)} after={round(after,4)} "
                  f"improvement={round(after-before,4)}", flush=True)

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase13_servicing_rate_results.csv")
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
            "mean_before_fed_frac": round(sum(g["before_fed_frac"] for g in group) / len(group), 4),
            "mean_after_fed_frac": round(sum(g["after_fed_frac"] for g in group) / len(group), 4),
        }
    out_json = os.path.join(OUT_ROOT, "phase13_servicing_rate_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")
    for h, s in summary.items():
        print(f"  h={h}: before={s['mean_before_fed_frac']} after={s['mean_after_fed_frac']}")


if __name__ == "__main__":
    main()
