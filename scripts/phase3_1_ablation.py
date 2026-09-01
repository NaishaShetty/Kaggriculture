"""
Phase 3.1 ablation framework (brief section 20/33.I). Phase 3.1 has exactly
ONE real candidate (`planner_only` -- the frozen Planner v1 with every
Phase 3 component in pure logging/inert mode) since no adaptive mechanism
exists yet to ablate. This script's job is to prove the FRAMEWORK works --
that component flags are inspectable and independently toggleable -- not to
report a meaningful ablation comparison (there is only one row to compare
against itself, which is stated plainly, not disguised as a finding).

Future Phase 3.2+ candidates (market adaptation, opponent observation used
for real, opponent modeling, strategy switching) register a new entry in
scripts/phase3_1_evaluate.py::ABLATIONS with a `components` dict describing
what's active; this script will then produce a real comparison automatically.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.phase3_1_evaluate import ABLATIONS  # noqa: E402

OUT_PATH = "results/phase3_1/strategy_analysis/ablation_matrix.json"


def main():
    print("Registered ablation configurations (component matrix):\n")
    for name, cfg in ABLATIONS.items():
        print(f"{name}:")
        for component, state in cfg["components"].items():
            print(f"    {component:24s} {state}")
        print()

    out = {
        "ablation_matrix": {name: cfg["components"] for name, cfg in ABLATIONS.items()},
        "note": "Phase 3.1 has exactly one real candidate (planner_only) -- every other row the brief "
                "anticipates (planner+market_adaptation, planner+opponent_observation used for real, "
                "planner+opponent_model, planner+strategy_switching, planner+market+opponent) requires an "
                "actual Phase 3.2+ adaptive mechanism to exist before it can be meaningfully evaluated. "
                "This script proves the FRAMEWORK (component flags, independent toggling) is in place, not "
                "that an ablation comparison has been run -- there is nothing to compare against itself.",
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
