"""
Phase 45 Part A Step 2 (diagnosis add-on): direct trace of WHY the day-0
CARROT/TOMATO slice, even through the new BUY_SEED-paced execution layer, is
still a mean -25.4% loss on the 4-seed screen (down from Phase 42's -37.4%
unpaced, but still clearly negative) -- same style of direct cash/land-timing
trace Phase 42 itself used, on the same seed 700003 Phase 42 traced.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase45.carrot_tomato_seed_paced import make_carrot_tomato_seed_paced_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
SEED = 700003


def trace_one(label, make_agent):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, SEED, None)
    record, _ = analyze_replay(replay, meta, "phase45_trace", f"{label}_seed{SEED}")
    daily = record["players"][0]["daily_summary"]
    print(f"--- {label} (final_money=${replay['rewards'][0]:,.2f}) ---")
    ending_money = [d["ending_money"] for d in daily]
    print("  ending_money by day 0-20:", [round(m, 0) for m in ending_money[:21]])
    land_buy_days = [d["day"] for d in daily if d.get("land_purchased")]
    print(f"  BUY_LAND days: {land_buy_days}")
    seed_spend = [round(d.get("seeds_purchased", 0)) for d in daily[:21]]
    print(f"  seeds_purchased (units) by day 0-20: {seed_spend}")
    return record


def main():
    trace_one("baseline (shipped)", make_paced_portfolio_agent)
    trace_one("variant (day-0 CARROT/TOMATO, seed-paced)", make_carrot_tomato_seed_paced_agent)


if __name__ == "__main__":
    main()
