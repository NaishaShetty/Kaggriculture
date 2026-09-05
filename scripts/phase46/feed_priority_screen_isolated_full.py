"""
Phase 46 Step 4/5 (mandatory follow-on): full 15-seed isolated-economy
validation -- same three candidates as feed_priority_screen_isolated.py
(baseline / Part B feed_priority / Part B+C feed_priority_throttled) vs.
"pass", but run across the FULL 15-seed set (development + validation +
held_out from scripts/phase3_2_configs.SEED_SETS), not just the 4-seed dev
screen. Per this project's own standing rule (Phase 17), no promotion
recommendation is made off a 4-seed screen alone -- this closes that gap
for the isolated-economy side of Section 4's validation.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase46.feed_priority_portfolio_agent import make_feed_priority_portfolio_agent  # noqa: E402
from scripts.phase46.feed_priority_throttled_portfolio_agent import make_feed_priority_throttled_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
ALL_SEEDS = SEED_SETS["development"] + SEED_SETS["validation"] + SEED_SETS["held_out"]
OUT_ROOT = "results/phase46"

CANDIDATES = {
    "baseline": make_paced_portfolio_agent,
    "feed_priority": make_feed_priority_portfolio_agent,
    "feed_priority_throttled": make_feed_priority_throttled_portfolio_agent,
}


def run_one(make_agent, seed, label):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    record, _ = analyze_replay(replay, meta, "phase46_isolated_full", f"{label}_seed{seed}")
    final_money = record["outcome"]["final_money"][0]
    action_eff = record["players"][0]["action_efficiency"]
    animal_metrics = record["players"][0]["animal_metrics"]
    purchased = sum(v.get("purchased", 0) for v in animal_metrics.values())
    escaped = sum(v.get("n_escaped", 0) for v in animal_metrics.values())
    placed = sum(v.get("n_placed", 0) for v in animal_metrics.values())
    return {
        "seed": seed,
        "final_money": final_money,
        "idle_fraction": action_eff["idle_fraction"],
        "crop_fraction": action_eff["crop_fraction"],
        "animal_fraction": action_eff["animal_fraction"],
        "animal_purchased": purchased,
        "animal_placed": placed,
        "animal_escaped": escaped,
        "animal_final_owned": placed - escaped,
    }


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    results = {}
    for label, make_agent in CANDIDATES.items():
        print(f"\n=== {label} vs. pass ({len(ALL_SEEDS)} seeds) ===", flush=True)
        rows = []
        for seed in ALL_SEEDS:
            row = run_one(make_agent, seed, label)
            rows.append(row)
            print(f"  seed={seed}: money=${row['final_money']:,.2f} idle={row['idle_fraction']} "
                  f"crop_frac={row['crop_fraction']} animals purchased={row['animal_purchased']} "
                  f"escaped={row['animal_escaped']} final_owned={row['animal_final_owned']}", flush=True)
        results[label] = rows

    summary = {}
    for label, rows in results.items():
        n = len(rows)
        summary[label] = {
            "n_seeds": n,
            "mean_money": round(sum(r["final_money"] for r in rows) / n, 2),
            "mean_idle_fraction": round(sum(r["idle_fraction"] for r in rows) / n, 4),
            "mean_crop_fraction": round(sum(r["crop_fraction"] for r in rows) / n, 4),
            "mean_purchased": round(sum(r["animal_purchased"] for r in rows) / n, 2),
            "mean_escaped": round(sum(r["animal_escaped"] for r in rows) / n, 2),
            "mean_final_owned": round(sum(r["animal_final_owned"] for r in rows) / n, 2),
        }
    base_money = summary["baseline"]["mean_money"]
    for label in summary:
        summary[label]["delta_pct_vs_baseline"] = round((summary[label]["mean_money"] - base_money) / base_money * 100, 2)

    print("\n=== SUMMARY (15-seed full) ===", flush=True)
    for label, s in summary.items():
        print(f"  {label}: mean_money=${s['mean_money']:,.2f} (delta {s['delta_pct_vs_baseline']:+.2f}%) "
              f"idle={s['mean_idle_fraction']} crop_frac={s['mean_crop_fraction']} "
              f"purchased={s['mean_purchased']} escaped={s['mean_escaped']} final_owned={s['mean_final_owned']}", flush=True)

    results["summary"] = summary
    with open(os.path.join(OUT_ROOT, "phase46_feed_priority_isolated_15seed_full.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase46_feed_priority_isolated_15seed_full.json", flush=True)


if __name__ == "__main__":
    main()
