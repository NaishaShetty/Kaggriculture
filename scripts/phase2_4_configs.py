"""
Phase 2.4 experiment cell definitions. Stage A (market-mechanics discovery)
is handled separately by scripts/phase2_4_stage_a_verify.py (analytical/
verification-style, not a sweep). This file covers Stages B-F: sale timing,
production x market interaction, inventory/shed interaction, town-demand
timing, and the final integrated comparison -- ONE continuing campaign that
builds on (never re-derives) Phase 2.3's frozen production findings.

Every crop/animal/labor/land configuration below is copied verbatim from a
specific Phase 2.3 finding or winning cell (cited in each group's
`production_source`), so Phase 2.4 never re-litigates Phase 2.3's own
questions -- it only asks how SELLING policy interacts with those
already-validated production choices.
"""

STEPS = 720

# ---------------------------------------------------------------------------
# STAGE B -- sale timing, single production config held fixed. n=8/cell,
# matching Phase 2.3's Stage-C sample size (these are directional-effect
# comparisons, not high-precision estimates).
# ---------------------------------------------------------------------------
SELL_POLICIES_B = {
    "passive": {"mode": "passive"},
    "threshold_0.9": {"mode": "threshold", "threshold_frac": 0.9},
    "threshold_1.0": {"mode": "threshold", "threshold_frac": 1.0},
    "threshold_1.1": {"mode": "threshold", "threshold_frac": 1.1},
    "batch_3d": {"mode": "batch", "batch_interval_days": 3},
    "batch_7d": {"mode": "batch", "batch_interval_days": 7},
    "threshold_batch": {"mode": "threshold_batch", "threshold_frac": 1.1, "batch_interval_days": 7},
}

STAGE_B = {
    "b1_sale_timing_by_crop": {
        "hypothesis": "Delaying sales until price recovers toward/above base is profitable for a crop "
                       "with a steep glut-side price curve (MELON: above_func=sq, above_target=3.60 -- "
                       "VERIFIED, MARKET_PARAMS) but not for a crop with a gentle one (WHEAT: "
                       "above_func=log, above_target=0.20) -- the opportunity cost of held capital and "
                       "shed occupancy should dominate for WHEAT, while MELON's much larger price swing "
                       "should reward patience.",
        "iv": "crop in {WHEAT, MELON} x sell_policy (7 levels)", "dv": "final_money, avg realized price, "
              "sold/unsold units, inventory_overflow_flag",
        "controls": "n_hands=2, no land, no animals, no fertilizer -- isolates the selling-policy effect "
                     "from every other Phase 2.3 dimension", "production_source": "n/a (isolated single-crop control)",
        "opponent": "pass", "seeds": list(range(200000, 200008)), "n": 8,
        "cells": [
            {"cell_id": f"b1_{crop}_{name}", "kwargs": {"crops": crop, "n_hands": 2, "sell_policy": policy}}
            for crop in ("WHEAT", "MELON") for name, policy in SELL_POLICIES_B.items()
        ],
        "success_criterion": "at least one non-passive policy beats passive for MELON by a margin "
                              "exceeding seed-to-seed noise, while WHEAT's best non-passive policy does "
                              "not exceed passive by a comparable margin (a genuine crop-dependent effect, "
                              "not a uniform 'holding is always better' result).",
    },
}

# ---------------------------------------------------------------------------
# STAGE C -- production x market interaction. Takes two Phase 2.3-validated
# production configs (the single best simple config and the single best
# integrated config) and re-tests them under every sell policy.
# ---------------------------------------------------------------------------
PRODUCTION_CONFIGS_C = {
    "simple_melon_2h": {  # Phase 2.3 finding F1/a1_labor_sweep's near-optimal simple config
        "crops": "MELON", "n_hands": 2,
    },
    "integrated_inv_high": {  # Phase 2.3 c6_inventory_bottleneck's inv_high cell (F13's winning config)
        "crops": {"MELON": 0.5, "STRAWBERRY": 0.5}, "n_hands": 4, "land_quadrants": 1, "land_buy_day": 0,
        "animals": {"GOOSE": 1, "COW": 1}, "animal_buy_day": 0,
    },
}
SELL_POLICIES_C = {
    "passive": {"mode": "passive"},
    "threshold_1.0": {"mode": "threshold", "threshold_frac": 1.0},
    "threshold_batch": {"mode": "threshold_batch", "threshold_frac": 1.1, "batch_interval_days": 7},
    "batch_5d": {"mode": "batch", "batch_interval_days": 5},
}

STAGE_C = {
    "c1_production_x_market": {
        "hypothesis": "Market-aware selling improves BOTH the simple and the integrated Phase 2.3 "
                       "production configuration over passive selling, but the SIZE of the improvement "
                       "differs -- the integrated config sells more distinct products at once, giving "
                       "market-aware timing more surface area to help (or, alternatively, more chances "
                       "for held inventory to compound into a shed-capacity problem, which would show up "
                       "as a SMALLER or negative improvement instead).",
        "iv": "production_config (2 levels) x sell_policy (4 levels)",
        "dv": "final_money, revenue, avg realized price, inventory_overflow_flag",
        "controls": "identical production config per Phase 2.3's own cited source cell",
        "opponent": "pass", "seeds": list(range(200100, 200108)), "n": 8,
        "cells": [
            {"cell_id": f"c1_{prod}_{pol}", "kwargs": {**PRODUCTION_CONFIGS_C[prod], "sell_policy": policy}}
            for prod in PRODUCTION_CONFIGS_C for pol, policy in SELL_POLICIES_C.items()
        ],
        "success_criterion": "the best sell_policy for each production config is identified, and whether "
                              "market awareness changes which PRODUCTION config wins (i.e. does the "
                              "integrated config's lead over the simple config grow, shrink, or reverse "
                              "once both use their own best selling policy, versus both under passive).",
    },
}

# ---------------------------------------------------------------------------
# STAGE D -- deliberate inventory holding vs shed capacity. Reuses the
# integrated (highest-throughput) production config from Stage C, since
# Phase 2.3's F12 found the shed never bound under passive selling with that
# same config -- the natural next test is whether market-aware HOLDING
# (not just higher production) can bind it instead.
# ---------------------------------------------------------------------------
STAGE_D = {
    "d1_inventory_holding": {
        "hypothesis": "Phase 2.3's F12 ('shed capacity did not bind') was specific to passive "
                       "always-sell selling. A sufficiently aggressive holding policy (high threshold, "
                       "no overflow safety valve) on the same high-throughput production config WILL "
                       "cause real shed overflow and measurable product loss, reversing F12's scope "
                       "(not its correctness under passive selling, which stands).",
        "iv": "sell_policy aggressiveness (3 levels) x overflow_safety (on/off)",
        "dv": "final_money, inventory_overflow_flag rate, revenue lost to overflow (vs the same policy "
              "with safety on, as a same-seed paired comparison)",
        "controls": "integrated_inv_high production config (Phase 2.3's F13 winning config)",
        "opponent": "pass", "seeds": list(range(200200, 200208)), "n": 8,
        "cells": [
            {"cell_id": f"d1_{name}_safety{'on' if safety else 'off'}",
             "kwargs": {**PRODUCTION_CONFIGS_C["integrated_inv_high"],
                        "sell_policy": {**policy, "overflow_safety": safety}}}
            for name, policy in {
                "threshold_1.0": {"mode": "threshold", "threshold_frac": 1.0},
                "threshold_1.3": {"mode": "threshold", "threshold_frac": 1.3},
                "batch_10d": {"mode": "batch", "batch_interval_days": 10},
            }.items()
            for safety in (True, False)
        ],
        "success_criterion": "at least one safety=off cell shows a materially lower final_money and/or "
                              "a nonzero inventory_overflow_flag rate versus its safety=on paired cell, "
                              "on the SAME seeds (a real, not incidental, overflow cost).",
    },
}

# ---------------------------------------------------------------------------
# STAGE E -- town-demand timing. Single crop (MELON, for the same reason as
# Stage B), n_hands=2, no other resources -- isolates the tick-timing effect.
# ---------------------------------------------------------------------------
STAGE_E = {
    "e1_town_demand_timing": {
        "hypothesis": "Selling on the turn immediately AFTER a town-shop consumption tick captures a "
                       "measurably higher realized price than selling immediately BEFORE the next tick, "
                       "since town consumption strictly reduces market inventory (VERIFIED, Phase 2.4 "
                       "Stage A part 2) and therefore nudges price up between ticks.",
        "iv": "sell_policy in {passive, tick_after, tick_before, threshold_1.0}",
        "dv": "final_money, avg realized price, sold units",
        "controls": "MELON solo, n_hands=2, no land/animals/fertilizer",
        "opponent": "pass", "seeds": list(range(200300, 200308)), "n": 8,
        "cells": [
            {"cell_id": "e1_passive", "kwargs": {"crops": "MELON", "n_hands": 2, "sell_policy": {"mode": "passive"}}},
            {"cell_id": "e1_tick_after", "kwargs": {"crops": "MELON", "n_hands": 2,
                                                     "sell_policy": {"mode": "tick_timed", "align": "after"}}},
            {"cell_id": "e1_tick_before", "kwargs": {"crops": "MELON", "n_hands": 2,
                                                      "sell_policy": {"mode": "tick_timed", "align": "before"}}},
            {"cell_id": "e1_threshold", "kwargs": {"crops": "MELON", "n_hands": 2,
                                                    "sell_policy": {"mode": "threshold", "threshold_frac": 1.0}}},
        ],
        "success_criterion": "tick_after's avg realized price exceeds tick_before's on a same-seed "
                              "paired basis for a clear majority of seeds -- a real, exploitable (if "
                              "small) town-demand timing effect, or, if not, an explicit conclusion that "
                              "tick-level timing is not economically exploitable at this granularity.",
    },
}

# ---------------------------------------------------------------------------
# STAGE F -- integrated comparison + independent-seed validation + head-to-head.
# Populated by the runner from Stage C's actual winning cell (see
# scripts/phase2_4_pick_validation_cells.py), not chosen in advance.
# ---------------------------------------------------------------------------
STAGE_F_VALIDATE_SEEDS = list(range(201000, 201010))   # n=10, independent of every Stage A-E seed range
STAGE_F_H2H_SEEDS = list(range(201100, 201110))        # n=10, independent again
