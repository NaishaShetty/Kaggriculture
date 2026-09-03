"""
Phase 27: per-crop, per-tile liquidation timing -- replaces Phase 24/26's
global LIQUIDATION_START_DAY / DIG_ONGOING_CROPS_DAY thresholds (one shared
day number for the whole farm) with logic computed from each crop's own
`vendor_kaggriculture.kaggriculture.CROPS` timing, and each STANDING TILE's
own `planted_day` -- not a blanket rule.

WHY A GLOBAL DAY THRESHOLD WAS WRONG (confirmed by Phase 26's direct trace,
results/phase26/PHASE26_RISK_POSTURE_REPORT.md): a fixed day-28 cutoff for
ALL crops/tiles helped some games (a tile that still had real production left
got to keep producing one more day) and hurt others (Submission G's own
game-specific harvest-cycle phase meant the "right" cutoff day varied game to
game) -- because the ACTUAL correct cutoff depends on each crop's own
first_yield_day/interval/max_yield and each tile's own planted_day, not one
number for the whole farm.

THE GOVERNING MECHANIC (read directly from vendor_kaggriculture/kaggriculture.py,
not assumed):
  - `_apply_unit_action`'s HARVEST branch (~line 453): blocks harvest until
    `day - planted_day >= first_yield_day`, for BOTH ongoing and non-ongoing
    crops identically. This means a NEWLY planted tile of ANY crop needs
    `planted_day + first_yield_day <= 29` for even one harvest to be
    possible before the season ends -- first_yield_day is the binding
    constraint either way, so both crop kinds share the same cutoff formula.
  - `_daily_refresh_plants` (~line 786-802): for ONGOING crops only, each
    scheduled yield lands on day = `planted_day + first_yield_day +
    k*interval` for k = 0 .. max_yield-1. A standing ongoing tile only has
    something left to wait for if at least one of those days is still
    `> current_day` and `<= 29`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vendor_kaggriculture.kaggriculture import CROPS  # noqa: E402

SEASON_END_DAY = 29


def planting_cutoff_day(crop):
    """Last day it is still worth PLANTING A NEW seed of `crop` -- the latest
    planted_day such that at least one real harvest can land on or before
    day 29. Per the module docstring, both ongoing and non-ongoing crops
    share the identical governing constraint (HARVEST blocked until
    first_yield_day, for either kind) -- so this is `SEASON_END_DAY -
    first_yield_day` for every crop, no special-casing needed.

    Per-crop values (computed here, not asserted -- see
    results/phase27/PHASE27_PER_TILE_LIQUIDATION_REPORT.md Section 1 for the
    full worked arithmetic for every crop in CROPS):
      WHEAT (first_yield_day=2):       29 - 2  = 27
      CARROT (first_yield_day=2):      29 - 2  = 27
      TOMATO (first_yield_day=8):      29 - 8  = 21
      MELON (first_yield_day=10):      29 - 10 = 19
      STRAWBERRY (first_yield_day=10): 29 - 10 = 19
    """
    return SEASON_END_DAY - CROPS[crop]["first_yield_day"]


def tile_has_future_yield(planted_day, crop, current_day, season_end=SEASON_END_DAY):
    """For a STANDING tile of an ONGOING crop (STRAWBERRY/TOMATO -- the only
    kind that needs explicit clearing; non-ongoing crops auto-clear
    themselves on harvest, per `_apply_unit_action`'s own HARVEST branch:
    `farm["tiles"][fy][fx] = None` once `not crop_data["ongoing"]`), returns
    True if at least one more scheduled yield (per `_daily_refresh_plants`'s
    own formula) will land in `(current_day, season_end]`. False means this
    specific tile has no more real production coming this season and is safe
    to explicitly clear (DIG) -- assuming it has no CURRENTLY pending
    harvest, which the caller's own task-priority order (HARVEST always
    checked before DIG) already guarantees is handled first."""
    cd = CROPS[crop]
    if not cd["ongoing"]:
        return False
    first_yield_day, interval, max_yield = cd["first_yield_day"], cd["interval"], cd["max_yield"]
    for k in range(max_yield):
        yield_day = planted_day + first_yield_day + k * interval
        if current_day < yield_day <= season_end:
            return True
    return False
