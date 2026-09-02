"""
Phase 3.5 opponent competitive-scaling detector.

MOTIVATION (real-competition evidence, not synthetic-benchmark-driven): of
18 real Kaggle episodes analyzed in results/phase3_5/ (see
competition_results_inventory.json, differential_summary.json), the 6
highest-margin losses (L001, L002, L003, L005, L008, L010 -- see
results/phase3_5/failure_knowledge_base.json) all share a mechanism NONE of
the 7 existing synthetic archetypes (agents/phase3/opponent_classes.py)
reproduce: the opponent commits to a SUSTAINED, LARGE multi-resource base
(hired hands, animals, sometimes land) starting early-to-mid game and
maintains it for the rest of the season, while our own agent's hands stay
fixed at 2 and animals at 1-2 the entire game regardless (Planner v1's
labor/animal targets are calibrated in ISOLATION, per Phase 2.3, with no
opponent-awareness at all). Real losing-episode opponents averaged
opp_hands_final=5.9 and opp_animals_final=6.2 vs. 1.62/0.12 in real winning
episodes.

DESIGN CHOICE: this is a deliberately SIMPLE, RULE-BASED, publicly-
observable-only detector (hand count and animal count are both directly
present in `obs["farms"][opponent]`, per AGENTS.md's documented observation
schema) -- not a trained classifier like Phase 3.3's ExpansionDetector. Per
the brief's explicit instruction ("do not build an enormous model before
simpler explanations are tested"), and because the signal here is a large,
simple magnitude gap (6-19 vs 0-2), not a subtle multi-feature pattern
requiring a nearest-centroid classifier to separate.

Thresholds (HANDS_THRESHOLD=5, ANIMALS_THRESHOLD=5) were chosen as ROUND
NUMBERS reflecting the rough real-data MAGNITUDE gap (roughly halfway
between our own ceiling of ~2 and the real losing-opponent mean of ~6), NOT
fit/tuned against the 18 real episodes themselves (which the brief
explicitly prohibits: "do not tune directly against individual live
episodes"). Validated instead via the controlled synthetic `heavy_scaler`
archetype (agents/phase3_5/opponent_classes_extended.py) across disjoint
development/validation/held-out seed sets, exactly like every prior phase's
detector/threshold work.

Sampling avoids the documented daily hands-reset artifact (hands count is
reset to 0 at hour==0 of every day, VERIFIED via kaggriculture.py and
directly re-discovered this phase while extracting real-replay
trajectories) by only ever reading the OpponentObservationLogger snapshot
closest to (but not exceeding) MIN_SAMPLE_HOUR within the current day.
"""
from dataclasses import dataclass

HANDS_THRESHOLD = 5
ANIMALS_THRESHOLD = 5
MIN_CONSECUTIVE_DAYS = 3
MIN_SAMPLE_HOUR = 18  # avoid sampling near the hour==0 daily hands-reset


@dataclass
class ScalingDetectionResult:
    active: bool
    reason: str
    days_checked: int
    opponent_hands_recent: list
    opponent_animals_recent: list


def _daily_late_samples(history):
    """One snapshot per day, the LATEST one with hour >= MIN_SAMPLE_HOUR
    seen so far for that day (falls back to the latest snapshot of the day
    if none meets the hour bar yet, e.g. early in a very short test)."""
    by_day = {}
    for snap in history:
        day = snap.day
        if day not in by_day or snap.hour > by_day[day].hour:
            if snap.hour >= MIN_SAMPLE_HOUR or day not in by_day:
                by_day[day] = snap
    return by_day


def check(history, current_day):
    """`history`: agents.phase3.opponent_observation.OpponentObservationLogger.history
    up to the current turn (never anything from the future -- same temporal
    discipline as Phase 3.3's ExpansionDetector). Returns a
    ScalingDetectionResult; `active=True` only when BOTH the last
    MIN_CONSECUTIVE_DAYS available daily samples show hands>=HANDS_THRESHOLD
    OR animals>=ANIMALS_THRESHOLD in EVERY one of those days (sustained, not
    a single-day spike)."""
    daily = _daily_late_samples(history)
    days_available = sorted(d for d in daily if d < current_day or daily[d].hour >= MIN_SAMPLE_HOUR)
    if len(days_available) < MIN_CONSECUTIVE_DAYS:
        return ScalingDetectionResult(active=False, reason="insufficient history", days_checked=len(days_available),
                                       opponent_hands_recent=[], opponent_animals_recent=[])

    recent_days = days_available[-MIN_CONSECUTIVE_DAYS:]
    hands_recent = [len(daily[d].visible_hand_positions) for d in recent_days]
    animals_recent = [sum(daily[d].visible_animal_tile_counts.values()) for d in recent_days]

    hands_sustained = all(h >= HANDS_THRESHOLD for h in hands_recent)
    animals_sustained = all(a >= ANIMALS_THRESHOLD for a in animals_recent)
    active = hands_sustained or animals_sustained

    if hands_sustained and animals_sustained:
        reason = f"sustained hands>={HANDS_THRESHOLD} AND animals>={ANIMALS_THRESHOLD} over {MIN_CONSECUTIVE_DAYS} days"
    elif hands_sustained:
        reason = f"sustained hands>={HANDS_THRESHOLD} over {MIN_CONSECUTIVE_DAYS} days"
    elif animals_sustained:
        reason = f"sustained animals>={ANIMALS_THRESHOLD} over {MIN_CONSECUTIVE_DAYS} days"
    else:
        reason = "no sustained scaling detected"

    return ScalingDetectionResult(active=active, reason=reason, days_checked=len(recent_days),
                                   opponent_hands_recent=hands_recent, opponent_animals_recent=animals_recent)
