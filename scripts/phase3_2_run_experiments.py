"""
Phase 3.2 controlled-opponent experiment runner. Runs the frozen Planner v1
(via the Phase 3.1 control adapter, strategy_mode=NO_SWITCH -- 100% inert,
per the frozen-control rule) as the PROTAGONIST (player 0) against each of
the 7 Phase 3.1 opponent archetypes (player 1), across development/
validation/held_out seeds.

For every episode: records the full competitive trace (already produced by
the control adapter), extracts observable features at every brief-mandated
checkpoint (24..600 turns) from the OpponentObservationLogger's history
(read-only, post-hoc -- the SAME history the protagonist could have built
online, since it is exactly what the control adapter already logs turn by
turn), and derives confidence-labeled transition events for the whole
episode. The ground-truth archetype label is recorded ONLY in the
experiment metadata row, never exposed to any feature/detector logic.

Usage:
    python scripts/phase3_2_run_experiments.py --seed-set development
    python scripts/phase3_2_run_experiments.py --seed-set validation
    python scripts/phase3_2_run_experiments.py --seed-set held_out
"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3.opponent_classes import OPPONENT_CLASSES  # noqa: E402
from agents.phase3.adapters.planner_v1_control import make_control_agent  # noqa: E402
from agents.phase3.feature_extractor import extract, WINDOWS  # noqa: E402
from agents.phase3.transition_inference import infer_events, events_to_records  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from scripts.phase3_2_configs import STEPS, CHECKPOINTS, SEED_SETS, ARCHETYPES  # noqa: E402

OUT_ROOT = "results/phase3_2"


def run_episode_experiment(archetype_name, seed, seed_set_name):
    opponent = OPPONENT_CLASSES[archetype_name]()
    trace_path = os.path.join(OUT_ROOT, "traces", f"planner_{archetype_name}_seed{seed}.jsonl")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    if os.path.exists(trace_path):
        os.remove(trace_path)
    agent = make_control_agent(trace_path=trace_path)  # NO_SWITCH -- inert, control unaffected

    t0 = time.time()
    record, replay, extracted = run_and_analyze(agent, opponent, STEPS, seed,
                                                 f"phase3_2_{archetype_name}", f"seed{seed}")
    agent._planner._tracer.close()

    history = agent._opponent_logger.history
    market_history = agent._market_logger.history

    # feature vectors at every checkpoint (turns) -- purely a function of history[:idx+1]
    features_by_checkpoint = {}
    for cp_turn in CHECKPOINTS:
        idx = next((i for i, s in enumerate(history) if s.turn >= cp_turn), len(history) - 1)
        if idx < len(history):
            features_by_checkpoint[cp_turn] = extract(history, idx, WINDOWS)

    # confidence-labeled transition events, full episode
    all_events = []
    for i in range(1, len(history)):
        all_events.extend(events_to_records(infer_events(history[i - 1], history[i])))

    outcome = record["outcome"]
    protagonist_money, opponent_money = outcome["final_money"]
    meta = {
        "archetype": archetype_name,   # GROUND TRUTH -- metadata only, never fed to any online feature/detector
        "seed": seed, "seed_set": seed_set_name,
        "protagonist_final_money": protagonist_money, "opponent_final_money": opponent_money,
        "margin": round(protagonist_money - opponent_money, 2),
        "win": 1 if outcome["winner"] == 0 else (0 if outcome["winner"] in (0, 1) else None),
        "protagonist_validation": record["players"][0]["validation"]["overall"],
        "n_observations": len(history), "n_transition_events": len(all_events),
        "elapsed_s": round(time.time() - t0, 2),
    }

    # economic detail for economic_analysis (brief section 9) -- direct simulator values, not estimated
    econ = {
        "starting_money": record["players"][0]["financial_summary"]["starting_money"],
        "final_money": protagonist_money,
        "total_revenue": record["players"][0]["financial_summary"]["total_income"],
        "total_cost": record["players"][0]["financial_summary"]["total_expenditure"],
        "opponent_final_money": opponent_money,
    }

    return meta, features_by_checkpoint, all_events, econ, [
        {"turn": s.turn, "day": s.day, "prices": s.prices, "inventory": s.inventory} for s in market_history
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-set", required=True, choices=list(SEED_SETS))
    args = ap.parse_args()

    seeds = SEED_SETS[args.seed_set]
    meta_rows = []
    for archetype in ARCHETYPES:
        for seed in seeds:
            meta, features_by_cp, events, econ, market_hist = run_episode_experiment(archetype, seed, args.seed_set)
            meta_rows.append(meta)

            base = f"{archetype}_seed{seed}"
            with open(os.path.join(OUT_ROOT, "features", f"{base}.json"), "w") as f:
                json.dump({"meta_archetype_GROUND_TRUTH_OFFLINE_ONLY": archetype, "seed": seed,
                           "features_by_checkpoint": features_by_cp}, f, default=str)
            with open(os.path.join(OUT_ROOT, "experiments", f"{base}_events.json"), "w") as f:
                json.dump(events, f, default=str)
            with open(os.path.join(OUT_ROOT, "economic_analysis", f"{base}_econ.json"), "w") as f:
                json.dump(econ, f, default=str)
            with open(os.path.join(OUT_ROOT, "market_analysis", f"{base}_market.json"), "w") as f:
                json.dump(market_hist, f, default=str)

            print(f"  [{archetype}] seed={seed} ({args.seed_set}) protagonist=${meta['protagonist_final_money']} "
                  f"opponent=${meta['opponent_final_money']} win={meta['win']} "
                  f"n_events={meta['n_transition_events']} ({meta['elapsed_s']}s)", flush=True)

    meta_path = os.path.join(OUT_ROOT, "experiments", "episode_metadata.csv")
    file_exists = os.path.exists(meta_path)
    with open(meta_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(meta_rows[0].keys()))
        if not file_exists:
            w.writeheader()
        for r in meta_rows:
            w.writerow(r)
    print(f"\nWrote {len(meta_rows)} rows to {meta_path}")


if __name__ == "__main__":
    main()
