"""
Phase 3.5 Competitive Agent V2 experiment runner. Runs V2 (or an ablation
of it) against a named opponent archetype across a named seed set, reusing
instrumentation.pipeline.run_and_analyze exactly like every prior phase.

Usage:
    python scripts/phase3_5_run_v2_experiments.py --agent v2_full --opponent heavy_scaler --seed-set development
    python scripts/phase3_5_run_v2_experiments.py --agent v2_scaling_only --opponent expansion_oriented --seed-set validation
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_5.adapters.competitive_v2_agent import make_competitive_v2_agent  # noqa: E402
from agents.phase3_3.interventions import variant_d_production_substitution  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from agents.phase3_5.opponent_classes_extended import OPPONENT_CLASSES_EXTENDED  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_5_configs import STEPS, SEED_SETS, ARCHETYPES  # noqa: E402

OUT_ROOT = "results/phase3_5"
ALL_OPPONENTS = {**OPPONENT_CLASSES, **OPPONENT_CLASSES_EXTENDED}

AGENT_VARIANTS = {
    "planner_v1_control": dict(market_response_fn=None, scaling_response_enabled=False),
    "variant_d_only": dict(market_response_fn=variant_d_production_substitution, scaling_response_enabled=False),
    "v2_scaling_only": dict(market_response_fn=None, scaling_response_enabled=True),
    "v2_full": dict(market_response_fn=variant_d_production_substitution, scaling_response_enabled=True),
}


def run_one(agent_variant, opponent_name, seed, seed_set_name):
    kwargs = AGENT_VARIANTS[agent_variant]
    opponent = ALL_OPPONENTS[opponent_name]()
    trace_path = os.path.join(OUT_ROOT, "traces", f"{agent_variant}_{opponent_name}_seed{seed}.jsonl")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    if os.path.exists(trace_path):
        os.remove(trace_path)
    agent = make_competitive_v2_agent(trace_path=trace_path, **kwargs)

    t0 = time.time()
    record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                 f"phase3_5_{agent_variant}_{opponent_name}", f"seed{seed}")
    if agent._planner._tracer:
        agent._planner._tracer.close()

    outcome = record["outcome"]
    protagonist_money, opponent_money = outcome["final_money"]
    row = {
        "agent_variant": agent_variant, "opponent": opponent_name, "seed": seed, "seed_set": seed_set_name,
        "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
        "margin": round(protagonist_money - opponent_money, 2),
        "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
        "market_activations": agent._state_ref["market_activations"],
        "scaling_activations": agent._state_ref["scaling_activations"],
        "elapsed_s": round(time.time() - t0, 2),
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, choices=list(AGENT_VARIANTS))
    ap.add_argument("--opponent", required=True, choices=list(ALL_OPPONENTS))
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    args = ap.parse_args()

    rows = []
    for seed in SEED_SETS[args.seed_set]:
        row = run_one(args.agent, args.opponent, seed, args.seed_set)
        rows.append(row)
        print(f"  [{args.agent}/{args.opponent}] seed={seed} ({args.seed_set}) "
              f"protagonist=${row['protagonist_final_money']} opponent=${row['opponent_final_money']} "
              f"win={row['win']} scaling_act={row['scaling_activations']} market_act={row['market_activations']} "
              f"({row['elapsed_s']}s)", flush=True)

    out_csv = os.path.join(OUT_ROOT, "experiments", "v2_results.csv")
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
