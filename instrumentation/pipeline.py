"""
Pipeline glue: run one episode -> extract raw layer -> build ledgers ->
build derived metrics -> validate -> assemble the canonical per-episode
telemetry record (brief section 7) and write raw/daily/episode/validation
outputs. This is the only module that touches the filesystem for episode
output; everything upstream is pure in-memory transformation.
"""
import copy
import json
import os

from .collector import run_episode
from .extractor import extract_episode
from .ledger import (
    build_financial_ledger, summarize_financial_ledger,
    build_crop_instances, build_animal_instances,
    build_fertilizer_ledger, build_land_ledger,
)
from .market_telemetry import build_market_price_stats, build_transaction_summary, build_town_telemetry
from .metrics import action_efficiency, crop_level_metrics, animal_level_metrics, daily_summary, episode_summary
from .validation import build_validation_report
from .schema import TELEMETRY_SCHEMA_VERSION


def analyze_replay(replay, meta, experiment_id=None, episode_id=None):
    """Pure function: replay(+meta) in, full telemetry record out. Never mutates `replay`."""
    replay_snapshot = replay  # never written to; extract_episode only reads
    extracted = extract_episode(replay_snapshot, meta)
    configuration = replay.get("configuration", {})
    board_size = int(configuration.get("boardSize", 10))

    market_prices_by_turn = {rec["turn"]: rec["prices"] for rec in extracted["market_history"]}

    per_player = {}
    for player in (0, 1):
        turns = extracted["turns"][player]
        production_events = extracted["production_events"][player]
        land_daily = extracted["land_daily"][player]

        financial_txns = build_financial_ledger(turns, configuration, production_events, market_prices_by_turn)
        starting_money = turns[0]["money_before"] if turns else None
        final_money = extracted["outcome"]["final_money"][player]
        financial_summary = summarize_financial_ledger(financial_txns, starting_money, final_money)

        crop_instances = build_crop_instances(production_events)
        animal_instances = build_animal_instances(production_events)
        fertilizer_ledger = build_fertilizer_ledger(turns, financial_txns, production_events)
        land_ledger = build_land_ledger(turns, financial_txns)

        action_eff = action_efficiency(turns, production_events, board_size)
        crop_metrics = crop_level_metrics(crop_instances, financial_txns)
        animal_metrics = animal_level_metrics(animal_instances, financial_txns)
        market_stats = build_market_price_stats(extracted["market_history"])
        town_telemetry = build_town_telemetry(extracted["town_history"], configuration)
        txn_summary = build_transaction_summary(financial_txns)

        validation = build_validation_report(
            financial_summary, land_ledger, fertilizer_ledger, turns, financial_txns,
            crop_instances, animal_instances,
        )

        daily = daily_summary(player, turns, financial_txns, land_daily, production_events)
        opponent_final_money = extracted["outcome"]["final_money"][1 - player]
        ep_summary = episode_summary(
            player, extracted["outcome"], financial_summary, action_eff, crop_metrics, animal_metrics,
            market_stats, town_telemetry, opponent_final_money,
        )

        per_player[player] = {
            "financial_transactions": financial_txns,
            "financial_summary": financial_summary,
            "crop_instances": crop_instances,
            "animal_instances": animal_instances,
            "fertilizer_ledger": fertilizer_ledger,
            "land_ledger": land_ledger,
            "action_efficiency": action_eff,
            "crop_metrics": crop_metrics,
            "animal_metrics": animal_metrics,
            "market_transaction_summary": txn_summary,
            "town_telemetry": town_telemetry,
            "validation": validation,
            "daily_summary": daily,
            "episode_summary": ep_summary,
        }

    record = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "episode_id": episode_id,
        "meta": meta,
        "outcome": extracted["outcome"],
        "market_price_stats": build_market_price_stats(extracted["market_history"]),
        "market_history": extracted["market_history"],
        "town_history": extracted["town_history"],
        "players": per_player,
    }
    return record, extracted


def run_and_analyze(p0, p1, episode_steps, seed, experiment_id, episode_id, extra_config=None):
    replay, meta = run_episode(p0, p1, episode_steps, seed, extra_config)
    replay_before = copy.deepcopy(replay)
    record, extracted = analyze_replay(replay, meta, experiment_id, episode_id)
    non_mutating = (replay == replay_before)
    record["non_interference_self_check"] = {
        "replay_unmutated_by_pipeline": non_mutating,
    }
    return record, replay, extracted


def write_episode_outputs(out_root, tag, episode_index, record):
    raw_dir = os.path.join(out_root, "raw", tag)
    daily_dir = os.path.join(out_root, "daily", tag)
    episode_dir = os.path.join(out_root, "episode", tag)
    validation_dir = os.path.join(out_root, "validation", tag)
    for d in (raw_dir, daily_dir, episode_dir, validation_dir):
        os.makedirs(d, exist_ok=True)

    fname = f"ep{episode_index:03d}.json"
    with open(os.path.join(raw_dir, fname), "w") as f:
        json.dump(record, f, indent=2, default=str)

    daily_out = {p: record["players"][p]["daily_summary"] for p in (0, 1)}
    with open(os.path.join(daily_dir, fname), "w") as f:
        json.dump(daily_out, f, indent=2, default=str)

    episode_out = {
        "schema_version": record["schema_version"], "meta": record["meta"], "outcome": record["outcome"],
        "players": {p: record["players"][p]["episode_summary"] for p in (0, 1)},
    }
    with open(os.path.join(episode_dir, fname), "w") as f:
        json.dump(episode_out, f, indent=2, default=str)

    validation_out = {p: record["players"][p]["validation"] for p in (0, 1)}
    with open(os.path.join(validation_dir, fname), "w") as f:
        json.dump(validation_out, f, indent=2, default=str)

    return {
        "raw": os.path.join(raw_dir, fname), "daily": os.path.join(daily_dir, fname),
        "episode": os.path.join(episode_dir, fname), "validation": os.path.join(validation_dir, fname),
    }
