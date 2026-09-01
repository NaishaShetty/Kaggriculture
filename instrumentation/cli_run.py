"""
CLI: run N episodes with full telemetry instrumentation, writing
raw/daily/episode/validation records under results/phase2_1/.

Usage (from repo root):
    python -m instrumentation.cli_run --p0 ../agents/baseline_agent.py --p1 pass \
        --episodes 15 --steps 720 --seed-base 100 --tag baseline_vs_pass
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instrumentation.pipeline import run_and_analyze, write_episode_outputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", required=True)
    ap.add_argument("--p1", required=True)
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--seed-base", type=int, default=None)
    ap.add_argument("--out", default="results/phase2_1")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--experiment-id", default=None)
    args = ap.parse_args()

    tag = args.tag or f"{os.path.basename(args.p0)}_vs_{os.path.basename(args.p1)}"
    experiment_id = args.experiment_id or tag

    validation_overalls = []
    runtimes = []
    money0, money1 = [], []
    winners = []

    for i in range(args.episodes):
        seed = (args.seed_base + i) if args.seed_base is not None else (10_000 + i)
        episode_id = f"{tag}_ep{i:03d}_seed{seed}"
        print(f"[{tag}] episode {i+1}/{args.episodes} (seed={seed}) ...", flush=True)
        record, replay, extracted = run_and_analyze(args.p0, args.p1, args.steps, seed, experiment_id, episode_id)
        paths = write_episode_outputs(args.out, tag, i, record)

        v0 = record["players"][0]["validation"]["overall"]
        v1 = record["players"][1]["validation"]["overall"]
        validation_overalls.extend([v0, v1])
        runtimes.append(record["meta"]["runtime_s"])
        money0.append(record["outcome"]["final_money"][0])
        money1.append(record["outcome"]["final_money"][1])
        winners.append(record["outcome"]["winner"])

        print(f"    -> money={record['outcome']['final_money']} winner={record['outcome']['winner']} "
              f"validation=[{v0},{v1}] runtime={record['meta']['runtime_s']:.2f}s "
              f"non_mutating={record['non_interference_self_check']['replay_unmutated_by_pipeline']}")

    summary = {
        "tag": tag, "experiment_id": experiment_id, "n_episodes": args.episodes,
        "p0": args.p0, "p1": args.p1,
        "p0_final_money": {"mean": statistics.mean(money0), "min": min(money0), "max": max(money0)},
        "p1_final_money": {"mean": statistics.mean(money1), "min": min(money1), "max": max(money1)},
        "p0_win_rate": sum(1 for w in winners if w == 0) / len(winners),
        "p1_win_rate": sum(1 for w in winners if w == 1) / len(winners),
        "tie_rate": sum(1 for w in winners if w == "tie") / len(winners),
        "mean_runtime_s": statistics.mean(runtimes),
        "validation_pass_count": sum(1 for v in validation_overalls if v == "PASS"),
        "validation_partial_count": sum(1 for v in validation_overalls if v == "PARTIAL"),
        "validation_fail_count": sum(1 for v in validation_overalls if v == "FAIL"),
        "n_validation_checks": len(validation_overalls),
    }
    summary_dir = os.path.join(args.out, "episode", tag)
    os.makedirs(summary_dir, exist_ok=True)
    with open(os.path.join(summary_dir, "_run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== TELEMETRY RUN SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
