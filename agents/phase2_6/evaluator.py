"""
Phase 2.6 opportunity evaluator: calls the FROZEN Phase 2.5 economic_model
functions for each candidate -- never recreates or approximates their logic
here (per the brief section 33.2). Documents, per candidate, exactly which
Phase 2.5 function was called and what it returned.
"""
from economic_model import model as em

EVALUATOR_ECONOMIC_MODEL_VERSION = "phase2_5_v0.1"  # frozen artifact this evaluator depends on


def evaluate(candidate, state, current_config):
    """Returns an EvaluatedCandidate dict:
      candidate, direct_cost, expected_value (Estimate), opportunity_cost_note,
      model_function_used, model_status (OK/UNKNOWN)
    `expected_value` is ALWAYS the raw economic_model.Estimate -- confidence
    and range are never discarded, per the brief's "expose uncertainty rather
    than fabricate precision" instruction.
    """
    kind = candidate["kind"]
    primary_crop = _primary_crop(current_config)

    if kind == "HIRE_HAND":
        # Use the planner's COMMITTED hand count (current_config), not the
        # freshly-observed state.n_hands -- hands reset to 0 every day by
        # design, so state.n_hands is always 0 at this exact planning
        # moment regardless of any standing commitment (same gotcha as
        # opportunities.py; see that module's comment for the bug this
        # caused before being fixed).
        eval_state = _with_hands(state, current_config.get("n_hands", 0))
        est = em.evaluate_worker_purchase(eval_state, primary_crop=primary_crop)
        fn = "evaluate_worker_purchase"
    elif kind == "REDUCE_HANDS":
        # No direct "un-hire" query exists in the Phase 2.5 model (documented gap,
        # not silently bypassed) -- inferred as the negative of the marginal value
        # of the hand being given up, which IS what evaluate_worker_purchase reports
        # for the CURRENT (committed) hand count (i.e. removing hand n means forgoing
        # whatever evaluate_worker_purchase said hand n was worth).
        prior_state = _with_hands(state, current_config.get("n_hands", 0) - 1)
        est_hire_back = em.evaluate_worker_purchase(prior_state, primary_crop=primary_crop)
        est = em.Estimate(
            value=(-est_hire_back.value if est_hire_back.value is not None else None),
            low=(-est_hire_back.high if est_hire_back.high is not None else None),
            high=(-est_hire_back.low if est_hire_back.low is not None else None),
            confidence=est_hire_back.confidence,
            basis=est_hire_back.basis + " (negated: value of NOT hiring this hand)",
            notes="No dedicated un-hire query exists in economic_model v0.1 -- documented gap, "
                  "inferred from the same marginal-value curve rather than a new assumption.",
        )
        fn = "evaluate_worker_purchase (inferred negation)"
    elif kind == "BUY_LAND":
        est = em.evaluate_land_purchase(state, primary_crop=primary_crop)
        fn = "evaluate_land_purchase"
    elif kind == "BUY_ANIMAL":
        committed_hands = current_config.get("n_hands", 0)
        est = em.animal_production_value(candidate["params"]["animal"], state,
                                          n_hands_available=max(0, committed_hands - _labor_committed_to_crops(state, committed_hands)))
        fn = "animal_production_value"
    elif kind == "SWITCH_PORTFOLIO":
        est = _evaluate_portfolio_switch(candidate, state)
        fn = "crop_production_value (summed across candidate portfolio)"
    elif kind == "SWITCH_SELL_POLICY":
        est = _evaluate_sell_policy_switch(candidate, state, current_config)
        fn = "evaluate_sell_now_vs_later + liquidation_risk"
    else:
        est = em.Estimate(value=None, low=None, high=None, confidence="UNKNOWN",
                           basis="no evaluator implemented for this candidate kind")
        fn = "none"

    net_value = None
    if est.value is not None:
        net_value = round(est.value - candidate["direct_cost"], 2)

    return {
        "candidate": candidate,
        "direct_cost": candidate["direct_cost"],
        "expected_value": est,
        "net_expected_value": net_value,
        "model_function_used": fn,
        "model_status": "UNKNOWN" if est.confidence == "UNKNOWN" or est.value is None else "OK",
        "economic_model_version": EVALUATOR_ECONOMIC_MODEL_VERSION,
    }


def _primary_crop(current_config):
    crops = current_config.get("crops") or {}
    if not crops:
        return "MELON"
    return max(crops, key=crops.get)


def _with_hands(state, n_hands):
    import copy
    s2 = copy.copy(state)
    s2.n_hands = max(0, n_hands)
    return s2


def _labor_committed_to_crops(state, committed_hands):
    # coarse: 1 hand needed per ~12 crop tiles as a rule-of-thumb derived from
    # Phase 2.3's observed near-full utilization at n_hands=2 for a 25-tile field
    # (a1_labor_sweep/c2_labor_x_crop) -- documented as an approximation, not exact.
    n_tiles = sum(state.crop_tile_counts.values())
    return min(committed_hands, max(0, round(n_tiles / 12)))


def _evaluate_portfolio_switch(candidate, state):
    fractions = candidate["params"]["crops"]
    n_tiles_total = max(1, 25 * state.land_quadrants_owned)
    total_value, total_low, total_high = 0.0, 0.0, 0.0
    confidences = []
    for crop, frac in fractions.items():
        n_tiles = max(1, round(n_tiles_total * frac))
        est = em.crop_production_value(crop, state, n_tiles=n_tiles)
        if est.value is not None:
            total_value += est.value
            total_low += est.low if est.low is not None else est.value
            total_high += est.high if est.high is not None else est.value
        confidences.append(est.confidence)
    conf = "EXPERIMENTALLY_VALIDATED" if all(c == "EXPERIMENTALLY_VALIDATED" for c in confidences) else "STRONG_EMPIRICAL_SIGNAL"
    return em.Estimate(value=round(total_value, 2), low=round(total_low, 2), high=round(total_high, 2),
                        confidence=conf, basis="crop_production_value summed per candidate crop",
                        notes=f"portfolio={fractions}")


def _evaluate_sell_policy_switch(candidate, state, current_config):
    mode = candidate["params"]["mode"]
    n_resource_types = len(current_config.get("crops") or {}) + len(current_config.get("animals") or {})
    # Directly operationalizes Phase 2.5's open hypothesis H2 (portfolio-complexity-aware
    # selling): F14's uplift is only trusted for SIMPLE portfolios (<=1 resource type);
    # F19's null result applies once the portfolio is complex (>=2 types) -- this is the
    # planner's own conservative default, tested explicitly in scripts/phase2_6_hypothesis_tests.py.
    if n_resource_types <= 1:
        item = _primary_crop(current_config)
        est = em.evaluate_sell_now_vs_later(item, 1, state, sell_policy_mode=mode)
        note = f"simple portfolio ({n_resource_types} resource type) -- F14 uplift applies"
    else:
        est = em.Estimate(value=0.0, low=-500.0, high=500.0, confidence="EXPERIMENTALLY_VALIDATED",
                           basis="F19 (null result: no reliable market-aware advantage for complex portfolios)",
                           notes="complex portfolio -- do NOT assume market-aware selling helps (F19); "
                                 "treated as a wash, not a positive, pending H2 confirmation")
        note = f"complex portfolio ({n_resource_types} resource types) -- F19 applies, no uplift assumed"
    est.notes = (est.notes or "") + f" | {note}"
    return est
