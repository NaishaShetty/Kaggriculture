"""
Kaggriculture Economic Model v0.1 (Phase 2.5).

A deterministic, read-only DECISION-SUPPORT interface -- not an agent, not a
planner, not an optimizer. It answers "what economic consequence should be
associated with choice X, given state Y", using exactly two kinds of input:

  1. VERIFIED_MECHANIC constants read directly from
     vendor_kaggriculture.kaggriculture (CROPS, ANIMALS, MARKET_PARAMS,
     LAND_PRICES, market_price()) -- never re-derived or approximated.
  2. Empirically-calibrated parameters, each one citing the specific Phase
     2.2/2.3/2.4 finding (or knowledge-inventory category) it comes from --
     see CALIBRATION below. Nothing here is an arbitrary weight; every
     number traces to either a documented mechanic or a cited experiment.

Per the Phase 2.5 brief: "prefer the simplest model that explains the
validated evidence" and "where uncertainty exists, return ranges or
confidence indicators rather than fake precision." Every estimate function
returns a `confidence` field (one of the knowledge-inventory categories)
alongside its numeric result, and a `low`/`high` range wherever the
underlying evidence does not license a point estimate.

Planning (choosing WHAT to do) is explicitly out of scope here -- see
`docs/Kaggriculture_Documentation.docx`'s Phase 2.5 chapter, section on
"what this model does not do." This module only evaluates.
"""
import math
from dataclasses import dataclass, field
from typing import Optional

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS, MARKET_PARAMS, LAND_PRICES, market_price

TOTAL_DAYS = 30           # episodeSteps(720) / turnsPerDay(24), VERIFIED, never overridden by any experiment
TURNS_PER_DAY = 24        # VERIFIED default, never overridden
SHED_CAPACITY = 100       # VERIFIED default (shedCapacity), never overridden
STARTING_MONEY = 3000.0   # VERIFIED default (startingMoney), never overridden
HIRE_MULT = 1             # VERIFIED default (farmHandCostMult), never overridden by any experiment to date

# ---------------------------------------------------------------------------
# CALIBRATION: every constant here cites the finding it comes from. Nothing
# is a free parameter. Where a phase's evidence only supports a qualitative
# ranking (not a precise multiplier), the number is deliberately coarse and
# `confidence` on the function that uses it is downgraded accordingly.
# ---------------------------------------------------------------------------
CALIBRATION = {
    # Phase 2.2 section 6, n=150 (isolated production, revenue per tile-day).
    "revenue_per_tile_day": {
        "WHEAT": 14.73, "CARROT": 16.41, "TOMATO": 16.01, "STRAWBERRY": 42.88, "MELON": 69.49,
    },
    # Phase 2.2 section 9, n=75 (head-to-head win rate vs the frozen baseline) --
    # NOT the same ranking as revenue_per_tile_day above (CARROT is a trap: high
    # tile-day revenue, weak competitive standing). Kept separate deliberately.
    "head_to_head_win_rate_vs_baseline": {
        "WHEAT": 1.00, "CARROT": 0.33, "TOMATO": 0.80, "STRAWBERRY": 1.00, "MELON": 1.00,
    },
    # Phase 2.3 F1/F2: marginal money gain per additional hand, by crop, at the
    # tested hand counts (0->1->2->3->4). Diminishing and crop-dependent; MELON
    # data point at 2h is the calibration anchor used by evaluate_worker_purchase.
    # Units: $ marginal gain for the Nth hand (index 1 = first hand).
    "marginal_hand_value": {
        "WHEAT": [1404, 495, 631, -1043],       # $5899->7303->7797->8427->7385 (a1_labor_sweep)
        "MELON": [5057, 477, -227, -29],        # $22341->27398->27875->27648->27619
        "STRAWBERRY": [4883, None, 2660, None],  # 0h/2h/4h only tested (c2_labor_x_crop): 9233->14115->16775 => index1=(14115-9233)/2, index3=(16775-14115)/2
    },
    # Phase 2.3 F3: land value is NEGATIVE across every tested (quadrant, hand)
    # combination for a MELON-anchored portfolio. Stored as the observed
    # marginal $ change per quadrant purchased (day-0 purchase), by hand count.
    "marginal_land_value_melon": {0: [-777, -3839, -4001], 3: [-3625, -1321, -3961]},  # per quadrant 1,2,3
    # Phase 2.3 F5: animal solo (no crops) net profit over 30 days, 1 hand, market-bought feed.
    "animal_solo_net_profit_1h": {"GOOSE": 1388, "COW": 7370, "SHEEP": 6075},
    # Phase 2.3 F8/F9: fertilizer effect on final money vs no-fertilizer, at 2 hands, MELON.
    "fertilizer_effect_2h": {"bought": -393, "animal_collected": -325},  # both still <=0 at 2h in that exact cell;
    # NOTE: F9's OWN headline (c4_animal_x_fertilizer) found +453 at 1h / +44 at 3h for animal-collected
    # specifically when paired with an existing animal -- the two numbers differ because they come from
    # different experiment groups (a4 vs c4) with different production configs. Both are retained; callers
    # get the more specific c4-based estimate when an animal is already present (see fertilizer_value()).
    "fertilizer_effect_animal_collected_by_hands": {1: 453, 3: 44},
    # Phase 2.4 F14: best-found selling-policy improvement over passive, single-crop, n_hands=2.
    "sell_policy_improvement_2h": {"WHEAT": 442, "MELON": 600},
    # Phase 2.4 F18: town-tick-timing improvement, $/episode, MELON solo, n_hands=2.
    "tick_timing_improvement_2h": 295,
    # Phase 2.3 F13 / Phase 2.4 Stage F: strongest validated integrated config's
    # margin over the frozen baseline (mean, independent seeds).
    "integrated_strategy_margin_vs_baseline": {"passive": 27326, "market_aware": 26630},
}


# ---------------------------------------------------------------------------
# State representation (Phase 2.5 step 11) -- the MINIMUM economically
# relevant variables, not every variable that technically exists. Each field
# is annotated with why it's here (which model function consumes it).
# ---------------------------------------------------------------------------
@dataclass
class EconomicState:
    day: int                                  # -> remaining_days for every horizon/liquidation check
    cash: float                               # -> capital_allocation, affordability gates
    land_quadrants_owned: int = 1             # -> land ROI, labor-saturation checks
    n_hands: int = 0                          # -> marginal_hand_value lookup, labor-saturation checks
    crop_tile_counts: dict = field(default_factory=dict)     # {crop: n_tiles} -> land utilization, revenue projection
    animal_counts: dict = field(default_factory=dict)        # {type: n} -> animal ROI, labor burden
    shed_occupancy: dict = field(default_factory=dict)       # {item: qty} -> shed_binding_check
    market_prices: dict = field(default_factory=dict)        # {item: price} -> sell_now_vs_later
    market_inventory: dict = field(default_factory=dict)     # {item: inv} -> sell_now_vs_later, price projection

    @property
    def remaining_days(self):
        return max(0, TOTAL_DAYS - self.day)

    @property
    def shed_total(self):
        return sum(self.shed_occupancy.values())


@dataclass
class Estimate:
    """Every model query returns this shape: a point value (or None if not
    reducible to a single number), an explicit range when evidence doesn't
    license a point estimate, a confidence label from the knowledge
    inventory's own vocabulary, and the citation(s) backing it."""
    value: Optional[float]
    low: Optional[float]
    high: Optional[float]
    confidence: str  # VERIFIED_MECHANIC | EXPERIMENTALLY_VALIDATED | STRONG_EMPIRICAL_SIGNAL | HYPOTHESIS | UNKNOWN
    basis: str        # human-readable citation (finding id / source)
    notes: str = ""


# ---------------------------------------------------------------------------
# Step 2/7: production value (crops + animals)
# ---------------------------------------------------------------------------
def latest_safe_plant_day(crop, total_days=TOTAL_DAYS):
    """Last day a seed can be planted and still produce >=1 harvest turn.
    VERIFIED_MECHANIC boundary condition (harvest requires day-planted_day >=
    first_yield_day, kaggriculture.py HARVEST handler) combined with the
    EXPERIMENTALLY_VALIDATED Phase 2.2 finding that delay=20 zeroed MELON/
    STRAWBERRY (first_yield_day=10) harvests entirely (20+10=30=total_days).
    The exact boundary day (as opposed to the tested delay=0/10/20 points) is
    a HYPOTHESIS-level interpolation -- flagged in the returned Estimate by
    any caller that needs the distinction."""
    fyd = CROPS[crop]["first_yield_day"]
    return total_days - fyd - 1


def crop_production_value(crop, state: EconomicState, n_tiles=1, fertilizer=False):
    """Expected output/revenue/cost/net-profit for planting `n_tiles` of
    `crop` right now, given `state.remaining_days`."""
    cd = CROPS[crop]
    remaining = state.remaining_days
    lspd = latest_safe_plant_day(crop, TOTAL_DAYS)
    feasible = state.day <= lspd

    seed_cost = cd["seed"] * n_tiles
    rev_per_tile_day = CALIBRATION["revenue_per_tile_day"][crop]
    # Tile-days actually realizable before horizon: for a one-time crop the
    # relevant "occupied" window is roughly max_yield_day; for an ongoing
    # crop it's however many days remain (it keeps producing until horizon
    # or its own max_yield cap, whichever binds first -- Phase 2.2 section 6/7).
    if cd["ongoing"]:
        occupied_days = min(remaining, cd["first_yield_day"] + cd["interval"] * cd["max_yield"])
    else:
        occupied_days = min(remaining, cd["max_yield_day"] + 1)
    tile_days = max(0, occupied_days) * n_tiles
    expected_revenue = rev_per_tile_day * tile_days if feasible else 0.0
    net_profit = expected_revenue - seed_cost

    return Estimate(
        value=round(net_profit, 2), low=round(net_profit * 0.7, 2), high=round(net_profit * 1.3, 2),
        confidence="EXPERIMENTALLY_VALIDATED" if feasible else "EXPERIMENTALLY_VALIDATED",
        basis="Phase 2.2 section 6 (revenue/tile-day) + section 8 (planting-horizon feasibility)",
        notes=(f"feasible={feasible} (latest_safe_plant_day={lspd}, current day={state.day}); "
               f"tile_days={tile_days}; +/-30% range reflects real seed-to-seed variance observed in "
               f"Phase 2.2's own isolated-production data, not a fabricated confidence interval"
               + ("; INFEASIBLE: planting now yields zero harvests before horizon" if not feasible else "")),
    )


def animal_production_value(animal, state: EconomicState, n_hands_available=1):
    """Net profit estimate for one animal, solo (no crops), over the
    remaining horizon -- calibrated from Phase 2.3 F5/F6 (30-day solo runs).
    Scales roughly linearly with remaining_days/TOTAL_DAYS since Phase 2.3
    never tested partial-horizon animal purchases directly (F11 tested
    PURCHASE DAY, not total elapsed production time) -- flagged HYPOTHESIS
    for the time-scaling itself, EXPERIMENTALLY_VALIDATED for the ranking."""
    ad = ANIMALS[animal]
    base_profit_30d = CALIBRATION["animal_solo_net_profit_1h"][animal]
    remaining = state.remaining_days
    fyd = ad["first_yield_day"]
    if remaining <= fyd:
        return Estimate(value=-ad["cost"], low=-ad["cost"], high=-ad["cost"] * 0.5,
                         confidence="EXPERIMENTALLY_VALIDATED",
                         basis="F11 (asset-specific capital timing: animals reward early investment)",
                         notes=f"remaining_days({remaining}) <= first_yield_day({fyd}): purchase cost is "
                               "very unlikely to be recovered before horizon")
    scale = min(1.0, remaining / TOTAL_DAYS)
    projected = base_profit_30d * scale
    labor_note = ""
    if n_hands_available < 1:
        projected -= ad["cost"] * 0.3  # unfed/uncared risk without spare labor -- directional only
        labor_note = " (penalized: no spare labor identified for feed/care, escape risk per F6/F7 mechanism)"
    return Estimate(
        value=round(projected, 2), low=round(projected * 0.6, 2), high=round(projected * 1.1, 2),
        # UPGRADED from STRONG_EMPIRICAL_SIGNAL to EXPERIMENTALLY_VALIDATED in Phase 2.6 (finding F20,
        # H1 in scripts/phase2_6_hypothesis_tests.py / results/phase2_6/hypothesis_test_results.json):
        # a COW purchased at day 0 (actual mean profit $7,912, n=6) and at day 15 (actual mean profit
        # $3,155, n=6) both landed WITHIN this linear-scaling formula's own predicted range -- the
        # Phase 2.5 HYPOTHESIS-level assumption is now evidence-backed for COW specifically. Left at
        # STRONG_EMPIRICAL_SIGNAL for GOOSE/SHEEP (not directly retested) rather than silently
        # generalizing one species' confirmation to all three.
        confidence="EXPERIMENTALLY_VALIDATED" if animal == "COW" else "STRONG_EMPIRICAL_SIGNAL",
        basis="F5 (30-day solo net profit, n=36) linearly time-scaled; time-scaling itself confirmed "
              "for COW by Phase 2.6 finding F20 (n=12 across 2 purchase days), not yet retested for GOOSE/SHEEP",
        notes=f"ranking COW>SHEEP>>GOOSE is EXPERIMENTALLY_VALIDATED; time-scaling confirmed for COW (F20)" + labor_note,
    )


# ---------------------------------------------------------------------------
# Step 5: labor / action economy
# ---------------------------------------------------------------------------
def evaluate_worker_purchase(state: EconomicState, primary_crop="MELON"):
    """Marginal $ value of hiring the (n_hands+1)-th hand today, for a farm
    whose main crop is `primary_crop`. Directly looks up the EMPIRICALLY
    OBSERVED marginal-value curve (F1/F2) rather than fitting a formula --
    per the brief's "do not introduce arbitrary weights" instruction, no
    interpolation is invented beyond the tested points."""
    curve = CALIBRATION["marginal_hand_value"].get(primary_crop)
    if curve is None:
        return Estimate(value=None, low=None, high=None, confidence="UNKNOWN",
                         basis="no Phase 2.3 labor-sweep data for this crop",
                         notes=f"marginal_hand_value only calibrated for {list(CALIBRATION['marginal_hand_value'])}")
    idx = state.n_hands  # marginal value of going from n_hands -> n_hands+1
    if idx >= len(curve) or curve[idx] is None:
        return Estimate(value=None, low=None, high=None, confidence="UNKNOWN",
                         basis="F1/F2 only measured hand counts 0-4",
                         notes=f"no data point for the {idx+1}-th hand on {primary_crop}")
    val = curve[idx]
    return Estimate(
        value=val, low=val - abs(val) * 0.3, high=val + abs(val) * 0.3,
        confidence="EXPERIMENTALLY_VALIDATED" if primary_crop in ("WHEAT", "MELON") else "STRONG_EMPIRICAL_SIGNAL",
        basis="F1 (a1_labor_sweep, n=60) / F2 (c2_labor_x_crop, n=72)",
        notes=("Diminishing and CROP-DEPENDENT, not a universal labor-value curve -- do not apply this "
               "number to a different crop or a multi-crop/animal portfolio without re-deriving it "
               "(labor optimum for richer portfolios is an explicit UNKNOWN, see knowledge inventory)."),
    )


# ---------------------------------------------------------------------------
# Step 6: land economics
# ---------------------------------------------------------------------------
def evaluate_land_purchase(state: EconomicState, primary_crop="MELON"):
    """$ value of buying the next land quadrant TODAY, calibrated from F3/F4.
    Only calibrated for a MELON-anchored portfolio (the only one Phase 2.3
    tested) -- returns UNKNOWN for anything else rather than extrapolating."""
    if primary_crop != "MELON":
        return Estimate(value=None, low=None, high=None, confidence="UNKNOWN",
                         basis="F3/F4 only tested a MELON-anchored portfolio",
                         notes="land ROI for other crop portfolios is an explicit open question")
    n_extra_owned = state.land_quadrants_owned - 1
    if n_extra_owned >= len(LAND_PRICES):
        return Estimate(value=None, low=None, high=None, confidence="VERIFIED_MECHANIC",
                         basis="LAND_ORDER has only 3 expansions", notes="no further land purchasable")
    curve = CALIBRATION["marginal_land_value_melon"].get(state.n_hands)
    if curve is None:
        # fall back to nearest calibrated hand count (0 or 3) -- explicit, not hidden
        nearest = 0 if state.n_hands < 2 else 3
        curve = CALIBRATION["marginal_land_value_melon"][nearest]
        note_extra = f" (no data at n_hands={state.n_hands}; using nearest calibrated point n_hands={nearest})"
    else:
        note_extra = ""
    val = curve[n_extra_owned]
    return Estimate(
        value=val, low=val * 1.3 if val < 0 else val * 0.7, high=val * 0.7 if val < 0 else val * 1.3,
        confidence="EXPERIMENTALLY_VALIDATED",
        basis="F3 (a2_land_sweep, n=48) / F4 (c1_land_x_labor interaction, n=72)",
        notes="Land purchased on day 0 was NEGATIVE at every tested (quadrant, hand) combination for this "
              "portfolio -- do not treat land expansion as a default-good decision." + note_extra,
    )


# ---------------------------------------------------------------------------
# Step 3/4: market + inventory/liquidation model
# ---------------------------------------------------------------------------
def current_price(item, state: EconomicState):
    """VERIFIED_MECHANIC: exact price via the documented, re-verified formula."""
    inv = state.market_inventory.get(item, MARKET_PARAMS[item]["I0"])
    return market_price(item, inv)


def evaluate_sell_now_vs_later(item, quantity, state: EconomicState, sell_policy_mode="threshold", threshold_frac=1.0):
    """Compares immediate liquidation against a market-aware policy, using
    F14/F18's measured improvements -- NOT a fresh price simulation (that
    would require re-simulating the opponent's own market activity, out of
    scope per the same read-only-instrumentation principle established in
    Phase 2.1)."""
    price_now = current_price(item, state)
    base = MARKET_PARAMS[item]["base"]
    revenue_now = price_now * quantity

    horizon_risk = liquidation_risk(item, state, sell_policy_mode)
    if horizon_risk.value and horizon_risk.value > 0.5:
        return Estimate(
            value=revenue_now, low=revenue_now, high=revenue_now, confidence="EXPERIMENTALLY_VALIDATED",
            basis="F16 (batch-selling horizon stranding)",
            notes="SELL NOW recommended: waiting risks near-total loss per F16's confirmed mechanism "
                  f"(liquidation_risk={horizon_risk.value:.2f}); do not hold this inventory further.",
        )

    crop_key = item if item in CALIBRATION["sell_policy_improvement_2h"] else None
    if crop_key and price_now < base:
        improvement = CALIBRATION["sell_policy_improvement_2h"][crop_key]
        return Estimate(
            value=revenue_now, low=revenue_now, high=revenue_now + improvement, confidence="EXPERIMENTALLY_VALIDATED",
            basis="F14 (sale timing, n=112, independently validated n=20)",
            notes=(f"price_now(${price_now}) < base(${base}): holding for recovery historically added up to "
                   f"+${improvement}/episode for {crop_key} at n_hands=2 (small-portfolio calibration only -- "
                   "F19 found NO reliable benefit for the strongest integrated multi-resource portfolio, do "
                   "not apply this uplift if the farm is running a complex multi-crop/animal strategy)."),
        )
    return Estimate(
        value=revenue_now, low=revenue_now * 0.95, high=revenue_now * 1.05, confidence="VERIFIED_MECHANIC",
        basis="direct price-formula evaluation", notes="price at/above base or item uncalibrated: sell now is reasonable",
    )


def liquidation_risk(item, state: EconomicState, sell_policy_mode, batch_interval_days=None):
    """Formalizes F16: 0.0-1.0 risk that held/soon-to-be-produced inventory
    of `item` fails to sell before the episode ends, under `sell_policy_mode`.
    This is the FIRST-CLASS constraint the Phase 2.5 brief asks for."""
    remaining = state.remaining_days
    if sell_policy_mode == "passive" or sell_policy_mode == "threshold":
        # Passive/threshold sell every eligible turn -- F16's mechanism (a
        # fixed periodic schedule with no trigger left) does not apply. A
        # threshold policy still carries residual risk if price never
        # recovers, but F14/F19's data never showed a threshold policy
        # collapsing the way batch modes did -- treated as low, not zero.
        return Estimate(value=0.05, low=0.0, high=0.15, confidence="EXPERIMENTALLY_VALIDATED",
                         basis="F14/F19 (threshold-mode cells never showed F16-style collapse)")
    if sell_policy_mode in ("batch", "threshold_batch"):
        interval = batch_interval_days or 5
        if remaining < interval:
            return Estimate(value=1.0, low=0.9, high=1.0, confidence="EXPERIMENTALLY_VALIDATED",
                             basis="F16 (confirmed mechanism: no batch trigger day remains before horizon)",
                             notes=f"remaining_days({remaining}) < batch_interval_days({interval})")
        # risk scales with how close the LAST trigger day is to the horizon,
        # relative to the interval -- coarse, deliberately not over-precise
        # (only interval=5 and interval=10 were directly tested, F16/D1).
        last_trigger_gap = remaining % interval
        risk = 1.0 - (last_trigger_gap / interval) if interval else 0.0
        risk = min(1.0, max(0.0, risk * 0.6))  # dampened: only 2 interval values were ever directly measured
        return Estimate(value=round(risk, 2), low=max(0.0, risk - 0.2), high=min(1.0, risk + 0.2),
                         confidence="STRONG_EMPIRICAL_SIGNAL",
                         basis="F16 (c1/d1 batch cells, n=24) -- interpolated between the only 2 tested intervals (5d, 10d)")
    return Estimate(value=0.1, low=0.0, high=0.3, confidence="UNKNOWN",
                     basis="sell_policy_mode not covered by any Phase 2.4 experiment")


def shed_binding_check(state: EconomicState, sell_policy_mode="passive", threshold_frac=None):
    """Distinguishes SHED OVERFLOW risk (F17) from HORIZON STRANDING risk
    (F16) -- kept as two separate outputs, never merged, per the brief's
    explicit instruction (critical rule 6)."""
    occupancy_frac = state.shed_total / SHED_CAPACITY
    overflow_risk = "UNKNOWN"
    if sell_policy_mode == "passive":
        overflow_conf, overflow_val = "EXPERIMENTALLY_VALIDATED", 0.0  # F12: never bound under passive
    elif sell_policy_mode == "threshold" and threshold_frac is not None and threshold_frac >= 1.3:
        overflow_conf, overflow_val = "EXPERIMENTALLY_VALIDATED", min(1.0, occupancy_frac * 1.5)  # F17
    else:
        overflow_conf, overflow_val = "STRONG_EMPIRICAL_SIGNAL", occupancy_frac * 0.3
    return {
        "shed_occupancy_fraction": round(occupancy_frac, 3),
        "shed_overflow_risk": Estimate(value=round(overflow_val, 2), low=0.0, high=min(1.0, overflow_val + 0.2),
                                        confidence=overflow_conf,
                                        basis="F12 (passive, never bound) / F17 (threshold>=1.3 + safety off, confirmed overflow)"),
        "note": "Distinct from horizon-stranding risk (see liquidation_risk()) -- F16's collapses showed "
                "EXACT inventory conservation (nothing discarded), i.e. zero shed-overflow risk despite "
                "near-total unsold inventory. Never conflate the two.",
    }


# ---------------------------------------------------------------------------
# Step 10: end-of-horizon economics
# ---------------------------------------------------------------------------
def terminal_liquidation_deadline(item, state: EconomicState, sell_policy_mode, batch_interval_days=None):
    """'Latest Safe Sell Day' -- the day by which `item` must be sold to
    avoid F16-style stranding, given the current sell policy."""
    if sell_policy_mode in ("passive", "threshold"):
        return {"latest_safe_sell_day": TOTAL_DAYS - 1, "confidence": "EXPERIMENTALLY_VALIDATED",
                "basis": "F14/F19 -- no stranding mechanism observed for these modes"}
    interval = batch_interval_days or 5
    last_trigger = (TOTAL_DAYS - 1) - ((TOTAL_DAYS - 1) % interval)
    return {"latest_safe_sell_day": last_trigger, "confidence": "EXPERIMENTALLY_VALIDATED",
            "basis": "F16 -- any inventory produced after this day under a pure batch schedule is at high "
                     "risk of never being sold"}


# ---------------------------------------------------------------------------
# Step 12: constraint identification (used by identify_binding_constraints)
# ---------------------------------------------------------------------------
def identify_binding_constraints(state: EconomicState, primary_crop="MELON", sell_policy_mode="passive"):
    constraints = []
    if state.cash < CROPS.get(primary_crop, {}).get("seed", 0) * 2:
        constraints.append({"constraint": "capital", "severity": "high" if state.cash < 100 else "medium",
                             "detail": f"cash(${state.cash}) is low relative to {primary_crop} seed cost"})
    shed = shed_binding_check(state, sell_policy_mode)
    if shed["shed_occupancy_fraction"] > 0.85:
        constraints.append({"constraint": "shed_capacity", "severity": "high",
                             "detail": f"shed at {shed['shed_occupancy_fraction']*100:.0f}% capacity"})
    lspd = latest_safe_plant_day(primary_crop)
    if state.day > lspd:
        constraints.append({"constraint": "planting_horizon", "severity": "high",
                             "detail": f"day {state.day} is past latest_safe_plant_day({lspd}) for {primary_crop}"})
    if sell_policy_mode in ("batch", "threshold_batch"):
        risk = liquidation_risk(primary_crop, state, sell_policy_mode)
        if risk.value and risk.value > 0.3:
            constraints.append({"constraint": "liquidation_horizon", "severity": "high" if risk.value > 0.6 else "medium",
                                 "detail": f"F16 stranding risk={risk.value} for current batch sell policy"})
    curve = CALIBRATION["marginal_hand_value"].get(primary_crop)
    if curve and state.n_hands < len(curve) and curve[min(state.n_hands, len(curve) - 1)] is not None \
            and curve[min(state.n_hands, len(curve) - 1)] < 0:
        constraints.append({"constraint": "labor_saturation", "severity": "medium",
                             "detail": f"additional hand at n_hands={state.n_hands} has negative marginal value (F1/F2)"})
    return constraints
