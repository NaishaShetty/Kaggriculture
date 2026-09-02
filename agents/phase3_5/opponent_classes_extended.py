"""
Phase 3.5 extension of Phase 3.1's controlled opponent archetype pool
(agents/phase3/opponent_classes.py, left completely UNTOUCHED -- this is a
separate, additive file, not an edit to frozen Phase 3.1 infrastructure).

`heavy_scaler` reuses the EXISTING, already-tested make_agent_23 factory
(no new agent logic, same discipline every prior archetype followed) with
parameter values chosen to reflect the rough MAGNITUDE of real losing
opponents found during Phase 3.5's live-competition forensics
(results/phase3_5/differential_summary.json: real losing-episode opponents
averaged opp_hands_final=5.9, opp_animals_final=6.2, opp_land_final=2.4) --
NOT curve-fit to any single real episode, which the brief explicitly
prohibits. None of the original 7 archetypes combine high sustained labor
AND high sustained animal count the way real losing opponents did.
"""
from agents.phase2_3.common import make_agent as make_agent_23


def heavy_scaler():
    """Sustained high labor + high animal count + moderate land, all
    committed early and held for the rest of the season -- the real-
    competition-motivated archetype neither Phase 3.1's expansion_oriented
    (land+MELON only) nor production_heavy/aggressive_investment (capped at
    4 hands, 2 animals total) represent.

    Deliberately uses WHEAT (not MELON) so this archetype tests the
    LABOR/ANIMAL-SCALING mechanism in isolation from the already-handled
    MELON-market-crash mechanism (Variant D). Parameters were tuned only for
    VIABILITY (does not go bankrupt funding this level of commitment from a
    $3000 starting bank -- an earlier, more aggressive attempt at
    n_hands=10/animals=8 immediately overspent before any crop revenue
    arrived and finished at $0) -- not curve-fit to match any real episode's
    exact win margin. LIMITATION (documented, not hidden): this archetype
    does not fully replicate the WINNING margin real high-scale opponents
    achieved (it still loses to the unmodified Planner v1 control on
    development seeds, ~$16-21k vs ~$29-30k) -- real opponents' apparent
    selling/execution efficiency was not fully reverse-engineered, only
    their resource-commitment MAGNITUDE. Countermeasures validated against
    this archetype should be read as tested against a moderate, non-
    bankrupt reconstruction of the real pattern, not its most extreme case.
    """
    return make_agent_23(crops="WHEAT", n_hands=8, land_quadrants=2, land_buy_day=8,
                          animals={"COW": 4, "SHEEP": 3}, animal_buy_day=6)


OPPONENT_CLASSES_EXTENDED = {
    "heavy_scaler": heavy_scaler,
}
