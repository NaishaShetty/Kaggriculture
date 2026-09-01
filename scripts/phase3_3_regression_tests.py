"""Phase 3.3 regression tests. Run: python scripts/phase3_3_regression_tests.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_3.adapters.intervention_agent import make_intervention_agent
from agents.phase3_3.interventions import INTERVENTIONS, variant_c_melon_avoidance
from agents.phase3_3.expansion_detector import ExpansionDetector
from agents.phase2_6.common import make_agent as make_planner_v1
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


def test_detection_only_is_inert():
    print("Variant B (detection-only) inertness:")
    seed = 900001
    opponent = OPPONENT_CLASSES["expansion_oriented"]()
    p1 = make_planner_v1(trace_path="results/phase3_3/tmp_t1.jsonl")
    r1, _, _ = run_and_analyze(p1, opponent, 300, seed, "t", "a")
    p1._tracer.close()

    b = make_intervention_agent(intervention_fn=None, trace_path="results/phase3_3/tmp_t2.jsonl")
    r2, _, _ = run_and_analyze(b, OPPONENT_CLASSES["expansion_oriented"](), 300, seed, "t", "b")
    b._planner._tracer.close()
    for p in ("results/phase3_3/tmp_t1.jsonl", "results/phase3_3/tmp_t2.jsonl"):
        os.remove(p)
    check("Variant B reproduces the frozen planner exactly (no behavioral change from detection alone)",
          r1["outcome"]["final_money"] == r2["outcome"]["final_money"])
    check("Variant B never activates any intervention", b._state_ref["n_activations"] == 0)


def test_intervention_inactive_by_default():
    print("intervention inactivity outside detection:")
    inactive_detection = {"active": False, "predicted_class": "passive", "confidence": 0.1}
    config = {"crops": {"MELON": 1.0}, "sell_policy": {"mode": "passive"}}
    for name, fn in INTERVENTIONS.items():
        if fn is None:
            continue
        result = fn(config, None, inactive_detection)
        check(f"{name}: no-op when detector is inactive", result == config)


def test_melon_redistribution_correctness():
    print("MELON redistribution correctness:")
    active = {"active": True, "predicted_class": "expansion_oriented", "confidence": 0.9}
    config = {"crops": {"MELON": 0.5, "STRAWBERRY": 0.5}}
    new_config = variant_c_melon_avoidance(config, None, active)
    check("MELON fraction fully removed from the portfolio", "MELON" not in new_config["crops"])
    check("fractions still sum to 1.0 after redistribution",
          abs(sum(new_config["crops"].values()) - 1.0) < 1e-9)

    config_solo = {"crops": {"MELON": 1.0}}
    new_config_solo = variant_c_melon_avoidance(config_solo, None, active)
    check("MELON-solo portfolio falls back to WHEAT (never an empty portfolio)",
          new_config_solo["crops"] == {"WHEAT": 1.0})


def test_detector_reproducibility():
    print("detector reproducibility:")
    detector1 = ExpansionDetector()
    detector2 = ExpansionDetector()
    check("two freshly constructed detectors load identical artifacts (deterministic, file-based, "
          "no re-fitting at runtime)", detector1.artifact == detector2.artifact)

    seed = 900002
    a1 = make_intervention_agent(intervention_fn=None, trace_path="results/phase3_3/tmp_t3.jsonl")
    r1, _, _ = run_and_analyze(a1, OPPONENT_CLASSES["expansion_oriented"](), 200, seed, "t", "det1")
    a1._planner._tracer.close()
    a2 = make_intervention_agent(intervention_fn=None, trace_path="results/phase3_3/tmp_t4.jsonl")
    r2, _, _ = run_and_analyze(a2, OPPONENT_CLASSES["expansion_oriented"](), 200, seed, "t", "det2")
    a2._planner._tracer.close()
    for p in ("results/phase3_3/tmp_t3.jsonl", "results/phase3_3/tmp_t4.jsonl"):
        if os.path.exists(p):
            os.remove(p)
    check("identical seed/opponent produces identical detection history (deterministic detector)",
          [h["active"] for h in [a1._detector.check(a1._opponent_logger.history, i) for i in range(1, 9)]] ==
          [h["active"] for h in [a2._detector.check(a2._opponent_logger.history, i) for i in range(1, 9)]])


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
    check("Planner v1 remains byte-for-byte unchanged after all Phase 3.3 experimentation", not mismatches)


def main():
    test_detection_only_is_inert()
    test_intervention_inactive_by_default()
    test_melon_redistribution_correctness()
    test_detector_reproducibility()
    test_control_still_frozen()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
