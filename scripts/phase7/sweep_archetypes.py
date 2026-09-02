"""
Phase 7, step 5: sweep Submission C (agents/phase3_8/adapters/
competitive_v3_agent.py::make_competitive_v3_agent, completely unmodified)
against the project's existing synthetic archetype battery, and record
final money for every (archetype, seed) pair. Run this script once against
the unpatched agents/phase2_6/common.py and once against the Phase 7-fixed
version (git stash agents/phase2_6/common.py between runs), then diff the
two output files -- every pair should be byte-identical UNLESS that
specific (archetype, seed) combination happens to hit the exact
threshold/batch-mode, non-empty-shed-at-day-29 condition the fix targets.

Usage: python scripts/phase7/sweep_archetypes.py <output_json_path>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_5_configs import STEPS, ARCHETYPES, SEED_SETS  # noqa: E402

try:
    from scripts.phase3_5_run_v2_experiments import OPPONENT_CLASSES_EXTENDED
    ALL_OPPONENTS = {**OPPONENT_CLASSES, **OPPONENT_CLASSES_EXTENDED}
except ImportError:
    ALL_OPPONENTS = OPPONENT_CLASSES

SEEDS = SEED_SETS["development"]  # 4 seeds, disjoint from every other seed range in this project


def main(out_path):
    results = {}
    for archetype_name in ARCHETYPES:
        for seed in SEEDS:
            protagonist = make_competitive_v3_agent()
            opponent = ALL_OPPONENTS[archetype_name]()
            record, replay, extracted = run_and_analyze(
                protagonist, opponent, STEPS, seed, f"phase7_sweep_{archetype_name}", f"seed{seed}")
            protagonist_money, opponent_money = record["outcome"]["final_money"]
            final_obs = replay["steps"][-1][0]["observation"]
            final_shed_total = sum(final_obs["private"]["shed"].values())
            key = f"{archetype_name}_seed{seed}"
            results[key] = {
                "archetype": archetype_name, "seed": seed,
                "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
                "final_shed_total": final_shed_total,
            }
            print(f"{key}: protagonist=${protagonist_money} opponent=${opponent_money} "
                  f"final_shed={final_shed_total}", flush=True)

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {len(results)} results to {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
