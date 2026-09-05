"""
Phase 49 Step 1 diagnosis: the isolated-economy sanity screen
(sanity_check_isolated.py) found the combined execution layer (BOTH Phase
45's BUY_SEED pacer AND Phase 46's FEED tier-0.5 fix) at -9.47% mean vs.
shipped -- worse than EITHER fix alone (seed_paced -0.41%, feed_priority
+0.72%). This traces WHY on seed 700001, the seed where combined ($55,908)
underperforms both shipped ($76,683) AND both individual fixes
(seed_paced $64,178, feed_priority $64,409) by the widest margin.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase45.seed_paced_portfolio_agent import make_seed_paced_portfolio_agent  # noqa: E402
from scripts.phase46.feed_priority_portfolio_agent import make_feed_priority_portfolio_agent  # noqa: E402
from scripts.phase49.combined_portfolio_agent import make_combined_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
SEED = 700001

CANDIDATES = {
    "shipped": make_paced_portfolio_agent,
    "seed_paced": make_seed_paced_portfolio_agent,
    "feed_priority": make_feed_priority_portfolio_agent,
    "combined": make_combined_portfolio_agent,
}


def trace_one(label, make_agent):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, SEED, None)
    record, _ = analyze_replay(replay, meta, "phase49_trace", f"{label}_seed{SEED}")
    daily = record["players"][0]["daily_summary"]
    action_eff = record["players"][0]["action_efficiency"]
    animal_metrics = record["players"][0]["animal_metrics"]
    print(f"--- {label} (final_money=${replay['rewards'][0]:,.2f}) ---")
    ending_money = [d["ending_money"] for d in daily]
    print("  ending_money by day 0-20:", [round(m, 0) for m in ending_money[:21]])
    land_buy_days = [d["day"] for d in daily if d.get("land_purchased")]
    print(f"  BUY_LAND days: {land_buy_days}")
    seed_spend = [round(d.get("seeds_purchased", 0)) for d in daily[:21]]
    print(f"  seeds_purchased (units) by day 0-20: {seed_spend}")
    print(f"  idle_fraction: {action_eff['idle_fraction']}  animal_fraction: {action_eff['animal_fraction']}"
          f"  crop_fraction: {action_eff['crop_fraction']}")
    market_orders = action_eff["market_by_category"]
    print(f"  market_by_category: {market_orders}")
    total_purchased = sum(v.get("purchased", 0) for v in animal_metrics.values())
    total_escaped = sum(v.get("n_escaped", 0) for v in animal_metrics.values())
    print(f"  animals purchased={total_purchased} escaped={total_escaped} net={total_purchased - total_escaped}")
    for animal, rec in animal_metrics.items():
        print(f"    {animal}: purchased={rec.get('purchased', 0)} escaped={rec.get('n_escaped', 0)} placed={rec.get('n_placed', 0)}")
    return record


def main():
    for label, make_agent in CANDIDATES.items():
        trace_one(label, make_agent)
        print()


if __name__ == "__main__":
    main()
