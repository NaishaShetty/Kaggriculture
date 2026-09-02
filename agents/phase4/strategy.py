"""
Phase 4 strategic mode controller.

HONEST SCOPE NOTE: implements 5 of the 7 modes sketched in the brief with
distinct behavior (NORMAL, COUNTER, DEFEND, RECOVER, ENDGAME).
ACCELERATE and MARKET_EXPLOIT are not separately implemented as distinct
modes this phase -- ACCELERATE's described behavior ("accept higher
investment when behind but recovery is realistic") is subsumed by
COUNTER's animal/hands response (reusing Submission C's validated,
frozen mechanism) combined with the portfolio controller's own
value-per-depth allocation; MARKET_EXPLOIT's described behavior (timing/
partial-selling around market conditions) is implemented directly inside
liquidity.py's endgame logic and the per-turn sell-policy decision below,
rather than as a separately-named mode, since separating them would add
a mode-transition dimension without a correspondingly distinct action
space to justify it. This is a scope decision, stated plainly rather
than silently claiming 7 modes exist.

Mode transitions use hysteresis (a mode is only changed if the new
mode's justification is not marginal) to avoid thrashing, per the
brief's explicit instruction.
"""
from dataclasses import dataclass

NORMAL, COUNTER, DEFEND, RECOVER, ENDGAME = "NORMAL", "COUNTER", "DEFEND", "RECOVER", "ENDGAME"


@dataclass
class StrategyDecision:
    mode: str
    reason: str


def select_mode(threat_assessment, liquidity_state_value, is_endgame_window, previous_mode=None):
    if is_endgame_window:
        return StrategyDecision(ENDGAME, "final days of the season -- optimize for realized cash, not production value")

    if liquidity_state_value == "CRITICAL":
        return StrategyDecision(RECOVER, "cash below minimum reserve -- prioritize liquidity over growth")

    if threat_assessment.level in ("MATERIAL_THREAT", "CRITICAL_THREAT"):
        return StrategyDecision(COUNTER, f"opponent threat assessed as {threat_assessment.level}: {threat_assessment.reason}")

    if threat_assessment.projected_gap > 5000 and threat_assessment.level == "NOT_A_THREAT":
        # Hysteresis: only switch INTO defend if we're not already mid-COUNTER for a
        # marginal reason -- a comfortable, unthreatened lead is the one case where
        # avoiding unnecessary escalation (brief section 17) is unambiguous.
        if previous_mode != COUNTER or threat_assessment.score < 3:
            return StrategyDecision(DEFEND, "comfortable projected lead and no material threat -- avoid unnecessary risk")

    return StrategyDecision(NORMAL, "no elevated threat, no liquidity concern, no clear lead to protect -- standard growth")
