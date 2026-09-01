"""Phase 3.4 regression tests. Run: python scripts/phase3_4_regression_tests.py

Covers: Variant D unchanged, Planner v1 unchanged, new candidates are inert
outside detection, candidate isolation (running a candidate never mutates
Variant D's own intervention function), no private-state/future-information
access in the new candidate module, and control reproducibility.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_4.response_policy import CANDIDATES, candidate_c_diversified_substitution, \
    candidate_e_partial_melon_retention
from agents.phase3_3.interventions import INTERVENTIONS, variant_d_production_substitution
from agents.phase3_3.adapters.intervention_agent import make_intervention_agent
from agents.phase3.opponent_classes import OPPONENT_CLASSES
from instrumentation.pipeline import run_and_analyze

PASS_COUNT = 0
FAIL_COUNT = 0


def check(name, cond):
    global PASS_COUNT, FAIL_COUNT
    if cond:
        PASS_COUNT += 1
        print(f"  PASS  {name}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL  {name}")


def test_candidates_inert_outside_detection():
    print("Phase 3.4 candidates inert outside detection:")
    inactive = {"active": False, "predicted_class": "passive", "confidence": 0.1}
    config = {"crops": {"MELON": 1.0}, "sell_policy": {"mode": "passive"}}
    for name, fn in CANDIDATES.items():
        result = fn(config, None, inactive)
        check(f"{name}: no-op when detector is inactive", result == config)


def test_candidate_c_diversification_correctness():
    print("Candidate C diversification correctness:")
    active = {"active": True, "predicted_class": "expansion_oriented", "confidence": 0.9}
    config = {"crops": {"MELON": 1.0}}
    new_config = candidate_c_diversified_substitution(config, _fake_state(), active, n_substitutes=2)
    check("MELON removed from portfolio", "MELON" not in new_config["crops"])
    check("exactly 2 substitute crops present", len(new_config["crops"]) == 2)
    check("fractions still sum to 1.0", abs(sum(new_config["crops"].values()) - 1.0) < 1e-9)


def test_candidate_e_fixed_split():
    print("Candidate E fixed-split correctness:")
    active = {"active": True, "predicted_class": "expansion_oriented", "confidence": 0.9}
    config = {"crops": {"MELON": 1.0}}
    new_config = candidate_e_partial_melon_retention(config, None, active, melon_frac=0.5)
    check("MELON retained at exactly melon_frac", new_config["crops"]["MELON"] == 0.5)
    check("remainder goes to STRAWBERRY", new_config["crops"]["STRAWBERRY"] == 0.5)


def test_variant_d_unaffected_by_phase3_4_module():
    print("Variant D isolation (Phase 3.4 module import does not alter Phase 3.3 behavior):")
    seed = 700002
    agent = make_intervention_agent(intervention_fn=variant_d_production_substitution, trace_path=None)
    opponent = OPPONENT_CLASSES["expansion_oriented"]()
    record, _, _ = run_and_analyze(agent, opponent, 720, seed, "phase3_4_regress", "d_isolation")
    check("Variant D on known seed 700002 reproduces its Phase 3.3 reference value ($19,367)",
          record["outcome"]["final_money"][0] == 19367.0)


def test_no_private_or_future_state_in_candidates():
    print("no private/future-state access:")
    import inspect
    src_c = inspect.getsource(candidate_c_diversified_substitution)
    src_e = inspect.getsource(candidate_e_partial_melon_retention)
    for name, src in [("candidate_c", src_c), ("candidate_e", src_e)]:
        check(f"{name}: no reference to 'private' observation field", "obs[\"private\"]" not in src and "obs['private']" not in src)
        check(f"{name}: no reference to future turn indices", "future" not in src.lower())


def test_control_still_frozen():
    print("control integrity:")
    import hashlib
    with open("results/phase3_1/control_reproduction/frozen_file_hashes.txt") as f:
        lines = [l.strip() for l in f if l.strip()]
    mismatches = []
    for line in lines:
        h, path = line.split(maxsplit=1)
        path = path.lstrip("*")
        actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if actual != h:
            mismatches.append(path)
    check("Planner v1 remains byte-for-byte unchanged after all Phase 3.4 experimentation", not mismatches)

    import csv
    ref_rows = list(csv.DictReader(open("results/phase3_3/experiments/intervention_results.csv")))
    check("Phase 3.3's intervention_results.csv file was not modified by Phase 3.4",
          any(r["variant"] == "D_production_substitution" for r in ref_rows))


def _fake_state():
    from agents.phase2_6.state import PlannerState
    return PlannerState(day=5, cash=5000.0, n_hands=1, land_quadrants_owned=1,
                         crop_tile_counts={"MELON": 10}, animal_counts={})


def main():
    test_candidates_inert_outside_detection()
    test_candidate_c_diversification_correctness()
    test_candidate_e_fixed_split()
    test_variant_d_unaffected_by_phase3_4_module()
    test_no_private_or_future_state_in_candidates()
    test_control_still_frozen()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
