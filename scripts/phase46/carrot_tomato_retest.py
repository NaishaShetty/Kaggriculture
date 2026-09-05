"""
Phase 46 Step 7: re-test Phase 42's CARROT/TOMATO day-15 slice
(scripts/phase42/carrot_tomato_portfolio.py::make_slice_target_fn, imported
UNCHANGED -- same 6 CARROT + 2 TOMATO tiles, same day-15 start) through
this phase's new capacity-fixed execution layer
(scripts/phase46/feed_priority_execution.py, Part B's FEED tier-0.5
reprioritization -- swapped in for scripts/phase36/paced_execution.py,
which Phase 42's own module used). This directly answers the Phase 46
brief's step 7: does fixing the FEED/WATER scheduling-capacity bottleneck
change the verdict on Phase 42's specific rejected addition (closed
negative there due to a BUY_SEED cash-flow collision, NOT a worker-turn
capacity collision -- so no strong reason to expect this to flip the
result, but the brief calls for checking directly rather than assuming).

Same 4-seed cheap-screen-first discipline as Phase 42 itself.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase42.carrot_tomato_portfolio import make_slice_target_fn  # noqa: E402
from scripts.phase46.feed_priority_execution import make_feed_priority_execution_agent  # noqa: E402
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase46"


def make_carrot_tomato_through_feed_priority_agent():
    opponent_logger = OpponentObservationLogger()
    target_fn = make_slice_target_fn()  # CARROT=6, TOMATO=2, slice_start_day=15 -- Phase 42's own defaults, unchanged
    execution_agent = make_feed_priority_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent


def run_one(make_agent, seed, label):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    record, _ = analyze_replay(replay, meta, "phase46_carrot_tomato_retest", f"{label}_seed{seed}")
    final_money = record["outcome"]["final_money"][0]
    txns = record["players"][0]["financial_transactions"]
    slice_sells = {}
    for item in ("CARROT", "TOMATO"):
        sells = [t for t in txns if t["type"] == "SELL" and t["item"] == item]
        qty = sum(t["quantity"] for t in sells)
        total = sum(t["total"] for t in sells if t["total"] is not None)
        slice_sells[item] = {"n_sell_orders": len(sells), "total_qty": qty, "total_revenue": round(total, 2),
                              "mean_realized_price": round(total / qty, 2) if qty else None}
    return {"seed": seed, "final_money": final_money, "slice_sells": slice_sells}


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    results = {"baseline_shipped": [], "baseline_feed_priority_no_slice": [], "carrot_tomato_through_feed_priority": []}

    print("=== Baseline A: Submission I shipped (Phase 36 pacer, no slice) vs. pass ===")
    for seed in DEV_SEEDS:
        row = run_one(make_paced_portfolio_agent, seed, "shipped")
        results["baseline_shipped"].append(row)
        print(f"  seed={seed}: final_money=${row['final_money']:,.2f}")

    print("\n=== Variant: CARROT/TOMATO day-15 slice THROUGH the new FEED-priority execution layer vs. pass ===")
    for seed in DEV_SEEDS:
        row = run_one(make_carrot_tomato_through_feed_priority_agent, seed, "slice_through_feed_priority")
        results["carrot_tomato_through_feed_priority"].append(row)
        cs, ts = row["slice_sells"]["CARROT"], row["slice_sells"]["TOMATO"]
        print(f"  seed={seed}: final_money=${row['final_money']:,.2f}  "
              f"CARROT: qty={cs['total_qty']} rev=${cs['total_revenue']:,.2f} price={cs['mean_realized_price']}  "
              f"TOMATO: qty={ts['total_qty']} rev=${ts['total_revenue']:,.2f} price={ts['mean_realized_price']}")

    mean_base = sum(r["final_money"] for r in results["baseline_shipped"]) / len(results["baseline_shipped"])
    mean_var = sum(r["final_money"] for r in results["carrot_tomato_through_feed_priority"]) / len(results["carrot_tomato_through_feed_priority"])
    delta_pct = (mean_var - mean_base) / mean_base * 100
    print(f"\n  Mean baseline (shipped): ${mean_base:,.2f}")
    print(f"  Mean CARROT/TOMATO slice through FEED-priority layer: ${mean_var:,.2f}")
    print(f"  Delta: {delta_pct:+.2f}%  (Phase 42's own original day-15 result: +0.08%, statistical wash)")

    results["summary"] = {"mean_baseline_shipped": round(mean_base, 2), "mean_variant": round(mean_var, 2),
                           "delta_pct": round(delta_pct, 2)}
    with open(os.path.join(OUT_ROOT, "phase46_carrot_tomato_retest_4seed.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase46_carrot_tomato_retest_4seed.json")


if __name__ == "__main__":
    main()
