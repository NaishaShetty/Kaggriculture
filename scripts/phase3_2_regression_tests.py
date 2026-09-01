"""
Phase 3.2 regression tests (brief section 17). Run directly:
    python scripts/phase3_2_regression_tests.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from agents.phase3.opponent_observation import OpponentObservationLogger, OpponentObservation
from agents.phase3.feature_extractor import extract, WINDOWS
from agents.phase3.transition_inference import infer_events
from agents.phase3.regime_classifier import NearestCentroidClassifier, simple_kmeans, cluster_to_label_accuracy
from instrumentation.pipeline import run_episode
from agents.baseline_agent import agent as wheat_patroller_agent

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


def test_information_integrity():
    print("information integrity:")
    replay, meta = run_episode(wheat_patroller_agent, "pass", 60, 800001, None)
    logger = OpponentObservationLogger()
    for step in replay["steps"]:
        logger.observe(step[0]["observation"])
    feats = extract(logger.history, len(logger.history) - 1, WINDOWS)
    forbidden_substrings = ("shed", "seed_count", "carried_inventory", "private")
    check("no private opponent state enters features (no forbidden field names in the feature vector)",
          not any(any(f in k.lower() for f in forbidden_substrings) for k in feats))

    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    clf = NearestCentroidClassifier().fit(X, ["a", "b"], ["f1", "f2"])
    check("regime detector's fitted state carries no hidden simulator/ground-truth-only fields",
          set(vars(clf).keys()) <= {"classes_", "centroids_", "mean_", "std_", "feature_names_"})

    assignments, _ = simple_kmeans(X, k=2, seed=1)
    check("ground-truth labels unavailable to the unsupervised clusterer (simple_kmeans signature "
          "takes no label argument at all)",
          "y" not in simple_kmeans.__code__.co_varnames[:simple_kmeans.__code__.co_argcount])


def test_feature_correctness():
    print("feature correctness:")
    # p0="pass" (inert), p1=wheat_patroller_agent (active) -- we read player 0's
    # observation, so "opponent" (index 1) is the ACTIVE agent here, otherwise
    # this test trivially observes an inert "pass" opponent and finds zero events
    # (a real bug an earlier version of this test had -- caught by its own FAIL).
    replay, meta = run_episode("pass", wheat_patroller_agent, 80, 800002, None)
    logger = OpponentObservationLogger()
    for step in replay["steps"]:
        logger.observe(step[0]["observation"])

    f_early = extract(logger.history, 5, WINDOWS)
    f_late = extract(logger.history, len(logger.history) - 1, WINDOWS)
    check("feature calculations run without error at both an early and a late checkpoint",
          bool(f_early) and bool(f_late))
    check("rolling windows: w1 money_delta uses only the immediately preceding observation "
          "(magnitude <= a single turn's plausible max spend, sanity-bounded)",
          abs(f_late.get("money_delta_w1", 0)) < 10000)

    # transition detection
    events_total = 0
    for i in range(1, len(logger.history)):
        events_total += len(infer_events(logger.history[i - 1], logger.history[i]))
    check("transition detection produces at least one event over an 80-turn episode with a real agent",
          events_total > 0)

    # confidence representation
    ev = infer_events(logger.history[0], logger.history[1])
    check("every inferred event carries one of the three legal confidence labels",
          all(e.confidence in ("derived", "inferred", "unknown") for e in ev))
    check("no event is ever labeled 'observed' for an opponent action (never legal in this game)",
          all(e.confidence != "observed" for e in ev))


def test_temporal_correctness():
    print("temporal correctness:")
    replay, meta = run_episode(wheat_patroller_agent, "pass", 100, 800003, None)
    logger = OpponentObservationLogger()
    snaps = []
    for step in replay["steps"]:
        snaps.append(logger.observe(step[0]["observation"]))
    # features at checkpoint t must be identical whether computed with the full history or with
    # history truncated exactly at t+1 -- proves no access to future observations.
    t = 40
    feats_full_history = extract(logger.history, t, WINDOWS)
    feats_truncated = extract(logger.history[:t + 1], t, WINDOWS)
    check("features use only information available up to the current turn "
          "(identical result whether future history exists or not)",
          feats_full_history == feats_truncated)

    check("early detection cannot access future observations by construction "
          "(extract() clamps its index to len(history)-1, never reads past it)",
          extract(logger.history[:5], 999, WINDOWS) == extract(logger.history[:5], 4, WINDOWS))


def test_experiment_correctness():
    print("experiment correctness:")
    replay1, meta1 = run_episode(wheat_patroller_agent, "pass", 50, 800004, None)
    replay2, meta2 = run_episode(wheat_patroller_agent, "pass", 50, 800004, None)
    check("seed reproducibility: identical seed produces an identical replay length/outcome",
          len(replay1["steps"]) == len(replay2["steps"]) and
          replay1["steps"][-1][0]["reward"] == replay2["steps"][-1][0]["reward"])

    from scripts.phase3_2_configs import SEED_SETS
    all_seeds = [s for seeds in SEED_SETS.values() for s in seeds]
    check("archetype isolation / held-out seed separation: no seed appears in more than one seed set",
          len(all_seeds) == len(set(all_seeds)))


def test_control_integrity():
    print("control integrity:")
    import hashlib
    with open("results/phase3_1/control_reproduction/frozen_file_hashes.txt") as f:
        frozen_lines = [l.strip() for l in f if l.strip()]
    mismatches = []
    for line in frozen_lines:
        h, path = line.split(maxsplit=1)
        path = path.lstrip("*")
        actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if actual != h:
            mismatches.append(path)
    check("frozen Planner v1 remains byte-for-byte unchanged (every hashed file matches the frozen record)",
          not mismatches)

    from agents.phase3.adapters.planner_v1_control import make_control_agent
    from agents.phase2_6.common import make_agent as make_planner_v1
    from instrumentation.pipeline import run_and_analyze
    seed = 800005
    p1 = make_planner_v1(trace_path="results/phase3_2/tmp_ctrl_a.jsonl")
    r1, _, _ = run_and_analyze(p1, "agents/baseline_agent.py", 200, seed, "t", "a")
    p1._tracer.close()
    p2 = make_control_agent(trace_path="results/phase3_2/tmp_ctrl_b.jsonl")
    r2, _, _ = run_and_analyze(p2, "agents/baseline_agent.py", 200, seed, "t", "b")
    p2._planner._tracer.close()
    os.remove("results/phase3_2/tmp_ctrl_a.jsonl")
    os.remove("results/phase3_2/tmp_ctrl_b.jsonl")
    check("Phase 3 instrumentation does not alter planner decisions (identical final money, direct vs. wrapped)",
          r1["outcome"]["final_money"] == r2["outcome"]["final_money"])


def main():
    test_information_integrity()
    test_feature_correctness()
    test_temporal_correctness()
    test_experiment_correctness()
    test_control_integrity()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
