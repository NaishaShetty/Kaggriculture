"""
Phase 5, section 15: independently validate agents/phase4/market_model.py's
simulate_sell() against the REAL kaggriculture engine, live, not just by
re-reading the source. A scripted agent buys a controlled quantity of
WHEAT (BUY_PRODUCT, which lands directly in the shed, bypassing production
timing so the shed quantity is exactly known) and then sells a controlled
batch of it in one turn, against a "pass" opponent (so no interleaving).
The actual money delta the engine reports is compared against
simulate_sell()'s prediction for the same starting inventory and quantity.

Usage: python scripts/phase5_market_model_validate.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instrumentation.collector import run_episode  # noqa: E402
from agents.phase4.market_model import simulate_sell  # noqa: E402
from vendor_kaggriculture.kaggriculture import MARKET_PARAMS  # noqa: E402

BUY_QTY = 40
SELL_QTY = 40


def scripted_agent(obs, config=None):
    day = obs["day"]
    hour = obs.get("hour", 0)
    if day == 0 and hour == 0:
        return {"market": [["BUY_PRODUCT", "WHEAT", BUY_QTY]]}
    if day == 0 and hour == 1:
        return {"market": [["SELL", "WHEAT", SELL_QTY]]}
    return {}


def main():
    replay, meta = run_episode(scripted_agent, "pass", episode_steps=24, seed=999001)
    steps = replay["steps"]

    # Inventory right before our SELL order (state at end of hour=0, i.e. steps[1]).
    obs_before_sell = steps[1][0]["observation"]
    inv_before = obs_before_sell["market"]["inventory"]["WHEAT"]
    money_before = obs_before_sell["farms"][0]["money"]

    # Money right after the SELL turn is processed (state at end of hour=1, steps[2]).
    obs_after_sell = steps[2][0]["observation"]
    money_after = obs_after_sell["farms"][0]["money"]
    inv_after = obs_after_sell["market"]["inventory"]["WHEAT"]

    actual_sell_revenue = money_after - money_before

    predicted_revenue, predicted_prices, predicted_final_inv = simulate_sell(
        "WHEAT", SELL_QTY, inv_before, MARKET_PARAMS)

    print(f"WHEAT inventory before SELL: {inv_before}")
    print(f"WHEAT inventory after SELL (actual engine): {inv_after}")
    print(f"WHEAT inventory after SELL (simulate_sell predicted): {predicted_final_inv}")
    print(f"Actual engine SELL revenue:      ${actual_sell_revenue:.2f}")
    print(f"simulate_sell predicted revenue: ${predicted_revenue:.2f}")
    print(f"First 5 predicted unit prices: {predicted_prices[:5]}")
    print(f"Last 5 predicted unit prices:  {predicted_prices[-5:]}")

    match = (abs(actual_sell_revenue - predicted_revenue) < 0.01) and (inv_after == predicted_final_inv)
    print(f"\nMARKET SIMULATOR VALIDATION: {'PASS -- exact match' if match else 'FAIL -- MISMATCH, DO NOT TRUST simulate_sell'}")
    return 0 if match else 1


if __name__ == "__main__":
    sys.exit(main())
