"""
Phase 22 Step 1: sweep agents/phase21/portfolio.py's day-0 opening WHEAT/MELON
fraction to find where the ramp-speed / market-durability tradeoff actually
sits, BEFORE picking a new number.

Diagnosis from Phase 21 (results/phase21/PHASE21_SHARED_MARKET_PORTFOLIO_REPORT.md
Section 4): the portfolio controller's day-0 opening (WHEAT 0.40 / MELON 0.60)
generates less early cash than the realistic-opponent benchmark's own
real-data-derived opening (WHEAT 0.35 / MELON 0.65), and in the worst traced
seed land doesn't reach 3 quadrants until day 24 (vs. the benchmark's day 11).

This script tests candidate day-0 WHEAT fractions (MELON = 1 - WHEAT) --
including the CURRENT portfolio ratio (0.40) and the benchmark's own ratio
(0.35) as two of the tested points, not assumed superior either -- and
measures BOTH isolated final money and the day land first reaches 3
quadrants, same 4 development seeds Phase 21 used.

Does NOT touch the land/hands/animal ramps, the opponent-aware STRAWBERRY
logic, or the cash-safety throttle -- only the day<5 crop-fraction constant,
via direct monkeypatch of agents.phase21.portfolio._base_crop_fractions
(the real portfolio.py file is edited separately, AFTER this sweep picks a
winner, per the brief's own "diagnose before you build" discipline).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import agents.phase21.portfolio as portfolio_mod  # noqa: E402
from agents.phase21.execution import make_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

DEV_SEEDS = [700000, 700001, 700002, 700003]
STEPS = 720
TURNS_PER_DAY = 24

# Candidate day-0 WHEAT fractions (MELON = 1 - wheat_frac). 0.35 is the
# realistic-opponent benchmark's own ratio; 0.40 is the current (pre-fix)
# portfolio ratio.
CANDIDATE_WHEAT_FRACTIONS = [0.35, 0.40, 0.45, 0.50, 0.55]


def make_targets_fn(wheat_frac):
    """Same as portfolio.portfolio_targets, except the day<5 opening uses
    the given WHEAT/MELON split instead of the hardcoded 0.40/0.60."""
    orig_base = portfolio_mod._base_crop_fractions

    def base_crop_fractions(day):
        if day < 5:
            return {"MELON": round(1 - wheat_frac, 4), "WHEAT": wheat_frac}
        return orig_base(day)

    def targets(day, obs, opponent_history):
        crop_fractions = dict(base_crop_fractions(day))
        if "STRAWBERRY" in crop_fractions:
            opp_share = portfolio_mod._opponent_strawberry_share(opponent_history)
            if opp_share is not None and opp_share > portfolio_mod.OPPONENT_STRAWBERRY_DOMINANCE_THRESHOLD:
                shift = min(portfolio_mod.STRAWBERRY_SHIFT_WHEN_OPPONENT_HEAVY, crop_fractions["STRAWBERRY"])
                crop_fractions["STRAWBERRY"] -= shift
                crop_fractions["WHEAT"] = crop_fractions.get("WHEAT", 0.0) + shift
        t = {
            "n_hands": portfolio_mod._rung_value(day, portfolio_mod._HANDS_RUNGS),
            "land_quadrants": portfolio_mod._rung_value(day, portfolio_mod._LAND_RUNGS),
            "animals": dict(portfolio_mod._rung_value(day, portfolio_mod._ANIMAL_SPECIES_RUNGS)),
            "crop_tile_target": portfolio_mod._rung_value(day, portfolio_mod._CROP_TILE_RUNGS),
            "crop_fractions": crop_fractions,
        }
        if day >= portfolio_mod.LIQUIDATION_START_DAY:
            t["crop_tile_target"] = 0
        if day >= portfolio_mod.DIG_ONGOING_CROPS_DAY:
            t["digging_ongoing"] = True
        return t

    return targets


def day_land_reaches_3(replay, board_size):
    for day in range(30):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= len(replay["steps"]):
            return None
        obs = replay["steps"][t][0]["observation"]
        farm = obs["farms"][0]
        if len(farm.get("unlocked_quadrants", ["NW"])) >= 3:
            return day
    return None


def run_one(wheat_frac, seed):
    targets_fn = make_targets_fn(wheat_frac)
    agent = make_execution_agent(targets_fn)
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))
    final_money = replay["rewards"][0]
    day3 = day_land_reaches_3(replay, board_size)
    return final_money, day3


def main():
    print(f"{'wheat_frac':<12}{'seed':<10}{'final_money':<14}{'day_land=3':<12}")
    summary = {}
    for wf in CANDIDATE_WHEAT_FRACTIONS:
        rows = []
        for seed in DEV_SEEDS:
            money, day3 = run_one(wf, seed)
            rows.append((seed, money, day3))
            print(f"{wf:<12}{seed:<10}{money:<14.0f}{str(day3):<12}")
        mean_money = sum(r[1] for r in rows) / len(rows)
        day3s = [r[2] for r in rows if r[2] is not None]
        mean_day3 = sum(day3s) / len(day3s) if day3s else None
        summary[wf] = {"mean_final_money": mean_money, "mean_day_land_3": mean_day3, "rows": rows}
        print(f"  MEAN wheat_frac={wf}: final_money=${mean_money:.0f}  mean_day_land=3: {mean_day3}")
        print()

    print("\n=== SWEEP SUMMARY ===")
    for wf, s in summary.items():
        print(f"  wheat_frac={wf}: mean_final=${s['mean_final_money']:.0f}  mean_day_land_3={s['mean_day_land_3']}")

    import json
    os.makedirs("results/phase22", exist_ok=True)
    with open("results/phase22/phase22_opening_ratio_sweep.json", "w") as f:
        json.dump({str(k): v for k, v in summary.items()}, f, indent=2, default=str)
    print("\nWrote results/phase22/phase22_opening_ratio_sweep.json")


if __name__ == "__main__":
    main()
