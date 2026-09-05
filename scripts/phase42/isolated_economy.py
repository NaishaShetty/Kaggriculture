"""
Phase 42 Step 1: cheap 4-seed isolated-economy screen -- Submission I
(shipped, unmodified) vs. the CARROT/TOMATO slice variant, both vs. "pass",
same 4 development seeds every prior phase's cheap screen has used.

Reports net final money AND realized CARROT/TOMATO sell price/volume (to
directly check the glut-headroom calibration in
scripts/phase42/carrot_tomato_portfolio.py's own docstring, not just assume
it holds).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase42.carrot_tomato_portfolio import make_carrot_tomato_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase42"


def run_one(make_agent, seed, label):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    record, _ = analyze_replay(replay, meta, "phase42_isolated", f"{label}_seed{seed}")
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
    results = {"baseline": [], "variant": []}

    print("=== Baseline: Submission I (shipped, unmodified) vs. pass ===")
    for seed in DEV_SEEDS:
        row = run_one(make_paced_portfolio_agent, seed, "baseline")
        results["baseline"].append(row)
        print(f"  seed={seed}: final_money=${row['final_money']:,.2f}")

    print("\n=== Variant: Submission I + CARROT/TOMATO slice vs. pass ===")
    for seed in DEV_SEEDS:
        row = run_one(make_carrot_tomato_agent, seed, "variant")
        results["variant"].append(row)
        cs, ts = row["slice_sells"]["CARROT"], row["slice_sells"]["TOMATO"]
        print(f"  seed={seed}: final_money=${row['final_money']:,.2f}  "
              f"CARROT: qty={cs['total_qty']} rev=${cs['total_revenue']:,.2f} price={cs['mean_realized_price']}  "
              f"TOMATO: qty={ts['total_qty']} rev=${ts['total_revenue']:,.2f} price={ts['mean_realized_price']}")

    mean_base = sum(r["final_money"] for r in results["baseline"]) / len(results["baseline"])
    mean_var = sum(r["final_money"] for r in results["variant"]) / len(results["variant"])
    delta_pct = (mean_var - mean_base) / mean_base * 100
    print(f"\n  Mean baseline: ${mean_base:,.2f}")
    print(f"  Mean variant:  ${mean_var:,.2f}")
    print(f"  Delta: {delta_pct:+.2f}%")

    results["summary"] = {"mean_baseline": round(mean_base, 2), "mean_variant": round(mean_var, 2),
                           "delta_pct": round(delta_pct, 2)}
    with open(os.path.join(OUT_ROOT, "phase42_isolated_economy_4seed.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase42_isolated_economy_4seed.json")


if __name__ == "__main__":
    main()
