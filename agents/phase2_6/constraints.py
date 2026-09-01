"""
Phase 2.6 constraint engine. Classifies each evaluated candidate into
exactly one of three DISTINCT categories (never collapsed into one boolean,
per the brief section 33.6):

  HARD        -- cannot legally/safely happen (insufficient cash, past the
                 planting/selling horizon, etc.)
  ECONOMIC    -- legal, but the model's own net_expected_value is <= 0
  UNCERTAIN   -- model_status == UNKNOWN (insufficient calibration)
  OK          -- passes every check, net_expected_value > 0, confidence known
"""
from economic_model.model import TOTAL_DAYS, SHED_CAPACITY, latest_safe_plant_day


def classify(evaluated, state):
    candidate = evaluated["candidate"]
    kind = candidate["kind"]
    reasons = []

    # --- HARD constraints ---
    if state.cash < candidate["direct_cost"]:
        reasons.append(f"insufficient cash: have ${state.cash}, need ${candidate['direct_cost']}")
    if state.day >= TOTAL_DAYS - 1:
        reasons.append("no remaining days to act on any new commitment")
    if kind == "SWITCH_PORTFOLIO":
        for crop in candidate["params"]["crops"]:
            lspd = latest_safe_plant_day(crop)
            if state.day > lspd:
                reasons.append(f"day {state.day} is past latest_safe_plant_day({lspd}) for {crop}")
    if reasons:
        return {"category": "HARD", "reasons": reasons}

    # --- UNCERTAIN ---
    if evaluated["model_status"] == "UNKNOWN":
        return {"category": "UNCERTAIN",
                "reasons": [f"economic_model returned UNKNOWN via {evaluated['model_function_used']}: "
                            f"{evaluated['expected_value'].basis}"]}

    # --- ECONOMIC (legal + known, but not worth it) ---
    net = evaluated["net_expected_value"]
    if net is None or net <= 0:
        return {"category": "ECONOMIC", "reasons": [f"net_expected_value={net} <= 0"]}

    # --- shed pressure note (informational, not blocking on its own --
    # F12/F17 distinction preserved: only genuinely relevant for SELL-lane
    # candidates and BUY_ANIMAL/production-increasing candidates) ---
    shed_frac = state.shed_total / SHED_CAPACITY
    if shed_frac > 0.85 and kind in ("BUY_ANIMAL", "SWITCH_PORTFOLIO"):
        reasons.append(f"shed at {shed_frac*100:.0f}% capacity -- production increase adds shed-overflow risk (F17)")

    return {"category": "OK", "reasons": reasons or ["passes all constraints"]}
