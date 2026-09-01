"""
Phase 3.3 final statistical analysis: paired comparison (Variant D vs. the
Phase 3.2 control, on identical seeds/opponents) plus the brief's required
comparison table.
"""
import csv
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = "results/phase3_3"


def load_intervention_rows():
    with open(os.path.join(ROOT, "experiments", "intervention_results.csv"), newline="") as f:
        return list(csv.DictReader(f))


def load_control_rows():
    with open("results/phase3_2/experiments/episode_metadata.csv", newline="") as f:
        return list(csv.DictReader(f))


def stats(vals):
    vals = [float(v) for v in vals if v not in (None, "")]
    if not vals:
        return {}
    return {"n": len(vals), "mean": round(statistics.mean(vals), 2), "median": round(statistics.median(vals), 2),
            "stdev": round(statistics.pstdev(vals), 2) if len(vals) > 1 else 0.0}


def effect_size(a, b):
    a, b = [float(x) for x in a], [float(x) for x in b]
    if len(a) < 2 or len(b) < 2:
        return None
    pooled = ((statistics.pstdev(a) ** 2 + statistics.pstdev(b) ** 2) / 2) ** 0.5
    return round((statistics.mean(a) - statistics.mean(b)) / pooled, 3) if pooled else None


def main():
    interventions = load_intervention_rows()
    control = load_control_rows()

    def control_subset(opponent):
        return [r for r in control if r["archetype"] == opponent]

    def intervention_subset(variant, opponent):
        return [r for r in interventions if r["variant"] == variant and r["opponent"] == opponent]

    # --- paired causal comparison: Variant D vs control, SAME seeds, expansion_oriented ---
    d_expansion = intervention_subset("D_production_substitution", "expansion_oriented")
    ctrl_expansion = control_subset("expansion_oriented")
    ctrl_by_seed = {r["seed"]: float(r["protagonist_final_money"]) for r in ctrl_expansion}
    paired = [(float(r["protagonist_final_money"]), ctrl_by_seed[r["seed"]]) for r in d_expansion if r["seed"] in ctrl_by_seed]
    diffs = [d - c for d, c in paired]

    causal = {
        "n_paired_episodes": len(paired),
        "mean_D": round(statistics.mean([p[0] for p in paired]), 2),
        "mean_control": round(statistics.mean([p[1] for p in paired]), 2),
        "mean_diff": round(statistics.mean(diffs), 2),
        "all_positive": all(d > 0 for d in diffs),
        "n_positive": sum(1 for d in diffs if d > 0),
        "effect_size_cohens_d": effect_size([p[0] for p in paired], [p[1] for p in paired]),
        "win_rate_D": round(sum(1 for r in d_expansion if r["win"] == "1") / len(d_expansion), 3),
        "win_rate_control": round(sum(1 for r in ctrl_expansion if r["win"] == "1") / len(ctrl_expansion), 3),
    }

    # --- full comparison table (brief section 17.B) ---
    table = []
    for variant, opponent in [("A_control", "expansion_oriented"), ("B_detection_only", "expansion_oriented"),
                               ("C_melon_avoidance", "expansion_oriented"), ("D_production_substitution", "expansion_oriented"),
                               ("E_market_timing", "expansion_oriented")]:
        if variant == "A_control":
            rows = control_subset("expansion_oriented")
        elif variant == "B_detection_only":
            rows = []  # proven identical to A by construction + regression test; not separately re-run at scale
        else:
            rows = intervention_subset(variant, "expansion_oriented")
        if not rows:
            continue
        moneys = [float(r["protagonist_final_money"]) for r in rows]
        wins = [int(r["win"]) for r in rows if r.get("win") not in (None, "")]
        melon_rev = [float(r.get("melon_revenue", 0) or 0) for r in rows if "melon_revenue" in r]
        table.append({
            "strategy": variant, "n": len(rows), "expansion_win_rate": round(sum(wins) / len(wins), 3) if wins else None,
            "final_bank_mean": round(statistics.mean(moneys), 2),
            "melon_revenue_mean": round(statistics.mean(melon_rev), 2) if melon_rev else None,
        })

    # overall win rate for D across ALL 7 archetypes, all seed sets combined
    d_all = [r for r in interventions if r["variant"] == "D_production_substitution"]
    d_all_wins = [int(r["win"]) for r in d_all if r.get("win") not in (None, "")]
    overall_D = {"n": len(d_all), "overall_win_rate": round(sum(d_all_wins) / len(d_all_wins), 3)}

    out = {"causal_paired_comparison_D_vs_control_expansion_oriented": causal,
           "comparison_table_expansion_oriented": table,
           "variant_D_overall_across_all_archetypes": overall_D}

    with open(os.path.join(ROOT, "tables", "phase3_3_final_analysis.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)

    print("Causal paired comparison (D vs control, expansion_oriented, same seeds):")
    print(json.dumps(causal, indent=2))
    print("\nComparison table (expansion_oriented):")
    for row in table:
        print(row)
    print("\nVariant D overall (all 7 archetypes, all seed sets):", overall_D)


if __name__ == "__main__":
    main()
