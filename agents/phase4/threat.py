"""
Phase 4 competitive threat manager.

Combines projected gap (forecast.py), opponent growth rate
(opponent_model.py), and remaining time into a single, interpretable
threat score. Deliberately simple and additive rather than a fitted model
-- there is no labeled dataset to fit a classifier against, and an
invented weighting scheme would be indistinguishable from arbitrary
numbers. Each term's sign/magnitude is justified from what it directly
measures, not tuned to any specific episode.
"""
from dataclasses import dataclass

NOT_A_THREAT, DEVELOPING_THREAT, MATERIAL_THREAT, CRITICAL_THREAT = (
    "NOT_A_THREAT", "DEVELOPING_THREAT", "MATERIAL_THREAT", "CRITICAL_THREAT")


@dataclass
class ThreatAssessment:
    level: str
    score: float
    projected_gap: float
    opponent_regime: str
    reason: str


def assess_threat(projected_gap_value, opponent_animal_velocity, opponent_hands_velocity,
                   opponent_regime, remaining_days, our_current_cash):
    """`projected_gap_value` > 0 means we are ahead. A large negative gap,
    combined with sustained opponent growth and enough remaining time to
    matter, raises the threat level. Time remaining modulates severity in
    both directions: a large deficit with almost no season left is not
    "critical" in the actionable sense (there is no time to respond), so
    it is reported as MATERIAL rather than CRITICAL to avoid provoking a
    wasteful last-minute over-reaction; the same deficit early in the
    season, with time to act, is CRITICAL."""
    growth_signal = max(0.0, opponent_animal_velocity) * 3 + max(0.0, opponent_hands_velocity) * 1
    deficit_signal = max(0.0, -projected_gap_value)
    time_factor = min(1.0, remaining_days / 15.0)  # scales up to 1.0 as more season remains

    score = (deficit_signal / 1000.0) + growth_signal * time_factor

    if score < 2:
        level = NOT_A_THREAT
        reason = "projected gap is small/favorable and opponent growth is modest"
    elif score < 8:
        level = DEVELOPING_THREAT
        reason = "a deficit or opponent growth trend exists but is not yet severe"
    elif score < 20 or remaining_days < 4:
        level = MATERIAL_THREAT
        reason = ("meaningful deficit/growth combination" if remaining_days >= 4
                  else "large deficit but insufficient remaining time to meaningfully respond")
    else:
        level = CRITICAL_THREAT
        reason = "large projected deficit, sustained opponent growth, and enough time remaining to matter"

    return ThreatAssessment(level=level, score=round(score, 2), projected_gap=projected_gap_value,
                             opponent_regime=opponent_regime, reason=reason)
