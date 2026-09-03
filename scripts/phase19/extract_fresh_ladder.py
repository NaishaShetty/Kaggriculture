"""
Phase 19 Step 1: extract day-by-day timelines from the 4 freshly-pulled,
current-top-ladder replays (results/phase19/fresh_ladder/*.json -- pulled
directly from Kaggle's public replay API, GET
https://www.kaggle.com/competitions/episodes/<id>/replay.json, same JSON
shape agents/phase6/replay_forensics.py already parses).

Reuses agents/phase6/replay_forensics.py::extract_episode_timelines UNCHANGED
-- no new parser. That function requires a `our_name` team name present in
the replay to pick a "viewer" side (only used to decide which side's private
state, if any, gets read -- irrelevant here since neither side is actually
"us"; both players' PUBLIC state is read either way, per that module's own
documented observability discipline). For each of these 4 episodes, this
script runs extraction ONCE PER TEAM NAME so BOTH players' full public
trajectories are captured, not just one -- giving up to 8 player-trajectories
across 4 episodes (Dmitry Larko appears in all 4, three different opponents
plus Milan Leonard).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import load_replay, extract_episode_timelines, to_day_row  # noqa: E402

IN_DIR = "results/phase19/fresh_ladder"
OUT_DIR = "results/phase19/fresh_ladder_extracted"
EPISODE_IDS = ["105027448", "105019962", "105008070", "105012251"]
SNAPSHOT_DAYS = [0, 5, 10, 15, 20, 25, 29]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = {}
    for eid in EPISODE_IDS:
        path = os.path.join(IN_DIR, f"{eid}.json")
        replay = load_replay(path)
        team_names = replay["info"]["TeamNames"]
        print(f"\n=== Episode {eid}: {team_names} ===")
        summary[eid] = {"team_names": team_names, "players": {}}

        for viewer_name in team_names:
            meta, self_tl, opp_tl = extract_episode_timelines(replay, our_name=viewer_name)
            rows = [to_day_row(s) for s in self_tl]
            out_csv_rows = rows
            print(f"  -- {viewer_name} (viewer side) --")
            snap_data = []
            for row in out_csv_rows:
                if row["day"] in SNAPSHOT_DAYS:
                    crop_tiles = {k[6:]: v for k, v in row.items() if k.startswith("tiles_") and v}
                    animal_tiles = {k[8:]: v for k, v in row.items() if k.startswith("animals_") and v}
                    entry = {
                        "day": row["day"], "bank": row["bank"], "hands": row["hands_count"],
                        "land_quadrants": row["land_quadrants"], "total_crop_tiles": row["total_crop_tiles"],
                        "total_animals": row["total_animal_count"], "crop_tiles": crop_tiles,
                        "animal_tiles": animal_tiles,
                    }
                    snap_data.append(entry)
                    print(f"    day {row['day']:2d}: bank=${row['bank']:>10,.0f}  hands={row['hands_count']:2d}  "
                          f"land={row['land_quadrants']}  crop_tiles={row['total_crop_tiles']:3d} {crop_tiles}  "
                          f"animals={row['total_animal_count']:2d} {animal_tiles}")
            summary[eid]["players"][viewer_name] = snap_data
            out_json = os.path.join(OUT_DIR, f"{eid}_{viewer_name.replace(' ', '_')}.json")
            with open(out_json, "w") as f:
                json.dump(snap_data, f, indent=2)

    with open(os.path.join(OUT_DIR, "_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote extracted timelines to {OUT_DIR}/")


if __name__ == "__main__":
    main()
