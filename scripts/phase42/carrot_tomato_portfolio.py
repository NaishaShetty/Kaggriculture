"""
Phase 42: a small, additive CARROT/TOMATO slice on top of Submission I's
shipped portfolio -- the actual configuration Phase 41's real ladder sample
showed (40% of 30 real trajectories, including gold-tier Crop Dusta and
keiz, run CARROT and/or TOMATO as a MINOR diversification slice alongside
an otherwise MELON/STRAWBERRY/WHEAT-anchored portfolio), not the monocrop
substitution Phase 33 Part A already tested and correctly rejected.

ISOLATED VARIANT, per this phase's own scope: this file wraps
`agents/phase21/portfolio.py::portfolio_targets` and
`scripts/phase37/paced_portfolio_agent.py::make_paced_portfolio_agent`
UNCHANGED -- neither is modified. Submission I's shipped behavior remains
exactly reproducible by calling those directly; this module only adds a new,
separate factory.

TILE-COUNT CALIBRATION (against the engine's own market constants, read
directly from vendor_kaggriculture/kaggriculture.py, not assumed):

  market_price(item, inventory) = base - amp*sqrt(inventory - I0), where
  amp = above_target * base / sqrt(T), for inventory > I0 (the game starts
  with inventory == I0 for every item, so `inventory - I0` is the net
  CUMULATIVE units sold above what's been bought back, shared across BOTH
  players and the whole 30-day game).

  CARROT (base=$35, T=450, above_target=0.70): amp = 0.70*35/sqrt(450) =
  1.156. Price stays above 60% of base ($21+) while net-sold volume stays
  under roughly 150-200 units. CARROT is a one-shot crop (not ongoing,
  max_yield=4/planting, first_yield_day=2) needing frequent replanting --
  over CARROT's own planting_cutoff_day=27 (agents/phase21/liquidation.py),
  a tile can realistically cycle ~5-6 plantings, so 6 tiles * ~5.5 cycles *
  4 units = ~130 units total -- comfortably inside the sub-200 "price stays
  healthy" zone even before accounting for the OTHER player's own CARROT
  buying/selling (which this project's real data shows some real opponents
  also do, further absorbing supply).

  TOMATO (base=$60, T=200, above_target=0.60): amp = 0.60*60/sqrt(200) =
  2.546. Price stays above ~57% of base ($34+) only under ~100 units net-
  sold -- a much tighter budget than CARROT, because TOMATO is ONGOING
  (interval=1, first_yield_day=8): once a tile matures it can in principle
  be harvested every single day through day 21 (its own planting_cutoff_day
  is 21, but an ALREADY-STANDING tile keeps yielding through
  tile_has_future_yield's day-29 window), so even 2-3 tiles could
  theoretically produce 200+ units if harvested every day. Kept
  deliberately SMALL (2 tiles) for exactly this reason -- a real scheduler
  competing for worker-turns against HARVEST/WATER/SELL on the existing
  MELON/STRAWBERRY/WHEAT/animal footprint will harvest TOMATO less than the
  theoretical daily maximum anyway, but 2 tiles keeps the worst case inside
  a defensible band rather than relying on that alone.

  CARROT_TILES = 6, TOMATO_TILES = 2 (8 total) -- inside Phase 41's own
  observed real range (roughly 5-15 tiles combined).

ADDITIVE, NOT A REALLOCATION: `crop_tile_target` is INCREASED by exactly
the slice size (8) every day; the existing crops' fractions are rescaled
proportionally so their RELATIVE split is unchanged, but applied against
the now-larger target -- since `bounded_multi_crop_tile_pool_assignment`
only fills VACANT tiles per the current fractions and never displaces an
already-growing (STICKY) tile, this means the existing MELON/STRAWBERRY/
WHEAT ramp keeps its original absolute tile-count target unchanged, and the
extra 8 slots are what CARROT/TOMATO fill -- never a reduction of what's
currently shipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase36.paced_execution import make_paced_execution_agent  # noqa: E402

CARROT_TILES = 6
TOMATO_TILES = 2


SLICE_START_DAY = 15
# PHASE 42 STEP 2 (added after the 4-seed screen below showed a severe
# negative on the naive day-0 version): the extra CARROT/TOMATO BUY_SEED
# spending collides with this agent's already-tightest cash window (day
# 0-11, simultaneous aggressive HIRE + the 2nd/3rd land-quadrant purchases
# -- confirmed directly by trace, see the Phase 42 report Section 4: the
# variant's own money sat at $0-52 for 14 straight days on seed 700003 vs.
# baseline's healthy $5k-14k over the same window, and the 3rd land
# quadrant purchase itself was delayed from day 11 to day 20). Delaying the
# slice until AFTER the core land/hand ramp settles (day 15, several days
# past `_LAND_RUNGS`'s day-11 3rd-quadrant rung and `_HANDS_RUNGS`'s day-10
# 11-hand rung in agents/phase21/portfolio.py) keeps the same additive
# design while no longer competing with the ramp for the exact days it
# needs uncontested cash -- still additive-only, still touches nothing in
# agents/phase21/execution.py or liquidation.py, per this phase's scope.


def make_slice_target_fn(base_target_fn=portfolio_targets, carrot_tiles=CARROT_TILES, tomato_tiles=TOMATO_TILES,
                          slice_start_day=SLICE_START_DAY):
    extra = carrot_tiles + tomato_tiles

    def target_fn(day, obs, opponent_history=None):
        base = base_target_fn(day, obs, opponent_history)
        t = dict(base)
        if extra <= 0 or day < slice_start_day:
            t["crop_fractions"] = dict(base["crop_fractions"])
            return t
        old_target = base["crop_tile_target"]
        new_target = old_target + extra
        old_fracs = base["crop_fractions"]
        old_sum = sum(old_fracs.values()) or 1.0
        # Rescale existing crops' fractions so their ABSOLUTE vacant-tile
        # fill count against the new (larger) target matches their original
        # absolute count against the old target -- never less than shipped.
        new_fracs = {crop: (frac / old_sum) * (old_target / new_target) for crop, frac in old_fracs.items()}
        if carrot_tiles > 0:
            new_fracs["CARROT"] = carrot_tiles / new_target
        if tomato_tiles > 0:
            new_fracs["TOMATO"] = tomato_tiles / new_target
        t["crop_tile_target"] = new_target
        t["crop_fractions"] = new_fracs
        return t

    return target_fn


def make_carrot_tomato_agent(carrot_tiles=CARROT_TILES, tomato_tiles=TOMATO_TILES, slice_start_day=SLICE_START_DAY):
    """Submission I's actual shipped execution layer (Phase 36's validated
    cash-flow-adaptive pacer, via scripts/phase36/paced_execution.py,
    reused unchanged) fed the slice-augmented targets above instead of
    agents/phase21/portfolio.py::portfolio_targets directly -- everything
    else (execution, liquidation, risk posture, pacing) is byte-identical
    to what Submission I ships."""
    opponent_logger = OpponentObservationLogger()
    target_fn = make_slice_target_fn(carrot_tiles=carrot_tiles, tomato_tiles=tomato_tiles, slice_start_day=slice_start_day)
    execution_agent = make_paced_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    agent._opponent_logger = opponent_logger
    return agent
