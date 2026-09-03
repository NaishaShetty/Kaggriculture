"""
Phase 12 archetype sweep: guard ENABLED vs DISABLED, across the same
archetype battery + seed sets Phase 3.8 used (results/phase3_8_VALIDATION.md
Sections B/D): passive, production_heavy, market_selling, expansion_oriented,
animal_oriented, conservative, aggressive_investment, at seeds
950001/950002 (dev) + 960001/960002 (held-out).

Since Phase 12's own regression tests found the widened guard's day==3 check
crosses CASH_DANGER_THRESHOLD in EVERY archetype tried so far (Planner v1's
day-0 commitment routinely dips cash into a $0-100 trough by day 3 -- this is
the exact "routine, not anomalous" trough Phase 3.7-C already documented,
not a rare crisis signal), "inert" in the literal never-fires sense will not
hold. What this sweep actually checks is the criterion that matters: does the
guard ever make a game's final money WORSE than it would have been without it?
Run: python -m scripts.phase12.archetype_sweep
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent
from agents.phase3.opponent_classes import OPPONENT_CLASSES
from instrumentation.pipeline import run_and_analyze

ARCHETYPES = ["passive", "production_heavy", "market_selling", "expansion_oriented",
              "animal_oriented", "conservative", "aggressive_investment"]
SEEDS = [950001, 950002, 960001, 960002]
EPISODE_STEPS = 300


def run_one(archetype, seed, guard_enabled):
    agent = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=guard_enabled)
    opp = OPPONENT_CLASSES[archetype]()
    tag = f"guard_{'on' if guard_enabled else 'off'}"
    record, _, _ = run_and_analyze(agent, opp, EPISODE_STEPS, seed, "phase12_sweep", tag)
    return record["outcome"]["final_money"][0], agent._state_ref["liquidity_guard_activations"]


def main():
    print(f"{'archetype':<22}{'seed':<10}{'off':<12}{'on':<12}{'delta':<12}{'fired':<8}")
    regressions = []
    improvements = []
    for archetype in ARCHETYPES:
        for seed in SEEDS:
            money_off, _ = run_one(archetype, seed, False)
            money_on, fired = run_one(archetype, seed, True)
            delta = money_on - money_off
            flag = ""
            if delta < -1e-6:
                flag = "REGRESSION"
                regressions.append((archetype, seed, money_off, money_on))
            elif delta > 1e-6:
                flag = "improved"
                improvements.append((archetype, seed, money_off, money_on))
            print(f"{archetype:<22}{seed:<10}{money_off:<12.1f}{money_on:<12.1f}{delta:<+12.1f}"
                  f"{fired:<8}{flag}")

    print(f"\nTotal comparisons: {len(ARCHETYPES) * len(SEEDS)}")
    print(f"Regressions (guard made final money worse): {len(regressions)}")
    for r in regressions:
        print(f"  {r}")
    print(f"Improvements: {len(improvements)}")
    for i in improvements:
        print(f"  {i}")


if __name__ == "__main__":
    main()
