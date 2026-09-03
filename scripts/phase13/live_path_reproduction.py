"""
Phase 13 Step 1/2: resolve whether Phase 11's animal-servicing gap is
inherited from the frozen tactical layer (case (a)) or specific to Phase
11's own new code (case (b)) -- by DIRECT CODE COMPARISON first, then by
reproducing the gap using the FROZEN, unmodified
`agents/phase2_4/common.py::make_agent` (the actual function Submission
C/D's live path runs, imported here read-only, never edited).

CODE-READING RESULT (step 1, reported here per the brief's "before doing
anything else" instruction):

`scripts/phase11/multi_resource_agent.py`'s animal-task generation block
(HARVEST_ANIMAL/FEED/CARE priorities) and its FETCH-entry construction
block are copied VERBATIM from `agents/phase2_3/common.py` (confirmed by
direct side-by-side reading, lines 337-371 and 384-409 of that file) --
not reimplemented or altered. `agents/phase2_4/common.py` (Submission
C/D's actual tactical-layer ancestor) imports `tile_pool_assignment` and
`structure_type_assignment` directly from `agents/phase2_3/common.py` and
re-implements the SAME task-scheduling/FETCH/greedy-assignment structure
(its own lines ~268-425), including the identical single-fetch-entry-per-
item-type construction (`fetch_entries.append((req_min_priority[item],
home, "FETCH", "PICKUP", item, take))` -- ONE entry per distinct item,
sized to the TOTAL deficit across every task needing it that turn, not one
entry per worker or per animal needing it).

**CONCLUSION: this is case (a).** The candidate mechanism (Section
docstring below) is a property of `agents/phase2_3/common.py`'s own
task-assignment design, inherited unchanged by BOTH `agents/phase2_4/
common.py` (Submission C/D's live path) and every research agent built on
top of it in Phases 9-11. It is not something Phase 11's new code
introduced. This script reproduces it using the frozen
`agents/phase2_4/common.py::make_agent` directly -- not Phase 9/11's
bespoke agents -- to confirm the gap is live-path-relevant, independent of
any research-only code.

New code only; `agents/phase2_4/common.py` is imported unchanged, never
edited.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase2_4.common import make_agent  # FROZEN, imported unchanged -- noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
SEED = 700000
STARTING_MONEY = 30000
OUT_ROOT = "results/phase13"

# n_hands=8 deliberately kept BELOW 10 to avoid Phase 9's already-diagnosed,
# separate HIRE-before-SELL/unconditional-HIRE-queuing bug (need_hire>=10 fills
# the entire 10-order/turn cap) -- this script tests ONLY the animal-feeding
# mechanism, not that already-characterized ordering bug.
N_HANDS = 8
LAND_QUADRANTS = 3
ANIMALS = {"COW": 6, "SHEEP": 6}


def daily_animal_state(replay, board_size):
    from agents.phase2_3.common import _owned_tiles
    out = []
    n_steps = len(replay["steps"])
    for day in range(TOTAL_DAYS):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= n_steps:
            break
        obs = replay["steps"][t][0]["observation"]
        farm = obs["farms"][0]
        tiles = farm["tiles"]
        owned = _owned_tiles(tiles, board_size)
        n_animal, n_fed, n_cared = 0, 0, 0
        for (x, y) in owned:
            tile = tiles[y][x]
            if isinstance(tile, dict) and "animal" in tile:
                n_animal += 1
                if tile.get("fed_today"):
                    n_fed += 1
                if tile.get("cared_today"):
                    n_cared += 1
        out.append({"day": day, "n_animal": n_animal, "n_fed": n_fed, "n_cared": n_cared})
    return out


def main():
    agent = make_agent(
        crops="STRAWBERRY", n_hands=N_HANDS, land_quadrants=LAND_QUADRANTS, land_buy_day=0,
        animals=ANIMALS, animal_buy_day=0, feed_source="market",
        sell_policy={"mode": "passive"},
    )
    replay, meta = run_episode(agent, "pass", STEPS, SEED, extra_config={"startingMoney": STARTING_MONEY})
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))

    daily = daily_animal_state(replay, board_size)
    record, extracted = analyze_replay(replay, meta, "phase13_live_path", f"h{N_HANDS}_seed{SEED}")
    final_money = record["outcome"]["final_money"][0]

    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase13_live_path_reproduction.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["day", "n_animal", "n_fed", "n_cared"])
        w.writeheader()
        for row in daily:
            w.writerow(row)

    print(f"agents/phase2_4/common.py::make_agent (FROZEN, unmodified), n_hands={N_HANDS}, "
          f"land_quadrants={LAND_QUADRANTS}, animals={ANIMALS}, starting_money=${STARTING_MONEY}")
    print(f"final_money=${final_money}\n")
    print(f"{'day':>3} {'n_animal':>8} {'n_fed':>6} {'n_cared':>7} {'fed_frac':>9} {'cared_frac':>10}")
    n_days_with_gap = 0
    for row in daily:
        fed_frac = row["n_fed"] / row["n_animal"] if row["n_animal"] else None
        cared_frac = row["n_cared"] / row["n_animal"] if row["n_animal"] else None
        if fed_frac is not None and fed_frac < 1.0:
            n_days_with_gap += 1
        print(f"{row['day']:>3} {row['n_animal']:>8} {row['n_fed']:>6} {row['n_cared']:>7} "
              f"{('%.2f' % fed_frac) if fed_frac is not None else '  -':>9} "
              f"{('%.2f' % cared_frac) if cared_frac is not None else '  -':>10}")
    print(f"\nDays with any animal missing feed: {n_days_with_gap} / {len(daily)}")

    with open(os.path.join(OUT_ROOT, "phase13_live_path_summary.json"), "w") as f:
        json.dump({"final_money": final_money, "daily": daily, "n_days_with_gap": n_days_with_gap}, f, indent=2)


if __name__ == "__main__":
    main()
