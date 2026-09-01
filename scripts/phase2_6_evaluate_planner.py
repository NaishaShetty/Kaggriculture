"""
Phase 2.6 planner evaluation harness (brief section 33.13). Runs Economic
Planner v1 head-to-head against each of the 3 baselines
(scripts/phase2_6_baselines.py) across three DISJOINT seed sets:

  development  -- used for debugging/iteration (not for the final gate)
  validation   -- used to select/confirm the planner variant (not for the
                  final gate either)
  held-out     -- used ONLY for the final Phase 2.6 gate decision; never
                  looked at before this script's held-out run, and the
                  planner is not modified in response to held-out results
                  (brief section 23's explicit anti-tuning discipline)

Usage:
    python scripts/phase2_6_evaluate_planner.py --seed-set development
    python scripts/phase2_6_evaluate_planner.py --seed-set validation
    python scripts/phase2_6_evaluate_planner.py --seed-set held_out
"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_6.common import make_agent as make_planner  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase2_6_baselines import BASELINES  # noqa: E402

STEPS = 720
OUT_ROOT = "results/phase2_6/planner_v1"

SEED_SETS = {
    "development": list(range(300000, 300005)),   # n=5
    "validation": list(range(301000, 301008)),     # n=8
    "held_out": list(range(302000, 302010)),       # n=10 -- never used until the final gate
}

FIELDNAMES = [
    "seed_set", "opponent", "seed", "planner_money", "opponent_money", "margin", "win",
    "planner_validation", "n_planning_cycles", "n_hard_blocked", "n_economic_rejected",
    "n_uncertain", "n_selected_total",
]


def summarize_trace(trace_path):
    if not os.path.exists(trace_path):
        return {"n_planning_cycles": 0, "n_hard_blocked": 0, "n_economic_rejected": 0,
                "n_uncertain": 0, "n_selected_total": 0}
    n_cycles = n_hard = n_econ = n_unc = n_sel = 0
    with open(trace_path) as f:
        for line in f:
            rec = json.loads(line)
            n_cycles += 1
            n_sel += len(rec["selected_decisions"])
            for c in rec["candidate_opportunities"]:
                cat = c["classification"]["category"]
                if cat == "HARD":
                    n_hard += 1
                elif cat == "ECONOMIC":
                    n_econ += 1
                elif cat == "UNCERTAIN":
                    n_unc += 1
    return {"n_planning_cycles": n_cycles, "n_hard_blocked": n_hard, "n_economic_rejected": n_econ,
            "n_uncertain": n_unc, "n_selected_total": n_sel}


def run_seed_set(seed_set_name):
    seeds = SEED_SETS[seed_set_name]
    rows = []
    for opponent_name, opponent_factory in BASELINES.items():
        for seed in seeds:
            trace_path = os.path.join(OUT_ROOT, "traces", f"{seed_set_name}_{opponent_name}_seed{seed}.jsonl")
            os.makedirs(os.path.dirname(trace_path), exist_ok=True)
            if os.path.exists(trace_path):
                os.remove(trace_path)
            planner = make_planner(trace_path=trace_path)
            opponent = opponent_factory()
            t0 = time.time()
            record, replay, extracted = run_and_analyze(planner, opponent, STEPS, seed,
                                                          f"phase2_6_{seed_set_name}_{opponent_name}", f"seed{seed}")
            planner._tracer.close()
            outcome = record["outcome"]
            planner_money, opp_money = outcome["final_money"]
            trace_stats = summarize_trace(trace_path)
            row = {
                "seed_set": seed_set_name, "opponent": opponent_name, "seed": seed,
                "planner_money": planner_money, "opponent_money": opp_money,
                "margin": round(planner_money - opp_money, 2),
                "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
                "planner_validation": record["players"][0]["validation"]["overall"],
                **trace_stats,
            }
            rows.append(row)
            print(f"  [{seed_set_name}/{opponent_name}] seed={seed} planner=${planner_money} "
                  f"opponent=${opp_money} margin=${row['margin']} win={row['win']} "
                  f"valid={row['planner_validation']} ({time.time()-t0:.2f}s)", flush=True)
    return rows


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    args = ap.parse_args()
    rows = run_seed_set(args.seed_set)
    write_csv(os.path.join(OUT_ROOT, "results.csv"), rows)
    print(f"\nWrote {len(rows)} rows to {os.path.join(OUT_ROOT, 'results.csv')}")


if __name__ == "__main__":
    main()
