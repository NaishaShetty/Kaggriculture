"""
Phase 15 macro-controller: computes PROPORTIONAL, day-indexed targets for
land quadrants, hand count, animal count/species, and crop-tile allocation,
ramping toward the real-data scale `docs/BIG_SWING_PLAN.md` and Phase 6's
real-replay forensics establish -- instead of Submission C's small, fixed
thresholds (hands locked at 5, animals capped at 6).

PHASE 19 RECALIBRATION (this update supersedes the Phase 15 constants below,
docstring kept for the historical record): Phase 6's local sample (4
opponents, max $104,569, land capping at 4) is now confirmed OUTDATED by
fresh replay data pulled directly from Kaggle's current top ladder
(results/phase19/fresh_ladder/, 4 episodes, 2 independent strong players --
Dmitry Larko across 4 games, Milan Leonard in 1 -- see
results/phase19/PHASE19_LADDER_RECALIBRATION_REPORT.md Section 2 for the
full table). Both players converge on a SMALLER, more intensively-worked
footprint than Phase 15 assumed: land caps at 3 (not 4), hands settle at
10-12 (not 13), animals run 12-17 (a range, not a fixed 13), crop footprint
runs 58-63 tiles (not ~50), and -- the biggest qualitative change -- the
crop mix does NOT stay STRAWBERRY-dominant: both players let WHEAT overtake
STRAWBERRY by day 25 (WHEAT 39 vs. STRAWBERRY 13-18), then fully liquidate
the crop side by day 29 (see agents/phase15/endgame.py for the new mechanic
that models this last part; Phase 15/16 modeled NONE of the endgame).
Final money at this scale: $114,357-$183,147 -- the real target Submission F
should have been compared against, not Phase 6's $104,569 ceiling.

REAL-DATA TARGETS (Phase 15 Step 1, re-extracted directly from
results/phase6/{moushun_chen,lai_eu_wen,achille_gohin,zach_locke}/
days_opponent.csv at days 5/10/15/20/25/29 -- see
results/phase15/PHASE15_MACRO_CONTROLLER_REPORT.md Section 2 for the full
table this module is built from). HISTORICAL RECORD ONLY -- superseded by
the Phase 19 update above:

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

# ---- PHASE 19 real-data-grounded target ceilings, re-extracted from the
# fresh top-ladder replays (results/phase19/fresh_ladder/) -- see the module
# docstring's Phase 19 update note and the Phase 19 report Section 2 for the
# exact day-by-day source numbers these constants are read off of. ----
TARGET_LAND_QUADRANTS = 3       # both fresh players cap at 3 (reached by day 15), not Phase 15's 4
TARGET_HANDS = 11               # both fresh players settle at 10-12 (median 11), not Phase 15's 13
ANIMALS_BASE_TARGET = 14        # ramp aims for this by default -- roughly the midpoint of the observed 12-17 range
TARGET_ANIMALS_TOTAL = 17       # hard ceiling for the opponent-ratchet -- Larko's own peak, observed episode 105027448
TARGET_ANIMAL_SPECIES = {"COW": 7, "SHEEP": 7}  # near-even split -- fresh data shows no consistent species
                                                 # preference (9/8, 9/5, 5/10, 6/6 all observed across the 5 trajectories)

# Day thresholds at which each axis reaches specific rungs, taken directly
# from the fresh replays' own day 0/5/10/15 snapshots (both players land on
# nearly identical numbers at each of these days) rather than an invented
# smooth curve -- ramps are piecewise, matching how real opponents actually
# move (step increases at hire/buy events, e.g. hands jump straight from ~5
# at day 5 to ~11 at day 10), not continuous.
_LAND_RUNGS = [(0, 1), (10, 2), (15, TARGET_LAND_QUADRANTS)]
_HANDS_RUNGS = [(0, 2), (5, 5), (10, TARGET_HANDS)]
_ANIMALS_RUNGS = [(0, 0), (5, 6), (10, 13), (15, ANIMALS_BASE_TARGET)]

# Crop-fraction schedule (of the crop-tile pool only; structure tiles are
# carved out separately) -- day-bucketed, re-derived from the fresh replays'
# own crop-tile counts at each sampled day (both players agree closely):
#   day 0:  WHEAT 6-7 / MELON 12           (~35% WHEAT / 65% MELON of ~18-19 tiles)
#   day 5:  WHEAT 3 / STRAWBERRY 4 / MELON 12  (~16% / 21% / 63% of ~19 tiles)
#   day 10: WHEAT 12-13 / STRAWBERRY 20-21     (~38% / 62% of ~32-34 tiles, MELON dropped)
#   day 15-24: WHEAT 23-25 / STRAWBERRY 33-38  (~40% / 60% of ~58-63 tiles, unchanged day15->day20)
#   day 25+: WHEAT 39 / CARROT 4-6 / STRAWBERRY 13-18  (~65% / 9% / 26% of ~58-62 tiles --
#            WHEAT overtakes STRAWBERRY; [INFERRED] this is a time-horizon effect, not a
#            profitability reversal -- WHEAT's first_yield_day=2 lets it keep cycling right up
#            to the season's end, while a freshly-planted STRAWBERRY (first_yield_day=10)
#            planted this late would not mature before the season ends)
# From day 26+, agents/phase15/endgame.py's liquidation mechanic takes over (stop
# planting, clear standing "ongoing" crops) -- this schedule's own fractions stop
# mattering once is_liquidating(day) suppresses all new PLANT tasks.
_CROP_SCHEDULE = [
    (0, {"MELON": 0.65, "WHEAT": 0.35}),
    (5, {"MELON": 0.63, "STRAWBERRY": 0.21, "WHEAT": 0.16}),
    (10, {"STRAWBERRY": 0.62, "WHEAT": 0.38}),
    (15, {"STRAWBERRY": 0.58, "WHEAT": 0.42}),
    (25, {"WHEAT": 0.65, "STRAWBERRY": 0.27, "CARROT": 0.08}),
]

CROP_TILE_TARGET_CEILING = 62  # both fresh players run 58-63 tiles at scale -- not Phase 15's ~50
# Footprint still RAMPS (not fixed at the ceiling from day 0) -- Phase 15 already
# found a day-0 fixed-footprint config produces a cash-collapse death spiral (seed
# costs outrunning the $3000 start before any harvest revenue arrives); this ramp
# instead tracks the fresh replays' own day 0/5/10/15 crop-tile counts directly
# (~19 tiles day 0-9, ~33 tiles day 10-14, then the full 58-63-tile ceiling from
# day 15), not an invented curve.
_CROP_TILE_RUNGS = [(0, 19), (10, 33), (15, CROP_TILE_TARGET_CEILING)]


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

    if ANIMALS_BASE_TARGET > 0 and animals_total > 0:
        # Scaled against ANIMALS_BASE_TARGET (the ramp's own default target, 14),
        # not TARGET_ANIMALS_TOTAL (17, the separate opponent-ratchet CEILING) --
        # TARGET_ANIMAL_SPECIES sums to ANIMALS_BASE_TARGET by construction, so
        # this keeps the species split proportional at the ramp's normal
        # operating point while still letting animals_total legitimately exceed
        # ANIMALS_BASE_TARGET (up to TARGET_ANIMALS_TOTAL) when ratcheted up.
        scale = animals_total / ANIMALS_BASE_TARGET
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
