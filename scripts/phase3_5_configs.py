"""Phase 3.5 seed sets -- disjoint from every prior phase's seeds (Phase 2.6:
300000s, Phase 3.2+: 700000s), following the same development/validation/
held_out split discipline. STEPS/ARCHETYPES reused from Phase 3.2's config
plus the new heavy_scaler archetype."""
from scripts.phase3_2_configs import STEPS, ARCHETYPES as ARCHETYPES_ORIGINAL

SEED_SETS = {
    "development": [800000, 800001, 800002, 800003],
    "validation": [801000, 801001, 801002, 801003, 801004],
    "held_out": [802000, 802001, 802002, 802003, 802004, 802005],
}

ARCHETYPES = ARCHETYPES_ORIGINAL + ["heavy_scaler"]
