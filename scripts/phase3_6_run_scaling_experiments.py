"""
Phase 3.6-B/C: run any adaptive-response candidate (B0-B5) against any
scaling-intensity archetype (scaler_5/7/10, or Phase 3.5's heavy_scaler),
across a named seed set. Paired same-seed design: run ALL candidates on
the SAME seeds for direct comparison.

Usage:
    python scripts/phase3_6_run_scaling_experiments.py --candidate B1_absolute_proportional --opponent scaler_10 --seed-set development
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_6.adapters.adaptive_agent import make_adaptive_agent  # noqa: E402
from agents.phase3_6.response_policy_v2 import CANDIDATES  # noqa: E402
from agents.phase3_6.opponent_classes_scaling_ladder import OPPONENT_CLASSES_SCALING_LADDER  # noqa: E402
from agents.phase3_5.opponent_classes_extended import OPPONENT_CLASSES_EXTENDED  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_6_configs import STEPS, SEED_SETS  # noqa: E402

OUT_ROOT = "results/phase3_6"
ALL_OPPONENTS = {**OPPONENT_CLASSES, **OPPONENT_CLASSES_EXTENDED, **OPPONENT_CLASSES_SCALING_LADDER}


def run_one(candidate, opponent_name, seed, seed_set_name):
    opponent = ALL_OPPONENTS[opponent_name]()
    trace_path = os.path.join(OUT_ROOT, "traces", f"{candidate}_{opponent_name}_seed{seed}.jsonl")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    if os.path.exists(trace_path):
        os.remove(trace_path)
    agent = make_adaptive_agent(candidate_name=candidate, trace_path=None)

    t0 = time.time()
    record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                 f"phase3_6_{candidate}_{opponent_name}", f"seed{seed}")

    outcome = record["outcome"]
    protagonist_money, opponent_money = outcome["final_money"]
    row = {
        "candidate": candidate, "opponent": opponent_name, "seed": seed, "seed_set": seed_set_name,
        "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
        "margin": round(protagonist_money - opponent_money, 2),
        "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
        "market_activations": agent._state_ref["market_activations"],
        "scaling_activations": agent._state_ref["scaling_activations"],
        "first_scaling_activation_turn": agent._state_ref["first_scaling_activation_turn"],
        "elapsed_s": round(time.time() - t0, 2),
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True, choices=list(CANDIDATES))
    ap.add_argument("--opponent", required=True, choices=list(ALL_OPPONENTS))
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    args = ap.parse_args()

    rows = []
    for seed in SEED_SETS[args.seed_set]:
        row = run_one(args.candidate, args.opponent, seed, args.seed_set)
        rows.append(row)
        print(f"  [{args.candidate}/{args.opponent}] seed={seed} ({args.seed_set}) "
              f"protagonist=${row['protagonist_final_money']} opponent=${row['opponent_final_money']} "
              f"win={row['win']} scaling_act={row['scaling_activations']} first_turn={row['first_scaling_activation_turn']} "
              f"({row['elapsed_s']}s)", flush=True)

    out_csv = os.path.join(OUT_ROOT, "experiments", "scaling_results.csv")
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
