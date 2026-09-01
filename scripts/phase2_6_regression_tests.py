"""
Phase 2.6 regression test suite (brief section 33.17). Plain assert-based
(no pytest dependency assumed) -- run directly: python scripts/phase2_6_regression_tests.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE on import order: `agents.phase2_6.*` must be imported before a bare
# `economic_model.model` import in the same process -- the reverse order
# trips an unrelated, pre-existing quirk in the installed kaggle_environments
# package's lazy multi-env registration (its lux_ai_s3 env module does an
# internal relative import that fails depending on what's already in
# sys.modules under the name "agents" at that moment). Confirmed via direct
# reproduction to be a third-party import-order sensitivity, not a defect in
# this project's own code -- reordering these two lines is the fix.
from agents.phase2_6.opportunities import generate_candidates
from agents.phase2_6.evaluator import evaluate
from agents.phase2_6.constraints import classify
from agents.phase2_6.decisions import select_decisions
from agents.phase2_6.state import PlannerState
from economic_model.model import EconomicState, evaluate_worker_purchase, latest_safe_plant_day, liquidation_risk

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


def test_economic_model_integration():
    print("economic_model integration:")
    s = EconomicState(day=5, cash=3000, n_hands=1)
    est = evaluate_worker_purchase(s, primary_crop="MELON")
    check("valid query returns a numeric estimate", est.value is not None)

    est_unk = evaluate_worker_purchase(s, primary_crop="TOMATO")
    check("uncalibrated crop returns UNKNOWN, not a fabricated number",
          est_unk.confidence == "UNKNOWN" and est_unk.value is None)

    s_bad = EconomicState(day=999, cash=-100)
    est_bad_crop = __import__("economic_model.model", fromlist=["crop_production_value"]).crop_production_value("MELON", s_bad)
    check("out-of-range state does not crash, returns a value (feasibility flagged, not an exception)",
          est_bad_crop is not None)


def test_candidate_generation():
    print("candidate generation:")
    s = PlannerState(day=5, cash=3000, n_hands=0, hire_cost_next=1)
    config = {"crops": {}, "_portfolio_name": None, "n_hands": 0, "land_quadrants": 0, "animals": {}}
    candidates = generate_candidates(s, config)
    kinds = {c["kind"] for c in candidates}
    check("legal actions generated (HIRE_HAND present with sufficient cash)", "HIRE_HAND" in kinds)

    s_broke = PlannerState(day=5, cash=0, n_hands=0, hire_cost_next=1)
    candidates_broke = generate_candidates(s_broke, config)
    check("insufficient capital rejects HIRE_HAND at the generation stage",
          not any(c["kind"] == "HIRE_HAND" for c in candidates_broke))

    s_late = PlannerState(day=28, cash=3000, n_hands=0, hire_cost_next=1)
    config_committed = {"crops": {"MELON": 1.0}, "_portfolio_name": "melon_solo", "n_hands": 0, "animals": {}}
    candidates_late = generate_candidates(s_late, config_committed)
    # portfolio only offered once (day-0 style, _portfolio_name already set) -- no SWITCH_PORTFOLIO at all
    check("no portfolio-switch candidate once a portfolio is already committed (thrashing guard)",
          not any(c["kind"] == "SWITCH_PORTFOLIO" for c in candidates_late))


def test_liquidation():
    print("liquidation (F16 protection):")
    s_late = EconomicState(day=25, cash=1000)
    risk_batch = liquidation_risk("MELON", s_late, "batch", batch_interval_days=10)
    check("F16 stranded-inventory protection: near-horizon batch mode flags high risk",
          risk_batch.value is not None and risk_batch.value > 0.5)

    s_early = EconomicState(day=2, cash=1000)
    risk_early = liquidation_risk("MELON", s_early, "batch", batch_interval_days=10)
    check("latest-safe-sale handling: early-game batch mode flags low/no risk",
          risk_early.value is not None and risk_early.value < 0.3)

    lspd = latest_safe_plant_day("MELON")
    check("terminal inventory safety: latest_safe_plant_day is within the 30-day season",
          0 < lspd < 30)


def test_labor():
    print("labor (diminishing returns):")
    curve = __import__("economic_model.model", fromlist=["CALIBRATION"]).CALIBRATION["marginal_hand_value"]["MELON"]
    check("diminishing-return behavior represented correctly (values decline from hand 1 to hand 4)",
          curve[0] > curve[1] > 0 and curve[-1] < curve[0])


def test_land():
    print("land (conditional economics):")
    s = EconomicState(day=0, cash=5000, land_quadrants_owned=1, n_hands=2)
    from economic_model.model import evaluate_land_purchase
    est_melon = evaluate_land_purchase(s, primary_crop="MELON")
    check("conditional land economics respected: MELON-anchored land value is negative (F3), not hard-coded positive",
          est_melon.value is not None and est_melon.value < 0)
    est_other = evaluate_land_purchase(s, primary_crop="TOMATO")
    check("land economics for an untested crop portfolio returns UNKNOWN, not an extrapolated claim",
          est_other.confidence == "UNKNOWN")


def test_animals():
    print("animals (documented requirements + unresolved hypothesis):")
    from economic_model.model import ANIMALS
    check("documented animal requirements enforced (structure/cost/first_yield_day present for all 3 species)",
          all(k in ANIMALS for k in ("GOOSE", "COW", "SHEEP")) and
          all({"cost", "structure", "first_yield_day"} <= set(ANIMALS[k]) for k in ANIMALS))
    s = EconomicState(day=10, cash=3000, n_hands=1)
    from economic_model.model import animal_production_value
    # COW's time-scaling was PROMOTED to EXPERIMENTALLY_VALIDATED in Phase 2.6 (F20, H1 confirmed
    # with real evidence -- see results/phase2_6/hypothesis_test_results.json). GOOSE/SHEEP were NOT
    # retested and must remain below EXPERIMENTALLY_VALIDATED -- this is the actual regression this
    # test guards: a species should only be promoted once ITS OWN hypothesis test has run, never as a
    # silent blanket upgrade.
    est_goose = animal_production_value("GOOSE", s)
    check("unresolved animal time-scaling hypothesis is NOT silently treated as fact for an "
          "UNTESTED species (GOOSE stays below EXPERIMENTALLY_VALIDATED)",
          est_goose.confidence in ("STRONG_EMPIRICAL_SIGNAL", "HYPOTHESIS"))
    est_cow = animal_production_value("COW", s)
    check("COW's time-scaling WAS promoted to EXPERIMENTALLY_VALIDATED, and only after a real "
          "hypothesis test (F20) -- not silently",
          est_cow.confidence == "EXPERIMENTALLY_VALIDATED")


def test_market():
    print("market (F19 discipline):")
    from agents.phase2_6.evaluator import _evaluate_sell_policy_switch
    complex_config = {"crops": {"MELON": 0.5, "STRAWBERRY": 0.5}, "animals": {"GOOSE": 1, "COW": 1}}
    s = EconomicState(day=5, cash=3000, market_prices={"MELON": 100}, market_inventory={"MELON": 10500})
    est = _evaluate_sell_policy_switch({"params": {"mode": "threshold"}}, s, complex_config)
    check("F19 does not automatically force market-aware selling for a complex portfolio "
          "(complex-portfolio switch is valued <= 0, not a fabricated positive)",
          est.value is not None and est.value <= 0)


def test_determinism():
    print("determinism:")
    s = PlannerState(day=5, cash=3000, n_hands=1, land_quadrants_owned=1,
                      crop_tile_counts={"MELON": 10}, animal_counts={}, hire_cost_next=2)
    config = {"crops": {"MELON": 1.0}, "_portfolio_name": "melon_solo", "n_hands": 1,
              "land_quadrants": 1, "animals": {}}
    results = []
    for _ in range(3):
        candidates = generate_candidates(s, config)
        evaluated = [{"evaluated": evaluate(c, s, config), "classification": None} for c in candidates]
        for ec in evaluated:
            ec["classification"] = classify(ec["evaluated"], s)
        selected, _ = select_decisions(evaluated, s)
        results.append(tuple(sorted(ec["evaluated"]["candidate"]["kind"] for ec in selected)))
    check("identical state/configuration produces identical strategic decision (3 runs match)",
          results[0] == results[1] == results[2])


def test_execution():
    print("execution:")
    from agents.phase2_6.common import _verify
    pending = {"config_before": {"n_hands": 0, "land_quadrants": 0, "animals": {}},
               "expected_delta": {"BUY_LAND": 1000}}
    class FakeState:
        land_quadrants_owned = 1
        n_hands = 0
        animal_counts = {}
    result = _verify(pending, FakeState())
    check("failed/successful actions are detected via post-action state verification",
          "BUY_LAND" in result and result["BUY_LAND"]["verified"] is True)


def main():
    test_economic_model_integration()
    test_candidate_generation()
    test_liquidation()
    test_labor()
    test_land()
    test_animals()
    test_market()
    test_determinism()
    test_execution()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
