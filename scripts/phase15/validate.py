"""
Phase 15 validation: three escalating tiers per the brief.
  (a) sanity: synthetic archetype battery, confirm no catastrophic failure.
  (b) head-to-head: isolated (vs "pass") final money, then live vs Submission C
      and Submission E, same 4 development seeds (700000-700003).
  (c) the real bar: report vs the $50-80k target and vs Phase 6's real opponent
      final banks.

New code only. Does not touch any frozen file.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

DEV_SEEDS = [700000, 700001, 700002, 700003]
STEPS = 720
OUT_ROOT = "results/phase15"

REAL_OPPONENT_FINAL_MONEY = {
    # From results/phase6/*/days_opponent.csv, day==29 row (final in-game day), "bank" column.
    "moushun_chen": 63798.0,
    "lai_eu_wen": 104569.0,
    "achille_gohin": 76076.0,
    "zach_locke": 83904.0,
}


def tier_a_sanity():
    print("=== TIER A: synthetic archetype sanity ===")
    results = {}
    for name, factory in OPPONENT_CLASSES.items():
        agent = make_macro_agent()
        opp = factory()
        replay, meta = run_episode(agent, opp, STEPS, 700000, None)
        money = replay["rewards"][0]
        crashed = money is None
        results[name] = {"final_money": money, "crashed": crashed}
        print(f"  {name:<22} final_money={money} crashed={crashed}")
    return results


def tier_b_head_to_head():
    print("\n=== TIER B: isolated + head-to-head vs Submission C / Submission E ===")
    results = {"isolated": [], "vs_submission_c": [], "vs_submission_e": []}
    for seed in DEV_SEEDS:
        agent = make_macro_agent()
        replay, _ = run_episode(agent, "pass", STEPS, seed, None)
        results["isolated"].append({"seed": seed, "final_money": replay["rewards"][0]})
        print(f"  isolated seed={seed}: {replay['rewards'][0]}")

    for seed in DEV_SEEDS:
        agent15 = make_macro_agent()
        agentC = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=False)  # Submission C (no F-005 guard)
        replay, _ = run_episode(agent15, agentC, STEPS, seed, None)
        results["vs_submission_c"].append({"seed": seed, "ours": replay["rewards"][0], "theirs": replay["rewards"][1]})
        print(f"  vs Submission C seed={seed}: ours={replay['rewards'][0]} theirs={replay['rewards'][1]}")

    for seed in DEV_SEEDS:
        agent15 = make_macro_agent()
        agentE = make_competitive_v3_agent(trace_path=None)  # Submission E (liquidity_guard_enabled=True, default)
        replay, _ = run_episode(agent15, agentE, STEPS, seed, None)
        results["vs_submission_e"].append({"seed": seed, "ours": replay["rewards"][0], "theirs": replay["rewards"][1]})
        print(f"  vs Submission E seed={seed}: ours={replay['rewards'][0]} theirs={replay['rewards'][1]}")

    return results


def tier_c_real_bar(tier_b_results):
    print("\n=== TIER C: the real bar ===")
    isolated_moneys = [r["final_money"] for r in tier_b_results["isolated"]]
    mean_isolated = sum(isolated_moneys) / len(isolated_moneys)
    print(f"  Mean isolated final money (4 dev seeds): ${mean_isolated:,.2f}")
    print(f"  Target bar: $50,000-80,000+")
    print(f"  Bar cleared: {mean_isolated >= 50000}")
    for name, money in REAL_OPPONENT_FINAL_MONEY.items():
        print(f"  vs {name}: real opponent finished at ${money:,.2f}; our mean isolated ${mean_isolated:,.2f} "
              f"({'above' if mean_isolated > money else 'below'})")
    return {"mean_isolated": mean_isolated, "bar_cleared": mean_isolated >= 50000,
            "real_opponent_final_money": REAL_OPPONENT_FINAL_MONEY}


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    a = tier_a_sanity()
    b = tier_b_head_to_head()
    c = tier_c_real_bar(b)
    out = {"tier_a_sanity": a, "tier_b_head_to_head": b, "tier_c_real_bar": c}
    with open(os.path.join(OUT_ROOT, "phase15_validation_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote results to {OUT_ROOT}/phase15_validation_results.json")


if __name__ == "__main__":
    main()
