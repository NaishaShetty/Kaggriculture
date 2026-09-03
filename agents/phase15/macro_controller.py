"""
Phase 15 macro-controller: computes PROPORTIONAL, day-indexed targets for
land quadrants, hand count, animal count/species, and crop-tile allocation,
ramping toward the real-data scale `docs/BIG_SWING_PLAN.md` and Phase 6's
real-replay forensics establish -- instead of Submission C's small, fixed
thresholds (hands locked at 5, animals capped at 6).

REAL-DATA TARGETS (Phase 15 Step 1, re-extracted directly from
results/phase6/{moushun_chen,lai_eu_wen,achille_gohin,zach_locke}/
days_opponent.csv at days 5/10/15/20/25/29 -- see
results/phase15/PHASE15_MACRO_CONTROLLER_REPORT.md Section 2 for the full
table this module is built from):

  land_quadrants (total owned):
    moushun_chen: 1(d5) -> 2(d10) -> 3(d15) -> 3(d20) -> 3(d25) -> 3(d29)
    lai_eu_wen:   2(d5) -> 4(d10) -> 4(d15) -> 4(d20) -> 4(d25) -> 4(d29)
    achille_gohin:1(d5) -> 1(d10) -> 3(d15) -> 4(d20) -> 4(d25) -> 4(d29)
    zach_locke:   2(d5) -> 2(d10) -> 2(d15) -> 2(d20) -> 2(d25) -> 2(d29)
    Synthesis: converges to 3-4 by day 15-20 in 3/4 opponents; zach_locke is
    the one outlier that never goes past 2 (and finished 3rd of 4 in final
    money). Target ramp below aims at the majority (3-4) shape.

  hands:
    moushun_chen: 5 -> 8 -> 10 -> 10 -> 10 -> 10
    lai_eu_wen:   8 -> 12 -> 13 -> 13 -> 13 -> 8 (drawn down late, likely
                  end-of-game liquidation/labor-cost trimming)
    achille_gohin:5 -> 5 -> 5 -> 5 -> 5 -> 5 (flat -- the low-labor archetype,
                  finished 2nd-LOWEST of the 4 in final money, "at least
                  consistent with... land-without-labor being the weaker of
                  the observed strategies" per Phase 6 report Section 17.5)
    zach_locke:   7 -> 8 -> 7 -> 6 -> 5 -> 7 (oscillating around 6-7)
    Synthesis: the highest-money opponent (Lai Eu Wen, $104,569) ran the
    highest sustained hands (10-13); the ramp below targets that upper band
    (8-13) by day 15, not achille_gohin's flat-5 floor.

  animals (total, all species):
    moushun_chen: 4 -> 9 -> 11 -> 14 -> 14 -> 14
    lai_eu_wen:   0 -> 5 -> 13 -> 13 -> 12 -> 12
    achille_gohin:4 -> 8 -> 10 -> 10 -> 10 -> 10
    zach_locke:   1 -> 1 -> 12 -> 11 -> 11 -> 12
    Synthesis: all 4 converge to 10-14 by day 15-20 despite very different
    day 0-10 paths -- this is the most consistent signal of the four axes.
    Target ramp below aims for 10-14 by day ~15-18.

  crop tile allocation (day 15+ dominant crop, from the same CSVs):
    moushun_chen: 100% STRAWBERRY (20-28 tiles, MELON dropped to 0 by d15)
    lai_eu_wen:   mixed WHEAT (33-36) + STRAWBERRY (20-30), MELON fading to 0
    achille_gohin:small total footprint (6-13 tiles), WHEAT/STRAWBERRY/MELON mixed
    zach_locke:   STRAWBERRY-dominant (24) + some MELON (5-10), WHEAT->0 by d15
    Synthesis (explicit simplifying assumption, stated here rather than
    silently baked in): all 4 opponents lean MELON/WHEAT early (day 0-9,
    matching this game's genuinely fast WHEAT first-yield at day 2) and
    STRAWBERRY-dominant by day 15+ (STRAWBERRY is the only "ongoing" crop
    among the ones any opponent used at volume -- CROPS["STRAWBERRY"]
    ["ongoing"]==True, interval=2 -- i.e. it yields repeatedly without
    replanting, which is exactly why every opponent that reaches a large,
    stable crop footprint ends up STRAWBERRY-heavy there). This module
    encodes that early-WHEAT/MELON -> late-STRAWBERRY ramp directly as a
    day-indexed fraction schedule grounded in the observed transition
    timing, NOT from any economic-model volume estimate (Phase 8 found
    `crop_production_value` undercounts non-ongoing crops by 3-8x; Phase 5
    already tried and rejected re-deriving volume from that calibration
    for a portfolio/substitution decision -- this module sidesteps that
    entire failure mode by using directly-measured real footprint targets,
    never `economic_model.model.crop_production_value`, for any crop-tile
    quantity decision).
"""

# ---- Real-data-grounded target ceilings (Step 1) ----
TARGET_LAND_QUADRANTS = 4       # total owned, matching Lai Eu Wen/Achille Gohin's converged level
TARGET_HANDS = 13               # matching Lai Eu Wen's own peak (the highest-money real opponent, $104,569)
TARGET_ANIMALS_TOTAL = 13       # matching Lai Eu Wen's own peak (13, days 15-20)
TARGET_ANIMAL_SPECIES = {"COW": 7, "SHEEP": 6}  # even split, no real-data signal favors one species

# Day thresholds at which each axis reaches specific rungs, taken directly
# from the median crossing-day across the 4 real opponents (rounded to
# whole days) rather than an invented smooth curve -- ramps are piecewise,
# matching how real opponents actually move (step increases at hire/buy
# events), not continuous.
_LAND_RUNGS = [(0, 1), (6, 2), (12, 3), (18, 4)]
_HANDS_RUNGS = [(0, 2), (4, 5), (8, 8), (13, 10), (18, TARGET_HANDS)]
_ANIMALS_RUNGS = [(0, 0), (4, 2), (8, 6), (13, 9), (18, TARGET_ANIMALS_TOTAL)]

# Crop-fraction schedule (of the crop-tile pool only; structure tiles are
# carved out separately) -- day-bucketed, per the docstring's synthesis.
_CROP_SCHEDULE = [
    (0, {"WHEAT": 0.6, "MELON": 0.4}),
    (5, {"WHEAT": 0.5, "MELON": 0.3, "STRAWBERRY": 0.2}),
    (10, {"STRAWBERRY": 0.5, "WHEAT": 0.3, "MELON": 0.2}),
    (15, {"STRAWBERRY": 0.7, "WHEAT": 0.3}),
    (20, {"STRAWBERRY": 0.8, "WHEAT": 0.2}),
]

CROP_TILE_TARGET_CEILING = 50  # bounded footprint ceiling, within the 26-76-tile range real opponents actually used
# Footprint also RAMPS (not fixed at the ceiling from day 0) -- an early smoke test
# at a fixed 40-tile footprint from day 0 produced a full cash-collapse death
# spiral (seed costs, esp. MELON at $80/seed, outrunning the $3000 start before
# any harvest revenue arrived) -- this ramp keeps early footprint closer to the
# real opponents' own early numbers (moushun_chen: 15(d5)->20(d10)) and grows
# toward the ceiling only as the game (and cash flow) matures. Documented here,
# not silently tuned away, per this project's standing discipline.
_CROP_TILE_RUNGS = [(0, 14), (5, 18), (10, 24), (15, 30), (20, 40), (24, CROP_TILE_TARGET_CEILING)]


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def _opponent_scale(opponent_history):
    """Best-effort read of the opponent's OWN most recent hands/animals/land,
    from the existing agents/phase3/opponent_observation.py telemetry
    (reused, not re-derived) -- used only to ratchet OUR targets up faster
    if the opponent is already ahead of our current ramp rung, never down."""
    if not opponent_history:
        return 0, 0, 0
    last = opponent_history[-1]
    opp_hands = len(last.visible_hand_positions) + 1  # +1 for the opponent's own farmer, same convention as our own hands count
    opp_animals = sum(last.visible_animal_tile_counts.values())
    opp_land = last.visible_land_quadrants
    return opp_hands, opp_animals, opp_land


def compute_targets(day, opponent_history=None):
    """Returns a dict: {n_hands, land_quadrants, animals (dict), crop_tile_target,
    crop_fractions (dict, sums to 1.0)}. Pure function of (day, opponent_history) --
    no hidden state, easy to unit-test and audit, per this project's standing
    preference for a simple, explainable mechanism over a complex one."""
    base_hands = _rung_value(day, _HANDS_RUNGS)
    base_animals_total = _rung_value(day, _ANIMALS_RUNGS)
    base_land = _rung_value(day, _LAND_RUNGS)

    opp_hands, opp_animals, opp_land = _opponent_scale(opponent_history or [])
    # Ratchet UP (never down) if the opponent's own current scale already exceeds
    # our current rung -- ramps encode a MINIMUM commitment schedule, not a ceiling
    # below TARGET_*'s own hard cap.
    n_hands = max(base_hands, min(opp_hands, TARGET_HANDS))
    animals_total = max(base_animals_total, min(opp_animals, TARGET_ANIMALS_TOTAL))
    land_quadrants = max(base_land, min(opp_land, TARGET_LAND_QUADRANTS))

    if TARGET_ANIMALS_TOTAL > 0 and animals_total > 0:
        scale = animals_total / TARGET_ANIMALS_TOTAL
        animals = {sp: max(0, round(n * scale)) for sp, n in TARGET_ANIMAL_SPECIES.items()}
    else:
        animals = {}

    crop_fractions = _CROP_SCHEDULE[0][1]
    for threshold_day, fractions in _CROP_SCHEDULE:
        if day >= threshold_day:
            crop_fractions = fractions
        else:
            break

    crop_tile_target = _rung_value(day, _CROP_TILE_RUNGS)

    return {
        "n_hands": n_hands,
        "land_quadrants": land_quadrants,
        "animals": animals,
        "crop_tile_target": crop_tile_target,
        "crop_fractions": dict(crop_fractions),
    }
