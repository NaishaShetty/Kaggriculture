"""
Phase 45 Part A Step 2: cheap 4-seed isolated-economy screen (vs "pass"),
same 4 development seeds every prior phase's cheap screen has used
(scripts/phase3_2_configs.py::SEED_SETS["development"]).

Three candidates:
  - shipped: Submission I exactly as shipped (scripts/phase37/
    paced_portfolio_agent.py, unmodified) -- the reference baseline.
  - seed_paced: shipped targets through the NEW BUY_SEED-paced execution
    layer alone (no CARROT/TOMATO) -- isolates whatever effect the new
    reserve gate has by itself on the existing portfolio.
  - carrot_tomato_seed_paced: the day-0-active CARROT/TOMATO slice, through
    the new pacer -- the actual Part A Step 2 question.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase45.seed_paced_portfolio_agent import make_seed_paced_portfolio_agent  # noqa: E402
from scripts.phase45.carrot_tomato_seed_paced import make_carrot_tomato_seed_paced_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
DEV_SEEDS = SEED_SETS["development"]
OUT_ROOT = "results/phase45"

CANDIDATES = {
    "shipped": make_paced_portfolio_agent,
    "seed_paced": make_seed_paced_portfolio_agent,
    "carrot_tomato_seed_paced": make_carrot_tomato_seed_paced_agent,
}


def run_one(make_agent, seed, label):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    record, _ = analyze_replay(replay, meta, "phase45_isolated", f"{label}_seed{seed}")
    final_money = record["outcome"]["final_money"][0]
    txns = record["players"][0]["financial_transactions"]
    slice_sells = {}
    for item in ("CARROT", "TOMATO"):
        sells = [t for t in txns if t["type"] == "SELL" and t["item"] == item]
        qty = sum(t["quantity"] for t in sells)
        total = sum(t["total"] for t in sells if t["total"] is not None)
        slice_sells[item] = {
            "n_sell_orders": len(sells), "total_qty": qty,
            "total_revenue": round(total, 2),
            "mean_realized_price": round(total / qty, 2) if qty else None,
        }
    return {"seed": seed, "final_money": final_money, "slice_sells": slice_sells}


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    results = {label: [] for label in CANDIDATES}

    for label, make_agent in CANDIDATES.items():
        print(f"=== {label} vs. pass ===")
        for seed in DEV_SEEDS:
            row = run_one(make_agent, seed, label)
            results[label].append(row)
            extra = ""
            if label == "carrot_tomato_seed_paced":
                cs, ts = row["slice_sells"]["CARROT"], row["slice_sells"]["TOMATO"]
                extra = (f"  CARROT: qty={cs['total_qty']} rev=${cs['total_revenue']:,.2f} price={cs['mean_realized_price']}"
                          f"  TOMATO: qty={ts['total_qty']} rev=${ts['total_revenue']:,.2f} price={ts['mean_realized_price']}")
            print(f"  seed={seed}: final_money=${row['final_money']:,.2f}{extra}")

    means = {label: sum(r["final_money"] for r in rows) / len(rows) for label, rows in results.items()}
    print("\n=== SUMMARY (4-seed dev screen) ===")
    base_mean = means["shipped"]
    for label, m in means.items():
        delta = (m - base_mean) / base_mean * 100 if base_mean else 0.0
        print(f"  {label}: mean=${m:,.2f}  delta_vs_shipped={delta:+.2f}%")

    results["summary"] = {label: round(m, 2) for label, m in means.items()}
    results["summary"]["delta_seed_paced_vs_shipped_pct"] = round((means["seed_paced"] - base_mean) / base_mean * 100, 2)
    results["summary"]["delta_carrot_tomato_seed_paced_vs_shipped_pct"] = round(
        (means["carrot_tomato_seed_paced"] - base_mean) / base_mean * 100, 2)

    with open(os.path.join(OUT_ROOT, "phase45_isolated_economy_4seed.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase45_isolated_economy_4seed.json")


if __name__ == "__main__":
    main()
