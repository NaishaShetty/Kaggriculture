"""
Phase 40: does Submission I's $/crop-tile/day change under REAL two-producer
competition vs. Phase 39's solo-vs-"pass" isolation measurement?

WHY THIS PHASE EXISTS: Phase 39 (results/phase39/
PHASE39_MATCHED_SCALE_EFFICIENCY_REPORT.md) measured Submission I's
$/crop-tile/day entirely in isolation (vs. "pass") because it needed a
controlled, matched-scale comparison against real Crop Dusta telemetry. But
Phase 21 Step 1 already proved solo-vs-"pass" and real two-producer
economics can differ sharply for a shared-pool crop (MELON there; this
project's own STRAWBERRY-heavy Submission I portfolio is exactly the kind
of shared-pool crop that mechanism could apply to). This phase re-runs
Phase 39's own measurement, unchanged, with a real competitor (Submission G,
then Submission C) standing in for "pass".

MEASUREMENT ONLY. No frozen file touched. Submission I's actual shipped
agent (scripts/phase37/paced_portfolio_agent.py::make_paced_portfolio_agent)
and the two opponents (agents/phase15/adapters/macro_agent.py::
make_macro_agent for Submission G, agents/phase3_8/adapters/
competitive_v3_agent.py::make_competitive_v3_agent for Submission C -- same
factories and kwargs scripts/phase23/vs_submission_g.py already used) are
all imported and run completely unchanged.

REUSED DIRECTLY FROM PHASE 39, NOT REBUILT:
  scripts/phase39/matched_scale_efficiency.py::
    own_daily_snapshots, tile_idle_fraction_by_day (re-exported there from
    scripts/phase10/idle_time_probe.py), summarize_matched_scale, _mean,
    MATCHED_SCALE_MIN_DAY, STEPS, DEV_SEEDS.
The only new code is `extract_own_telemetry_vs`, a thin variant of Phase
39's own `extract_own_telemetry` that takes a real opponent agent instead of
hardcoding "pass" as the second `run_episode` argument -- every extraction
step inside it (daily_summary, tile_idle, own_daily_snapshots, sell_txns,
$/crop-tile/day) is identical to Phase 39's own logic, called the same way.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.phase39.matched_scale_efficiency import (  # noqa: E402
    own_daily_snapshots, tile_idle_fraction_by_day, summarize_matched_scale, _mean,
    MATCHED_SCALE_MIN_DAY, STEPS, DEV_SEEDS,
)
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

OUT_ROOT = "results/phase40"

OPPONENTS = {
    "submission_g": (make_macro_agent, {}),
    "submission_c": (make_competitive_v3_agent, {"trace_path": None, "liquidity_guard_enabled": False}),
}


def extract_own_telemetry_vs(make_opponent, opponent_kwargs, seed, label):
    """Identical extraction to scripts/phase39/matched_scale_efficiency.py::
    extract_own_telemetry, EXCEPT the second run_episode argument is a real
    opponent agent instead of "pass". Every downstream call
    (own_daily_snapshots, tile_idle_fraction_by_day, daily_summary,
    financial_transactions) is the same Phase 39 code, imported unchanged."""
    agent = make_paced_portfolio_agent()
    agent_opp = make_opponent(**opponent_kwargs)
    replay, meta = run_episode(agent, agent_opp, STEPS, seed, None)
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))

    record, _ = analyze_replay(replay, meta, f"phase40_vs_{label}", f"seed{seed}")
    daily_summary = {row["day"]: row for row in record["players"][0]["daily_summary"]}
    tile_idle = {row[0]: row for row in tile_idle_fraction_by_day(replay, board_size)}
    snapshots = {row["day"]: row for row in own_daily_snapshots(replay)}
    sell_txns = [t for t in record["players"][0]["financial_transactions"] if t["type"] == "SELL"]

    daily = []
    for day in sorted(snapshots.keys()):
        snap = snapshots[day]
        ds = daily_summary.get(day, {})
        idle = tile_idle.get(day)
        n_plant, n_idle = (idle[1], idle[2]) if idle else (0, 0)
        day_sells = [t for t in sell_txns if t["day"] == day]
        daily.append({
            "day": day,
            "bank": snap["bank"], "hands_count": snap["hands_count"], "land_quadrants": snap["land_quadrants"],
            "total_crop_tiles": snap["total_crop_tiles"], "crop_tile_counts": snap["crop_tile_counts"],
            "total_animal_count": snap["total_animal_count"], "animal_servicing_rate": snap["animal_servicing_rate"],
            "n_plant_tiles": n_plant, "n_idle_tiles": n_idle,
            "tile_idle_fraction": round(n_idle / n_plant, 4) if n_plant else None,
            "crops_harvested": ds.get("crops_harvested", 0),
            "products_sold": ds.get("products_sold", 0),
            "revenue": ds.get("revenue", 0),
            "n_sell_orders": len(day_sells),
            "mean_sell_batch_size": round(sum(t["quantity"] for t in day_sells) / len(day_sells), 2) if day_sells else None,
            "mean_realized_unit_price": (
                round(sum(t["total"] for t in day_sells) / sum(t["quantity"] for t in day_sells), 2)
                if day_sells and sum(t["quantity"] for t in day_sells) else None
            ),
        })
    action_eff = record["players"][0]["action_efficiency"]
    final_money = record["outcome"]["final_money"][0]
    opponent_final_money = record["outcome"]["final_money"][1]
    return {
        "seed": seed, "final_money": final_money, "opponent_final_money": opponent_final_money,
        "won": final_money > opponent_final_money,
        "idle_action_fraction": action_eff["idle_fraction"],
        "productive_action_rate": action_eff["productive_action_rate"],
        "daily": daily,
    }


def net_dollar_per_tile_day(daily_rows, min_day=MATCHED_SCALE_MIN_DAY):
    """Same $/crop-tile/day definition Phase 39's own report Section 2 used
    (net bank delta / active crop tiles that day), computed here directly
    since Phase 39 only inlined this in its own ad hoc analysis, not as a
    reusable function -- same formula, applied identically."""
    rows = [r for r in daily_rows if r["day"] >= min_day - 1]  # need day (min_day-1) as the delta anchor
    per_tile = []
    per_day_net = []
    for i in range(1, len(rows)):
        if rows[i]["day"] < min_day:
            continue
        net = rows[i]["bank"] - rows[i - 1]["bank"]
        per_day_net.append(net)
        tiles = rows[i]["total_crop_tiles"]
        if tiles > 0:
            per_tile.append(net / tiles)
    return {
        "mean_net_dollar_per_day": _mean(per_day_net),
        "mean_dollar_per_crop_tile_per_day": _mean(per_tile),
    }


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    all_results = {}

    for label, (make_opponent, kwargs) in OPPONENTS.items():
        print(f"\n=== Submission I vs. {label} ({len(DEV_SEEDS)} dev seeds) ===")
        per_seed = {}
        for seed in DEV_SEEDS:
            tel = extract_own_telemetry_vs(make_opponent, kwargs, seed, label)
            per_seed[seed] = tel
            summ = summarize_matched_scale(tel["daily"])
            dpt = net_dollar_per_tile_day(tel["daily"])
            print(f"  seed={seed}: final_money=${tel['final_money']:,.2f} opp=${tel['opponent_final_money']:,.2f} "
                  f"won={tel['won']} | matched-scale(day>={MATCHED_SCALE_MIN_DAY}): "
                  f"crop_tiles={summ['mean_total_crop_tiles']} tile_idle={summ['mean_tile_idle_fraction']} "
                  f"animal_servicing={summ['mean_animal_servicing_rate']} "
                  f"net_$/day={dpt['mean_net_dollar_per_day']} $/tile/day={dpt['mean_dollar_per_crop_tile_per_day']}",
                  flush=True)
        all_results[label] = per_seed
        with open(os.path.join(OUT_ROOT, f"phase40_vs_{label}_telemetry.json"), "w") as f:
            json.dump(per_seed, f, indent=2)

    print("\n=== SUMMARY: matched-scale (day >= {}) $/crop-tile/day, by opponent ===".format(MATCHED_SCALE_MIN_DAY))
    summary = {}
    for label, per_seed in all_results.items():
        seed_summaries = []
        for seed, tel in per_seed.items():
            ms = summarize_matched_scale(tel["daily"])
            dpt = net_dollar_per_tile_day(tel["daily"])
            seed_summaries.append({
                "seed": seed, "final_money": tel["final_money"], "won": tel["won"],
                "mean_total_crop_tiles": ms["mean_total_crop_tiles"],
                "mean_tile_idle_fraction": ms["mean_tile_idle_fraction"],
                "mean_animal_servicing_rate": ms["mean_animal_servicing_rate"],
                "mean_net_dollar_per_day": dpt["mean_net_dollar_per_day"],
                "mean_dollar_per_crop_tile_per_day": dpt["mean_dollar_per_crop_tile_per_day"],
            })
        summary[label] = {
            "per_seed": seed_summaries,
            "wins": sum(1 for s in seed_summaries if s["won"]),
            "mean_tile_idle_fraction": _mean([s["mean_tile_idle_fraction"] for s in seed_summaries]),
            "mean_animal_servicing_rate": _mean([s["mean_animal_servicing_rate"] for s in seed_summaries]),
            "mean_net_dollar_per_day": _mean([s["mean_net_dollar_per_day"] for s in seed_summaries]),
            "mean_dollar_per_crop_tile_per_day": _mean([s["mean_dollar_per_crop_tile_per_day"] for s in seed_summaries]),
        }
        print(f"  vs {label}: wins={summary[label]['wins']}/{len(seed_summaries)} "
              f"tile_idle={summary[label]['mean_tile_idle_fraction']} "
              f"animal_servicing={summary[label]['mean_animal_servicing_rate']} "
              f"net_$/day={summary[label]['mean_net_dollar_per_day']} "
              f"$/tile/day={summary[label]['mean_dollar_per_crop_tile_per_day']}")

    with open(os.path.join(OUT_ROOT, "phase40_comparison_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote telemetry and summary to {OUT_ROOT}/")


if __name__ == "__main__":
    main()
