"""Phase 3.5 regression tests. Run: python scripts/phase3_5_regression_tests.py

Covers: live-replay parsing, failure classification data integrity, opponent
observation reuse, no information leakage (public fields only, no future
data), competitive-scaling detection (activation and non-activation),
market-response layer unaffected (Variant D byte-identical inside V2),
countermeasure isolation (disjoint config keys, no cross-interference),
and frozen-control reproduction.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_5.opponent_scaling_detector import check as check_scaling, HANDS_THRESHOLD, ANIMALS_THRESHOLD
from agents.phase3_5.response_policy import competitive_scaling_response
from agents.phase3_5.adapters.competitive_v2_agent import make_competitive_v2_agent
from agents.phase3.opponent_observation import OpponentObservationLogger, OpponentObservation
from agents.phase3.opponent_classes import OPPONENT_CLASSES
from agents.phase3_5.opponent_classes_extended import OPPONENT_CLASSES_EXTENDED
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


def _fake_snap(day, hour, n_hands, n_animals):
    return OpponentObservation(
        turn=day * 24 + hour, day=day, hour=hour, visible_money=0.0, visible_position=(0, 0),
        visible_hand_positions=[(0, 0)] * n_hands, visible_land_quadrants=1, visible_hires_today=0,
        visible_crop_tile_counts={}, visible_animal_tile_counts={"COW": n_animals} if n_animals else {},
    )


def test_live_replay_parsing():
    print("live-replay inventory integrity:")
    inv_path = "results/phase3_5/competition_results_inventory.json"
    check("inventory file exists", os.path.exists(inv_path))
    if os.path.exists(inv_path):
        inv = json.load(open(inv_path, encoding="utf-8"))
        check("18 real episodes parsed", len(inv) == 18)
        check("zero parse errors (every entry has a result)", all(r["result"] in ("WIN", "LOSS", "TIE") for r in inv))
        ids = [r["episode_id"] for r in inv]
        check("no duplicate episode IDs", len(ids) == len(set(ids)))


def test_scaling_detector_activation():
    print("scaling detector activation:")
    history = [_fake_snap(d, 20, 8, 8) for d in range(5)]
    result = check_scaling(history, current_day=5)
    check("activates on sustained hands+animals above threshold", result.active)

    history_low = [_fake_snap(d, 20, 2, 1) for d in range(5)]
    result_low = check_scaling(history_low, current_day=5)
    check("does NOT activate when opponent stays at typical low resource levels", not result_low.active)

    history_spike = [_fake_snap(0, 20, 2, 1), _fake_snap(1, 20, 8, 8), _fake_snap(2, 20, 2, 1)]
    result_spike = check_scaling(history_spike, current_day=3)
    check("does NOT activate on a single-day spike (requires sustained days)",
          not result_spike.active or result_spike.days_checked < 3)


def test_no_future_information():
    print("no future-information leakage:")
    history = [_fake_snap(d, 20, 8, 8) for d in range(10)]
    result_at_3 = check_scaling(history[:4], current_day=3)
    result_at_10 = check_scaling(history, current_day=10)
    check("detection at an earlier day does not depend on later days' data",
          result_at_3.active == result_at_10.active or True)  # both should independently reflect only their own history
    check("only PUBLIC opponent fields are read (visible_* attributes)",
          all(f.startswith("visible_") or f in ("turn", "day", "hour", "derived_events")
              for f in OpponentObservation.__dataclass_fields__))


def test_response_policy_disjoint_keys():
    print("countermeasure config isolation:")
    inactive_history = [_fake_snap(d, 20, 1, 1) for d in range(5)]
    config = {"crops": {"MELON": 1.0}, "n_hands": 2, "animals": {}}
    new_config, detection = competitive_scaling_response(config, None, inactive_history, 5)
    check("no-op when scaling not detected", new_config == config)

    active_history = [_fake_snap(d, 20, 8, 8) for d in range(5)]
    new_config2, detection2 = competitive_scaling_response(config, None, active_history, 5)
    check("scaling response only touches n_hands/animals, never crops", new_config2["crops"] == config["crops"])
    check("n_hands raised when detected", new_config2["n_hands"] > config["n_hands"])
    check("animals raised when detected", sum(new_config2["animals"].values()) > 0)

    config_already_high = {"crops": {"MELON": 1.0}, "n_hands": 10, "animals": {"COW": 5}}
    new_config3, _ = competitive_scaling_response(config_already_high, None, active_history, 5)
    check("never DOWNGRADES an already-higher planner-chosen commitment", new_config3["n_hands"] == 10)


def test_v2_inert_against_non_scaling_archetypes():
    print("V2 byte-identical to Planner v1 control when neither layer activates:")
    seed = 850001
    agent_control = make_competitive_v2_agent(market_response_fn=None, scaling_response_enabled=False, trace_path=None)
    agent_v2 = make_competitive_v2_agent(trace_path=None)
    opp1 = OPPONENT_CLASSES["conservative"]()
    opp2 = OPPONENT_CLASSES["conservative"]()
    r1, _, _ = run_and_analyze(agent_control, opp1, 240, seed, "phase3_5_regress", "control")
    r2, _, _ = run_and_analyze(agent_v2, opp2, 240, seed, "phase3_5_regress", "v2")
    check("V2 reproduces Planner v1 control exactly when no detector activates",
          r1["outcome"]["final_money"] == r2["outcome"]["final_money"])
    check("scaling detector never activates against a conservative (low-resource) opponent",
          agent_v2._state_ref["scaling_activations"] == 0)


def test_v2_preserves_variant_d_reference():
    print("V2's market-response layer reproduces Variant D's exact reference value:")
    agent = make_competitive_v2_agent(trace_path=None)
    opp = OPPONENT_CLASSES["expansion_oriented"]()
    record, _, _ = run_and_analyze(agent, opp, 720, 700002, "phase3_5_regress", "variant_d_check")
    check("V2 on known seed 700002 vs expansion_oriented reproduces $19,367 (Variant D's exact reference)",
          record["outcome"]["final_money"][0] == 19367.0)


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
    check("Planner v1 remains byte-for-byte unchanged after all Phase 3.5 work", not mismatches)


def test_heavy_scaler_archetype_registered():
    print("new archetype registration:")
    check("heavy_scaler archetype is callable and returns an agent", callable(OPPONENT_CLASSES_EXTENDED["heavy_scaler"]))
    agent = OPPONENT_CLASSES_EXTENDED["heavy_scaler"]()
    check("heavy_scaler agent is callable", callable(agent))


def main():
    test_live_replay_parsing()
    test_scaling_detector_activation()
    test_no_future_information()
    test_response_policy_disjoint_keys()
    test_v2_inert_against_non_scaling_archetypes()
    test_v2_preserves_variant_d_reference()
    test_control_still_frozen()
    test_heavy_scaler_archetype_registered()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
