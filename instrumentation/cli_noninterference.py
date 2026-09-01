"""
CLI: mandatory non-interference proof (brief section 23).

Run A -- calls the actual frozen harness function (harness/run_episodes.py,
`run_one_episode`, imported unmodified) with a fixed seed: "normal frozen
environment."
Run B -- calls instrumentation.collector.run_episode (same underlying
kaggle_environments make()/env.run() calls) with the identical seed and
agents, then runs the full extraction/ledger/metrics/validation pipeline on
top of it: "instrumentation enabled."

Compares: full per-turn action sequence for both players, final money,
statuses, winner. Also verifies the pipeline never mutates the replay object
it analyzes (a stronger, structural non-interference guarantee, since the
architecture is: run the unmodified simulator to completion first, THEN
analyze a fully-formed, already-serialized replay -- there is no code path
by which telemetry could feed back into gameplay).

Usage:
    python -m instrumentation.cli_noninterference --p0 ../agents/baseline_agent.py --p1 starter --steps 200 --seed 42
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.run_episodes import run_one_episode  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from instrumentation.collector import run_episode as instrumented_run_episode  # noqa: E402


def extract_action_sequence(replay):
    seq = []
    for i, step in enumerate(replay["steps"]):
        for player, entry in enumerate(step):
            seq.append({"turn": i, "player": player, "action": entry["action"]})
    return seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", required=True)
    ap.add_argument("--p1", required=True)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="results/phase2_1/noninterference")
    args = ap.parse_args()

    # Run A: plain frozen harness, requesting the replay via the harness's own
    # --save-replays mechanism so we're comparing what the frozen harness
    # itself would have produced, unmodified.
    os.makedirs(args.out, exist_ok=True)
    replay_a_path = os.path.join(args.out, "_run_a_replay.json")
    result_a = run_one_episode(args.p0, args.p1, args.steps, args.seed, save_replay_path=replay_a_path)
    with open(replay_a_path) as f:
        replay_a = json.load(f)

    # Run B: instrumentation collector + full analysis pipeline.
    record_b, replay_b, extracted_b = run_and_analyze(
        args.p0, args.p1, args.steps, args.seed, experiment_id="noninterference", episode_id="noninterference_run_b",
    )

    seq_a = extract_action_sequence(replay_a)
    seq_b = extract_action_sequence(replay_b)
    actions_identical = seq_a == seq_b

    rewards_a = [s["reward"] for s in replay_a["steps"][-1]]
    statuses_a = [s["status"] for s in replay_a["steps"][-1]]
    rewards_b = record_b["outcome"]["final_money"]
    statuses_b = record_b["outcome"]["statuses"]

    money_identical = rewards_a == rewards_b
    statuses_identical = statuses_a == statuses_b
    pipeline_non_mutating = record_b["non_interference_self_check"]["replay_unmutated_by_pipeline"]

    overall_pass = actions_identical and money_identical and statuses_identical and pipeline_non_mutating

    report = {
        "p0": args.p0, "p1": args.p1, "steps": args.steps, "seed": args.seed,
        "run_a_final_money": rewards_a, "run_b_final_money": rewards_b,
        "run_a_statuses": statuses_a, "run_b_statuses": statuses_b,
        "n_actions_compared": len(seq_a),
        "actions_identical": actions_identical,
        "final_money_identical": money_identical,
        "statuses_identical": statuses_identical,
        "pipeline_non_mutating": pipeline_non_mutating,
        "overall": "PASS" if overall_pass else "FAIL",
    }

    if not actions_identical:
        first_diff = next((i for i in range(min(len(seq_a), len(seq_b))) if seq_a[i] != seq_b[i]), None)
        report["first_action_diff_index"] = first_diff
        if first_diff is not None:
            report["first_diff_a"] = seq_a[first_diff]
            report["first_diff_b"] = seq_b[first_diff]

    with open(os.path.join(args.out, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(json.dumps(report, indent=2, default=str))
    print(f"\nNON-INTERFERENCE: {report['overall']}")


if __name__ == "__main__":
    main()
