"""
Phase 49 Step 1, part 1: cheap 4-seed isolated-economy screen (vs "pass"),
same 4 development seeds every prior phase's cheap screen has used
(scripts/phase3_2_configs.py::SEED_SETS["development"]).

Candidates, all running Submission I's EXISTING (unchanged) crop fractions
via agents/phase21/portfolio.py::portfolio_targets -- no CARROT/TOMATO slice
anywhere in this script:
  - shipped: Submission I exactly as shipped (scripts/phase37/
    paced_portfolio_agent.py, unmodified) -- the reference baseline.
  - seed_paced: Phase 45's BUY_SEED-pacer fix ALONE (scripts/phase45/
    seed_paced_portfolio_agent.py, unmodified).
  - feed_priority: Phase 46's FEED tier-0.5 fix ALONE (scripts/phase46/
    feed_priority_portfolio_agent.py, unmodified) -- this IS Submission J,
    validated and ready but not yet uploaded.
  - combined: THIS phase's new combined_execution.py, carrying BOTH fixes
    at once (scripts/phase49/combined_portfolio_agent.py).

The question this screen answers: does combining both fixes regress vs.
either fix alone, or vs. shipped Submission I? Per the phase brief, this
must be checked BEFORE any CARROT/TOMATO slice is layered on top.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from scripts.phase45.seed_paced_portfolio_agent import make_seed_paced_portfolio_agent  # noqa: E402
from scripts.phase46.feed_priority_portfolio_agent import make_feed_priority_portfolio_agent  # noqa: E402
from scripts.phase49.combined_portfolio_agent import make_combined_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402
from scripts.phase3_2_configs import SEED_SETS  # noqa: E402

STEPS = 720
DEV_SEEDS = SEED_SETS["development"]
OUT_ROOT = "results/phase49"

CANDIDATES = {
    "shipped": make_paced_portfolio_agent,
    "seed_paced": make_seed_paced_portfolio_agent,
    "feed_priority": make_feed_priority_portfolio_agent,
    "combined": make_combined_portfolio_agent,
}


def run_one(make_agent, seed, label):
    agent = make_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    record, _ = analyze_replay(replay, meta, "phase49_isolated", f"{label}_seed{seed}")
    final_money = record["outcome"]["final_money"][0]
    return {"seed": seed, "final_money": final_money}


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    results = {label: [] for label in CANDIDATES}

    for label, make_agent in CANDIDATES.items():
        print(f"=== {label} vs. pass ===")
        for seed in DEV_SEEDS:
            row = run_one(make_agent, seed, label)
            results[label].append(row)
            print(f"  seed={seed}: final_money=${row['final_money']:,.2f}")

    means = {label: sum(r["final_money"] for r in rows) / len(rows) for label, rows in results.items()}
    print("\n=== SUMMARY (4-seed dev screen, isolated economy) ===")
    base_mean = means["shipped"]
    for label, m in means.items():
        delta = (m - base_mean) / base_mean * 100 if base_mean else 0.0
        print(f"  {label}: mean=${m:,.2f}  delta_vs_shipped={delta:+.2f}%")

    results["summary"] = {label: round(m, 2) for label, m in means.items()}
    for label in ("seed_paced", "feed_priority", "combined"):
        results["summary"][f"delta_{label}_vs_shipped_pct"] = round((means[label] - base_mean) / base_mean * 100, 2)
    results["summary"]["delta_combined_vs_seed_paced_pct"] = round(
        (means["combined"] - means["seed_paced"]) / means["seed_paced"] * 100, 2)
    results["summary"]["delta_combined_vs_feed_priority_pct"] = round(
        (means["combined"] - means["feed_priority"]) / means["feed_priority"] * 100, 2)

    with open(os.path.join(OUT_ROOT, "phase49_sanity_isolated_4seed.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase49_sanity_isolated_4seed.json")


if __name__ == "__main__":
    main()
