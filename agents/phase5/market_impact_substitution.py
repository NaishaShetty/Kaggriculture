"""
Phase 5 targeted experiment: a market-impact-aware replacement for
agents/phase3_3/interventions.py's `variant_d_production_substitution` --
the SINGLE function Variant D uses to pick which crop absorbs the tile
capacity freed when the expansion-oriented detector fires and MELON is
pulled out of the portfolio.

SCOPE, stated plainly: this file changes ONLY the crop-ranking criterion
used at that one decision point. Everything else Submission C does --
detection (agents/phase3_3/expansion_detector.py), the scaling response
(agents/phase3_5/response_policy.py), the animal response
(agents/phase3_8/animal_response.py), Planner v1, the tactical layer -- is
untouched, imported, and reused exactly as-is. This module's functions are
drop-in replacements for the `market_response_fn` parameter that
agents/phase3_8/adapters/competitive_v3_agent.py::make_competitive_v3_agent
already exposes -- no new adapter or controller was required.

WHY THE EXISTING VARIANT D IS AT RISK OF THE FAILURE MODE THIS TARGETS:
`variant_d_production_substitution` (frozen, unchanged) ranks candidates by
`economic_model.model.crop_production_value`, which returns net profit from
a FIXED, Phase-2.2-calibrated $/tile-day constant (CALIBRATION
["revenue_per_tile_day"]) -- a historical average, not a live re-evaluation
of what selling a large batch into the CURRENT market would actually
realize. If the freed capacity is large enough to move a candidate crop's
own price (Phase 3.4/3.6's documented self_inflicted_narrow_market_price_
crash), the calibrated constant systematically overstates the achievable
revenue, and Variant D has no way to see that -- it picks the crop with
the best "average" isolated economics, not the best crop GIVEN what our
own added supply will do to that crop's specific market.

MARKET-IMPACT METHODOLOGY (documented, not invented):
  1. Estimate freed tile capacity from the config fraction Variant D is
     about to redirect (`melon_frac`) times the farm's total tile budget
     (`land_quadrants_owned * 25`, the VERIFIED per-quadrant tile count --
     see vendor_kaggriculture.kaggriculture's board-construction code).
     APPROXIMATION, disclosed: this ignores tiles already consumed by
     animal structures (PASTURE/COOP) and any other non-crop tile use, so
     it is an upper bound on freed capacity, not an exact count. The
     existing frozen Variant D has no tile-accurate estimate either (it
     only reasons in fractions), so this is not a regression relative to
     what C already does -- it is disclosed here because Phase 4's
     portfolio module made an unstated version of the same approximation
     and that omission made its failure harder to diagnose.
  2. Estimate the QUANTITY of units producible with that tile capacity by
     reusing crop_production_value's own feasibility/occupied-days logic
     (VERIFIED_MECHANIC-derived, unchanged) to get an isolated $ estimate,
     then dividing by the crop's CURRENT market price to back out a unit
     count. This reuses the already-validated Phase 2.5 model for
     feasibility and scale, and only replaces the PRICING step with the
     verified market simulator -- deliberately isolating "market impact"
     as the one new variable, rather than also re-deriving a new yield
     model (which would risk inventing an un-verified mechanic).
  3. Feed that unit count through agents.phase4.market_model.simulate_sell,
     which reproduces the engine's own unit-by-unit SELL loop exactly
     (re-verified in this phase, see scripts/phase5_market_model_validate.py).
  4. Net value = simulated revenue - seed cost. Pick the candidate (or
     MELON itself, if retaining it scores highest) with the best net value.

ON NOT SPREADING PRODUCTION OVER TIME: the brief asks not to assume all
production is sold in one instant. VERIFIED_MECHANIC finding (read
directly from vendor_kaggriculture.kaggriculture): market inventory only
moves via BUY/SELL orders -- there is no inventory-recovery-over-time
mechanic in the implementation (searched for and not found; the brief's
own section 15 phrase "town-demand recovery where relevant" does NOT
correspond to any mechanic in this engine, and is not implemented here --
inventing one would violate the "do not invent mechanics" rule). Given
that, `simulate_sell`'s cumulative revenue for N units of OUR OWN
production is invariant to how those N units are split across turns,
AS LONG AS no other party's orders land in between (which we cannot
observe or predict about the opponent's future actions, and are not
allowed to use their private state to estimate). We therefore evaluate a
single N-unit batch, anchored at the CURRENT PUBLIC market inventory
(state.market_inventory) -- an explicit, disclosed simplification that is
mathematically exact for our own contribution and only uncertain insofar
as the opponent's future orders are unknowable, which no amount of
"spreading" could fix without private information we are not allowed to use.

FALLBACK (section 10): if any estimate is unavailable, or the market
model raises, or the top two candidates are within a noise margin of each
other, this module falls back to calling the EXISTING frozen
`variant_d_production_substitution` directly -- never a hand-rolled
guess, never a crash.
"""
from economic_model.model import crop_production_value
from vendor_kaggriculture.kaggriculture import CROPS, MARKET_PARAMS, market_price
from agents.phase3_3.interventions import variant_d_production_substitution, _redistribute_away_from_melon
from agents.phase4.market_model import simulate_sell

TILES_PER_QUADRANT = 25  # VERIFIED_MECHANIC (board construction), same constant Phase 4 used
CANDIDATES = ["WHEAT", "STRAWBERRY", "CARROT", "TOMATO", "MELON"]  # MELON included: "do not force diversification"
CLOSE_MARGIN_FRAC = 0.03  # if top-2 candidates are within 3% of each other, treat as noise -> fallback


def _freed_tiles(config, state):
    crops = config.get("crops") or {}
    melon_frac = crops.get("MELON", 0.0)
    if melon_frac <= 0:
        return 0
    total_tiles = max(1, state.land_quadrants_owned) * TILES_PER_QUADRANT
    return max(1, round(melon_frac * total_tiles))


def _estimate_units(crop, state, n_tiles):
    """Isolated $ estimate (validated Phase 2.5 calibration) / current market
    price -> unit count. Returns (units, seed_cost, current_price) or
    (None, None, None) if infeasible / no usable price."""
    est = crop_production_value(crop, state, n_tiles=n_tiles)
    if est.value is None or "INFEASIBLE" in (est.notes or ""):
        return None, None, None
    seed_cost = CROPS[crop]["seed"] * n_tiles
    gross_revenue = est.value + seed_cost
    if gross_revenue <= 0:
        return None, None, None
    inv = state.market_inventory.get(crop, MARKET_PARAMS[crop]["I0"])
    price_now = market_price(crop, inv)
    if price_now <= 0:
        return None, None, None
    units = max(1, round(gross_revenue / price_now))
    return units, seed_cost, price_now


def _score_candidates(config, state, use_market_impact):
    """Returns dict crop -> {units, seed_cost, price_now, net_value} for
    every scoreable candidate, using either the real decay-aware simulator
    (use_market_impact=True) or a naive units*current_price calculation
    (use_market_impact=False, the Phase 5 diagnostic baseline, ablation D)."""
    n_tiles = _freed_tiles(config, state)
    if n_tiles <= 0:
        return {}
    scored = {}
    for crop in CANDIDATES:
        units, seed_cost, price_now = _estimate_units(crop, state, n_tiles)
        if units is None:
            continue
        if use_market_impact:
            revenue, _, _ = simulate_sell(crop, units, state.market_inventory.get(crop, MARKET_PARAMS[crop]["I0"]))
        else:
            revenue = units * price_now
        scored[crop] = {
            "units": units, "seed_cost": seed_cost, "price_now": price_now,
            "revenue": round(revenue, 2), "net_value": round(revenue - seed_cost, 2),
        }
    return scored


def _pick_best(scored):
    if not scored:
        return None, None
    ranked = sorted(scored.items(), key=lambda kv: -kv[1]["net_value"])
    best_crop, best = ranked[0]
    if len(ranked) > 1:
        second = ranked[1][1]
        denom = max(1.0, abs(best["net_value"]))
        if abs(best["net_value"] - second["net_value"]) / denom < CLOSE_MARGIN_FRAC:
            return None, None  # too close to call -> caller falls back
    return best_crop, best


def _apply(config, best_crop):
    if best_crop is None or best_crop == "MELON":
        # MELON itself scored best, or no confident decision: leave the
        # existing MELON share exactly as Planner v1 already has it.
        return dict(config)
    new_config = dict(config)
    new_config["crops"] = _redistribute_away_from_melon(config.get("crops") or {}, substitute=best_crop)
    return new_config


def make_market_impact_substitution(trace_sink=None):
    """Factory returning a 3-arg function with the exact signature
    `variant_d_production_substitution` uses, so it plugs directly into
    make_competitive_v3_agent(market_response_fn=...) with no adapter
    changes. `trace_sink`, if given, is a list that receives one dict per
    substitution decision (section 16 traceability requirement) -- no
    private opponent information is ever written to it."""

    def variant_d_market_impact_substitution(config, state, detector_result):
        if not detector_result["active"]:
            return config
        try:
            scored = _score_candidates(config, state, use_market_impact=True)
            best_crop, best = _pick_best(scored)
        except Exception as exc:  # noqa: BLE001 -- fallback rule (section 10): never let this break the agent
            if trace_sink is not None:
                trace_sink.append({"day": state.day, "fallback": True, "reason": f"exception: {exc!r}"})
            return variant_d_production_substitution(config, state, detector_result)

        if best_crop is None:
            # infeasible for every candidate, or top-2 too close to call
            if trace_sink is not None:
                trace_sink.append({"day": state.day, "fallback": True, "reason": "no confident candidate",
                                    "scored": scored})
            return variant_d_production_substitution(config, state, detector_result)

        if trace_sink is not None:
            trace_sink.append({
                "day": state.day, "fallback": False, "freed_tiles": _freed_tiles(config, state),
                "candidates": scored, "selected": best_crop, "selected_net_value": best["net_value"],
            })
        return _apply(config, best_crop)

    return variant_d_market_impact_substitution


def make_naive_price_substitution(trace_sink=None):
    """Ablation D (section 11): same unit-count methodology, but pricing
    uses a single current-price quote (units * price_now) instead of the
    unit-by-unit decay simulator. Isolates whether any improvement over
    the frozen Variant D comes specifically from modeling OUR OWN price
    impact, versus merely from using a live market price instead of the
    Phase 2.2 calibration constant."""

    def variant_d_naive_price_substitution(config, state, detector_result):
        if not detector_result["active"]:
            return config
        try:
            scored = _score_candidates(config, state, use_market_impact=False)
            best_crop, best = _pick_best(scored)
        except Exception as exc:  # noqa: BLE001
            if trace_sink is not None:
                trace_sink.append({"day": state.day, "fallback": True, "reason": f"exception: {exc!r}"})
            return variant_d_production_substitution(config, state, detector_result)

        if best_crop is None:
            if trace_sink is not None:
                trace_sink.append({"day": state.day, "fallback": True, "reason": "no confident candidate",
                                    "scored": scored})
            return variant_d_production_substitution(config, state, detector_result)

        if trace_sink is not None:
            trace_sink.append({
                "day": state.day, "fallback": False, "freed_tiles": _freed_tiles(config, state),
                "candidates": scored, "selected": best_crop, "selected_net_value": best["net_value"],
            })
        return _apply(config, best_crop)

    return variant_d_naive_price_substitution
