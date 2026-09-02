"""Phase 3.6 seed sets -- disjoint from every prior phase (2.6: 300000s,
3.2+: 700000s, 3.5: 800000s)."""
from scripts.phase3_2_configs import STEPS

SEED_SETS = {
    "development": [900000, 900001, 900002],
    "validation": [901000, 901001, 901002, 901003],
    "held_out": [902000, 902001, 902002, 902003, 902004],
}
