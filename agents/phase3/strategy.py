"""
Phase 3.1 strategy representation -- a DATA MODEL for what the project means
by "strategy" (brief section 12), plus MEASUREMENT of candidate regime
dimensions against existing Phase 2 evidence (brief section 13/30). No
strategy SELECTION logic lives here (that's strategy_interface.py's stub,
and real selection is explicitly Phase 3.2+ scope).

A strategy is a higher-level economic POLICY/REGIME (a configuration the
Economic Planner could run under), not a single action -- consistent with
how agents/phase2_6/common.py's `current_config` already works (crops,
n_hands, land_quadrants, animals, sell_policy). This module names and
measures regimes that config space already implicitly encodes.
"""
from dataclasses import dataclass, field

STRATEGY_DIMENSIONS = {
    # name -> (measurable_from, phase2_evidence_citation, classification)
    "production_heavy": {
        "measurable_from": "n_hands + land_quadrants + n active crop/animal resource types (from current_config)",
        "evidence": "F1/F2 (labor), F13 (integrated strategy dominance) -- Phase 2.3",
        "classification": "validated",
        "note": "the F13 integrated config IS this regime, empirically the strongest tested strategy",
    },
    "conservative_capital": {
        "measurable_from": "cash_reserve_frac, fraction of cash left uncommitted after planning cycles",
        "evidence": "no direct Phase 2 experiment varied a 'hold more cash' policy as its own IV",
        "classification": "hypothesis",
        "note": "plausible dimension (opposite of production_heavy) but never isolated and measured on its own",
    },
    "animal_oriented": {
        "measurable_from": "animal_counts relative to crop_tile_counts (from current_config/state)",
        "evidence": "F5/F6/F7 (Phase 2.3) -- animal profitability and crop-animal sub-additivity",
        "classification": "validated",
        "note": "measurable and economically meaningful; F7 shows it's a real, distinguishable resource-competition axis",
    },
    "crop_oriented": {
        "measurable_from": "crop_tile_counts relative to animal_counts",
        "evidence": "Phase 2.2 (crop economics), F13 (crop share of the winning portfolio)",
        "classification": "validated",
        "note": "the natural complement of animal_oriented on the same measured axis",
    },
    "market_aware": {
        "measurable_from": "sell_policy.mode != 'passive'",
        "evidence": "F14 (helps simple portfolios), F19 (no reliable help for complex ones)",
        "classification": "validated",
        "note": "measurable directly from config; its ECONOMIC VALUE is portfolio-complexity-CONDITIONAL (F19), not "
                "a strategy that is unconditionally 'better' -- do not treat market_aware=True as inherently superior",
    },
    "liquidity_preserving": {
        "measurable_from": "shed_occupancy relative to SHED_CAPACITY, and whether sell_policy forces frequent liquidation",
        "evidence": "F16/F17 (Phase 2.4) -- horizon stranding and shed overflow are the two risks this regime would mitigate",
        "classification": "promising",
        "note": "the RISK this regime addresses is validated (F16/F17); whether deliberately over-indexing on "
                "liquidity ever beats the planner's existing mandatory horizon_aware safety net is UNTESTED",
    },
    "expansion_oriented": {
        "measurable_from": "land_quadrants relative to n_hands (i.e. land bought ahead of labor to work it)",
        "evidence": "F3/F4 (Phase 2.3) -- land was NET-NEGATIVE at every tested labor level for the tested portfolio",
        "classification": "unsupported",
        "note": "the one regime with DIRECT NEGATIVE evidence in the only portfolio tested -- flagged explicitly "
                "so a future regime selector does not default to this without new evidence for a land-hungry mix "
                "(Phase 2.5's inventory already flagged this exact combination as UNKNOWN)",
    },
}


@dataclass
class StrategySnapshot:
    """A measured point-in-time reading of every dimension above, from a
    given planner `current_config` + `CompetitiveState` -- NOT a classification
    into a single regime label (that would be premature; Phase 3.2's job)."""
    day: int
    production_heavy_score: float   # 0-1, fraction of (hands+land+resource-types) vs a reference max
    animal_orientation_score: float  # 0-1, animal tiles / (animal+crop tiles)
    market_aware: bool
    liquidity_pressure: float        # 0-1, shed_occupancy fraction
    land_ahead_of_labor: float       # land_quadrants - hands_needed_estimate (can be negative)
    raw: dict = field(default_factory=dict)


def measure_snapshot(day, current_config, shed_occupancy_frac) -> StrategySnapshot:
    n_hands = current_config.get("n_hands", 0)
    land_quadrants = current_config.get("land_quadrants", 0) + 1  # +1 for always-owned NW
    n_resource_types = len(current_config.get("crops") or {}) + len(current_config.get("animals") or {})
    animal_count = sum((current_config.get("animals") or {}).values())
    crop_count = len(current_config.get("crops") or {})

    production_heavy = min(1.0, (n_hands / 4 + (land_quadrants - 1) / 3 + n_resource_types / 4) / 3)
    animal_orientation = animal_count / max(1, animal_count + crop_count)
    market_aware = current_config.get("sell_policy", {}).get("mode", "passive") != "passive"
    land_ahead_of_labor = (land_quadrants - 1) - n_hands  # positive = land bought ahead of labor (F3/F4 risk zone)

    return StrategySnapshot(
        day=day, production_heavy_score=round(production_heavy, 3),
        animal_orientation_score=round(animal_orientation, 3), market_aware=market_aware,
        liquidity_pressure=round(shed_occupancy_frac, 3), land_ahead_of_labor=land_ahead_of_labor,
        raw={"n_hands": n_hands, "land_quadrants": land_quadrants, "n_resource_types": n_resource_types},
    )
