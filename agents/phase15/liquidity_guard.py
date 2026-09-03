"""
Phase 20 liquidity guard for agents/phase15/ -- adapted from, NOT copied
from, agents/phase3_7/f005_liquidity_guard.py (the Submission C/E lineage's
guard: checks cash on a day-indexed window, and if triggered ONCE, halves
the (static) crop-portfolio config for the rest of the episode).

WHY THIS IS A DIFFERENT MECHANISM, NOT A PORT: Phase 20's own diagnosis
(results/phase20/PHASE20_LIQUIDITY_GUARD_REPORT.md Section 2) traced several
losing head-to-head seeds and found the collapse pattern is NOT a single
early crisis the way Submission C's F-005 case was -- it RECURS repeatedly
across the first ~25 days of the game (cash hits exactly $0 for several days,
partially recovers, then hits $0 again, 3-4 separate times in one episode),
each time coinciding with a big lump expenditure (a new BUY_LAND purchase,
or a large HIRE batch after hands had dropped to 0). A single "halve the
crop config, then never touch it again" guard -- fine for Submission C's
one-time early crisis -- is the wrong shape for a RECURRING pattern: it can
only fire once, but this agent needs to defer big purchases EVERY time cash
gets critically low, not just the first time.

THE MECHANISM: every turn, before HIRE/BUY_LAND are decided, check the
farm's current cash. If it's below CASH_DANGER_THRESHOLD, temporarily CAP
this turn's targets down to whatever is ALREADY committed (current actual
hand count, current actual land quadrant count) -- i.e., freeze further
hiring and land purchases for this turn only, re-checked fresh every turn
(not "at most once per episode" -- the recurring nature of the diagnosed
problem requires a guard that can re-arm). This can only ever REDUCE a
turn's targets relative to what the macro controller proposed, never raise
them -- the same "can only reduce risk, never add it" safety principle every
guard in this project has used (F-005, Section 3 of this module's own
report).

Deliberately does NOT touch the crop-tile ceiling or crop fractions --
Phase 20's diagnosis (Section 2) found the collapses coincide with
LAND/HIRE lump costs, not crop-seed spend, so the lever that addresses the
actual observed cause is throttling land/hire, not halving crop footprint
(unlike F-005, which correctly targeted crop footprint because Phase 3.7's
own diagnosis found THAT was the lever binding in Submission C's case).
"""

CASH_DANGER_THRESHOLD = 300.0  # [OBSERVED] every traced collapse spends multiple
                               # consecutive days at exactly $0-$200 before recovering

# [VERIFIED, found while validating this guard's first draft] Freezing n_hands
# down to the RAW current hand count is the wrong floor: hands reset to []
# every single day (a verified engine mechanic, documented since Phase 6), so
# `current_hands` read at the start of a turn is 0 on any day the FIRST turn
# also sees low cash -- capping the target to that would target ZERO hands for
# the entire day, guaranteeing zero production and deepening the exact cash
# drought the guard is trying to escape. MIN_HANDS_WHEN_GUARDED is a small,
# cheap floor (far below the Fibonacci-cost cliff of the full 11-hand target)
# that keeps the farm minimally staffed even while the guard is suppressing
# further growth.
MIN_HANDS_WHEN_GUARDED = 3

# [VERIFIED, found while validating this guard's first two drafts] The
# recurring collapse is not actually stopped by freezing hiring/land AFTER
# cash is already low -- several traced seeds show cash HIGH the turn before
# a big lump purchase (e.g. $2,442 the day before a land-quadrant buy) and
# exactly $0 the turn after, because the purchase itself is sized close to
# or larger than a comfortable reserve. Once cash actually hits $0, even the
# cheapest possible hire (fib(0)=$1) is unaffordable that whole day (hands
# reset to [] daily -- a $0-cash day is a total production standstill, not
# just a slower-growth day). The fix has to be PRE-EMPTIVE: require a
# reserve to remain AFTER a land purchase, not just react once cash is
# already critical.
LAND_PURCHASE_RESERVE = 500.0


def land_purchase_affordable(money, cost):
    """Pre-emptive check used by the BUY_LAND block: only buy if a reserve
    would remain afterward, not just if the raw cost is technically covered."""
    return money >= cost + LAND_PURCHASE_RESERVE


def apply_liquidity_guard(targets, cash, current_hands, current_land_quadrants):
    """Returns (new_targets, triggered). `targets` is whatever
    agents.phase15.macro_controller.compute_targets already proposed for
    this turn. Never mutates `targets` in place."""
    if cash >= CASH_DANGER_THRESHOLD:
        return targets, False

    new_targets = dict(targets)
    # Cap hiring growth to a small, cheap operating floor -- never below what's
    # already hired (so an already-larger workforce is never force-fired), and
    # never above the floor while guarded (so the expensive climb to the full
    # target waits until cash recovers).
    new_targets["n_hands"] = max(current_hands, min(targets["n_hands"], MIN_HANDS_WHEN_GUARDED))
    # Freeze further land purchases this turn: don't buy the next quadrant.
    new_targets["land_quadrants"] = min(targets["land_quadrants"], current_land_quadrants)

    triggered = (new_targets["n_hands"] != targets["n_hands"]
                 or new_targets["land_quadrants"] != targets["land_quadrants"])
    return new_targets, triggered
