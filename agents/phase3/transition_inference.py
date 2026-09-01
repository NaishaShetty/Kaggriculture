"""
Phase 3.2 state-transition inference (brief section 6). Produces richer,
EXPLICITLY CONFIDENCE-LABELED events than Phase 3.1's raw
`derived_from_observable` tags -- but the underlying legality is identical:
the opponent's literal submitted action is NEVER observable (VERIFIED,
Phase 3.1 observability audit), so every event here is `derived` (a change
in public state that can only be caused by a small, known set of actions)
or `inferred` (a plausible but not certain interpretation, given multiple
possible causes) or `unknown` (the evidence doesn't discriminate). The
category `observed` is never used for an OPPONENT action anywhere in this
module -- reserved terminology for information that genuinely is a raw
observation (e.g. a price, a tile's crop type), never for an opponent's
choice, which this game never exposes to the other player.
"""
from dataclasses import dataclass, field
from typing import Optional

from vendor_kaggriculture.kaggriculture import CROPS, ANIMALS


@dataclass
class TransitionEvent:
    event_type: str
    timestamp: int
    evidence: dict
    confidence: str          # "derived" | "inferred" | "unknown" -- NEVER "observed" for an opponent action
    source_features: list = field(default_factory=list)


def infer_events(prev_snap, cur_snap) -> list:
    """prev_snap/cur_snap: consecutive OpponentObservation objects (Phase 3.1).
    Returns a list of TransitionEvent. Multiple events per turn are possible
    (e.g. a land expansion AND a hire in the same window)."""
    events = []
    t = cur_snap.turn

    # --- Land expansion: DERIVED, high certainty -- unlocked_quadrants can
    # ONLY change via BUY_LAND (VERIFIED, kaggriculture.py::_do_buy_land is
    # the sole writer of that field). No other action touches it.
    if cur_snap.visible_land_quadrants > prev_snap.visible_land_quadrants:
        events.append(TransitionEvent(
            event_type="LIKELY_LAND_EXPANSION", timestamp=t, confidence="derived",
            evidence={"land_before": prev_snap.visible_land_quadrants, "land_after": cur_snap.visible_land_quadrants},
            source_features=["visible_land_quadrants"],
        ))

    # --- Hiring: DERIVED, high certainty -- hires_today only increments via HIRE
    # (VERIFIED, kaggriculture.py::_do_hire), and resets to 0 only at day boundaries,
    # so an increase strictly within the same day is unambiguous.
    if cur_snap.day == prev_snap.day and cur_snap.visible_hires_today > prev_snap.visible_hires_today:
        events.append(TransitionEvent(
            event_type="LIKELY_HIRE", timestamp=t, confidence="derived",
            evidence={"hires_today_before": prev_snap.visible_hires_today, "hires_today_after": cur_snap.visible_hires_today},
            source_features=["visible_hires_today"],
        ))

    # --- Crop tile count changes: INFERRED, medium confidence -- an increase is
    # consistent with PLANT, but for an ongoing crop it could also reflect the
    # tile persisting through a harvest (no new PLANT needed); a decrease is
    # consistent with HARVEST (one-time crop clears the tile) or DIG or a WEED
    # conversion (neither a purchase nor a sale). Multiple causes -> "inferred", not "derived".
    for crop, n in cur_snap.visible_crop_tile_counts.items():
        prev_n = prev_snap.visible_crop_tile_counts.get(crop, 0)
        if n > prev_n:
            events.append(TransitionEvent(
                event_type="LIKELY_PLANT", timestamp=t, confidence="inferred",
                evidence={"crop": crop, "tile_count_before": prev_n, "tile_count_after": n,
                          "seed_cost_if_true": CROPS[crop]["seed"] * (n - prev_n)},
                source_features=["visible_crop_tile_counts"],
            ))
        elif n < prev_n:
            events.append(TransitionEvent(
                event_type="LIKELY_HARVEST_OR_WEED_LOSS", timestamp=t, confidence="unknown",
                evidence={"crop": crop, "tile_count_before": prev_n, "tile_count_after": n,
                          "note": "cannot distinguish HARVEST (one-time crop) from DIG or WEED_CONVERSION "
                                  "from tile counts alone -- money-delta cross-check may help (see below)"},
                source_features=["visible_crop_tile_counts"],
            ))

    # --- Animal tile count changes ---
    for animal, n in cur_snap.visible_animal_tile_counts.items():
        prev_n = prev_snap.visible_animal_tile_counts.get(animal, 0)
        if n > prev_n:
            events.append(TransitionEvent(
                event_type="LIKELY_BUY_ANIMAL", timestamp=t, confidence="inferred",
                evidence={"animal": animal, "count_before": prev_n, "count_after": n,
                          "cost_if_true": ANIMALS[animal]["cost"] * (n - prev_n)},
                source_features=["visible_animal_tile_counts"],
            ))
        elif n < prev_n:
            events.append(TransitionEvent(
                event_type="LIKELY_ANIMAL_ESCAPE", timestamp=t, confidence="inferred",
                evidence={"animal": animal, "count_before": prev_n, "count_after": n,
                          "note": "escape (2 consecutive unfed days) is the only DOCUMENTED cause of an "
                                  "animal-tile-count decrease with the structure surviving; a sold/dug "
                                  "structure would also remove it from this count -- cannot fully "
                                  "distinguish without also seeing the tile's own 'kind' field, which "
                                  "this feature (a count) does not carry"},
                source_features=["visible_animal_tile_counts"],
            ))

    # --- Money-delta cross-check: attempt to corroborate a PURCHASE/SALE inference
    # by checking whether the money delta is CONSISTENT with a plausible priced
    # event already inferred above (still "inferred", never upgraded to "derived",
    # since market prices are dynamic and an exact match is not guaranteed even
    # when the event genuinely happened).
    money_delta = cur_snap.visible_money - prev_snap.visible_money
    if money_delta == 0:
        pass
    else:
        candidate_costs = [e.evidence.get("seed_cost_if_true") or e.evidence.get("cost_if_true")
                           for e in events if "seed_cost_if_true" in e.evidence or "cost_if_true" in e.evidence]
        corroborated = any(abs(-c - money_delta) < 1e-6 for c in candidate_costs if c)
        events.append(TransitionEvent(
            event_type="MONEY_CHANGED", timestamp=t, confidence="inferred",
            evidence={"delta": money_delta, "corroborates_a_purchase_event_above": corroborated},
            source_features=["visible_money"],
        ))

    return events


def events_to_records(events):
    return [{"event_type": e.event_type, "timestamp": e.timestamp, "confidence": e.confidence,
             "evidence": e.evidence, "source_features": e.source_features} for e in events]
