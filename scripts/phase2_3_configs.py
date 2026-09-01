"""
Phase 2.3 experiment cell definitions -- ONE integrated campaign (per the
brief's explicit instruction not to treat labor/land/animals/fertilizer/
capital as disconnected sequential phases), organized into stages:

  STAGE A -- broad exploration (single-factor sweeps, small n, vs `pass`)
  STAGE B -- focused resolution (n increased on economically important
             regions identified in Stage A -- see docs/PHASE2_3_REPORT.md
             section "Stage A -> B adaptation" for the reasoning)
  STAGE C -- explicit interaction tests (land x labor, labor x crop,
             animal x crop, animal x fertilizer, capital x horizon,
             inventory/shed bottleneck)
  STAGE D -- validation on independent seed sets + head-to-head vs the
             frozen Wheat Patroller baseline for the strongest configs found

Every cell states: hypothesis, independent variable(s), controls, opponent,
seed set, episode count, and what would count as a success/failure signal --
per the Phase 2.3 brief's requirement that every experiment record this
before being run (not decided post-hoc from the results).

All cells use agents/phase2_3/common.py::make_agent -- one shared
implementation, per-cell only the keyword arguments differ. 720-turn
episodes throughout (the documented full 30-day season) unless noted.
Every seed set is disjoint across stages (broad exploration seeds are never
reused as "validation" seeds) so Stage D's re-runs are genuinely independent
samples, not the same episodes re-labeled.
"""

STEPS = 720

# ---------------------------------------------------------------------------
# STAGE A -- broad exploration. n=6 seeds/cell: matches Phase 2.2's own
# justification for pilot-scale sweeps (deterministic `pass` opponent -> the
# only variance source is weed-spawn/RNG timing, not opponent behavior), used
# here to survey a much larger parameter space before committing a larger
# budget to the regions Stage B focuses on.
# ---------------------------------------------------------------------------
STAGE_A = {
    "a1_labor_sweep": {
        "hypothesis": "Additional hired hands raise harvested units and final money with "
                       "diminishing marginal returns, and the marginal value differs by crop "
                       "(fast one-time WHEAT vs capital-intensive one-time MELON).",
        "iv": "n_hands in {0,1,2,3,4}, crop in {WHEAT, MELON}",
        "dv": "final_money, harvest_units, hire_cost, land utilization, productive_action_rate",
        "controls": "0 extra land, no animals, no fertilizer, plant_delay_day=0",
        "opponent": "pass", "seeds": list(range(100000, 100006)), "n": 6,
        "cells": [
            {"cell_id": f"labor_{crop}_{h}h", "kwargs": {"crops": crop, "n_hands": h}}
            for crop in ("WHEAT", "MELON") for h in (0, 1, 2, 3, 4)
        ],
        "success_criterion": "final_money is non-decreasing in n_hands for at least one crop, "
                              "with a measurably shrinking per-hand increment (diminishing returns).",
    },
    "a2_land_sweep": {
        "hypothesis": "Extra land only raises final money if there is enough labor to work it; "
                       "buying land with 0 hands underperforms the same capital left as cash/seeds.",
        "iv": "land_quadrants in {0,1,2,3} x n_hands in {0,3}", "dv": "final_money, land utilization, land ROI",
        "controls": "MELON only (highest revenue/tile-day crop per Phase 2.2), land_buy_day=0",
        "opponent": "pass", "seeds": list(range(100100, 100106)), "n": 6,
        "cells": [
            {"cell_id": f"land_{q}q_{h}h", "kwargs": {"crops": "MELON", "land_quadrants": q, "n_hands": h}}
            for q in (0, 1, 2, 3) for h in (0, 3)
        ],
        "success_criterion": "land's marginal value (money at land=q minus money at land=q-1) is "
                              "measurably larger at n_hands=3 than at n_hands=0 for at least one q -- "
                              "i.e. land and labor show a positive interaction, not additive-independent value.",
    },
    "a3_animal_lifecycle": {
        "hypothesis": "Each animal type's net economic value (product revenue minus purchase/feed/"
                       "care cost) differs materially by species, and none is profitable without "
                       "enough spare labor to feed/care for it daily.",
        "iv": "animal type in {GOOSE, COW, SHEEP}, n_hands in {1,3}",
        "dv": "final_money, product units, n_escaped, feed cost, break-even horizon",
        "controls": "no crops (feed bought via market, isolates animal economics from crop "
                     "labor competition), 1 animal, animal_buy_day=0, feed/care daily",
        "opponent": "pass", "seeds": list(range(100200, 100206)), "n": 6,
        "cells": [
            {"cell_id": f"animal_{a}_{h}h", "kwargs": {"animals": {a: 1}, "n_hands": h, "feed_source": "market"}}
            for a in ("GOOSE", "COW", "SHEEP") for h in (1, 3)
        ],
        "success_criterion": "at least one animal type is net-profitable (final_money > starting "
                              "money) at n_hands=3 but not at n_hands=1, or vice versa -- a "
                              "labor-dependent profitability threshold.",
    },
    "a4_fertilizer_retest": {
        "hypothesis": "Phase 2.2 found a naive single-farmer fertilizer policy unprofitable "
                       "(fetch-overhead exceeded yield gain). With hands available to delegate "
                       "fertilizing to, and/or free animal-collected fertilizer, this may reverse.",
        "iv": "fertilizer condition in {none, bought+applied, animal-collected+applied}, n_hands in {0,2}",
        "dv": "final_money, harvest_units, fertilizer cost, fertilize_events",
        "controls": "MELON solo crop; animal condition uses 1 GOOSE (animal_buy_day=0)",
        "opponent": "pass", "seeds": list(range(100300, 100306)), "n": 6,
        "cells": [
            {"cell_id": "fert_none_0h", "kwargs": {"crops": "MELON", "n_hands": 0}},
            {"cell_id": "fert_none_2h", "kwargs": {"crops": "MELON", "n_hands": 2}},
            {"cell_id": "fert_buy_0h", "kwargs": {"crops": "MELON", "n_hands": 0, "buy_fertilizer": True, "fertilizer_apply": True}},
            {"cell_id": "fert_buy_2h", "kwargs": {"crops": "MELON", "n_hands": 2, "buy_fertilizer": True, "fertilizer_apply": True}},
            {"cell_id": "fert_animal_2h", "kwargs": {"crops": "MELON", "n_hands": 2, "animals": {"GOOSE": 1},
                                                      "animal_buy_day": 0, "collect_fertilizer": True, "fertilizer_apply": True}},
        ],
        "success_criterion": "fertilizer's effect on final_money at n_hands=2 differs in sign or "
                              "magnitude from Phase 2.2's n_hands=0 finding, for at least one condition.",
    },
}

# ---------------------------------------------------------------------------
# STAGE C -- explicit interaction tests. n=8 seeds/cell (larger than Stage A:
# interaction *differences* are a smaller, noisier signal than main effects).
# Stage B's focused re-sweeps are folded into these cells (each grid already
# increases resolution around Stage A's most informative axis; see the
# report for which Stage A results motivated which Stage C cell).
# ---------------------------------------------------------------------------
STAGE_C = {
    "c1_land_x_labor": {
        "hypothesis": "Land and labor are economic complements for a land-hungry crop: the "
                       "money gained from adding land is larger when labor is also added, and "
                       "vice versa (super-additive, not independent).",
        "iv": "land_quadrants in {0,1,2} x n_hands in {0,2,4}", "dv": "final_money, land utilization",
        "controls": "MELON solo, land_buy_day=0", "opponent": "pass", "seeds": list(range(101000, 101008)), "n": 8,
        "cells": [
            {"cell_id": f"lxl_{q}q_{h}h", "kwargs": {"crops": "MELON", "land_quadrants": q, "n_hands": h}}
            for q in (0, 1, 2) for h in (0, 2, 4)
        ],
        "success_criterion": "interaction term (money[2q,4h] - money[2q,0h]) - (money[0q,4h] - money[0q,0h]) "
                              "is positive and larger in magnitude than either main effect alone.",
    },
    "c2_labor_x_crop": {
        "hypothesis": "The marginal value of a hand differs by crop congestion profile: ongoing, "
                       "watering-heavy STRAWBERRY (Phase 2.2's most congestion-sensitive crop) "
                       "benefits more from an extra hand than fast one-time WHEAT.",
        "iv": "crop in {WHEAT, MELON, STRAWBERRY} x n_hands in {0,2,4}", "dv": "final_money, weed/dig events, watering events",
        "controls": "no land expansion, no animals/fertilizer", "opponent": "pass",
        "seeds": list(range(101100, 101108)), "n": 8,
        "cells": [
            {"cell_id": f"lxc_{crop}_{h}h", "kwargs": {"crops": crop, "n_hands": h}}
            for crop in ("WHEAT", "MELON", "STRAWBERRY") for h in (0, 2, 4)
        ],
        "success_criterion": "STRAWBERRY's proportional final_money gain from 0->4 hands exceeds "
                              "WHEAT's proportional gain over the same range.",
    },
    "c3_animal_x_crop": {
        "hypothesis": "Animals and crops compete for the same limited labor pool; a mixed "
                       "crop+animal farm underperforms the sum of running each in isolation with "
                       "the same total labor, unless the animal's fertilizer materially helps the crop.",
        "iv": "condition in {crop_only, animal_only, crop+animal, crop+animal+fertilizer_use}",
        "dv": "final_money, harvest_units, product_units, fertilize_events",
        "controls": "MELON crop, GOOSE animal (1), n_hands=2 fixed, animal_buy_day=0",
        "opponent": "pass", "seeds": list(range(101200, 101208)), "n": 8,
        "cells": [
            {"cell_id": "axc_crop_only", "kwargs": {"crops": "MELON", "n_hands": 2}},
            {"cell_id": "axc_animal_only", "kwargs": {"animals": {"GOOSE": 1}, "n_hands": 2, "animal_buy_day": 0, "feed_source": "market"}},
            {"cell_id": "axc_crop_animal", "kwargs": {"crops": "MELON", "n_hands": 2, "animals": {"GOOSE": 1}, "animal_buy_day": 0}},
            {"cell_id": "axc_crop_animal_fert", "kwargs": {"crops": "MELON", "n_hands": 2, "animals": {"GOOSE": 1},
                                                            "animal_buy_day": 0, "collect_fertilizer": True, "fertilizer_apply": True}},
        ],
        "success_criterion": "crop+animal final_money is measurably below crop_only_money + "
                              "animal_only_money - starting_money (sub-additive => genuine "
                              "competition), OR crop+animal+fertilizer_use reverses that gap "
                              "(fertilizer makes them complements instead).",
    },
    "c4_animal_x_fertilizer": {
        "hypothesis": "Collecting and applying an animal's free fertilizer to crops raises crop "
                       "revenue enough to be worth the extra COLLECT_FERTILIZER/FERTILIZE actions, "
                       "even when those actions compete with the same hands feeding the animal.",
        "iv": "fertilizer_use in {off, on} x n_hands in {1,3}",
        "dv": "final_money, fertilize_events, harvest_units, fertilizer collected/used/sold",
        "controls": "MELON + 1 GOOSE, animal_buy_day=0", "opponent": "pass",
        "seeds": list(range(101300, 101308)), "n": 8,
        "cells": [
            {"cell_id": f"axf_{onoff}_{h}h",
             "kwargs": {"crops": "MELON", "n_hands": h, "animals": {"GOOSE": 1}, "animal_buy_day": 0,
                        **({"collect_fertilizer": True, "fertilizer_apply": True} if onoff == "on" else {})}}
            for onoff in ("off", "on") for h in (1, 3)
        ],
        "success_criterion": "turning fertilizer_use on changes final_money by a magnitude "
                              "comparable to or larger than the fertilizer-collection/application "
                              "action cost implies, in either direction.",
    },
    "c5_capital_x_horizon": {
        "hypothesis": "Land and animal investments made late in the 30-day season strand "
                       "capital before it can be recovered, mirroring Phase 2.2's crop-timing "
                       "finding (delay=20 zeroed out Melon/Strawberry harvests entirely) -- but "
                       "the loss may be even larger for these because they require several "
                       "additional setup turns/days before any production starts.",
        "iv": "investment_day (in-game DAY, 0-indexed, max 29 for a 720-turn/24-turn-per-day "
              "season -- NOT a turn/step count) in {0,10,20} x investment type in {land, animal}",
        "dv": "final_money, ROI, break-even",
        "controls": "MELON solo crop background, n_hands=2, land_quadrants target=1 (or animals={'GOOSE':1})",
        "opponent": "pass", "seeds": list(range(101400, 101408)), "n": 8,
        "cells": (
            [{"cell_id": f"cxh_land_day{d}", "kwargs": {"crops": "MELON", "n_hands": 2, "land_quadrants": 1, "land_buy_day": d}}
             for d in (0, 10, 20)] +
            [{"cell_id": f"cxh_animal_day{d}", "kwargs": {"crops": "MELON", "n_hands": 2, "animals": {"GOOSE": 1}, "animal_buy_day": d}}
             for d in (0, 10, 20)]
        ),
        "success_criterion": "final_money declines monotonically with investment_day for at "
                              "least one investment type, with day=20's money below day=0's "
                              "money by more than the raw purchase cost (net value destroyed, "
                              "not just delayed).",
    },
    "c6_inventory_bottleneck": {
        "hypothesis": "A high-production, multi-resource farm (many hands, extra land, multiple "
                       "crops+animals) can out-produce the fixed 100-unit shed capacity, causing "
                       "end-of-day overflow discards that a lower-throughput farm never hits.",
        "iv": "throughput condition in {low, high}", "dv": "final_money, inventory overflow (validation discrepancy sign), revenue/harvested-unit",
        "controls": "high = 4 hands, 1 extra land, MELON+STRAWBERRY 50/50, 1 GOOSE+1 COW; "
                     "low = 1 hand, no extra land, MELON solo, no animals",
        "opponent": "pass", "seeds": list(range(101500, 101508)), "n": 8,
        "cells": [
            {"cell_id": "inv_low", "kwargs": {"crops": "MELON", "n_hands": 1}},
            {"cell_id": "inv_high", "kwargs": {"crops": {"MELON": 0.5, "STRAWBERRY": 0.5}, "n_hands": 4,
                                                "land_quadrants": 1, "land_buy_day": 0,
                                                "animals": {"GOOSE": 1, "COW": 1}, "animal_buy_day": 0}},
        ],
        "success_criterion": "the high-throughput condition shows a positive inventory-check "
                              "discrepancy (validation.py's documented overflow signal) on at "
                              "least some episodes where the low-throughput condition shows none.",
    },
}

# ---------------------------------------------------------------------------
# STAGE D -- validation (independent seeds) + head-to-head vs frozen baseline.
# Populated programmatically in the runner from Stage A/C's winning cells
# (see scripts/phase2_3_run_experiments.py::group_validation) so the exact
# set validated is traceable to real Stage A/C results, not chosen in advance.
# ---------------------------------------------------------------------------
STAGE_D_SEEDS = list(range(102000, 102010))  # n=10, independent of every Stage A/C seed range
STAGE_D_H2H_SEEDS = list(range(102100, 102110))  # n=10, independent again
