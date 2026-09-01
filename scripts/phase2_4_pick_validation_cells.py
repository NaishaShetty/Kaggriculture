"""
Selects Phase 2.4 Stage F cells from actual Stage B/C/D/E results
(results/phase2_4/analysis_summary.json) -- not chosen in advance. Mirrors
scripts/phase2_3_pick_validation_cells.py's selection discipline.

Rule: from Stage C's production_x_market grid, pick each production config's
best-performing sell_policy cell BY MEAN FINAL MONEY AMONG CELLS WITH
validation_fail_rate == 0 (never picks a policy whose failures we can't
trust) -- explicitly excludes any batch_* mode from consideration for the
"best" title once Stage D's batch-stranding finding is confirmed, since a
policy that performs well on 8 seeds by fluke ordering of its trigger-day
alignment is not a policy we should validate on more seeds, it's a policy
we should already reject on mechanism grounds (documented in the knowledge
base, not silently applied here).
"""
import json
import os
import re

ROOT = "results/phase2_4"
# Excludes PURE batch mode (cell_id ends "..._batch_<N>d", e.g. "batch_5d", "batch_10d") --
# the confirmed horizon-stranding failure mode (Stage D). Does NOT exclude "threshold_batch"
# (a materially different, safer hybrid mode that only falls back to a batch day when the
# threshold is never hit -- Stage C showed it performs close to or better than passive).
PURE_BATCH_RE = re.compile(r"_batch_\d+d$")


def is_bad_mode(cell_id):
    return bool(PURE_BATCH_RE.search(cell_id))


def main():
    with open(os.path.join(ROOT, "analysis_summary.json")) as f:
        data = json.load(f)
    cells = data["cells"]

    def cell(group, cell_id):
        for v in cells.values():
            if v["group"] == group and v["cell_id"] == cell_id:
                return v
        return None

    validate = []

    def add(group, cell_id):
        c = cell(group, cell_id)
        if c:
            validate.append({"cell_id": c["cell_id"], "kwargs": c["config"], "source_group": group})

    # Stage F production configs: best sell_policy per production config from Stage C,
    # excluding batch-mode cells (mechanism-level flaw, not a fair "best" candidate).
    for prod in ("simple_melon_2h", "integrated_inv_high"):
        candidates = [v for v in cells.values() if v["group"] == "c1_production_x_market"
                      and v["cell_id"].startswith(f"c1_{prod}_")
                      and v["validation_fail_rate"] == 0
                      and not is_bad_mode(v["cell_id"])]
        if candidates:
            best = max(candidates, key=lambda v: v["final_money"]["mean"])
            add("c1_production_x_market", best["cell_id"])
        passive = cell("c1_production_x_market", f"c1_{prod}_passive")
        if passive:
            add("c1_production_x_market", passive["cell_id"])

    # b1: best policy per crop (excluding batch modes for the same reason)
    for crop in ("WHEAT", "MELON"):
        b_candidates = [v for v in cells.values() if v["group"] == "b1_sale_timing_by_crop"
                         and v["cell_id"].startswith(f"b1_{crop}_")
                         and v["validation_fail_rate"] == 0
                         and not is_bad_mode(v["cell_id"])]
        if b_candidates:
            best = max(b_candidates, key=lambda v: v["final_money"]["mean"])
            add("b1_sale_timing_by_crop", best["cell_id"])

    # e1: whichever tick alignment or threshold won
    e_candidates = [v for v in cells.values() if v["group"] == "e1_town_demand_timing"]
    if e_candidates:
        best = max(e_candidates, key=lambda v: v["final_money"]["mean"])
        add("e1_town_demand_timing", best["cell_id"])

    seen = set()
    deduped = []
    for v in validate:
        key = (v["source_group"], v["cell_id"])
        if key not in seen:
            seen.add(key)
            deduped.append(v)

    with open(os.path.join(ROOT, "stage_f_validate_cells.json"), "w") as f:
        json.dump(deduped, f, indent=2)
    print(f"Selected {len(deduped)} cells for Stage F validation:")
    for v in deduped:
        print(f"  {v['source_group']}/{v['cell_id']}: {v['kwargs']}")

    # Head-to-head: the frozen Phase 2.3 winning config under passive selling,
    # vs the same config under its best-found Stage C market-aware policy.
    passive_integrated = cell("c1_production_x_market", "c1_integrated_inv_high_passive")
    best_integrated = None
    integrated_candidates = [v for v in cells.values() if v["group"] == "c1_production_x_market"
                              and v["cell_id"].startswith("c1_integrated_inv_high_")
                              and v["validation_fail_rate"] == 0
                              and not is_bad_mode(v["cell_id"])
                              and v["cell_id"] != "c1_integrated_inv_high_passive"]
    if integrated_candidates:
        best_integrated = max(integrated_candidates, key=lambda v: v["final_money"]["mean"])

    h2h = []
    if passive_integrated:
        h2h.append({"cell_id": passive_integrated["cell_id"], "kwargs": passive_integrated["config"],
                     "source_group": "c1_production_x_market_passive"})
    if best_integrated:
        h2h.append({"cell_id": best_integrated["cell_id"], "kwargs": best_integrated["config"],
                     "source_group": "c1_production_x_market_market_aware"})
    with open(os.path.join(ROOT, "stage_f_headtohead_cells.json"), "w") as f:
        json.dump(h2h, f, indent=2)
    print(f"\nSelected {len(h2h)} cells for head-to-head vs frozen baseline:")
    for v in h2h:
        print(f"  {v['source_group']}/{v['cell_id']}: {v['kwargs']}")


if __name__ == "__main__":
    main()
