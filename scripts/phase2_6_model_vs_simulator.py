"""
Phase 2.6 model-vs-simulator validation (brief section 25 / 33.14). Mines
the planner's OWN decision traces (already recorded by every evaluation run)
for every SELECTED decision, and compares the model's predicted
net_expected_value at decision time against the ACTUAL money delta observed
in the simulator over the following day -- a real, not synthetic,
prediction-error analysis.

Usage: python scripts/phase2_6_model_vs_simulator.py --traces-glob "results/phase2_6/planner_v1/traces/development_*.jsonl"
"""
import argparse
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT_PATH = "results/phase2_6/planner_v1/prediction_error_analysis.json"


def analyze_trace(path):
    with open(path) as f:
        records = [json.loads(l) for l in f]
    rows = []
    for i, rec in enumerate(records):
        if not rec["selected_decisions"]:
            continue
        if i + 1 >= len(records):
            continue  # no next-day observation available
        cash_before = rec["state_summary"]["cash"]
        cash_after = records[i + 1]["state_summary"]["cash"]
        actual_cash_delta = cash_after - cash_before
        for sel in rec["selected_decisions"]:
            predicted = sel["net_expected_value"]
            if predicted is None:
                continue
            rows.append({
                "trace_file": os.path.basename(path), "day": rec["day"],
                "decision_kind": sel["candidate"]["kind"], "decision_description": sel["candidate"]["description"],
                "predicted_net_value": predicted, "actual_cash_delta_next_day": round(actual_cash_delta, 2),
                "confidence": sel["expected_value"]["confidence"],
            })
    return rows


def analyze_episode_aggregate(path):
    """A COARSER, less-confounded comparison: sum of every decision's
    predicted net_expected_value across the whole episode vs. the episode's
    actual total profit (final_money - starting_money). Every model
    calibration constant (F1-F19) was itself measured as a FULL 30-day-episode
    effect, not a single-day effect -- so this aggregate comparison is
    actually the fairer test of the model's calibration, while the per-
    decision "next day" comparison above is better read as a sanity check
    for sign/order-of-magnitude only, not a precise attribution."""
    with open(path) as f:
        records = [json.loads(l) for l in f]
    if not records:
        return None
    total_predicted = sum(sel["net_expected_value"] for rec in records for sel in rec["selected_decisions"]
                           if sel["net_expected_value"] is not None)
    starting_cash = records[0]["state_summary"]["cash"]
    ending_cash = records[-1]["state_summary"]["cash"]
    return {"trace_file": os.path.basename(path), "total_predicted_value_of_all_decisions": round(total_predicted, 2),
            "starting_cash": starting_cash, "last_observed_cash": ending_cash,
            "note": "last_observed_cash is from the FINAL planning cycle, not literally turn 720 "
                    "(planning stops once no further day-boundary occurs) -- a lower bound on the "
                    "episode's actual final money, not the exact reward."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces-glob", required=True)
    args = ap.parse_args()

    all_rows = []
    episode_aggregates = []
    for path in sorted(glob.glob(args.traces_glob)):
        all_rows.extend(analyze_trace(path))
        agg = analyze_episode_aggregate(path)
        if agg:
            episode_aggregates.append(agg)

    if not all_rows:
        print("No decisions with a next-day observation found.")
        return

    by_kind = {}
    for r in all_rows:
        by_kind.setdefault(r["decision_kind"], []).append(r)

    summary = {}
    for kind, rows in by_kind.items():
        preds = [r["predicted_net_value"] for r in rows]
        # NOTE: "actual_cash_delta_next_day" is a NOISY, CONFOUNDED proxy --
        # multiple decisions are often selected the same day, and cash also
        # moves from ordinary production/selling unrelated to this specific
        # decision. This is documented as a limitation of the comparison,
        # not hidden -- see the Phase 2.6 report's "known limitations of
        # this validation" note.
        actuals = [r["actual_cash_delta_next_day"] for r in rows]
        errors = [a - p for p, a in zip(preds, actuals)]
        summary[kind] = {
            "n": len(rows), "mean_predicted": round(statistics.mean(preds), 2),
            "mean_actual_next_day_cash_delta": round(statistics.mean(actuals), 2),
            "mean_error": round(statistics.mean(errors), 2),
            "note": "actual_cash_delta_next_day is CONFOUNDED (multiple same-day decisions + ordinary "
                    "production/selling cash flow all mix together) -- directional/order-of-magnitude "
                    "comparison only, not a clean per-decision attribution.",
        }

    out = {"n_total_decisions_analyzed": len(all_rows), "by_decision_kind": summary, "raw_rows": all_rows,
           "episode_aggregate_comparison": episode_aggregates}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, default=str)

    print(f"Analyzed {len(all_rows)} decisions across {len(by_kind)} kinds (per-decision, CONFOUNDED, sign/magnitude only):")
    for kind, s in summary.items():
        print(f"  {kind}: n={s['n']} mean_predicted=${s['mean_predicted']} "
              f"mean_actual_next_day_delta=${s['mean_actual_next_day_cash_delta']} mean_error=${s['mean_error']}")
    print(f"\nEpisode-aggregate comparison ({len(episode_aggregates)} episodes, less confounded):")
    for agg in episode_aggregates:
        print(f"  {agg['trace_file']}: total_predicted=${agg['total_predicted_value_of_all_decisions']} "
              f"starting_cash=${agg['starting_cash']}")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
