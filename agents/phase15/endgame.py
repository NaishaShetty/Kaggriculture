"""
Phase 19 endgame-liquidation mechanic -- new, distinct from the sell-timing
layer Phase 16 already cut (agents/phase15/sell_timing.py, left in place,
still disabled by default; NOT revived here).

GROUNDED IN FRESH DATA (results/phase19/fresh_ladder/, 4 real replays pulled
directly from Kaggle's current top ladder -- see
results/phase19/PHASE19_LADDER_RECALIBRATION_REPORT.md Section 2 for the full
table): both independent strong players observed (Dmitry Larko, 4 episodes;
Milan Leonard, 1 episode) show a FULL crop-tile wind-down -- 58-63 tiles still
standing at day 25, 0-2 tiles remaining by day 29. Neither Phase 15 nor
Phase 16 modeled this at all (both let the macro controller's crop-fraction
schedule keep planting new crop right up to the season's end).

SAMPLING LIMITATION, disclosed rather than hidden: the source replays were
only sampled at days {0, 5, 10, 15, 20, 25, 29} (agents/phase6/
replay_forensics.py's own snapshot convention). day 25 is still full, day 29
is empty -- the EXACT day the wind-down starts is not directly observed
anywhere in the days 26-28 window. The thresholds below are therefore
[INFERRED], not [VERIFIED] -- chosen as a reasonable estimate inside that
window, not read directly off a day-26/27/28 snapshot that doesn't exist in
the sampled data.

MECHANISM: from LIQUIDATION_START_DAY, stop planting new crop (existing
non-ongoing crops like WHEAT/MELON still finish their current cycle and
auto-clear per the engine's own logic -- vendor_kaggriculture.kaggriculture.py
`_apply_unit_action`'s HARVEST branch already sets `farm["tiles"][fy][fx] =
None` for any non-`ongoing` crop). From DIG_ONGOING_CROPS_DAY (a few days
later, closer to the season's actual end), explicitly DIG any tile still
holding an "ongoing" crop (STRAWBERRY/TOMATO) -- the only way to clear one,
since it never auto-clears on its own (`_apply_unit_action`'s DIG branch:
"Removes plants, weeds, empty coop/pasture. Does NOT remove a placed
animal.") -- matching the observed day-29 shape (0-2 tiles, essentially
fully cleared) rather than leaving still-standing STRAWBERRY plants
un-harvested-and-abandoned at the season's end.

Deliberately does NOT touch animals, hands, or land -- both fresh episodes
show animal counts held STEADY through day 29 (17/17/15/14 -> unchanged;
12 -> unchanged), only the crop side gets wound down.
"""

LIQUIDATION_START_DAY = 26  # [INFERRED] stop planting from here (day 25 sample still full, day 29 empty)
DIG_ONGOING_CROPS_DAY = 28  # [INFERRED] explicitly clear any still-standing ongoing crop with 1-2 days left


def is_liquidating(day):
    """True from LIQUIDATION_START_DAY onward -- gates new PLANT/BUY_SEED activity off."""
    return day >= LIQUIDATION_START_DAY


def should_dig_ongoing_crop(day):
    """True from DIG_ONGOING_CROPS_DAY onward -- an "ongoing" crop (STRAWBERRY/
    TOMATO) that never naturally clears itself should be explicitly DIG'd
    rather than left standing, unharvested-from-here-on, at season's end."""
    return day >= DIG_ONGOING_CROPS_DAY
