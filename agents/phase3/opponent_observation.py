"""
Phase 3.1 opponent observation interface -- a DATA COLLECTION layer only.
No opponent modeling, no strategy inference, no classification happens here
(explicitly deferred to Phase 3.2+). This module only records what is
LEGALLY observable about the opponent, at the moment it becomes observable,
and derives simple state-delta events (a tile changing kind, money moving,
land count increasing) -- never the opponent's literal submitted action,
which is never present in `obs` (see results/phase3_1/observability/
observability_audit.json for the full audit this module implements).

Every field here traces to a row in that audit table with observable=true.
Nothing here reads `obs['private']` for any player other than the field
that legitimately belongs to the calling agent's own private state (never
touched by this module at all -- opponent-only concern).
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OpponentObservation:
    """One snapshot of legally-observable opponent state, plus events
    DERIVED (not directly observed) from the delta against the prior
    snapshot. `derived_events` are explicitly labeled as inferences."""
    turn: int
    day: int
    hour: int
    visible_money: float                     # mechanically observable
    visible_position: tuple                  # mechanically observable (farmer)
    visible_hand_positions: list             # mechanically observable
    visible_land_quadrants: int               # mechanically observable
    visible_hires_today: int                  # mechanically observable
    visible_crop_tile_counts: dict            # mechanically observable (derived by counting tiles, not inferred)
    visible_animal_tile_counts: dict          # mechanically observable (same basis)
    derived_events: list = field(default_factory=list)  # list of dicts, each tagged "derived_from_observable"


def _count_tiles(tiles):
    crop_counts, animal_counts = {}, {}
    for row in tiles:
        for tile in row:
            if isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    crop_counts[tile["crop"]] = crop_counts.get(tile["crop"], 0) + 1
                elif "animal" in tile:
                    animal_counts[tile["animal"]] = animal_counts.get(tile["animal"], 0) + 1
    return crop_counts, animal_counts


class OpponentObservationLogger:
    """Stateful, per-episode logger. Call `.observe(obs)` every turn (or at
    whatever cadence the caller wants); it derives events from the delta
    against the PREVIOUS call, then appends the new OpponentObservation to
    `.history`. Never mutates `obs`."""

    def __init__(self):
        self.history = []
        self._prev = None

    def observe(self, obs) -> OpponentObservation:
        own_player = obs["player"]
        opp_player = 1 - own_player
        opp_farm = obs["farms"][opp_player]
        crop_counts, animal_counts = _count_tiles(opp_farm["tiles"])

        snap = OpponentObservation(
            turn=obs["day"] * 24 + obs.get("hour", 0), day=obs["day"], hour=obs.get("hour", 0),
            visible_money=opp_farm["money"], visible_position=tuple(opp_farm["farmer"]),
            visible_hand_positions=[tuple(h) for h in opp_farm.get("hands", [])],
            visible_land_quadrants=len(opp_farm.get("unlocked_quadrants", ["NW"])),
            visible_hires_today=opp_farm.get("hires_today", 0),
            visible_crop_tile_counts=crop_counts, visible_animal_tile_counts=animal_counts,
        )

        if self._prev is not None:
            snap.derived_events = self._derive_events(self._prev, snap)

        self.history.append(snap)
        self._prev = snap
        return snap

    def _derive_events(self, prev: OpponentObservation, cur: OpponentObservation):
        """Every event here is DERIVED_FROM_OBSERVABLE -- a plausible
        inference from a state delta, never the opponent's literal action.
        E.g. a crop-count increase for a specific crop is consistent with a
        PLANT (or a HARVEST of an ongoing crop not clearing the tile), and
        is logged as such, not asserted as certain."""
        events = []
        if cur.visible_land_quadrants > prev.visible_land_quadrants:
            events.append({"kind": "derived_from_observable", "label": "LIKELY_BUY_LAND",
                            "detail": f"unlocked_quadrants {prev.visible_land_quadrants} -> {cur.visible_land_quadrants}"})
        if cur.visible_hires_today > prev.visible_hires_today:
            events.append({"kind": "derived_from_observable", "label": "LIKELY_HIRE",
                            "detail": f"hires_today {prev.visible_hires_today} -> {cur.visible_hires_today}"})
        for crop, n in cur.visible_crop_tile_counts.items():
            prev_n = prev.visible_crop_tile_counts.get(crop, 0)
            if n > prev_n:
                events.append({"kind": "derived_from_observable", "label": "LIKELY_PLANT_OR_GROWTH",
                                "detail": f"{crop} tile count {prev_n} -> {n}"})
        for animal, n in cur.visible_animal_tile_counts.items():
            prev_n = prev.visible_animal_tile_counts.get(animal, 0)
            if n > prev_n:
                events.append({"kind": "derived_from_observable", "label": "LIKELY_BUY_ANIMAL",
                                "detail": f"{animal} tile count {prev_n} -> {n}"})
            elif n < prev_n:
                events.append({"kind": "derived_from_observable", "label": "LIKELY_ANIMAL_ESCAPE_OR_SOLD_STRUCTURE",
                                "detail": f"{animal} tile count {prev_n} -> {n}"})
        money_delta = cur.visible_money - prev.visible_money
        if money_delta != 0:
            events.append({"kind": "derived_from_observable", "label": "MONEY_CHANGED",
                            "detail": f"delta={money_delta:+.1f} (could be sale, purchase, or a mix -- not separable "
                                      "from money alone)"})
        return events

    def to_records(self):
        return [
            {"turn": s.turn, "day": s.day, "hour": s.hour, "visible_money": s.visible_money,
             "visible_position": s.visible_position, "visible_land_quadrants": s.visible_land_quadrants,
             "visible_hires_today": s.visible_hires_today, "visible_crop_tile_counts": s.visible_crop_tile_counts,
             "visible_animal_tile_counts": s.visible_animal_tile_counts, "derived_events": s.derived_events}
            for s in self.history
        ]
