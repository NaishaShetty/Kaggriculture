"""
Phase 2.6 results summarizer: reads results/phase2_6/planner_v1/results.csv
and produces summary.json (brief section 30's comparison table plus
mean/median/variance/worst-case per seed-set/opponent).
"""
import csv
import json
import os
import statistics

IN_PATH = "results/phase2_6/planner_v1/results.csv"
OUT_PATH = "results/phase2_6/planner_v1/summary.json"


def load():
    rows = []
    with open(IN_PATH, newline="") as f:
        for r in csv.DictReader(f):
            for k in ("planner_money", "opponent_money", "margin", "win"):
                r[k] = float(r[k]) if r[k] not in (None, "") else None
            rows.append(r)
    return rows


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {}
    return {
        "n": len(vals), "mean": round(statistics.mean(vals), 2), "median": round(statistics.median(vals), 2),
        "stdev": round(statistics.pstdev(vals), 2) if len(vals) > 1 else 0.0,
        "min": round(min(vals), 2), "max": round(max(vals), 2),
    }


def main():
    rows = load()
    summary = {}
    for seed_set in ("development", "validation", "held_out"):
        summary[seed_set] = {}
        for opponent in ("wheat_patroller", "phase2_3_integrated", "phase2_4_best"):
            subset = [r for r in rows if r["seed_set"] == seed_set and r["opponent"] == opponent]
            if not subset:
                continue
            summary[seed_set][opponent] = {
                "n_episodes": len(subset),
                "win_rate": round(sum(r["win"] for r in subset) / len(subset), 3),
                "planner_money": stats([r["planner_money"] for r in subset]),
                "opponent_money": stats([r["opponent_money"] for r in subset]),
                "margin": stats([r["margin"] for r in subset]),
                "worst_case_margin": min(r["margin"] for r in subset),
                "validation_pass_rate": sum(1 for r in subset if r["planner_validation"] == "PASS") / len(subset),
                "validation_partial_rate": sum(1 for r in subset if r["planner_validation"] == "PARTIAL") / len(subset),
                "validation_fail_rate": sum(1 for r in subset if r["planner_validation"] == "FAIL") / len(subset),
            }

    # brief section 30's headline table, using the FINAL GATE seed set (held_out)
    table = []
    for opponent in ("wheat_patroller", "phase2_3_integrated", "phase2_4_best"):
        ho = summary.get("held_out", {}).get(opponent)
        if ho:
            table.append({"matchup": f"Planner v1 vs {opponent}", "mean_planner_money": ho["planner_money"]["mean"],
                           "win_rate": ho["win_rate"], "mean_margin": ho["margin"]["mean"],
                           "worst_case_margin": ho["worst_case_margin"]})

    out = {"by_seed_set_and_opponent": summary, "held_out_headline_table": table}
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, default=str)

    print(json.dumps(table, indent=2))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
