"""Phase 3.2 experiment configuration -- seed sets and checkpoints, recorded
once here so every script shares the identical, machine-readable design
(brief section 13's requirement)."""

STEPS = 720
CHECKPOINTS = [24, 48, 72, 120, 180, 240, 360, 480, 600]  # turns; brief section 8's required minimum set

# Disjoint from every seed range used in Phase 2.2-3.1 (all of which stay below 600000).
SEED_SETS = {
    "development": list(range(700000, 700004)),   # n=4 -- feature discovery only
    "validation": list(range(701000, 701005)),     # n=5 -- representation selection only
    "held_out": list(range(702000, 702006)),       # n=6 -- final evaluation, used exactly once
}

ARCHETYPES = ["passive", "production_heavy", "market_selling", "expansion_oriented",
              "animal_oriented", "conservative", "aggressive_investment"]
