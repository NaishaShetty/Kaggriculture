"""
Phase 3.3 intervention experiment runner. Runs a named variant (from
agents/phase3_3/interventions.py, or "B_detection_only" for the inert
control-with-logging variant) against a named opponent archetype, across a
named seed set. Variant A (frozen Planner v1, unmodified) is NEVER re-run
here -- its data already exists in results/phase3_2/experiments/
episode_metadata.csv (identical seeds/opponents/steps), reused directly for
paired comparison, per the project's "don't re-run what's already measured"
discipline.

Usage:
    python scripts/phase3_3_run_experiments.py --variant C_melon_avoidance --opponent expansion_oriented --seed-set development
"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_3.adapters.intervention_agent import make_intervention_agent  # noqa: E402
from agents.phase3_3.interventions import INTERVENTIONS  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_2_configs import STEPS, SEED_SETS, ARCHETYPES  # noqa: E402

OUT_ROOT = "results/phase3_3"


def run_one(variant, opponent_name, seed, seed_set_name):
    fn = INTERVENTIONS[variant]
    opponent = OPPONENT_CLASSES[opponent_name]()
    trace_path = os.path.join(OUT_ROOT, "traces", f"{variant}_{opponent_name}_seed{seed}.jsonl")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    if os.path.exists(trace_path):
        os.remove(trace_path)
    agent = make_intervention_agent(intervention_fn=fn, trace_path=trace_path)

    t0 = time.time()
    record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                 f"phase3_3_{variant}_{opponent_name}", f"seed{seed}")
    agent._planner._tracer.close()

    outcome = record["outcome"]
    protagonist_money, opponent_money = outcome["final_money"]

    melon_metrics = record["players"][0]["crop_metrics"].get("MELON", {})
    fin = record["players"][0]["financial_summary"]
    melon_sell_txns = [t for t in record["players"][0]["financial_transactions"]
                       if t["type"] == "SELL" and t["item"] == "MELON"]
    melon_sold = sum(t["quantity"] for t in melon_sell_txns)
    melon_revenue = sum(t["total"] or 0 for t in melon_sell_txns)
    melon_avg_price = round(melon_revenue / melon_sold, 2) if melon_sold else None

    row = {
        "variant": variant, "opponent": opponent_name, "seed": seed, "seed_set": seed_set_name,
        "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
        "margin": round(protagonist_money - opponent_money, 2),
        "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
        "validation": record["players"][0]["validation"]["overall"],
        "total_revenue": fin["total_income"], "total_cost": fin["total_expenditure"],
        "melon_harvested": melon_metrics.get("total_harvested_units", 0),
        "melon_sold": melon_sold, "melon_unsold": melon_metrics.get("total_harvested_units", 0) - melon_sold,
        "melon_revenue": round(melon_revenue, 2), "melon_avg_sell_price": melon_avg_price,
        "n_activations": agent._state_ref["n_activations"],
        "first_activation_turn": agent._state_ref["first_activation_turn"],
        "elapsed_s": round(time.time() - t0, 2),
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(INTERVENTIONS))
    ap.add_argument("--opponent", required=True, choices=ARCHETYPES)
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    args = ap.parse_args()

    rows = []
    for seed in SEED_SETS[args.seed_set]:
        row = run_one(args.variant, args.opponent, seed, args.seed_set)
        rows.append(row)
        print(f"  [{args.variant}/{args.opponent}] seed={seed} ({args.seed_set}) "
              f"protagonist=${row['protagonist_final_money']} opponent=${row['opponent_final_money']} "
              f"win={row['win']} melon_avg_price={row['melon_avg_sell_price']} "
              f"activations={row['n_activations']} ({row['elapsed_s']}s)", flush=True)

    out_csv = os.path.join(OUT_ROOT, "experiments", "intervention_results.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    file_exists = os.path.exists(out_csv)
    with open(out_csv, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows to {out_csv}")


if __name__ == "__main__":
    main()
