"""
Phase 51: direct trace of the sanity-check regression found in
isolated_screen_sanity.py -- confirms, rather than assumes, WHY gating HIRE
against `money - land_purchase_reserve` collapses Submission K's own
unmodified portfolio by ~89%. Prints day-by-day hand count, money, and land
quadrants owned for one seed (700002, the same seed used for continuity with
Phase 33/48's own SE-quadrant trace) under both the baseline and the
HIRE-paced execution layer.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase48.capped_animal_portfolio_agent import make_capped_animal_portfolio_agent  # noqa: E402
from scripts.phase51.hire_paced_capped_animal_portfolio_agent import make_hire_paced_capped_animal_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
SEED = 700002
TURNS_PER_DAY = 24


def trace(label, agent_factory):
    agent = agent_factory()
    replay, meta = run_episode(agent, "pass", STEPS, SEED, None)
    print(f"\n=== {label} (seed={SEED}) ===")
    print(f"{'day':>4} {'hands':>6} {'money':>10} {'quadrants':>10}")
    for day in range(30):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= len(replay["steps"]):
            break
        obs = replay["steps"][t][0]["observation"]
        me = obs["farms"][0]
        hands = len(me.get("hands", []))
        money = me["money"]
        quads = len(me.get("unlocked_quadrants", [])) - 1
        if day % 2 == 0 or day >= 25:
            print(f"{day:>4} {hands:>6} {money:>10.2f} {quads:>10}")
    final = replay["rewards"][0]
    print(f"final_money=${final:.2f}")
    return replay


if __name__ == "__main__":
    trace("baseline (Submission K, unpaced HIRE)", make_capped_animal_portfolio_agent)
    trace("hire_paced (reserve-gated HIRE)", make_hire_paced_capped_animal_portfolio_agent)
