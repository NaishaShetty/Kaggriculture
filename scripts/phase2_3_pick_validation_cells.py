"""
Selects which cells from Stage A/C get re-validated on independent seeds in
Stage D, based on actual results in results/phase2_3/analysis_summary.json --
so the validated set is traceable to real findings, not chosen in advance.

Selection rule (documented, not tuned post-hoc against Stage D's own
results): for each interaction-effect / sweep group, pick the 1-2 cells that
represent the group's headline claim (e.g. the largest-money cell of a labor
sweep, the two endpoints of an interaction). Also emits a head-to-head list:
the single best-performing cell overall (by mean final_money among fully
PASS/PARTIAL-validated cells), to compare against the frozen baseline.
"""
import json
import os

ROOT = "results/phase2_3"


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

    # a1: best labor level per crop (highest mean final_money)
    for crop in ("WHEAT", "MELON"):
        crop_cells = [v for v in cells.values() if v["group"] == "a1_labor_sweep" and v["cell_id"].startswith(f"labor_{crop}_")]
        if crop_cells:
            best = max(crop_cells, key=lambda v: v["final_money"]["mean"] or -1e18)
            add("a1_labor_sweep", best["cell_id"])
        zero = [v for v in crop_cells if v["cell_id"].endswith("_0h")]
        if zero:
            add("a1_labor_sweep", zero[0]["cell_id"])

    # a2: best land x labor combo
    land_cells = [v for v in cells.values() if v["group"] == "a2_land_sweep"]
    if land_cells:
        best = max(land_cells, key=lambda v: v["final_money"]["mean"] or -1e18)
        add("a2_land_sweep", best["cell_id"])

    # a3: best animal type
    animal_cells = [v for v in cells.values() if v["group"] == "a3_animal_lifecycle"]
    if animal_cells:
        best = max(animal_cells, key=lambda v: v["final_money"]["mean"] or -1e18)
        add("a3_animal_lifecycle", best["cell_id"])

    # a4: best fertilizer condition
    fert_cells = [v for v in cells.values() if v["group"] == "a4_fertilizer_retest"]
    if fert_cells:
        best = max(fert_cells, key=lambda v: v["final_money"]["mean"] or -1e18)
        add("a4_fertilizer_retest", best["cell_id"])

    # c1/c2/c3/c4/c5/c6: the highest-money cell in each group
    for group in ("c1_land_x_labor", "c2_labor_x_crop", "c3_animal_x_crop",
                  "c4_animal_x_fertilizer", "c5_capital_x_horizon", "c6_inventory_bottleneck"):
        group_cells = [v for v in cells.values() if v["group"] == group]
        if group_cells:
            best = max(group_cells, key=lambda v: v["final_money"]["mean"] or -1e18)
            add(group, best["cell_id"])

    # dedupe by (group, cell_id)
    seen = set()
    deduped = []
    for v in validate:
        key = (v["source_group"], v["cell_id"])
        if key not in seen:
            seen.add(key)
            deduped.append(v)

    with open(os.path.join(ROOT, "stage_d_validate_cells.json"), "w") as f:
        json.dump(deduped, f, indent=2)
    print(f"Selected {len(deduped)} cells for Stage D validation:")
    for v in deduped:
        print(f"  {v['source_group']}/{v['cell_id']}: {v['kwargs']}")

    # head-to-head: single best cell overall among fully-valid cells
    valid_cells = [v for v in cells.values() if v["validation_fail_rate"] == 0]
    if valid_cells:
        overall_best = max(valid_cells, key=lambda v: v["final_money"]["mean"] or -1e18)
        h2h = [{"cell_id": overall_best["cell_id"], "kwargs": overall_best["config"],
                "source_group": overall_best["group"]}]
        # also include a simple WHEAT-solo-0h baseline for reference if present
        wheat0 = cell("a1_labor_sweep", "labor_WHEAT_0h")
        if wheat0:
            h2h.append({"cell_id": wheat0["cell_id"], "kwargs": wheat0["config"], "source_group": wheat0["group"]})
        with open(os.path.join(ROOT, "stage_d_headtohead_cells.json"), "w") as f:
            json.dump(h2h, f, indent=2)
        print(f"\nSelected {len(h2h)} cells for head-to-head vs frozen baseline:")
        for v in h2h:
            print(f"  {v['source_group']}/{v['cell_id']}: {v['kwargs']}")


if __name__ == "__main__":
    main()
