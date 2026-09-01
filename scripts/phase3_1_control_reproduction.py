"""
Phase 3.1 control reproduction test (brief section 25/26). Runs the frozen
Planner v1, through the NEW Phase 3 control adapter, on the EXACT SAME
held_out seeds/baselines/steps as Phase 2.6's final gate, and compares
against the recorded Phase 2.6 results. Any discrepancy must be explained
before any Phase 3 experiment proceeds -- per the brief, "If it does not
[reproduce]: STOP."
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3.adapters.planner_v1_control import make_control_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase2_6_baselines import BASELINES  # noqa: E402

STEPS = 720
HELD_OUT_SEEDS = list(range(302000, 302010))
OUT_ROOT = "results/phase3_1/control_reproduction"
PHASE2_6_RESULTS_CSV = "results/phase2_6/planner_v1/results.csv"


def load_phase2_6_held_out():
    rows = {}
    with open(PHASE2_6_RESULTS_CSV, newline="") as f:
        for r in csv.DictReader(f):
            if r["seed_set"] == "held_out":
                rows[(r["opponent"], int(r["seed"]))] = float(r["planner_money"])
    return rows


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    phase2_6_reference = load_phase2_6_held_out()

    rows = []
    discrepancies = []
    for opponent_name, opponent_factory in BASELINES.items():
        for seed in HELD_OUT_SEEDS:
            trace_path = os.path.join(OUT_ROOT, f"trace_{opponent_name}_seed{seed}.jsonl")
            if os.path.exists(trace_path):
                os.remove(trace_path)
            agent = make_control_agent(trace_path=trace_path)  # NO_SWITCH mode -- must be 100% inert
            opponent = opponent_factory()
            record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                          "phase3_1_control_repro", f"{opponent_name}_seed{seed}")
            agent._planner._tracer.close()
            money_now = record["outcome"]["final_money"][0]
            reference = phase2_6_reference.get((opponent_name, seed))
            match = (reference is not None and money_now == reference)
            row = {"opponent": opponent_name, "seed": seed, "phase3_harness_money": money_now,
                   "phase2_6_reference_money": reference, "exact_match": match}
            rows.append(row)
            if not match:
                discrepancies.append(row)
            print(f"  [{opponent_name}] seed={seed} phase3_harness=${money_now} "
                  f"phase2_6_reference=${reference} match={match}", flush=True)

    out = {"n_episodes": len(rows), "n_exact_matches": sum(1 for r in rows if r["exact_match"]),
           "n_discrepancies": len(discrepancies), "rows": rows, "discrepancies": discrepancies,
           "verdict": "CONTROL REPRODUCED EXACTLY" if not discrepancies else "DISCREPANCY FOUND -- STOP AND DIAGNOSE"}
    with open(os.path.join(OUT_ROOT, "control_reproduction_result.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)

    print(f"\n{out['n_exact_matches']}/{out['n_episodes']} exact matches. Verdict: {out['verdict']}")
    if discrepancies:
        print("STOP: diagnose the evaluation infrastructure before continuing with any Phase 3 experiment.")
        sys.exit(1)


if __name__ == "__main__":
    main()
