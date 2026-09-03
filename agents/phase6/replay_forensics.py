"""
Phase 6 replay forensics pipeline -- a reusable, additive parser for the
real, uploaded competition episode JSON files under
`COMPETITION RESULTS/SUBMISSION */*.json` (the raw Kaggle replay format:
`replay["steps"][turn][player_index]` = {"action", "observation", "reward",
"status", "info"}).

OBSERVABILITY DISCIPLINE (identical to agents/phase3/opponent_observation.py,
extended, not replaced): every field extracted here is read from EXACTLY
ONE player's own recorded `observation` per episode -- call it the "viewer".
`observation["farms"]` contains BOTH players' PUBLIC farm state (tiles,
money, hands, unlocked_quadrants -- everything a live opponent's board
state legitimately shows); `observation["private"]` contains ONLY the
viewer's own shed/seeds/inventories. By always reading both farms from the
SAME viewer's observation object, this module NEVER touches the other
player's own recorded `action` or `observation["private"]` -- the same
boundary a live agent operates under, applied here to post-hoc analysis of
already-completed public episodes, per this phase's explicit instruction
not to use "opponent shed contents, carried inventory, private seeds, or
private actions" even for offline forensics.

VERIFIED_MECHANIC note: `MARKET_PARAMS`/`market_price` are reused, unchanged,
from vendor_kaggriculture -- this module derives no new game mechanic.
"""
import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS  # noqa: E402

TILES_PER_QUADRANT = 25


def load_replay(path):
    """Loads a raw Kaggle replay JSON. Tries utf-8 first (most files),
    falls back to utf-8 with errors ignored for the small number of files
    with non-ASCII team names that trip a platform-default codec."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(path, encoding="utf-8", errors="replace") as f:
            return json.load(f)


def viewer_index_for_us(replay, our_name="shettynaisha"):
    """Returns (our_index, opponent_index, opponent_name) using ONLY the
    public info.TeamNames metadata."""
    names = replay["info"]["TeamNames"]
    if our_name not in names:
        raise ValueError(f"{our_name!r} not found in TeamNames={names}")
    us = names.index(our_name)
    return us, 1 - us, names[1 - us]


def _count_tiles(tiles):
    crop_counts, animal_counts = {}, {}
    fertilized_count = 0
    cared_count = 0
    fed_count = 0
    for row in tiles:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crop_counts[tile["crop"]] = crop_counts.get(tile["crop"], 0) + 1
                if tile.get("fertilized_until_day", -1) is not None and tile.get("fertilized_until_day", -1) >= 0:
                    fertilized_count += 1
            elif "animal" in tile:
                animal_counts[tile["animal"]] = animal_counts.get(tile["animal"], 0) + 1
                if tile.get("cared_today"):
                    cared_count += 1
                if tile.get("fed_today"):
                    fed_count += 1
    return crop_counts, animal_counts, fertilized_count, cared_count, fed_count


@dataclass
class PlayerDaySnapshot:
    """One end-of-day snapshot for ONE player, built entirely from fields
    that are public (both players) or, for `is_self=True` only, additionally
    from the viewer's own private state. Every field here maps 1:1 to a
    real key in the engine's own observation dict -- nothing is derived
    beyond simple counting (see `_count_tiles`)."""
    day: int
    turn: int
    is_self: bool
    bank: float
    hands_count: int
    land_quadrants: int
    crop_tile_counts: dict
    animal_tile_counts: dict
    fertilized_tile_count: int
    cared_animal_count: int
    fed_animal_count: int
    hires_today: int
    market_inventory: dict
    market_prices: dict
    # self-only (None for opponent snapshots -- never populated from the
    # opponent's own private state, see module docstring)
    shed: dict = None
    seeds: dict = None
    inventories: dict = None
    # self-only, OBSERVED directly from our own submitted action (never the
    # opponent's action -- see module docstring)
    own_action: dict = None


def _snapshot_from_obs(obs, day, turn, is_self, own_action=None):
    farms = obs["farms"]
    idx = obs["player"] if is_self else 1 - obs["player"]
    farm = farms[idx]
    crop_counts, animal_counts, fert_ct, cared_ct, fed_ct = _count_tiles(farm["tiles"])
    market = obs.get("market", {})
    snap = PlayerDaySnapshot(
        day=day, turn=turn, is_self=is_self, bank=farm["money"],
        hands_count=len(farm.get("hands", [])),
        land_quadrants=len(farm.get("unlocked_quadrants", ["NW"])),
        crop_tile_counts=crop_counts, animal_tile_counts=animal_counts,
        fertilized_tile_count=fert_ct, cared_animal_count=cared_ct, fed_animal_count=fed_ct,
        hires_today=farm.get("hires_today", 0),
        market_inventory=dict(market.get("inventory", {})), market_prices=dict(market.get("prices", {})),
    )
    if is_self:
        private = obs.get("private", {})
        snap.shed = dict(private.get("shed", {}))
        snap.seeds = dict(private.get("seeds", {}))
        snap.inventories = list(private.get("inventories", []))  # one dict per hand's carried inventory
        snap.own_action = own_action
    return snap


def extract_episode_timelines(replay, our_name="shettynaisha", sample_hour=23):
    """Returns (episode_meta, self_timeline, opponent_timeline): two lists
    of PlayerDaySnapshot, one per in-game day, sampled at `sample_hour`
    (default 23, the last hour of each day -- the most stable point, after
    that day's hire/plant/harvest/sell actions have all landed and before
    the next day's hand-reset). Reads ONLY steps[t][our_index] -- see
    module docstring for why this is sufficient and sufficient to never
    touch the opponent's own action or private state."""
    us_idx, opp_idx, opp_name = viewer_index_for_us(replay, our_name)
    steps = replay["steps"]
    self_timeline, opp_timeline = [], []
    seen_days = set()
    for t, step in enumerate(steps):
        rec = step[us_idx]
        obs = rec["observation"]
        day, hour = obs["day"], obs.get("hour", 0)
        if hour != sample_hour or day in seen_days:
            continue
        seen_days.add(day)
        turn = day * 24 + hour
        self_timeline.append(_snapshot_from_obs(obs, day, turn, is_self=True, own_action=rec.get("action")))
        opp_timeline.append(_snapshot_from_obs(obs, day, turn, is_self=False))

    # Always include the FINAL recorded step too (episode may end mid-day
    # relative to sample_hour, e.g. a 720-step/30-day episode's last step
    # is day 29 hour 23 -- already covered above for a full episode; this
    # guards short/aborted episodes so the endgame snapshot is never missed).
    last_rec = steps[-1][us_idx]
    last_obs = last_rec["observation"]
    if last_obs["day"] not in seen_days:
        turn = last_obs["day"] * 24 + last_obs.get("hour", 0)
        self_timeline.append(_snapshot_from_obs(last_obs, last_obs["day"], turn, True, last_rec.get("action")))
        opp_timeline.append(_snapshot_from_obs(last_obs, last_obs["day"], turn, False))

    meta = {
        "episode_id": replay["info"].get("EpisodeId"), "seed": replay["info"].get("seed"),
        "team_names": replay["info"]["TeamNames"], "our_index": us_idx, "opponent_index": opp_idx,
        "opponent_name": opp_name, "n_steps": len(steps), "n_days": len(self_timeline),
    }
    return meta, self_timeline, opp_timeline


def infer_sell_events_own(self_timeline):
    """OBSERVED-level market activity for OUR OWN side only: reads our own
    submitted `market` sub-actions directly (legitimately ours). Returns a
    list of {day, op, item, quantity} for every BUY_PRODUCT/SELL/BUY_SEED/
    BUY_ANIMAL/HIRE/BUY_LAND order WE issued. This is exact, not inferred --
    labeled OBSERVED in the report."""
    events = []
    for snap in self_timeline:
        action = snap.own_action or {}
        for order in action.get("market", []) or []:
            if not isinstance(order, list) or not order:
                continue
            op = order[0]
            item = order[1] if len(order) > 1 else None
            qty = order[2] if len(order) > 2 else None
            events.append({"day": snap.day, "op": op, "item": item, "quantity": qty})
    return events


def infer_opponent_money_deltas(opp_timeline):
    """INFERRED-level (not observed) per-day opponent bank delta. A positive
    delta is CONSISTENT WITH a net sale (or could be nothing -- money only
    decreases via purchases/hires, so any day where delta is strongly
    positive and no land/hand/animal/crop-tile increase co-occurs is a
    reasonable, but not certain, signal of market selling activity).
    Explicitly does NOT claim to know quantity, item, or price -- those
    require the opponent's own action, which is never read here."""
    out = []
    prev = None
    for snap in opp_timeline:
        delta = None if prev is None else round(snap.bank - prev.bank, 2)
        out.append({"day": snap.day, "bank": snap.bank, "bank_delta": delta})
        prev = snap
    return out


def to_day_row(snap: PlayerDaySnapshot):
    """Flattens one snapshot into a CSV-friendly dict."""
    row = {
        "day": snap.day, "turn": snap.turn, "is_self": snap.is_self, "bank": snap.bank,
        "hands_count": snap.hands_count, "land_quadrants": snap.land_quadrants,
        "fertilized_tile_count": snap.fertilized_tile_count, "cared_animal_count": snap.cared_animal_count,
        "fed_animal_count": snap.fed_animal_count, "hires_today": snap.hires_today,
        "total_crop_tiles": sum(snap.crop_tile_counts.values()),
        "total_animal_count": sum(snap.animal_tile_counts.values()),
    }
    for crop in CROPS:
        row[f"tiles_{crop}"] = snap.crop_tile_counts.get(crop, 0)
    for animal in ANIMALS:
        row[f"animals_{animal}"] = snap.animal_tile_counts.get(animal, 0)
    if snap.is_self:
        row["shed_total"] = sum(snap.shed.values()) if snap.shed else 0
        row["seeds_total"] = sum(snap.seeds.values()) if snap.seeds else 0
    return row


def velocities(rows, fields, day_field="day"):
    """First-difference (per in-game day) for each field in `fields`, plus
    second difference (acceleration). `rows` must be sorted by day and
    contiguous (gaps produce None for that step, never a divide-by-a-gap
    average that would silently smear the estimate)."""
    out = []
    prev_v = {f: None for f in fields}
    prev_d1 = {f: None for f in fields}
    for i, row in enumerate(rows):
        entry = {day_field: row[day_field]}
        for f in fields:
            v = row.get(f)
            d1 = None
            if i > 0 and rows[i - 1][day_field] == row[day_field] - 1 and prev_v[f] is not None:
                d1 = v - prev_v[f]
            entry[f"d_{f}"] = d1
            d2 = None
            if d1 is not None and prev_d1[f] is not None:
                d2 = d1 - prev_d1[f]
            entry[f"d2_{f}"] = d2
            prev_v[f] = v
            prev_d1[f] = d1
        out.append(entry)
    return out
