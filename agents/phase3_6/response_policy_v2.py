"""
Phase 3.6 adaptive scaling-response candidates (B1-B5), evaluated against
Submission B's fixed response (B0, `agents.phase3_5.response_policy
.competitive_scaling_response`, UNMODIFIED -- reused directly as the
control, never edited).

Each candidate reuses the EXACT SAME trigger condition (Phase 3.5's
`agents.phase3_5.opponent_scaling_detector.check`, unmodified) -- Phase
3.5's real-world evidence already established that detection works; this
phase's question is whether the RESPONSE MAGNITUDE can be smarter than a
fixed target. Candidates differ only in what they do once triggered.

All candidates take (config, obs, opponent_history, current_day) rather
than Phase 3.5's (config, state, ...) signature, because B4/B5 need our own
cash, which the frozen Phase 3.5 adapter never populates (state is always
None there -- a real, documented gap, not silently worked around by
editing that file). `obs` is passed instead, read-only, exactly the same
object Planner v1 itself already receives -- no new information channel.
"""
from agents.phase3_5.opponent_scaling_detector import check as check_scaling
from agents.phase3_5.response_policy import competitive_scaling_response as _b0_fixed_response

# -- shared constants --
MAX_HANDS_CAP = 12          # never propose more than this -- matches the ceiling above which
                             # even a synthetic opponent could not sustain itself (Phase 3.6-C)
MIN_CASH_RESERVE = 500.0    # B4: never let a response commitment be proposed if it would leave
                             # less than this much cash on the triggering day (a simple, principled
                             # solvency guard, not a tuned/fitted parameter)


def _our_cash(obs):
    return obs["farms"][obs["player"]]["money"]


MIN_SAMPLE_HOUR = 18  # matches agents.phase3_5.opponent_scaling_detector's own sampling discipline


def _opponent_hands_animals(opponent_history):
    """Reads a STABLE daily late-hour sample of the opponent's hands/
    animals count, not the raw most-recent snapshot -- hands reset to 0 at
    hour==0 of every day (documented mechanic), so reading the live,
    momentary snapshot would make every candidate's target thrash up and
    down every turn as the opponent's own hand count cycles through each
    day. This mirrors exactly how agents.phase3_5.opponent_scaling_detector
    itself samples, for consistency between detection and response."""
    by_day = {}
    for snap in opponent_history:
        if snap.hour >= MIN_SAMPLE_HOUR or snap.day not in by_day:
            by_day[snap.day] = snap
    latest_day = max(by_day)
    latest = by_day[latest_day]
    return len(latest.visible_hand_positions), sum(latest.visible_animal_tile_counts.values())


def b0_fixed(config, obs, opponent_history, current_day):
    """Control -- Submission B's own unmodified fixed response. Included
    here only so every candidate can be dispatched through one interface;
    the function itself is Phase 3.5's, untouched."""
    new_config, detection = _b0_fixed_response(config, None, opponent_history, current_day)
    return new_config, detection


def b1_absolute_proportional(config, obs, opponent_history, current_day, proportion=0.6):
    """B1: target = proportion * opponent's OWN absolute hands/animals count
    (capped at MAX_HANDS_CAP), rather than B0's fixed 5/4. A opponent with
    12 hands gets a stronger response than one with 6, unlike B0."""
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection
    opp_hands, opp_animals = _opponent_hands_animals(opponent_history)
    target_hands = min(MAX_HANDS_CAP, max(config.get("n_hands", 0), round(proportion * opp_hands)))
    target_animals_total = min(8, max(sum((config.get("animals") or {}).values()), round(proportion * opp_animals)))
    new_config = dict(config)
    new_config["n_hands"] = target_hands
    half = target_animals_total // 2
    new_config["animals"] = {"COW": half, "SHEEP": target_animals_total - half}
    return new_config, detection


def b2_relative_gap(config, obs, opponent_history, current_day, close_fraction=0.7, our_baseline_hands=2, our_baseline_animals=2):
    """B2: close a FRACTION of the GAP between our baseline (~2 hands/2
    animals, Planner v1's own isolated-economics default) and the
    opponent's current level -- rather than B1's direct proportion of the
    opponent's absolute count. Differs from B1 when our own baseline
    itself changes (e.g. if Planner v1 had already independently chosen
    more than baseline for economic reasons, B2 respects that; B1 does not
    reference our baseline at all)."""
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection
    opp_hands, opp_animals = _opponent_hands_animals(opponent_history)
    gap_hands = max(0, opp_hands - our_baseline_hands)
    gap_animals = max(0, opp_animals - our_baseline_animals)
    target_hands = min(MAX_HANDS_CAP, max(config.get("n_hands", 0), our_baseline_hands + round(close_fraction * gap_hands)))
    target_animals_total = min(8, max(sum((config.get("animals") or {}).values()),
                                       our_baseline_animals + round(close_fraction * gap_animals)))
    new_config = dict(config)
    new_config["n_hands"] = target_hands
    half = target_animals_total // 2
    new_config["animals"] = {"COW": half, "SHEEP": target_animals_total - half}
    return new_config, detection


def b3_growth_rate_aware(config, obs, opponent_history, current_day, window_days=5, proportion=0.6, acceleration_bonus=0.3):
    """B3: same proportional base as B1, but STRENGTHENED if the opponent's
    hands/animals count is still actively increasing (checked over the
    last `window_days`), on the hypothesis that a still-accelerating
    opponent will be even larger by the time our response takes effect
    than a plateaued one at the same CURRENT count."""
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection
    opp_hands, opp_animals = _opponent_hands_animals(opponent_history)

    by_day = {}
    for snap in opponent_history:
        if snap.hour >= 18 or snap.day not in by_day:
            by_day[snap.day] = snap
    days_sorted = sorted(d for d in by_day if d <= current_day)
    still_growing = False
    if len(days_sorted) >= window_days:
        earlier = by_day[days_sorted[-window_days]]
        earlier_hands = len(earlier.visible_hand_positions)
        earlier_animals = sum(earlier.visible_animal_tile_counts.values())
        still_growing = (opp_hands > earlier_hands) or (opp_animals > earlier_animals)

    effective_proportion = proportion + (acceleration_bonus if still_growing else 0.0)
    target_hands = min(MAX_HANDS_CAP, max(config.get("n_hands", 0), round(effective_proportion * opp_hands)))
    target_animals_total = min(8, max(sum((config.get("animals") or {}).values()), round(effective_proportion * opp_animals)))
    new_config = dict(config)
    new_config["n_hands"] = target_hands
    half = target_animals_total // 2
    new_config["animals"] = {"COW": half, "SHEEP": target_animals_total - half}
    return new_config, detection


def b4_budget_constrained(config, obs, opponent_history, current_day, proportion=0.6):
    """B4: same proportional target as B1, but explicitly capped by
    affordability -- never propose a target whose estimated recurring daily
    hire cost would leave less than MIN_CASH_RESERVE, given our currently
    OBSERVABLE cash (obs, read-only, same object Planner v1 already sees).
    Addresses the Phase 3.5 open question of why 104768097's animal target
    was only half-reached -- makes the constraint EXPLICIT and adaptive
    instead of an implicit, undiagnosed side effect."""
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection
    opp_hands, opp_animals = _opponent_hands_animals(opponent_history)
    cash = _our_cash(obs)

    def _fib_sum(n):
        a, b, total = 1, 1, 0
        for _ in range(n):
            total += a
            a, b = b, a + b
        return total

    desired_hands = min(MAX_HANDS_CAP, round(proportion * opp_hands))
    # reduce the target until its daily re-hire cost fits within our affordable margin
    while desired_hands > config.get("n_hands", 0) and (cash - _fib_sum(desired_hands)) < MIN_CASH_RESERVE:
        desired_hands -= 1
    target_hands = max(config.get("n_hands", 0), desired_hands)

    desired_animals_total = min(8, round(proportion * opp_animals))
    animal_cost_est = desired_animals_total * 450  # rough average of COW($400)/SHEEP($500), a coarse affordability check
    if cash - animal_cost_est < MIN_CASH_RESERVE:
        desired_animals_total = max(0, int((cash - MIN_CASH_RESERVE) // 450))
    target_animals_total = max(sum((config.get("animals") or {}).values()), desired_animals_total)

    new_config = dict(config)
    new_config["n_hands"] = target_hands
    half = target_animals_total // 2
    new_config["animals"] = {"COW": half, "SHEEP": target_animals_total - half}
    return new_config, detection


def b5_hybrid(config, obs, opponent_history, current_day):
    """B5: growth-rate-aware proportional target (B3's logic), THEN capped
    by the same budget constraint as B4. Combines the two mechanisms
    whose individual rationale is strongest, per the brief's instruction
    not to assume the hybrid is best without testing it against B1-B4
    individually."""
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection
    b3_config, _ = b3_growth_rate_aware(config, obs, opponent_history, current_day)
    b4_config, _ = b4_budget_constrained(b3_config, obs, opponent_history, current_day)
    return b4_config, detection


CANDIDATES = {
    "B0_fixed": b0_fixed,
    "B1_absolute_proportional": b1_absolute_proportional,
    "B2_relative_gap": b2_relative_gap,
    "B3_growth_rate_aware": b3_growth_rate_aware,
    "B4_budget_constrained": b4_budget_constrained,
    "B5_hybrid": b5_hybrid,
}
