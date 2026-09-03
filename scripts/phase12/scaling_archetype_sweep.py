"""Phase 12 scaling-archetype sweep -- guard ENABLED vs DISABLED against
heavy_scaler/scaler_5/scaler_7/scaler_10 (the same archetypes + seeds Phase
3.8's own validation record used: results/phase3_8/phase3_8_VALIDATION.md
Section B, seeds 950001-950002 dev + 960001-960002 held-out).
Run: python -m scripts.phase12.scaling_archetype_sweep
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent
from agents.phase3_5.opponent_classes_extended import OPPONENT_CLASSES_EXTENDED
from agents.phase3_6.opponent_classes_scaling_ladder import OPPONENT_CLASSES_SCALING_LADDER
from instrumentation.pipeline import run_and_analyze

ALL_SCALERS = {**OPPONENT_CLASSES_EXTENDED, **OPPONENT_CLASSES_SCALING_LADDER}
SEEDS = [950001, 950002, 960001, 960002]
EPISODE_STEPS = 300


def run_one(name, seed, guard_enabled):
    agent = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=guard_enabled)
    opp = ALL_SCALERS[name]()
    tag = f"guard_{'on' if guard_enabled else 'off'}"
    record, _, _ = run_and_analyze(agent, opp, EPISODE_STEPS, seed, "phase12_scaling_sweep", tag)
    return record["outcome"]["final_money"][0], agent._state_ref["liquidity_guard_activations"]


def main():
    print(f"{'archetype':<16}{'seed':<10}{'off':<12}{'on':<12}{'delta':<12}{'fired':<8}")
    regressions, improvements = [], []
    for name in ALL_SCALERS:
        for seed in SEEDS:
            money_off, _ = run_one(name, seed, False)
            money_on, fired = run_one(name, seed, True)
            delta = money_on - money_off
            flag = ""
            if delta < -1e-6:
                flag = "REGRESSION"
                regressions.append((name, seed, money_off, money_on))
            elif delta > 1e-6:
                flag = "improved"
                improvements.append((name, seed, money_off, money_on))
            print(f"{name:<16}{seed:<10}{money_off:<12.1f}{money_on:<12.1f}{delta:<+12.1f}{fired:<8}{flag}")
    print(f"\nTotal comparisons: {len(ALL_SCALERS) * len(SEEDS)}")
    print(f"Regressions: {len(regressions)}")
    for r in regressions:
        print(f"  {r}")
    print(f"Improvements: {len(improvements)}")
    for i in improvements:
        print(f"  {i}")


if __name__ == "__main__":
    main()
