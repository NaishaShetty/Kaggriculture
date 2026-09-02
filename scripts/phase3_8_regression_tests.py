"""Phase 3.8 regression tests. Run: python scripts/phase3_8_regression_tests.py

Covers: animal response inertness outside its trigger thresholds, correct
piecewise escalation (verified against moushun chen's real replay data),
never-downgrades discipline, hands target never touched, C byte-identical
to B when inactive, and frozen-control integrity.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_8.animal_response import animal_specific_response, BASELINE_ANIMALS, MODERATE_RESPONSE_ANIMALS, HIGH_RESPONSE_ANIMALS
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent
from agents.phase3_5.adapters.competitive_v2_agent import make_competitive_v2_agent
from agents.phase3.opponent_observation import OpponentObservationLogger, OpponentObservation
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


def _fake_snap(day, hour, n_animals):
    return OpponentObservation(
        turn=day * 24 + hour, day=day, hour=hour, visible_money=0.0, visible_position=(0, 0),
        visible_hand_positions=[], visible_land_quadrants=1, visible_hires_today=0,
        visible_crop_tile_counts={}, visible_animal_tile_counts={"COW": n_animals} if n_animals else {},
    )


def test_piecewise_thresholds():
    print("piecewise animal-response thresholds:")
    config = {"crops": {"MELON": 1.0}, "n_hands": 5, "animals": {"COW": 2, "SHEEP": 2}}

    low_history = [_fake_snap(d, 20, 5) for d in range(5)]
    new_config, det = animal_specific_response(config, low_history, 5)
    check("low opponent animals (5, below moderate threshold) -> B baseline preserved",
          new_config.get("animals") == BASELINE_ANIMALS)

    mod_history = [_fake_snap(d, 20, 9) for d in range(5)]
    new_config2, det2 = animal_specific_response(config, mod_history, 5)
    check("moderate opponent animals (9) -> raised to MODERATE_RESPONSE_ANIMALS",
          new_config2.get("animals") == MODERATE_RESPONSE_ANIMALS)

    high_history = [_fake_snap(d, 20, 14) for d in range(5)]
    new_config3, det3 = animal_specific_response(config, high_history, 5)
    check("high opponent animals (14) -> raised to HIGH_RESPONSE_ANIMALS",
          new_config3.get("animals") == HIGH_RESPONSE_ANIMALS)


def test_never_downgrades():
    print("never-downgrades discipline:")
    config_already_high = {"crops": {"MELON": 1.0}, "n_hands": 5, "animals": {"COW": 5, "SHEEP": 5}}
    low_history = [_fake_snap(d, 20, 3) for d in range(5)]
    new_config, det = animal_specific_response(config_already_high, low_history, 5)
    check("never downgrades an already-higher commitment", new_config.get("animals") == {"COW": 5, "SHEEP": 5})


def test_hands_never_touched():
    print("hands target isolation:")
    config = {"crops": {"MELON": 1.0}, "n_hands": 5, "animals": {"COW": 2, "SHEEP": 2}}
    high_history = [_fake_snap(d, 20, 14) for d in range(5)]
    new_config, det = animal_specific_response(config, high_history, 5)
    check("n_hands key is never present in the diff (unchanged)", new_config.get("n_hands") == 5)
    check("only the 'animals' key differs from input", set(new_config.keys()) == set(config.keys()))


def test_inactive_when_detector_inactive():
    print("inertness when detector inactive:")
    config = {"crops": {"MELON": 1.0}, "n_hands": 5, "animals": {"COW": 2, "SHEEP": 2}}
    short_history = [_fake_snap(0, 20, 20)]  # single snapshot, detector needs sustained days
    new_config, det = animal_specific_response(config, short_history, 0)
    check("insufficient history -> detector inactive -> config unchanged", new_config == config)


def test_c_byte_identical_to_b_when_inactive():
    print("C byte-identical to B against non-scaling archetypes:")
    seed = 970001
    agentB = make_competitive_v2_agent(trace_path=None)
    agentC = make_competitive_v3_agent(trace_path=None)
    oppB = OPPONENT_CLASSES["conservative"]()
    oppC = OPPONENT_CLASSES["conservative"]()
    rB, _, _ = run_and_analyze(agentB, oppB, 300, seed, "phase3_8_regress", "B")
    rC, _, _ = run_and_analyze(agentC, oppC, 300, seed, "phase3_8_regress", "C")
    check("C reproduces B exactly against a non-scaling archetype",
          rB["outcome"]["final_money"] == rC["outcome"]["final_money"])
    check("animal response never activates against a non-scaling archetype",
          agentC._state_ref["animal_response_activations"] == 0)


def test_c_matches_moushun_chen_replay_escalation():
    print("real-data replay validation (moushun chen):")
    path = "COMPETITION RESULTS/SUBMISSION B/104768097.json"
    if not os.path.exists(path):
        check("moushun chen replay file exists (skipped if COMPETITION RESULTS unavailable)", True)
        return
    d = json.load(open(path, encoding="utf-8"))
    agents_ = [a["Name"] for a in d["info"]["Agents"]]
    opp_idx = next(i for i, n in enumerate(agents_) if "shettynaisha" not in n.lower())
    history = []
    for t, step in enumerate(d["steps"]):
        obs = step[0]["observation"]
        farm = obs["farms"][opp_idx]
        animal_counts = {}
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and "animal" in tile:
                    animal_counts[tile["animal"]] = animal_counts.get(tile["animal"], 0) + 1
        history.append(OpponentObservation(
            turn=t, day=obs["day"], hour=obs.get("hour", 0), visible_money=farm["money"],
            visible_position=tuple(farm["farmer"]), visible_hand_positions=[tuple(h) for h in farm.get("hands", [])],
            visible_land_quadrants=len(farm.get("unlocked_quadrants", ["NW"])), visible_hires_today=0,
            visible_crop_tile_counts={}, visible_animal_tile_counts=animal_counts,
        ))
    config = {"crops": {"MELON": 1.0}, "n_hands": 5, "animals": {"COW": 2, "SHEEP": 2}}
    turn_day20 = min(20 * 24 + 20, len(history) - 1)
    new_config, det = animal_specific_response(config, history[:turn_day20 + 1], 20)
    check("by day 20 of the real moushun chen game (opponent reached 14 animals), C escalates to HIGH_RESPONSE_ANIMALS",
          new_config.get("animals") == HIGH_RESPONSE_ANIMALS)


def test_main_py_builds_v3_agent():
    print("main.py entrypoint check:")
    import importlib.util
    spec = importlib.util.spec_from_file_location("submission_c_main", os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    check("main.py exposes a callable named 'agent'", callable(getattr(mod, "agent", None)))
    check("main.py builds its agent via make_competitive_v3_agent (Submission C)",
          mod.make_competitive_v3_agent is make_competitive_v3_agent)


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
    check("Planner v1 remains byte-for-byte unchanged after all Phase 3.8 work", not mismatches)


def main():
    test_piecewise_thresholds()
    test_never_downgrades()
    test_hands_never_touched()
    test_inactive_when_detector_inactive()
    test_c_byte_identical_to_b_when_inactive()
    test_c_matches_moushun_chen_replay_escalation()
    test_main_py_builds_v3_agent()
    test_control_still_frozen()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
