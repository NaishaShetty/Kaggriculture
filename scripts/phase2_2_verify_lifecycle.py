"""
Phase 2.2 section 10: empirically verify each crop's lifecycle mechanics
against the documented constants, using the Phase 2.1 instrumentation
pipeline (read-only, non-invasive) over a real episode -- not just reading
source. Writes results/phase2_2/lifecycle_verification.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vendor_kaggriculture.kaggriculture import CROPS  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

CROP_AGENTS = {
    "WHEAT": "agents/phase2_2/wheat_only.py",
    "CARROT": "agents/phase2_2/carrot_only.py",
    "TOMATO": "agents/phase2_2/tomato_only.py",
    "STRAWBERRY": "agents/phase2_2/strawberry_only.py",
    "MELON": "agents/phase2_2/melon_only.py",
}
STEPS = 500  # ~20.8 days -- covers even melon's max_yield_day=12 plus decay window
SEED = 42


def verify_crop(crop, agent_path):
    record, replay, extracted = run_and_analyze(agent_path, "pass", STEPS, SEED, "lifecycle_verify", f"{crop}_ep0")
    events = extracted["production_events"][0]
    plant_events = sorted((e for e in events if e["event"] == "PLANT"), key=lambda e: e["turn"])
    if not plant_events:
        return {"crop": crop, "error": "no PLANT event observed in the episode"}
    first = plant_events[0]
    x, y, planted_turn, planted_day = first["x"], first["y"], first["turn"], first["day"]

    def close_turn(evs_after_plant):
        for e in evs_after_plant:
            if e["event"] in ("HARVEST",) and not e.get("ongoing", True):
                return e["turn"]
            if e["event"] in ("DIG", "WEED_CONVERSION"):
                return e["turn"]
        return None

    instance_events = [e for e in events if e["x"] == x and e["y"] == y and e["turn"] >= planted_turn]
    end_turn = close_turn(instance_events[1:]) or (STEPS - 1)
    instance_events = [e for e in instance_events if e["turn"] <= end_turn]

    waters = [e for e in instance_events if e["event"] == "WATER"]
    growths = [e for e in instance_events if e["event"] == "GROWTH"]
    harvests = [e for e in instance_events if e["event"] == "HARVEST"]
    fertilizes = [e for e in instance_events if e["event"] == "FERTILIZE"]
    weeded = [e for e in instance_events if e["event"] == "WEED_CONVERSION"]
    dug = [e for e in instance_events if e["event"] == "DIG"]

    documented = dict(CROPS[crop])
    verified = {
        "planted_day": planted_day,
        "first_watering_day": waters[0]["day"] if waters else None,
        "first_growth_day": growths[0]["day"] if growths else None,
        "first_growth_age_days": (growths[0]["day"] - planted_day) if growths else None,
        "first_harvest_day": harvests[0]["day"] if harvests else None,
        "first_harvest_age_days": (harvests[0]["day"] - planted_day) if harvests else None,
        "n_harvest_events_this_instance": len(harvests),
        "harvest_days": [h["day"] for h in harvests],
        "max_single_harvest_units": max((h["units"] for h in harvests), default=None),
        "weed_converted": bool(weeded),
        "dug": bool(dug),
        "watering_events_before_close": len(waters),
        "growth_events_before_close": len(growths),
        "fertilize_events_before_close": len(fertilizes),
        "ongoing_observed": len(harvests) > 1 or (harvests and harvests[0].get("ongoing") is True),
    }
    matches = {
        "first_yield_day_matches": verified["first_harvest_age_days"] is not None and
            verified["first_harvest_age_days"] >= documented["first_yield_day"],
        "ongoing_flag_matches": verified["ongoing_observed"] == documented["ongoing"] if harvests else None,
    }
    return {
        "crop": crop, "documented": documented, "verified": verified, "checks": matches,
        "instance_position": [x, y], "n_total_instances_observed": len(plant_events),
    }


def main():
    results = {c: verify_crop(c, p) for c, p in CROP_AGENTS.items()}
    os.makedirs("results/phase2_2", exist_ok=True)
    with open("results/phase2_2/lifecycle_verification.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    for c, r in results.items():
        print(f"\n=== {c} ===")
        print(json.dumps(r, indent=2, default=str))


if __name__ == "__main__":
    main()
