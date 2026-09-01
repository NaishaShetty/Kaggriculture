"""
CLI: runtime and storage overhead measurement (brief section 25).

Usage:
    python -m instrumentation.cli_benchmark --p0 ../agents/baseline_agent.py --p1 starter --steps 720 --episodes 5
"""
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.run_episodes import run_one_episode  # noqa: E402
from instrumentation.pipeline import run_and_analyze, write_episode_outputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", required=True)
    ap.add_argument("--p1", required=True)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--episodes", type=int, default=5)
    ap.add_argument("--seed-base", type=int, default=90_000)
    ap.add_argument("--out", default="results/phase2_1/benchmark")
    args = ap.parse_args()

    plain_runtimes = []
    for i in range(args.episodes):
        seed = args.seed_base + i
        t0 = time.time()
        run_one_episode(args.p0, args.p1, args.steps, seed)
        plain_runtimes.append(time.time() - t0)

    instrumented_runtimes = []
    file_sizes = None
    for i in range(args.episodes):
        seed = args.seed_base + i
        t0 = time.time()
        record, replay, extracted = run_and_analyze(args.p0, args.p1, args.steps, seed, "benchmark", f"benchmark_ep{i:03d}")
        instrumented_runtimes.append(time.time() - t0)
        if i == 0:
            paths = write_episode_outputs(args.out, "benchmark_tag", i, record)
            file_sizes = {k: os.path.getsize(v) for k, v in paths.items()}

    plain_mean = statistics.mean(plain_runtimes)
    instrumented_mean = statistics.mean(instrumented_runtimes)

    report = {
        "p0": args.p0, "p1": args.p1, "steps": args.steps, "episodes": args.episodes,
        "plain_runtime_s": {"mean": plain_mean, "min": min(plain_runtimes), "max": max(plain_runtimes)},
        "instrumented_runtime_s": {"mean": instrumented_mean, "min": min(instrumented_runtimes), "max": max(instrumented_runtimes)},
        "overhead_s_mean": instrumented_mean - plain_mean,
        "overhead_pct_mean": round(100 * (instrumented_mean - plain_mean) / plain_mean, 2) if plain_mean else None,
        "output_file_sizes_bytes_one_episode": file_sizes,
        "output_file_sizes_kb_one_episode": {k: round(v / 1024, 1) for k, v in file_sizes.items()} if file_sizes else None,
    }

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
