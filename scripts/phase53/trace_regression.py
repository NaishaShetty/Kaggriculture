"""
Phase 53 Step 5/diagnostic: the 4-seed screen found a decisive, consistent
regression (-6.1%, 4/4 seeds worse) despite idle_fraction actually
IMPROVING (0.107->0.091) -- ruling out the naive "ran out of worker-turns"
explanation Phase 30/46 already characterized. This traces seed 700000
directly to find the real mechanism: daily money, land/hire purchase
timing, and daily WATER/HARVEST/walk-only action counts (to check whether
"more active" (lower idle_fraction) is actually being spent WALKING to the
newly-distant 4th quadrant rather than doing productive tile work).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase48.capped_animal_portfolio_agent import make_capped_animal_portfolio_agent  # noqa: E402
from scripts.phase53.fourth_quadrant_portfolio_agent import make_fourth_quadrant_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
SEED = 700000


def trace(label, make_agent):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, SEED, None)
    steps = replay["steps"]

    print(f"\n=== {label} (seed={SEED}) ===")
    prev_money = None
    prev_land = None
    prev_hands = None
    action_kind_by_day = {}
    for t, step in enumerate(steps):
        rec = step[0]
        obs = rec["observation"]
        day, hour = obs["day"], obs.get("hour", 0)
        farm = obs["farms"][0]
        money = farm["money"]
        land = len(farm.get("unlocked_quadrants", ["NW"]))
        hands = len(farm.get("hands", []))

        action = rec.get("action") or {}
        kinds = []
        for a in [action.get("farmer")] + (action.get("hands") or []):
            if a and isinstance(a, list) and a:
                kinds.append(a[0])
        day_counts = action_kind_by_day.setdefault(day, {})
        for k in kinds:
            day_counts[k] = day_counts.get(k, 0) + 1

        if land != prev_land:
            print(f"  day={day:2d} hour={hour:2d}: LAND {prev_land} -> {land}  money=${money:,.2f}")
            prev_land = land
        if hands != prev_hands:
            print(f"  day={day:2d} hour={hour:2d}: HANDS {prev_hands} -> {hands}  money=${money:,.2f}")
            prev_hands = hands

    final_obs = steps[-1][0]["observation"]
    final_money = final_obs["farms"][0]["money"]
    print(f"  FINAL money=${final_money:,.2f}")

    print("  Per-day action-kind tallies (selected days):")
    for day in sorted(action_kind_by_day):
        if day not in (0, 5, 10, 11, 12, 15, 16, 17, 18, 20, 25, 29):
            continue
        counts = action_kind_by_day[day]
        total = sum(counts.values())
        move_ct = counts.get("MOVE_UP", 0) + counts.get("MOVE_DOWN", 0) + counts.get("MOVE_LEFT", 0) + counts.get("MOVE_RIGHT", 0)
        pass_ct = counts.get("PASS", 0)
        work_ct = total - move_ct - pass_ct
        print(f"    day={day:2d}: total_acts={total} move={move_ct} pass={pass_ct} work={work_ct}  {counts}")
    return final_money


def main():
    base = trace("baseline_k (3-quadrant)", make_capped_animal_portfolio_agent)
    cand = trace("fourth_quadrant (4-quadrant)", make_fourth_quadrant_portfolio_agent)
    print(f"\nDelta: ${cand - base:+,.2f} ({(cand - base) / base * 100:+.1f}%)")


if __name__ == "__main__":
    main()
