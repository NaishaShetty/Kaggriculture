"""
Phase 3.5 Candidate: Competitive Labor/Animal Scaling Response.

HYPOTHESIS (H-LIVE-1, H-LIVE-3, H-LIVE-7 from the Phase 3.5 kickoff): Planner
v1's labor (n_hands) and animal targets are calibrated in ISOLATION (Phase
2.3), with no opponent-awareness -- they converge to a fixed ~2 hands/1-2
animals regardless of what the opponent does (confirmed: our_hands_final
and our_animals_final are essentially constant across ALL 18 real
competition episodes analyzed, results/phase3_5/differential_summary.json).
When a real opponent commits to a sustained, much larger resource base
(mean opp_hands_final=5.9, opp_animals_final=6.2 in real losses vs.
1.62/0.12 in real wins), our static commitment cannot generate comparable
revenue, regardless of crop choice or selling policy -- this is a distinct
mechanism from Phase 3.4's self_inflicted_narrow_market_price_crash.

MECHANISM: detect sustained opponent labor/animal scaling via
agents.phase3_5.opponent_scaling_detector (a simple, rule-based, publicly-
observable-only detector -- see that module's docstring for why a trained
classifier was not used here). When active, override this episode's
n_hands and animals TARGETS upward -- reusing the exact same "mutate
Planner v1's own current_config from outside, AFTER it has made its own
unmodified decision" pattern Phase 3.3's Variant D already uses for crops
(agents/phase3_3/adapters/intervention_agent.py), applied here to the
labor/animal lanes instead of the crop lane. Planner v1's own opportunities.py
2-animal cap and its own isolated hiring economics are bypassed the same
way Variant D bypasses its own crop-portfolio logic -- via the tactical
execution layer (agents/phase2_4/common.py) which treats n_hands/animals as
plain targets to build toward, with no cap of its own.

EXPECTED BENEFIT: closes some of the production-scale gap against a
sustained high-labor/high-animal opponent, without touching Planner v1's
own decision logic (frozen, unmodified).
EXPECTED DOWNSIDE: raises recurring hiring cost (fibonacci-scaled per day)
and animal-feeding cost (wheat) regardless of whether the extra labor is
actually productively used -- if the extra hands/animals cannot be kept
fed/watered/harvested effectively (e.g. insufficient tile capacity), this
could be a net loss. This is exactly what the held-out validation must
measure, not assume.
"""
from agents.phase3_5.opponent_scaling_detector import check as check_scaling

RESPONSE_N_HANDS = 5
RESPONSE_ANIMALS = {"COW": 2, "SHEEP": 2}


def competitive_scaling_response(config, state, opponent_history, current_day):
    """TRIGGER: sustained opponent labor/animal scaling detected (see
    agents.phase3_5.opponent_scaling_detector, thresholds hands>=5 or
    animals>=5 sustained >=3 consecutive days).
    INTERVENTION: override n_hands to RESPONSE_N_HANDS and animals to
    RESPONSE_ANIMALS if the current targets are lower, never DOWNGRADING an
    already-higher commitment the planner independently chose.
    """
    detection = check_scaling(opponent_history, current_day)
    if not detection.active:
        return config, detection
    new_config = dict(config)
    if config.get("n_hands", 0) < RESPONSE_N_HANDS:
        new_config["n_hands"] = RESPONSE_N_HANDS
    current_animals = dict(config.get("animals") or {})
    for species, target in RESPONSE_ANIMALS.items():
        if current_animals.get(species, 0) < target:
            current_animals[species] = target
    new_config["animals"] = current_animals
    return new_config, detection
