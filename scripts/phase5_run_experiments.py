"""
Phase 5 experiment runner: ablations A/B (Submission C, i.e. C + existing
frozen Variant D), C (+ market-impact-aware replacement), D (+ naive
current-price diagnostic), E (+ Phase 3.3's simple diversified
substitution) -- against the expansion_oriented archetype across the exact
seed sets that established Variant D (development/validation/held_out,
same as results/phase3_3/experiments/intervention_results.csv), plus a
non-target inertness check across the other Phase 3.2 archetypes.

Nothing here modifies main.py or any frozen file. Results written to
results/phase5/.
"""
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402
from agents.phase3_3.interventions import variant_c_melon_avoidance, variant_d_production_substitution  # noqa: E402
from agents.phase5.market_impact_substitution import make_market_impact_substitution, make_naive_price_substitution  # noqa: E402
from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_2_configs import STEPS  # noqa: E402

OUT_ROOT = "results/phase5"
TARGET_SEEDS = {
    "development": [700000, 700001, 700002, 700003],
    "validation": [701000, 701001, 701002, 701003, 701004],
    "held_out": [702000, 702001, 702002, 702003, 702004, 702005],
}
NON_TARGET_ARCHETYPES = ["passive", "production_heavy", "market_selling", "animal_oriented",
                          "conservative", "aggressive_investment"]
NON_TARGET_SEEDS = [700000, 701000]

CANDIDATES = {
    "AB_submission_C": lambda trace: variant_d_production_substitution,
    "C_market_impact": lambda trace: make_market_impact_substitution(trace_sink=trace),
    "D_naive_price": lambda trace: make_naive_price_substitution(trace_sink=trace),
    "E_diversified": lambda trace: variant_c_melon_avoidance,
}


def run_one(label, fn_factory, opponent_name, seed, seed_set_name, save_trace=False):
    opponent = OPPONENT_CLASSES[opponent_name]()
    trace = [] if save_trace else None
    fn = fn_factory(trace)
    agent = make_competitive_v3_agent(market_response_fn=fn)

    t0 = time.time()
    record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                 f"phase5_{label}_{opponent_name}", f"seed{seed}")
    protagonist_money, opponent_money = record["outcome"]["final_money"]

    melon_metrics = record["players"][0]["crop_metrics"].get("MELON", {})
    fin = record["players"][0]["financial_summary"]

    row = {
        "candidate": label, "opponent": opponent_name, "seed": seed, "seed_set": seed_set_name,
        "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
        "margin": round(protagonist_money - opponent_money, 2),
        "win": 1 if protagonist_money > opponent_money else (0 if protagonist_money < opponent_money else None),
        "total_revenue": fin["total_income"], "total_cost": fin["total_expenditure"],
        "melon_harvested": melon_metrics.get("total_harvested_units", 0),
        "market_activations": agent._state_ref["market_activations"],
        "scaling_activations": agent._state_ref["scaling_activations"],
        "animal_response_activations": agent._state_ref["animal_response_activations"],
        "elapsed_s": round(time.time() - t0, 2),
    }
    if save_trace and trace:
        trace_path = os.path.join(OUT_ROOT, "traces", f"{label}_{opponent_name}_seed{seed}.json")
        os.makedirs(os.path.dirname(trace_path), exist_ok=True)
        with open(trace_path, "w") as f:
            json.dump(trace, f, indent=2, default=str)
    return row


def main():
    rows = []

    print("=== TARGET (expansion_oriented, same seeds that established Variant D) ===")
    for seed_set_name, seeds in TARGET_SEEDS.items():
        for seed in seeds:
            for label, factory in CANDIDATES.items():
                row = run_one(label, factory, "expansion_oriented", seed, seed_set_name, save_trace=True)
                rows.append(row)
                print(f"  [{label}/expansion_oriented] seed={seed} ({seed_set_name}) "
                      f"protagonist=${row['protagonist_final_money']} opponent=${row['opponent_final_money']} "
                      f"win={row['win']} ({row['elapsed_s']}s)", flush=True)

    print("\n=== NON-TARGET INERTNESS CHECK ===")
    for opponent_name in NON_TARGET_ARCHETYPES:
        for seed in NON_TARGET_SEEDS:
            for label in ["AB_submission_C", "C_market_impact"]:
                row = run_one(label, CANDIDATES[label], opponent_name, seed, "non_target", save_trace=False)
                rows.append(row)
                print(f"  [{label}/{opponent_name}] seed={seed} "
                      f"protagonist=${row['protagonist_final_money']} market_activations={row['market_activations']} "
                      f"({row['elapsed_s']}s)", flush=True)

    out_csv = os.path.join(OUT_ROOT, "phase5_results.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows to {out_csv}")


if __name__ == "__main__":
    main()
