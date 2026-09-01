"""
Kaggriculture Phase 1 evaluation harness.

Runs N episodes of a matchup between two agents (built-in names, python files,
or importable callables), collects per-episode raw results (JSON, one file per
episode) plus an aggregate summary (JSON + CSV), and preserves replay JSON for
each episode so nothing is lost to averaging.

Usage:
    python run_episodes.py --p0 starter --p1 random --episodes 20 --seed-base 1000
    python run_episodes.py --p0 ../agents/baseline_agent.py --p1 starter --episodes 10
"""
import argparse
import csv
import json
import os
import statistics
import time

from kaggle_environments import make


def run_one_episode(p0, p1, episode_steps, seed, save_replay_path=None):
    config = {"episodeSteps": episode_steps}
    if seed is not None:
        config["seed"] = seed
    env = make("kaggriculture", configuration=config, debug=False)

    t0 = time.time()
    env.run([p0, p1])
    runtime_s = time.time() - t0

    final = env.steps[-1]
    rewards = [s.reward for s in final]
    statuses = [s.status for s in final]

    if rewards[0] is None or rewards[1] is None:
        winner = None
    elif rewards[0] > rewards[1]:
        winner = 0
    elif rewards[1] > rewards[0]:
        winner = 1
    else:
        winner = "tie"

    result = {
        "p0": p0 if isinstance(p0, str) else getattr(p0, "__name__", str(p0)),
        "p1": p1 if isinstance(p1, str) else getattr(p1, "__name__", str(p1)),
        "seed": seed,
        "episode_steps": episode_steps,
        "final_money": rewards,
        "statuses": statuses,
        "winner": winner,
        "runtime_s": runtime_s,
        "n_steps_recorded": len(env.steps),
    }

    if save_replay_path:
        with open(save_replay_path, "w") as f:
            json.dump(env.toJSON(), f)

    return result


def summarize(results):
    money0 = [r["final_money"][0] for r in results if r["final_money"][0] is not None]
    money1 = [r["final_money"][1] for r in results if r["final_money"][1] is not None]
    n = len(results)
    wins0 = sum(1 for r in results if r["winner"] == 0)
    wins1 = sum(1 for r in results if r["winner"] == 1)
    ties = sum(1 for r in results if r["winner"] == "tie")
    errors0 = sum(1 for r in results if r["statuses"][0] not in ("DONE",))
    errors1 = sum(1 for r in results if r["statuses"][1] not in ("DONE",))

    def stats(vals):
        if not vals:
            return {"mean": None, "median": None, "std": None, "min": None, "max": None}
        return {
            "mean": statistics.mean(vals),
            "median": statistics.median(vals),
            "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals),
            "max": max(vals),
        }

    return {
        "n_episodes": n,
        "p0_name": results[0]["p0"] if results else None,
        "p1_name": results[0]["p1"] if results else None,
        "p0_win_rate": wins0 / n if n else None,
        "p1_win_rate": wins1 / n if n else None,
        "tie_rate": ties / n if n else None,
        "p0_error_count": errors0,
        "p1_error_count": errors1,
        "p0_final_money": stats(money0),
        "p1_final_money": stats(money1),
        "mean_runtime_s": statistics.mean([r["runtime_s"] for r in results]) if results else None,
    }


def resolve_agent(spec):
    """Pass through built-in names and .py file paths unchanged; kaggle_environments
    handles both natively via env.run(). No custom resolution needed."""
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", required=True, help="built-in name ('pass'/'random'/'starter') or path to .py agent")
    ap.add_argument("--p1", required=True)
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--seed-base", type=int, default=None, help="if set, episode i uses seed seed_base+i (reproducible)")
    ap.add_argument("--random-seeds", action="store_true", help="use env-default (non-fixed) seeding instead")
    ap.add_argument("--out", default="../results", help="output directory")
    ap.add_argument("--tag", default=None, help="label for this run, used in output filenames")
    ap.add_argument("--save-replays", action="store_true")
    args = ap.parse_args()

    tag = args.tag or f"{os.path.basename(args.p0)}_vs_{os.path.basename(args.p1)}"
    out_dir = os.path.join(args.out, tag)
    os.makedirs(out_dir, exist_ok=True)
    replay_dir = os.path.join(out_dir, "replays")
    if args.save_replays:
        os.makedirs(replay_dir, exist_ok=True)

    p0 = resolve_agent(args.p0)
    p1 = resolve_agent(args.p1)

    results = []
    for i in range(args.episodes):
        seed = None if args.random_seeds else (args.seed_base + i if args.seed_base is not None else 10_000 + i)
        replay_path = os.path.join(replay_dir, f"ep{i:03d}.json") if args.save_replays else None
        print(f"[{tag}] episode {i+1}/{args.episodes} (seed={seed}) ...", flush=True)
        r = run_one_episode(p0, p1, args.steps, seed, replay_path)
        r["episode_index"] = i
        results.append(r)
        print(f"    -> money={r['final_money']} winner={r['winner']} status={r['statuses']} runtime={r['runtime_s']:.2f}s")

    raw_path = os.path.join(out_dir, "raw_episodes.json")
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2)

    summary = summarize(results)
    summary_path = os.path.join(out_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    csv_path = os.path.join(out_dir, "raw_episodes.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["episode_index", "seed", "p0", "p1", "money0", "money1", "winner", "status0", "status1", "runtime_s"])
        for r in results:
            w.writerow([
                r["episode_index"], r["seed"], r["p0"], r["p1"],
                r["final_money"][0], r["final_money"][1], r["winner"],
                r["statuses"][0], r["statuses"][1], f"{r['runtime_s']:.3f}",
            ])

    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nRaw episodes: {raw_path}")
    print(f"Summary: {summary_path}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
