"""
Phase 3.2 observable feature extractor. Computes a documented feature
vector from the Phase 3.1 OpponentObservationLogger's history -- PURELY a
function of observations already logged UP TO AND INCLUDING the requested
checkpoint index. Never looks ahead: `extract(history, t, windows)` only
ever reads `history[:t+1]`.

Every feature is either:
  - "observable": read directly from one OpponentObservation snapshot
  - "derived": computed from one or more observable fields (arithmetic)
  - "derived_from_derived_events": counts of the Phase 3.1
    OpponentObservationLogger's own "derived_from_observable"-tagged events
No feature here is "inferred" in the confidence-weighted sense (section 6
of the Phase 3.2 brief) -- state-transition inference with explicit
confidence is a SEPARATE concern, implemented in transition_inference.py.
"""
import math
from dataclasses import dataclass, field

WINDOWS = (1, 6, 12, 24, 48, 72)  # turns; brief section 5's required minimum set


def _entropy(fractions):
    return -sum(f * math.log(f + 1e-12) for f in fractions if f > 0)


def _distribution_features(prefix, counts: dict):
    total = sum(counts.values())
    out = {f"{prefix}_total": total, f"{prefix}_n_types": len(counts)}
    if total == 0:
        out[f"{prefix}_entropy"] = 0.0
        out[f"{prefix}_concentration"] = 0.0
        return out
    fractions = [c / total for c in counts.values()]
    out[f"{prefix}_entropy"] = round(_entropy(fractions), 4)
    out[f"{prefix}_concentration"] = round(max(fractions), 4)  # 1.0 = monoculture, low = diversified
    return out


def extract(history, t, windows=WINDOWS):
    """history: list of OpponentObservation (Phase 3.1). t: index of the
    current checkpoint (inclusive). Returns a flat dict feature vector."""
    if t >= len(history):
        t = len(history) - 1
    if t < 0:
        return {}
    cur = history[t]
    feats = {"turn": cur.turn, "day": cur.day}

    feats["money_now"] = cur.visible_money
    feats["land_quadrants_now"] = cur.visible_land_quadrants
    feats.update(_distribution_features("crop", cur.visible_crop_tile_counts))
    feats.update(_distribution_features("animal", cur.visible_animal_tile_counts))
    feats["productive_tiles_now"] = feats["crop_total"] + feats["animal_total"]
    feats["utilization_now"] = feats["productive_tiles_now"] / max(1, 25 * feats["land_quadrants_now"])

    for w in windows:
        past_idx = max(0, t - w)
        past = history[past_idx]
        span = max(1, cur.turn - past.turn)
        money_delta = cur.visible_money - past.visible_money
        feats[f"money_delta_w{w}"] = round(money_delta, 2)
        feats[f"money_growth_rate_w{w}"] = round(money_delta / span, 4)
        past_prod = sum(past.visible_crop_tile_counts.values()) + sum(past.visible_animal_tile_counts.values())
        feats[f"productive_tiles_delta_w{w}"] = feats["productive_tiles_now"] - past_prod
        feats[f"land_delta_w{w}"] = feats["land_quadrants_now"] - past.visible_land_quadrants

        # derived-event counts within the window (each already tagged "derived_from_observable"
        # by OpponentObservationLogger -- counted here, never re-labeled as more certain than that)
        window_events = [e for snap in history[past_idx:t + 1] for e in snap.derived_events]
        for label in ("LIKELY_BUY_LAND", "LIKELY_HIRE", "LIKELY_PLANT_OR_GROWTH", "LIKELY_BUY_ANIMAL",
                      "LIKELY_ANIMAL_ESCAPE_OR_SOLD_STRUCTURE", "MONEY_CHANGED"):
            feats[f"event_count_{label}_w{w}"] = sum(1 for e in window_events if e["label"] == label)

    return feats


FEATURE_CLASSIFICATION_NOTE = (
    "Every feature returned by extract() is 'observable' (direct obs field) or 'derived' (arithmetic "
    "over observable fields, including counts of Phase 3.1's own derived_from_observable-tagged events). "
    "None is 'inferred' in the confidence-weighted sense -- see agents/phase3/transition_inference.py "
    "for confidence-labeled event inference, a separate concern from feature extraction."
)
