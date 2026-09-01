"""
Phase 3.4 Stage-1 candidate screening. Reuses the EXACT Phase 3.3 harness
(agents/phase3_3/adapters/intervention_agent.make_intervention_agent,
instrumentation.pipeline.run_and_analyze) so results are directly comparable
to results/phase3_3/experiments/intervention_results.csv (same seeds, same
opponent factories, same trace schema). Only the intervention function
differs (agents/phase3_4/response_policy.py::CANDIDATES).

Usage:
    python scripts/phase3_4_run_candidates.py --candidate C_diversified_substitution --seed-set development
    python scripts/phase3_4_run_candidates.py --candidate E_partial_melon_retention --opponent expansion_oriented --seed-set held_out
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_3.adapters.intervention_agent import make_intervention_agent  # noqa: E402
from agents.phase3_4.response_policy import CANDIDATES  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_2_configs import STEPS, SEED_SETS, ARCHETYPES  # noqa: E402

OUT_ROOT = "results/phase3_4"


def run_one(candidate, opponent_name, seed, seed_set_name):
    fn = CANDIDATES[candidate]
    opponent = OPPONENT_CLASSES[opponent_name]()
    trace_path = os.path.join(OUT_ROOT, "traces", f"{candidate}_{opponent_name}_seed{seed}.jsonl")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    if os.path.exists(trace_path):
        os.remove(trace_path)
    agent = make_intervention_agent(intervention_fn=fn, trace_path=trace_path)

    t0 = time.time()
    record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                 f"phase3_4_{candidate}_{opponent_name}", f"seed{seed}")
    agent._planner._tracer.close()

    outcome = record["outcome"]
    protagonist_money, opponent_money = outcome["final_money"]
    strawberry_txns = [t for t in record["players"][0]["financial_transactions"]
                        if t["type"] == "SELL" and t["item"] == "STRAWBERRY"]
    strawberry_sold = sum(t["quantity"] for t in strawberry_txns)
    strawberry_revenue = sum(t["total"] or 0 for t in strawberry_txns)
    strawberry_avg_price = round(strawberry_revenue / strawberry_sold, 2) if strawberry_sold else None
    melon_txns = [t for t in record["players"][0]["financial_transactions"]
                  if t["type"] == "SELL" and t["item"] == "MELON"]
    melon_revenue = sum(t["total"] or 0 for t in melon_txns)

    row = {
        "candidate": candidate, "opponent": opponent_name, "seed": seed, "seed_set": seed_set_name,
        "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
        "margin": round(protagonist_money - opponent_money, 2),
        "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
        "strawberry_sold": strawberry_sold, "strawberry_revenue": round(strawberry_revenue, 2),
        "strawberry_avg_sell_price": strawberry_avg_price, "melon_revenue": round(melon_revenue, 2),
        "n_activations": agent._state_ref["n_activations"],
        "elapsed_s": round(time.time() - t0, 2),
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True, choices=list(CANDIDATES))
    ap.add_argument("--opponent", default="expansion_oriented", choices=ARCHETYPES)
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    args = ap.parse_args()

    rows = []
    for seed in SEED_SETS[args.seed_set]:
        row = run_one(args.candidate, args.opponent, seed, args.seed_set)
        rows.append(row)
        print(f"  [{args.candidate}/{args.opponent}] seed={seed} ({args.seed_set}) "
              f"protagonist=${row['protagonist_final_money']} opponent=${row['opponent_final_money']} "
              f"win={row['win']} strawberry_avg_price={row['strawberry_avg_sell_price']} "
              f"({row['elapsed_s']}s)", flush=True)

    out_csv = os.path.join(OUT_ROOT, "candidate_experiments", "candidate_results.csv")
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
