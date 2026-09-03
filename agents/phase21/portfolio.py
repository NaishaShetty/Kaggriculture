"""
Phase 21 Step 2: first-cut portfolio controller -- built ONLY because Step 1
(scripts/phase21/market_glut_experiment.py) confirmed the shared-market glut
hypothesis directly through the real engine, not assumed:

  A=MELON alone (no MELON competitor):  mean final $24,566, avg sell price ~$100/unit
  A=MELON vs. a MELON competitor:        mean final $8,212  (-66.5%), avg price ~$49-61/unit
  A=WHEAT alone (no WHEAT competitor):   mean final $5,754,  avg sell price ~$21.4/unit
  A=WHEAT vs. a WHEAT competitor:        mean final $5,038  (-12.4%), avg price ~$20.4/unit

MELON's final money is roughly 5x more sensitive (in relative terms) to a
second producer entering its pool than WHEAT's is -- a direct, real-engine
confirmation of the reframe (docs/FRESH_STRATEGY.md): MELON is a fine
OPENING crop (no competitor has scaled into it yet) and a bad SUSTAINED one
once a second real producer shares the pool; WHEAT's flat `log` glut curve
barely notices a second producer at comparable scale.

DESIGN (first cut, NOT submission-ready -- see the Phase 21 report's own
honest assessment):
  - MELON is time-boxed to the opening only (days 0-7, matching the fresh
    real-ladder data's own observed MELON window) -- never re-entered.
  - WHEAT is the durable backbone for the SUSTAINED, scaled portion of the
    portfolio (not a starter crop to graduate away from, per the reframe),
    weighted more heavily than the realistic-opponent benchmark's own
    observed split (which still ran STRAWBERRY-heavy through mid-game).
  - STRAWBERRY is a mid-game addition, but its SIZE is opponent-aware: this
    controller reads the opponent's own current crop-tile commitment (fully
    public, obs["farms"] -- same public-only telemetry convention this
    project has used since Phase 3, agents/phase3/opponent_observation.py)
    and shrinks its own STRAWBERRY allocation (shifting the difference into
    WHEAT) if the opponent is ALREADY heavily committed to STRAWBERRY --
    piling into the same glut-prone pool the opponent is already scaling
    into is exactly the mistake the reframe identifies.
  - Land/hands/animal targets reuse the same real-data ceilings Phase 19
    already validated (land 3, hands 11, animals up to 17) -- this phase's
    scope is Reframe 1 (portfolio/market) only, not re-deriving those.

Land/hands/animal ramp timing and the endgame-liquidation day thresholds are
carried over unchanged from scripts/phase21/realistic_opponent.py's own
real-data-grounded rungs (both this controller and the benchmark are built
on the same fresh-ladder data) -- only the CROP-FRACTION logic differs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402
from agents.phase21.liquidation import planting_cutoff_day  # noqa: E402

_LAND_RUNGS = [(0, 1), (6, 2), (11, 3)]
_HANDS_RUNGS = [(0, 5), (6, 8), (10, 11)]
_ANIMALS_RUNGS = [(0, 4), (4, 7), (6, 10), (10, 16), (11, 17)]
_ANIMAL_SPECIES_RUNGS = [
    (0, {"COW": 2, "SHEEP": 2}), (4, {"COW": 4, "SHEEP": 2}), (6, {"COW": 6, "SHEEP": 2}),
    (10, {"COW": 9, "SHEEP": 7}), (11, {"COW": 9, "SHEEP": 8}),
]
_CROP_TILE_RUNGS = [(0, 18), (6, 31), (10, 32), (11, 53), (15, 58)]

MELON_OPENING_END_DAY = 8  # MELON never appears in the crop mix after this day
# PHASE 27: the old global LIQUIDATION_START_DAY / DIG_ONGOING_CROPS_DAY
# (Phase 24/26) are REMOVED -- replaced by agents/phase21/liquidation.py's
# per-crop planting_cutoff_day() and per-tile tile_has_future_yield(),
# applied directly in agents/phase21/execution.py's task-scheduling loop.
# See results/phase27/PHASE27_PER_TILE_LIQUIDATION_REPORT.md for why a
# single shared day number for the whole farm was found to help some games
# and hurt others (Phase 26's own direct trace).

# Opponent-awareness threshold: if the opponent's own current crop footprint
# is more than this fraction STRAWBERRY, treat their STRAWBERRY pool draw as
# significant and shrink our own STRAWBERRY allocation accordingly.
#
# PHASE 24 DISCLOSURE: this mechanism is now DORMANT (threshold set above 1.0,
# so it can never fire), not removed -- kept as a documented dead lever rather
# than deleted, since it was a deliberate design choice this phase's trace
# specifically overturned. It was built on the assumption that STRAWBERRY's
# glut curve makes piling in alongside a STRAWBERRY-heavy opponent costly --
# the same assumption Phase 24 found does NOT hold at these agents' actual
# combined production/selling pace (STRAWBERRY's realized price stayed
# $269-288/unit even with Submission G alone selling 146-157 units/game into
# the shared pool). Shrinking STRAWBERRY specifically because the opponent is
# ALSO heavy in it would now work directly against the fix above. Left in
# place, dormant, rather than deleted, in case a future phase finds a
# production scale where the original concern becomes real again.
OPPONENT_STRAWBERRY_DOMINANCE_THRESHOLD = 1.1
STRAWBERRY_SHIFT_WHEN_OPPONENT_HEAVY = 0.20  # fraction points moved from STRAWBERRY to WHEAT (dormant, see above)


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def _base_crop_fractions(day):
    """MELON opening-only (unchanged, empirically confirmed -- see Phase 21
    Step 1); STRAWBERRY is the durable BULK backbone from day 8 onward, WHEAT
    a smaller diversification slice -- reversed from the original design, per
    Phase 24's direct head-to-head trace against Submission G.

    PHASE 22 TUNING (day<5 opening, UNCHANGED by Phase 24): a direct sweep of
    day-0 WHEAT fractions found 0.40 was a local minimum for cash-flow ramp
    speed; 0.50 was the best point (results/phase22/
    phase22_opening_ratio_sweep.json) and remains unchanged here -- Phase 24's
    finding is about the WHEAT/STRAWBERRY balance from day 8 onward, a
    different question from the day<5 MELON/WHEAT opening ratio.

    PHASE 24 FIX (day>=8 WHEAT/STRAWBERRY balance, REVERSED): Phase 21 Step 1
    confirmed MELON's glut curve (`sq`, above_target=3.60) crashes hard under
    two-producer competition -- but never separately tested whether the same
    conclusion holds for STRAWBERRY (`linear`, above_target=1.60, a much
    softer curve, base price $120 vs. WHEAT's $25). Phase 24's direct
    head-to-head trace against Submission G (results/phase24/
    PHASE24_LOSS_DIAGNOSIS_REPORT.md) found it does NOT: across all 4 traced
    losses, STRAWBERRY's REALIZED sell price for BOTH agents stayed
    $269-288/unit -- essentially uncrashed, base-price-adjacent -- even with
    Submission G alone selling 146-157 STRAWBERRY units into the shared pool
    per game. Submission G's near-total STRAWBERRY portfolio outsold this
    controller's WHEAT-heavy one by $30,000-33,000 in STRAWBERRY revenue
    alone, because WHEAT's own realized price (~$33-41/unit) is simply far
    lower in absolute terms, glut-resistance notwithstanding, at the actual
    combined production/selling PACE these two agents reach (harvests and
    sales are spread across many turns, never dumping enough at once to
    clear STRAWBERRY's T=100 glut threshold in practice). THE FIX: reverse
    the day>=8 WHEAT/STRAWBERRY weighting to favor STRAWBERRY as the bulk
    crop, matching what the trace showed actually wins -- MELON's
    opening-only role is untouched, since that specific glut conclusion was
    directly confirmed, unlike the STRAWBERRY assumption this replaces.

    PHASE 25 SWEEP (day 8-14 and day 15+ STRAWBERRY fractions, TESTED AND
    KEPT AS-IS): Phase 24 picked 0.65 (day 8-14) and 0.80 (day 15+) by
    inference from one trace, not a sweep -- the same risk Phase 22 flagged
    for the original opening ratio. A systematic sequential sweep
    (scripts/phase25/ratio_sweep.py, results/phase25/phase25_ratio_sweep.json)
    over day15+ in {0.70..0.95} and day8-14 in {0.55..0.75}, screened
    head-to-head against Submission G on the same 4 development seeds Phase
    22 used, found NO candidate came close to a positive margin -- unlike
    Phase 22's sweep, which found a clear winner. The apparent "best" 4-seed
    candidate (mid=0.70, late=0.70) was validated on the full 15-seed set and
    found to perform WORSE than Phase 24's original inferred ratios (3/15
    win rate vs. Submission G, down from 6/15) -- a small-sample-screening
    trap, the same risk Phase 17 already warned this project about. Phase
    24's original 0.65/0.80 was RESTORED after this check, since it is the
    better-validated choice on the full 15-seed sample. See
    results/phase25/PHASE25_CROP_RATIO_SWEEP_REPORT.md for the full sweep
    and honest conclusion: this ratio has plateaued as a lever for closing
    the remaining gap to Submission G.
    """
    if day < 5:
        return {"MELON": 0.5, "WHEAT": 0.5}
    if day < MELON_OPENING_END_DAY:
        return {"MELON": 0.35, "STRAWBERRY": 0.45, "WHEAT": 0.20}
    if day < 15:
        return {"STRAWBERRY": 0.65, "WHEAT": 0.35}
    if day <= planting_cutoff_day("STRAWBERRY"):
        return {"STRAWBERRY": 0.80, "WHEAT": 0.20}
    # PHASE 27: past STRAWBERRY's own per-crop planting cutoff (day 19 -- see
    # agents/phase21/liquidation.py), newly-vacant tiles should no longer be
    # NOMINALLY allocated to STRAWBERRY at all (agents/phase21/execution.py's
    # PLANT gate would block planting it anyway, but leaving the fraction as-is
    # would keep assigning those tile SLOTS to a crop that can never use them,
    # instead of redirecting them to WHEAT -- which remains plantable through
    # day 27). This is a mechanical consequence of the per-crop cutoff fix,
    # not a re-tuning of the validated 0.65/0.80 ratios themselves (which
    # still govern every day up to this point unchanged).
    return {"WHEAT": 1.0}


def _opponent_strawberry_share(opponent_history):
    """Reads the opponent's own most recent PUBLIC crop-tile counts (via the
    existing agents/phase3/opponent_observation.py telemetry convention --
    the caller wires opponent_history the same way agents/phase15/ and every
    phase since 3.3 has). Returns the opponent's STRAWBERRY share of their
    own total crop-tile footprint, or None if there's no history yet."""
    if not opponent_history:
        return None
    last = opponent_history[-1]
    counts = getattr(last, "visible_crop_tile_counts", None)
    if not counts:
        return None
    total = sum(counts.values())
    if total <= 0:
        return None
    return counts.get("STRAWBERRY", 0) / total


def portfolio_targets(day, obs, opponent_history=None):
    crop_fractions = dict(_base_crop_fractions(day))

    if "STRAWBERRY" in crop_fractions:
        opp_share = _opponent_strawberry_share(opponent_history)
        if opp_share is not None and opp_share > OPPONENT_STRAWBERRY_DOMINANCE_THRESHOLD:
            shift = min(STRAWBERRY_SHIFT_WHEN_OPPONENT_HEAVY, crop_fractions["STRAWBERRY"])
            crop_fractions["STRAWBERRY"] -= shift
            crop_fractions["WHEAT"] = crop_fractions.get("WHEAT", 0.0) + shift

    targets = {
        "n_hands": _rung_value(day, _HANDS_RUNGS),
        "land_quadrants": _rung_value(day, _LAND_RUNGS),
        "animals": dict(_rung_value(day, _ANIMAL_SPECIES_RUNGS)),
        "crop_tile_target": _rung_value(day, _CROP_TILE_RUNGS),
        "crop_fractions": crop_fractions,
    }
    # PHASE 27: no global liquidation-day override here anymore -- planting
    # cutoffs and ongoing-crop digging are now handled per-crop/per-tile
    # directly in agents/phase21/execution.py (imports agents/phase21/
    # liquidation.py). crop_tile_target keeps ramping normally; the execution
    # layer's own PLANT/DIG gates enforce the real per-crop timing.
    return targets


def make_portfolio_agent():
    return make_execution_agent(portfolio_targets)
