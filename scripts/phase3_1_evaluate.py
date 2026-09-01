"""
Phase 3.1 standardized competitive evaluation harness (brief section 16/33.H).
Runs the Phase 3 control adapter (agents/phase3/adapters/planner_v1_control.py)
-- with an optional ablation config -- across a named seed set vs. a named
baseline, recording both the standard outcome metrics (final money, margin,
win) AND the new competitive-trace-derived metrics (opponent event counts,
strategy-switch counts) this phase's infrastructure adds.

This is infrastructure for FUTURE Phase 3.2+ candidates to reuse -- Phase
3.1 itself only ever runs it in the inert NO_SWITCH configuration (no
adaptive candidate exists yet).

Usage:
    python scripts/phase3_1_evaluate.py --seed-set development --ablation planner_only
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3.adapters.planner_v1_control import make_control_agent  # noqa: E402
from agents.phase3.strategy_interface import SwitchMode  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase2_6_baselines import BASELINES  # noqa: E402
from scripts.phase2_6_evaluate_planner import SEED_SETS  # noqa: E402

STEPS = 720
OUT_ROOT = "results/phase3_1/strategy_analysis"

# Ablation framework (brief section 20): each entry names which Phase 3
# components are ACTIVE. Phase 3.1 only has "planner_only" for real (every
# other row is a placeholder for Phase 3.2+ candidates to fill in once they
# exist -- listed here so the harness's --ablation flag already has a home
# for them, per the brief's "make it easy to disable components individually").
ABLATIONS = {
    "planner_only": {"strategy_mode": SwitchMode.NO_SWITCH, "forced_config": None,
                      "components": {"planner": True, "market_adaptation": False, "opponent_observation": "logged_only",
                                     "opponent_model": False, "strategy_switching": False}},
}


def run(seed_set_name, ablation_name):
    seeds = SEED_SETS[seed_set_name]
    ablation = ABLATIONS[ablation_name]
    rows = []
    for opponent_name, opponent_factory in BASELINES.items():
        for seed in seeds:
            trace_path = os.path.join(OUT_ROOT, "traces", f"planner_{seed_set_name}_{opponent_name}_seed{seed}.jsonl")
            ctrace_path = os.path.join(OUT_ROOT, "traces", f"competitive_{seed_set_name}_{opponent_name}_seed{seed}.jsonl")
            os.makedirs(os.path.dirname(trace_path), exist_ok=True)
            for p in (trace_path, ctrace_path):
                if os.path.exists(p):
                    os.remove(p)
            agent = make_control_agent(trace_path=trace_path, competitive_trace_path=ctrace_path,
                                        strategy_mode=ablation["strategy_mode"], forced_config=ablation["forced_config"])
            opponent = opponent_factory()
            record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                          f"phase3_1_{ablation_name}_{seed_set_name}",
                                                          f"{opponent_name}_seed{seed}")
            agent._planner._tracer.close()
            if agent._ctrace:
                agent._ctrace.close()
            outcome = record["outcome"]
            planner_money, opp_money = outcome["final_money"]
            row = {
                "ablation": ablation_name, "seed_set": seed_set_name, "opponent": opponent_name, "seed": seed,
                "planner_money": planner_money, "opponent_money": opp_money,
                "margin": round(planner_money - opp_money, 2),
                "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
                "validation": record["players"][0]["validation"]["overall"],
                "n_opponent_events_logged": len(agent._opponent_logger.history),
                "n_strategy_switches": agent._selector.switch_count,
            }
            rows.append(row)
            print(f"  [{ablation_name}/{seed_set_name}/{opponent_name}] seed={seed} "
                  f"planner=${planner_money} opponent=${opp_money} win={row['win']}", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    ap.add_argument("--ablation", default="planner_only", choices=list(ABLATIONS))
    args = ap.parse_args()

    rows = run(args.seed_set, args.ablation)
    out_csv = os.path.join(OUT_ROOT, "results.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    file_exists = os.path.exists(out_csv)
    fieldnames = list(rows[0].keys())
    with open(out_csv, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows to {out_csv}")


if __name__ == "__main__":
    main()
