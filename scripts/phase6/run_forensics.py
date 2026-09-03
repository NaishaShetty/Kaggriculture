"""
Phase 6 forensics runner: parses selected real competition episodes and
writes per-day CSVs (self + opponent), a velocity/acceleration CSV, and an
own-side market-event log, under results/phase6/.

Usage: python scripts/phase6/run_forensics.py
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import (  # noqa: E402
    load_replay, extract_episode_timelines, to_day_row, infer_sell_events_own,
    infer_opponent_money_deltas, velocities,
)

OUT_ROOT = "results/phase6"

EPISODES = {
    # label: path -- priority strong/notable real opponents actually present
    # in this repo's data (see Section 3 of the final report for why "MTN"
    # itself could not be analyzed: no episode named/tagged MTN exists in
    # COMPETITION RESULTS).
    "lai_eu_wen":    "COMPETITION RESULTS/SUBMISSION C/104797306.json",   # strongest real opponent by final $, Submission C episode
    "zach_locke":    "COMPETITION RESULTS/SUBMISSION C/104797848.json",  # 2nd Submission C episode
    "moushun_chen":  "COMPETITION RESULTS/SUBMISSION B/104768097.json",  # previously known 10h/14 animal opponent
    "achille_gohin": "COMPETITION RESULTS/SUBMISSION B/104772378.json",
}


def run_one(label, path):
    replay = load_replay(path)
    meta, self_tl, opp_tl = extract_episode_timelines(replay)

    out_dir = os.path.join(OUT_ROOT, label)
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    for side_name, timeline in (("self", self_tl), ("opponent", opp_tl)):
        rows = [to_day_row(s) for s in timeline]
        with open(os.path.join(out_dir, f"days_{side_name}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        vel_fields = ["bank", "hands_count", "total_animal_count", "total_crop_tiles", "land_quadrants"]
        vel = velocities(rows, vel_fields)
        with open(os.path.join(out_dir, f"velocity_{side_name}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(vel[0].keys()))
            w.writeheader()
            w.writerows(vel)

    own_events = infer_sell_events_own(self_tl)
    with open(os.path.join(out_dir, "own_market_events.json"), "w") as f:
        json.dump(own_events, f, indent=2)

    opp_deltas = infer_opponent_money_deltas(opp_tl)
    with open(os.path.join(out_dir, "opponent_money_deltas_INFERRED.json"), "w") as f:
        json.dump(opp_deltas, f, indent=2)

    print(f"[{label}] episode={meta['episode_id']} opponent={meta['opponent_name']!r} "
          f"days={meta['n_days']} final_self=${self_tl[-1].bank} final_opp=${opp_tl[-1].bank} "
          f"-> {out_dir}")


def main():
    for label, path in EPISODES.items():
        run_one(label, path)


if __name__ == "__main__":
    main()
