"""
Phase 39: matched-scale execution-efficiency measurement.

QUESTION: at matched land/hand scale (3 quadrants, ~11-12 hands -- the SAME
scale agents/phase21/'s shipped Submission I already runs, and the SAME
scale real gold-tier opponent Crop Dusta (rank #1, ~3030 rating) reaches
$148,520 final money at), does Submission I actually harvest and sell LESS
per day than Crop Dusta does? This is the first direct measurement of raw
execution throughput at matched resource scale -- every prior phase this
session tested portfolio composition, land/hand targets, or purchase
pacing, never this.

MEASUREMENT ONLY. No frozen file touched (agents/phase21/ itself is not
modified; Submission I's actual shipped agent --
scripts/phase37/paced_portfolio_agent.py::make_paced_portfolio_agent,
confirmed by Phase 37 to be exactly what was packaged -- is imported and
run unchanged).

REUSED, UNCHANGED:
  - agents/phase6/replay_forensics.py::load_replay, extract_episode_timelines,
    infer_opponent_money_deltas, _count_tiles (opponent-safe by construction --
    see that module's own docstring).
  - agents/phase2_3/common.py::_owned_tiles, _shed_tiles, _needs_harvest_crop
    (Phase 10's own tile-idle-fraction primitives).
  - scripts/phase10/idle_time_probe.py::tile_idle_fraction_by_day (applied to
    OUR OWN replay, player 0 -- exactly as Phase 10 used it).
  - instrumentation/collector.py::run_episode, instrumentation/pipeline.py::
    analyze_replay (OUR OWN side's full telemetry -- daily_summary,
    action_efficiency, financial_transactions).
  - scripts/phase37/paced_portfolio_agent.py::make_paced_portfolio_agent
    (Submission I's actual shipped agent, unmodified).

OBSERVABILITY DISCIPLINE (same as every phase since 3): Crop Dusta's own
shed/seeds/inventories/submitted actions are NEVER read. Both downloaded
real episodes are parsed with our_name="Jesse Bullard" (Crop Dusta's real
opponent in those games), so Crop Dusta is always the OPPONENT timeline --
extract_episode_timelines only ever reads Crop Dusta's PUBLIC farm state
(tiles, money, hands, unlocked_quadrants) via the viewer's (Jesse Bullard's)
own recorded observation, per that module's documented boundary. The one
new helper added here, `opponent_tile_idle_by_day`, reads tile-level detail
(kind/watered_today/yield_units/planted_day/crop) for Crop Dusta the exact
same way -- from farms[opp_idx] embedded in the viewer's own observation,
which the engine marks PUBLIC (both players' tiles are visible board state,
not private inventory) -- never Crop Dusta's shed/seeds/inventories/action.
Selling activity for Crop Dusta is INFERRED ONLY from bank deltas
(infer_opponent_money_deltas) -- never quantity/item/price, which would
require reading their own action.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import (  # noqa: E402
    load_replay, extract_episode_timelines, infer_opponent_money_deltas, _count_tiles,
)
from agents.phase2_3.common import _owned_tiles, _shed_tiles, _needs_harvest_crop  # noqa: E402
from scripts.phase10.idle_time_probe import tile_idle_fraction_by_day  # noqa: E402
from scripts.phase37.paced_portfolio_agent import make_paced_portfolio_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
TOTAL_DAYS = 30
DEV_SEEDS = [700000, 700001, 700002, 700003]
REAL_REPLAYS = [
    "results/phase34/raw_replays/105373474.json",
    "results/phase34/raw_replays/105341441.json",
]
CROP_DUSTA_NAME = "Crop Dusta"
OUT_ROOT = "results/phase39"


# ---------------------------------------------------------------------------
# Crop Dusta (real, public-only) telemetry
# ---------------------------------------------------------------------------

def opponent_tile_idle_by_day(replay, us_idx, opp_idx, board_size, sample_hour=23):
    """Same idle definition as scripts/phase10/idle_time_probe.py::
    tile_idle_fraction_by_day (unwatered-or-unharvested standing crop at
    end of day), applied to Crop Dusta's PUBLIC tiles array
    (farms[opp_idx]["tiles"], embedded in the viewer's -- Jesse Bullard's --
    own recorded observation). Never reads Crop Dusta's own action or
    private state."""
    out = []
    seen_days = set()
    shed_tiles = set(_shed_tiles(board_size))
    for step in replay["steps"]:
        obs = step[us_idx]["observation"]
        day, hour = obs["day"], obs.get("hour", 0)
        if hour != sample_hour or day in seen_days:
            continue
        seen_days.add(day)
        tiles = obs["farms"][opp_idx]["tiles"]
        owned = _owned_tiles(tiles, board_size)
        n_plant, n_idle = 0, 0
        for (x, y) in owned:
            if (x, y) in shed_tiles:
                continue
            tile = tiles[y][x]
            if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                continue
            n_plant += 1
            needs_water = not tile.get("watered_today", False)
            needs_harvest = _needs_harvest_crop(tile, tile["crop"], day)
            if needs_water or needs_harvest:
                n_idle += 1
        out.append({
            "day": day, "n_plant_tiles": n_plant, "n_idle_tiles": n_idle,
            "idle_fraction": round(n_idle / n_plant, 4) if n_plant else None,
        })
    return out


def extract_crop_dusta_telemetry(path):
    replay = load_replay(path)
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))
    names = replay["info"]["TeamNames"]
    viewer_name = next(n for n in names if n != CROP_DUSTA_NAME)
    meta, self_timeline, opp_timeline = extract_episode_timelines(replay, our_name=viewer_name)
    us_idx, opp_idx = meta["our_index"], meta["opponent_index"]
    assert meta["opponent_name"] == CROP_DUSTA_NAME, meta["opponent_name"]

    money_deltas = infer_opponent_money_deltas(opp_timeline)
    tile_idle = opponent_tile_idle_by_day(replay, us_idx, opp_idx, board_size)

    daily = []
    for snap, delta_row, idle_row in zip(opp_timeline, money_deltas, tile_idle):
        assert snap.day == delta_row["day"] == idle_row["day"]
        daily.append({
            "day": snap.day,
            "bank": snap.bank,
            "bank_delta": delta_row["bank_delta"],
            "hands_count": snap.hands_count,
            "land_quadrants": snap.land_quadrants,
            "total_crop_tiles": sum(snap.crop_tile_counts.values()),
            "crop_tile_counts": snap.crop_tile_counts,
            "total_animal_count": sum(snap.animal_tile_counts.values()),
            "cared_animal_count": snap.cared_animal_count,
            "fed_animal_count": snap.fed_animal_count,
            "animal_servicing_rate": (
                round(min(snap.cared_animal_count, snap.fed_animal_count) / sum(snap.animal_tile_counts.values()), 4)
                if sum(snap.animal_tile_counts.values()) else None
            ),
            "n_plant_tiles": idle_row["n_plant_tiles"],
            "n_idle_tiles": idle_row["n_idle_tiles"],
            "tile_idle_fraction": idle_row["idle_fraction"],
        })
    return {
        "episode_id": meta["episode_id"], "seed": meta["seed"], "final_bank_last_day": daily[-1]["bank"],
        "daily": daily,
    }


# ---------------------------------------------------------------------------
# Submission I (ours, full access to own actions) telemetry
# ---------------------------------------------------------------------------

def own_daily_snapshots(replay, sample_hour=23):
    """Mirrors agents/phase6/replay_forensics.py::_snapshot_from_obs's
    public-field counting (_count_tiles, reused unchanged) applied to OUR
    OWN side (player 0) -- full access is legitimate here, it's our own
    agent's data, not the opponent's."""
    out = []
    seen_days = set()
    for step in replay["steps"]:
        obs = step[0]["observation"]
        day, hour = obs["day"], obs.get("hour", 0)
        if hour != sample_hour or day in seen_days:
            continue
        seen_days.add(day)
        farm = obs["farms"][0]
        crop_counts, animal_counts, fert_ct, cared_ct, fed_ct = _count_tiles(farm["tiles"])
        out.append({
            "day": day, "bank": farm["money"], "hands_count": len(farm.get("hands", [])),
            "land_quadrants": len(farm.get("unlocked_quadrants", ["NW"])),
            "total_crop_tiles": sum(crop_counts.values()), "crop_tile_counts": crop_counts,
            "total_animal_count": sum(animal_counts.values()),
            "cared_animal_count": cared_ct, "fed_animal_count": fed_ct,
            "animal_servicing_rate": (
                round(min(cared_ct, fed_ct) / sum(animal_counts.values()), 4) if sum(animal_counts.values()) else None
            ),
        })
    return out


def extract_own_telemetry(seed):
    agent = make_paced_portfolio_agent()
    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    board_size = int(replay.get("configuration", {}).get("boardSize", 10))

    record, _ = analyze_replay(replay, meta, "phase39_matched_scale", f"seed{seed}")
    daily_summary = {row["day"]: row for row in record["players"][0]["daily_summary"]}
    tile_idle = {row[0]: row for row in tile_idle_fraction_by_day(replay, board_size)}  # (day, n_plant, n_idle)
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
    return {
        "seed": seed, "final_money": final_money,
        "idle_action_fraction": action_eff["idle_fraction"],
        "productive_action_rate": action_eff["productive_action_rate"],
        "daily": daily,
    }


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

MATCHED_SCALE_MIN_DAY = 11  # land reaches 3 quadrants by day 11 (agents/phase21/portfolio.py _LAND_RUNGS)


def _mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 4) if values else None


def summarize_matched_scale(daily_rows, min_day=MATCHED_SCALE_MIN_DAY):
    rows = [r for r in daily_rows if r["day"] >= min_day]
    return {
        "n_days": len(rows),
        "mean_total_crop_tiles": _mean([r["total_crop_tiles"] for r in rows]),
        "mean_tile_idle_fraction": _mean([r["tile_idle_fraction"] for r in rows]),
        "mean_animal_servicing_rate": _mean([r["animal_servicing_rate"] for r in rows]),
        "mean_hands_count": _mean([r["hands_count"] for r in rows]),
        "mean_land_quadrants": _mean([r["land_quadrants"] for r in rows]),
    }


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)

    print("=== Crop Dusta (real, public-only) telemetry ===")
    crop_dusta = {}
    for path in REAL_REPLAYS:
        tel = extract_crop_dusta_telemetry(path)
        crop_dusta[tel["episode_id"]] = tel
        summ = summarize_matched_scale(tel["daily"])
        print(f"  episode={tel['episode_id']} seed={tel['seed']} matched-scale(day>={MATCHED_SCALE_MIN_DAY}): "
              f"crop_tiles={summ['mean_total_crop_tiles']} tile_idle={summ['mean_tile_idle_fraction']} "
              f"animal_servicing={summ['mean_animal_servicing_rate']} hands={summ['mean_hands_count']} "
              f"land={summ['mean_land_quadrants']}", flush=True)
    with open(os.path.join(OUT_ROOT, "phase39_crop_dusta_real_telemetry.json"), "w") as f:
        json.dump(crop_dusta, f, indent=2)

    print("\n=== Submission I (isolated vs. pass, dev seeds) telemetry ===")
    ours = {}
    for seed in DEV_SEEDS:
        tel = extract_own_telemetry(seed)
        ours[seed] = tel
        summ = summarize_matched_scale(tel["daily"])
        print(f"  seed={seed} final_money=${tel['final_money']} matched-scale(day>={MATCHED_SCALE_MIN_DAY}): "
              f"crop_tiles={summ['mean_total_crop_tiles']} tile_idle={summ['mean_tile_idle_fraction']} "
              f"animal_servicing={summ['mean_animal_servicing_rate']} hands={summ['mean_hands_count']} "
              f"land={summ['mean_land_quadrants']}", flush=True)
    with open(os.path.join(OUT_ROOT, "phase39_submission_i_telemetry.json"), "w") as f:
        json.dump(ours, f, indent=2)

    print("\n=== SUMMARY: matched-scale (day >= {}) comparison ===".format(MATCHED_SCALE_MIN_DAY))
    cd_summaries = [summarize_matched_scale(tel["daily"]) for tel in crop_dusta.values()]
    our_summaries = [summarize_matched_scale(tel["daily"]) for tel in ours.values()]

    comparison = {
        "crop_dusta": {
            "mean_total_crop_tiles": _mean([s["mean_total_crop_tiles"] for s in cd_summaries]),
            "mean_tile_idle_fraction": _mean([s["mean_tile_idle_fraction"] for s in cd_summaries]),
            "mean_animal_servicing_rate": _mean([s["mean_animal_servicing_rate"] for s in cd_summaries]),
        },
        "submission_i": {
            "mean_total_crop_tiles": _mean([s["mean_total_crop_tiles"] for s in our_summaries]),
            "mean_tile_idle_fraction": _mean([s["mean_tile_idle_fraction"] for s in our_summaries]),
            "mean_animal_servicing_rate": _mean([s["mean_animal_servicing_rate"] for s in our_summaries]),
        },
    }
    # Sell throughput: Crop Dusta side is INFERRED-only (mean positive bank-delta
    # day count as a proxy), ours is OBSERVED (mean products_sold/day).
    cd_positive_delta_days = []
    for tel in crop_dusta.values():
        rows = [r for r in tel["daily"] if r["day"] >= MATCHED_SCALE_MIN_DAY and r["bank_delta"] is not None]
        cd_positive_delta_days.append(sum(1 for r in rows if r["bank_delta"] > 0) / len(rows) if rows else None)
    comparison["crop_dusta"]["mean_fraction_days_with_positive_bank_delta_INFERRED"] = _mean(cd_positive_delta_days)

    our_products_sold = []
    for tel in ours.values():
        rows = [r for r in tel["daily"] if r["day"] >= MATCHED_SCALE_MIN_DAY]
        our_products_sold.append(_mean([r["products_sold"] for r in rows]))
    comparison["submission_i"]["mean_products_sold_per_day_OBSERVED"] = _mean(our_products_sold)
    our_harvested = []
    for tel in ours.values():
        rows = [r for r in tel["daily"] if r["day"] >= MATCHED_SCALE_MIN_DAY]
        our_harvested.append(_mean([r["crops_harvested"] for r in rows]))
    comparison["submission_i"]["mean_crops_harvested_per_day_OBSERVED"] = _mean(our_harvested)

    print(json.dumps(comparison, indent=2))
    with open(os.path.join(OUT_ROOT, "phase39_comparison_summary.json"), "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"\nWrote telemetry and summary to {OUT_ROOT}/")


if __name__ == "__main__":
    main()
