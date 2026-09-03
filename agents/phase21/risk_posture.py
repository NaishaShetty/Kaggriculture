"""
Phase 26: a risk-posture layer for agents/phase21/ -- reads the LIVE,
fully-public relative score margin (own money - opponent money) every turn
and adjusts a small number of already-existing cash-safety parameters
accordingly, instead of using the same fixed reserve regardless of whether
the game is currently being won or lost.

WHY THIS IS LEGITIMATE, MECHANICALLY (confirmed directly from source, not
assumed): vendor_kaggriculture/kaggriculture.py assigns `obs0.farms` as the
SAME shared list object to both players' observation records (read directly
at the lines that build each step's per-player observation) -- meaning
`obs["farms"][opponent_index]["money"]` is exactly as public as
`obs["farms"][own_index]["money"]`, no inference or telemetry needed, every
single turn. No agent in this project (Submission C through agents/phase21/'s
own prior phases) has ever used live opponent CASH as a decision input --
the existing scaling detectors (agents/phase3_5/, agents/phase3_8/) key off
opponent tile/animal counts, a different signal entirely.

THRESHOLDS, grounded in Phase 26's own traced data (results/phase26/
PHASE26_RISK_POSTURE_REPORT.md Section 1), not picked arbitrarily: across 5
traced close/moderate losses to Submission G, the live margin oscillates
in the low single-thousands range for most of the mid-late game (e.g.
$34, $79, $682, -$543, -$754, -$950 all appear as real "close" moments) and
only opens up into a clear multi-thousand-dollar lead or deficit outside
that band (e.g. +$5,007, +$9,564, -$3,565). CLOSE_BAND is set at $3,000 to
sit just above the observed close-moment cluster and below the observed
clear-lead/deficit cluster.

HONEST CAVEAT (see the Phase 26 report's own Section 1-2 for the full
diagnosis): the SAME traces that motivated this module's thresholds also
found the actual dominant mechanism behind these specific losses is NOT a
risk-posture/spending-behavior difference -- it is an endgame-liquidation
TIMING gap (Submission G captures one more day of harvest-and-sell revenue
than agents/phase21/'s own liquidation schedule allows). This module is
built and validated in full regardless, per this phase's explicit brief,
but is not expected to be the mechanism that closes those particular games.
"""

CLOSE_BAND = 3000.0  # |margin| below this -> CLOSE; grounded in the traced close-moment cluster

# Cash-safety parameters this module adjusts (mirrors the fixed values
# agents/phase21/execution.py used before this phase: $150 for both the
# hiring-freeze threshold and the land-purchase reserve).
POSTURE_PARAMS = {
    "BEHIND": {"cash_danger_threshold": 75.0, "land_purchase_reserve": 75.0},
    "CLOSE": {"cash_danger_threshold": 150.0, "land_purchase_reserve": 150.0},
    "AHEAD": {"cash_danger_threshold": 300.0, "land_purchase_reserve": 300.0},
}


def classify_posture(own_money, opponent_money):
    """Returns one of "AHEAD", "CLOSE", "BEHIND" from the live, fully-public
    margin (own_money - opponent_money). Pure function, no hidden state --
    same "simple, auditable" discipline as every classifier this project has
    built (Phase 3.5's scaling detector, Phase 15's macro-controller ramps)."""
    margin = own_money - opponent_money
    if margin > CLOSE_BAND:
        return "AHEAD"
    if margin < -CLOSE_BAND:
        return "BEHIND"
    return "CLOSE"


def posture_params(own_money, opponent_money):
    """Returns the {cash_danger_threshold, land_purchase_reserve} dict for
    the current posture. BEHIND accepts more risk (smaller reserves, to
    invest/catch up); AHEAD protects the lead (larger reserves, since a
    liquidity-guard-triggered stall late in an already-winning game is a
    pure self-inflicted loss); CLOSE uses the same fixed values this
    project's execution layer already validated (Phase 21/24/25)."""
    posture = classify_posture(own_money, opponent_money)
    return posture, POSTURE_PARAMS[posture]
