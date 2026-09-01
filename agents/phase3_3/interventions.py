"""
Phase 3.3 targeted interventions -- pure functions that take Planner v1's
OWN chosen `config` (never modifying Planner v1's code) and the current
observable state, and return a MODIFIED config to apply instead, ONLY when
the expansion-oriented detector is active. Every intervention is documented
with: what changed, why (which Phase 3.2 observation motivated it), what
should happen if the hypothesis is correct, and what would falsify it --
per the brief's section 5 discipline.
"""
from economic_model.model import EconomicState, crop_production_value

NON_MELON_CANDIDATES = ["WHEAT", "STRAWBERRY", "CARROT", "TOMATO"]


def _redistribute_away_from_melon(crops: dict, substitute: str = None):
    """Removes MELON's fraction from the portfolio, redistributing it to
    `substitute` if given, else proportionally to the remaining crops
    (falling back to 100% WHEAT if MELON was the only crop)."""
    if not crops or "MELON" not in crops:
        return dict(crops or {})
    melon_frac = crops["MELON"]
    remaining = {c: f for c, f in crops.items() if c != "MELON"}
    if substitute:
        remaining[substitute] = remaining.get(substitute, 0.0) + melon_frac
        return remaining
    if not remaining:
        return {"WHEAT": 1.0}
    total = sum(remaining.values())
    return {c: f + (f / total) * melon_frac for c, f in remaining.items()}


def variant_c_melon_avoidance(config, state, detector_result):
    """
    WHAT CHANGED: MELON's fraction of the crop portfolio is set to 0 and
      redistributed proportionally across whatever other crops the planner
      already has (falls back to WHEAT if MELON was the sole crop). No
      existing planted tiles are dug up (per the brief: "do not destroy
      existing assets merely to force a result") -- this only affects what
      the tactical layer plants GOING FORWARD (agents/phase2_4/common.py's
      own crop_assignment recomputes from the current `crops` fraction dict
      every turn, so already-growing MELON tiles are harvested normally,
      only NEW planting stops targeting MELON).
    WHY: Phase 3.2 (section 6) directly observed MELON's market price
      collapsing to $4-10 (vs $108-120 for a passive opponent) specifically
      when facing expansion_oriented -- the single most direct, evidence-
      backed lever available is to stop adding MORE MELON supply to an
      already-oversupplied shared market.
    PREDICTION IF CORRECT: protagonist MELON revenue and overall final money
      against expansion_oriented should measurably improve versus the
      unmodified Planner v1 control, with win rate improving from 0%.
    FALSIFIED IF: final money/win rate against expansion_oriented does NOT
      improve, or improves only marginally while WHEAT/substitute crop
      revenue fails to compensate for lost MELON revenue.
    """
    if not detector_result["active"]:
        return config
    new_config = dict(config)
    new_config["crops"] = _redistribute_away_from_melon(config.get("crops") or {})
    return new_config


def variant_d_production_substitution(config, state, detector_result):
    """
    WHAT CHANGED: MELON's fraction is redistributed to whichever SINGLE
      non-MELON crop the frozen Phase 2.5 economic_model currently ranks
      highest by crop_production_value() given the CURRENT state (not a
      hard-coded "always STRAWBERRY" choice -- the brief explicitly warns
      "do not assume another crop is superior, measure it"; here we defer
      to the already-validated model rather than inventing a new ranking).
    WHY: same market-oversupply motivation as Variant C, but tests whether
      DELIBERATELY choosing the best-ranked alternative (rather than a
      passive proportional split) captures more of the freed production
      capacity's value.
    PREDICTION IF CORRECT: should perform AT LEAST as well as Variant C,
      and better if the model's crop ranking meaningfully favors one
      specific substitute over an even split.
    FALSIFIED IF: performs no better (or worse) than Variant C, suggesting
      the substitute-crop choice doesn't matter as much as simply reducing
      MELON exposure.
    """
    if not detector_result["active"]:
        return config
    best_crop, best_value = None, None
    for candidate in NON_MELON_CANDIDATES:
        est = crop_production_value(candidate, state, n_tiles=10)
        if est.value is not None and (best_value is None or est.value > best_value):
            best_crop, best_value = candidate, est.value
    new_config = dict(config)
    new_config["crops"] = _redistribute_away_from_melon(config.get("crops") or {}, substitute=best_crop)
    return new_config


def variant_e_market_timing(config, state, detector_result):
    """
    WHAT CHANGED: the SELLING policy (not the crop portfolio) switches to
      `threshold` mode at threshold_frac=1.5 (hold out for 1.5x base price,
      not just 1.0x) with the mandatory `horizon_aware` F16 safety net still
      enabled -- MELON production is UNCHANGED, only when it gets sold
      changes. Uses ONLY the already-documented Phase 2.4 selling-policy
      mechanism (agents/phase2_4/common.py) -- no new mechanic invented.

      IMPORTANT DISCOVERY THAT SHAPED THIS DESIGN: an initial version of
      this intervention used threshold_frac=1.0 and was found, by direct
      inspection, to be a COMPLETE NO-OP -- Planner v1 ALREADY independently
      chooses exactly `{"mode":"threshold","threshold_frac":1.0,
      "horizon_aware":True}` for a simple MELON-solo portfolio on its own
      (consistent with F14's finding that threshold selling beats passive
      for simple portfolios). This is itself a real finding, not a bug (see
      the Phase 3.3 report's failure-analysis section): the frozen planner's
      selling behavior is ALREADY reasonably sophisticated, so a genuinely
      different intervention must go further than the planner's own default,
      hence 1.5x rather than 1.0x here.
    WHY: tests whether the damage is avoidable purely through MORE
      AGGRESSIVE TIMING (holding out longer than the planner already does)
      rather than reducing production -- the more conservative,
      production-preserving hypothesis.
    PREDICTION IF CORRECT: MELON average realized price should rise
      relative to Planner v1's own (already-threshold) baseline, recovering
      some final money, without reducing total MELON units harvested.
    FALSIFIED IF: no meaningful price/revenue improvement over the
      un-intervened baseline, OR F16-style stranding occurs despite the
      horizon-aware safety net -- consistent with Phase 2.4's F19 (market-
      aware selling did not reliably help the strongest INTEGRATED
      portfolio) extending to this adversarial case too, i.e. the oversupply
      is severe/sustained enough that holding out even longer doesn't help
      because the price never meaningfully recovers while the opponent
      keeps flooding the market.
    """
    if not detector_result["active"]:
        return config
    new_config = dict(config)
    new_config["sell_policy"] = {"mode": "threshold", "threshold_frac": 1.5, "horizon_aware": True}
    return new_config


def variant_f_combined(config, state, detector_result):
    """
    WHAT CHANGED: applies whichever of Variant D (production substitution)
      and Variant E (market timing) individually showed measurable promise
      in Stage 1 (brief section 4: "Only create this variant if individual
      interventions demonstrate measurable promise") -- populated dynamically
      by scripts/phase3_3_run_experiments.py based on Stage 1 results, not
      hard-coded in advance.
    """
    if not detector_result["active"]:
        return config
    cfg = variant_d_production_substitution(config, state, detector_result)
    cfg = variant_e_market_timing(cfg, state, detector_result)
    return cfg


INTERVENTIONS = {
    "B_detection_only": None,
    "C_melon_avoidance": variant_c_melon_avoidance,
    "D_production_substitution": variant_d_production_substitution,
    "E_market_timing": variant_e_market_timing,
    "F_combined": variant_f_combined,
}
