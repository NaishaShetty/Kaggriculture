"""
Phase 14: re-run Phase 13's exact before/after servicing-rate measurement
(`scripts/phase13/servicing_rate_experiment.py`) unchanged in every respect
EXCEPT the two parameters this phase's brief asks to re-scope to Submission
C's ACTUAL live-path targets (confirmed by direct code read this phase --
see the report, Section 1):

  - animals: Submission C's live ceiling is agents/phase3_8/animal_response.py's
    HIGH_RESPONSE_ANIMALS = {"COW": 3, "SHEEP": 3} -- 6 total, not 12.
  - hands: Submission C's live target is agents/phase3_5/response_policy.py's
    RESPONSE_N_HANDS = 5, not the 4-13 sweep Phase 13 used. Swept 2-8 here,
    centered on 5, to see the shape around the real operating point.

Everything else -- CROP="STRAWBERRY", CROP_TILE_TARGET=24, LAND_QUADRANTS=3,
$30,000 starting cushion, development seeds 700000-700003, Phase 13's own
`make_multi_resource_agent` (before) and `make_multi_resource_agent_fixed`
(after), the daily-fed-fraction metric -- is reused byte-for-byte from
`scripts/phase13/servicing_rate_experiment.py`; this is a re-scoped
re-measurement, not a redesign.

New code only. Does not touch scripts/phase13/, scripts/phase11/,
agents/phase2_3/common.py, agents/phase2_4/common.py, or any frozen file.
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
from scripts.phase11.multi_resource_experiment import CROP, CROP_TILE_TARGET, LAND_QUADRANTS  # noqa: E402
from scripts.phase13.fixed_agent import make_multi_resource_agent_fixed  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
OUT_ROOT = "results/phase14"

# Submission C's actual live animal ceiling (agents/phase3_8/animal_response.py::HIGH_RESPONSE_ANIMALS)
LIVE_SCALE_ANIMALS = {"COW": 3, "SHEEP": 3}  # 6 total -- the real cap, not Phase 13's 12
# Swept centered on Submission C's actual live hand target (agents/phase3_5/response_policy.py::RESPONSE_N_HANDS == 5)
VARIABLE_HANDS = [2, 3, 4, 5, 6, 7, 8]


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
        animals=LIVE_SCALE_ANIMALS, animal_buy_day=0, feed_source="market",
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
    out_csv = os.path.join(OUT_ROOT, "phase14_live_scale_servicing_results.csv")
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
        summary[h]["improvement_pts"] = round(
            (summary[h]["mean_after_fed_frac"] - summary[h]["mean_before_fed_frac"]) * 100, 2)
    out_json = os.path.join(OUT_ROOT, "phase14_live_scale_servicing_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")
    for h, s in summary.items():
        print(f"  h={h}: before={s['mean_before_fed_frac']} after={s['mean_after_fed_frac']} "
              f"(+{s['improvement_pts']} pts)")


if __name__ == "__main__":
    main()
