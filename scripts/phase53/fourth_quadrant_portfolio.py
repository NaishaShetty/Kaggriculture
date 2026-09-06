"""
Phase 53: a capacity-aware wrapper around
agents/phase21/portfolio.py::portfolio_targets (imported unmodified, per the
Phase 42/45/48 "wrap, don't edit" composition pattern) that extends the
EXISTING 3-quadrant land/hands/crop-tile rung tables with a 4th tier --
same MELON/STRAWBERRY/WHEAT crop mix, same ratios, same execution layer.
Only `land_quadrants`, `n_hands`, and `crop_tile_target` are touched; the
`crop_fractions` and `animals` fields pass through byte-for-byte from
`portfolio_targets`'s own `_base_crop_fractions(day)` -- reused, not
reimplemented -- so the 4th quadrant's tiles get planted with the SAME
ratios already validated for quadrants 1-3.

WHY THIS PHASE EXISTS: Phase 52's forensic analysis of our 3 most recent
real losses found 2 of 3 (vs. real opponents "yuki" and "Sarthak Patel")
were opponents running our OWN exact crop portfolio, just with a 4th land
quadrant we never take -- not a different strategy, not a different crop,
not copied numbers from a real opponent's whole different scale (the thing
Phase 43 already tested and found underperforms). Every PRIOR 4th-quadrant
attempt in this project failed for a reason specific to what made it
DIFFERENT from our own working schedule: Phase 33/48 added a NEW dedicated
crop (TOMATO/GOOSE) with dedicated hands -- a recurring Fibonacci HIRE-cost
problem, confirmed twice by direct trace; Phase 43 copied a real opponent's
raw target numbers wholesale (different crop mix/scale entirely) and it
underperformed our own tuned targets; Phase 51's generic HIRE cash-flow
pacer failed its own sanity check before the 4th-quadrant question was even
reached. This phase is the one variant nobody tried: same crops, same
ratios, same execution, just scaled land/hands/crop-tile targets.

RUNG DESIGN, GROUNDED DIRECTLY IN REAL DATA (not guessed round numbers) --
confirmed by a fresh direct trace of BOTH real opponent trajectories this
phase re-pulled from Phase 52's own already-downloaded replay JSONs
(results/phase52/raw_replays/105745378.json for yuki,
results/phase52/raw_replays/105744439.json for Sarthak Patel), NOT merely
assumed from the Phase 52 report's coarser final-day-only summary (which
only recorded final_land_quadrants and first_land_expansion_day = first day
land_quadrants > 1, not specifically when a 4th quadrant was reached):

  - yuki: land_quadrants hits 3 on day 11 (matching our OWN existing day-11
    rung exactly), then 4 on day 17. Hands stay FLAT at 10 the entire game
    (never above our own current 11-hand target) even while running up to
    88 crop tiles at peak.
  - Sarthak Patel: land_quadrants hits 3 on day 10, then 4 on day 12 (a much
    tighter 2-day gap than yuki's 6-day one). Hands jump to 14 on day 11
    (one day BEFORE their own 3rd-quadrant purchase even lands) and hold at
    14 through day 26; peak crop tiles 67.
  - So real day-9-to-11 land-4 timing (the brief's initial framing) does NOT
    hold precisely for either real trajectory -- day 12 (Sarthak) and day 17
    (yuki) is the real, directly-confirmed range. This module targets day 16
    for the 4th land-quadrant rung: inside that real range, and consistent
    with our OWN agent's existing ~5-day cadence between quadrant purchases
    (day 6 -> day 11 is a 5-day gap; day 11 -> day 16 continues the same
    cadence rather than inventing a new one).
  - HANDS: real data brackets a wide range (10-14) around our own existing
    11-hand target, not a clean "scale hands proportionally to land"
    signal -- yuki succeeded at land=4 with FEWER hands than we already run.
    Combined with Phase 30/46's own idle-worker-turn measurement (~7-9% idle
    at the current 11-hand/50-58-tile scale -- essentially no slack left,
    the same finding that sank Phase 30's fertilizer attempt and Phase
    33/48's dedicated-hands 4th-quadrant attempts), a full proportional
    scale-up (11 * 4/3 ~= 15) risks manufacturing capacity the schedule
    can't use efficiently, the exact failure mode already diagnosed twice.
    This module picks 13 hands -- a moderate increase (not the full
    proportional jump, not zero increase either), inside the real
    10-14 range and closer to Sarthak's successful 14 than a blind guess,
    added one day before the land-4 purchase (day 15), mirroring the
    existing table's own hands-before-land offset pattern (hands rung at
    day 10 precedes the land-3 rung at day 11).
  - CROP_TILE_TARGET: proportional scaling from the existing terminal rung
    (58 at day 15, for 3 quadrants) by land ratio (4/3) gives ~77 -- inside
    the real range actually observed (Sarthak peaked at 67, yuki peaked at
    88). This module targets 75, added at day 16 (same day as the land-4
    rung) since new tile capacity only exists once the 4th quadrant is
    actually owned.

ANIMAL CAP (Phase 48's cap_total=8): left UNCHANGED per this phase's own
explicit instruction not to touch it without a fresh measurement-based
reason. The real data here gives no such reason -- yuki's own animal count
under land=4 was 8, matching our existing cap almost exactly; Sarthak's
reached 10-13 but that opponent also ran meaningfully more hands (14) for
crop/tile servicing, not evidence that MORE hands specifically raises the
sustainable ANIMAL ceiling (a separate FEED/CARE labor question Phase 48's
own steady-state probe already measured directly). No fresh probe of the
animal ceiling AT the extended hand/land scale was run this phase since the
screen below (Section 3 of the report) found no basis to justify one.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402

_LAND_RUNGS_EXT = [(0, 1), (6, 2), (11, 3), (16, 4)]
_HANDS_RUNGS_EXT = [(0, 5), (6, 8), (10, 11), (15, 13)]
_CROP_TILE_RUNGS_EXT = [(0, 18), (6, 31), (10, 32), (11, 53), (15, 58), (16, 75)]


def _rung_value(day, rungs):
    value = rungs[0][1]
    for threshold_day, v in rungs:
        if day >= threshold_day:
            value = v
        else:
            break
    return value


def make_fourth_quadrant_target_fn(base_target_fn=portfolio_targets):
    """Wraps `base_target_fn` (portfolio_targets, or another wrapper already
    composed on top of it, e.g. Phase 48's capped-animal wrapper) and
    overrides ONLY `land_quadrants`, `n_hands`, and `crop_tile_target` with
    the extended 4-quadrant rung tables above. `crop_fractions` and
    `animals` pass through untouched -- same "wrap, don't edit" pattern as
    scripts/phase48/capped_animal_portfolio.py, which this module composes
    with (not replaces) in scripts/phase53/fourth_quadrant_portfolio_agent.py.
    """

    def target_fn(day, obs, opponent_history=None):
        targets = dict(base_target_fn(day, obs, opponent_history))
        targets["land_quadrants"] = _rung_value(day, _LAND_RUNGS_EXT)
        targets["n_hands"] = _rung_value(day, _HANDS_RUNGS_EXT)
        targets["crop_tile_target"] = _rung_value(day, _CROP_TILE_RUNGS_EXT)
        return targets

    return target_fn
