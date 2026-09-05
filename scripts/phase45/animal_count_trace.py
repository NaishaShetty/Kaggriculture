"""
Phase 45 Part A, Step 3: direct trace of WHY Submission I's own final animal
count sits flat at 7-9 across real games despite agents/phase21/portfolio.py
::_ANIMALS_RUNGS targeting up to 17 by day 11 (Phase 41's own noted-but-
untraced open question). Traces 2 seeds -- one isolated (vs "pass") and one
head-to-head vs. Submission G -- reading `agents/phase21/execution.py`'s own
BUY_ANIMAL mechanics (via Phase 36's pacer, Submission I's actual shipped
execution layer) directly: money trajectory, the pacer's own
animal_reserve_now() value at each purchase attempt, animals purchased vs.
escaped (agents/phase2_3/common.py's animal_level_metrics), and FEED spend.

Nothing here modifies agents/phase21/ or scripts/phase36/ -- this is a
read-only instrumentation wrapper around the SAME unmodified shipped agent
factory (scripts/phase37/paced_portfolio_agent.py::make_paced_portfolio_agent).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets, _ANIMAL_SPECIES_RUNGS, _rung_value  # noqa: E402
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
SEEDS = [700000, 701002]


def trace(seed, opponent_label, make_opponent):
    ours = make_paced_portfolio_agent()
    theirs = "pass" if make_opponent is None else make_opponent()
    replay, meta = run_episode(ours, theirs, STEPS, seed, None)
    record, _ = analyze_replay(replay, meta, "phase45_animal_trace", f"seed{seed}_{opponent_label}")
    daily = record["players"][0]["daily_summary"]
    animal_metrics = record["players"][0].get("animal_metrics", {})

    print(f"\n=== seed={seed} vs {opponent_label}: final_money=${replay['rewards'][0]:,.2f} ===")
    print("  day | ending_money | animals_purchased_that_day | target_animal_total (per _ANIMAL_SPECIES_RUNGS)")
    for d in daily[:22]:
        day = d["day"]
        target_total = sum(_rung_value(day, _ANIMAL_SPECIES_RUNGS).values()) if False else None
        target_dict = _rung_value(day, _ANIMAL_SPECIES_RUNGS)
        target_total = sum(target_dict.values())
        print(f"    {day:>3} | ${d['ending_money']:>9,.0f} | {d.get('animals_purchased', 0):>3} | target={target_total}")

    print("  --- animal_metrics (purchased vs escaped/final, per species) ---")
    total_purchased, total_escaped = 0, 0
    for animal, rec in animal_metrics.items():
        purchased = rec.get("purchased", 0)
        escaped = rec.get("n_escaped", 0)
        placed = rec.get("n_placed", 0)
        total_purchased += purchased
        total_escaped += escaped
        print(f"    {animal}: purchased={purchased}  n_placed={placed}  n_escaped={escaped}")
    print(f"  TOTALS: purchased={total_purchased}  escaped={total_escaped}  net={total_purchased - total_escaped}")

    total_feed_spend = sum(1 for d in daily for _ in range(0) )  # placeholder, feed cost tracked via BUY_PRODUCT below
    wheat_buys = [t for t in record["players"][0]["financial_transactions"] if t["type"] == "BUY_PRODUCT" and t["item"] == "WHEAT"]
    total_wheat_spend = sum(t["total"] for t in wheat_buys if t["total"] is not None)
    print(f"  Total BUY_PRODUCT:WHEAT spend (feed top-up via market): ${total_wheat_spend:,.2f} over {len(wheat_buys)} orders")


def main():
    trace(700000, "pass (isolated)", None)
    trace(701002, "Submission G", make_macro_agent)


if __name__ == "__main__":
    main()
