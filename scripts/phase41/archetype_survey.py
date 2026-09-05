"""
Phase 41: real opponent archetype survey.

WHY THIS PHASE EXISTS: Phases 39 and 40 each refuted a candidate
execution-side explanation for the real-vs-synthetic gap (tile idle-time,
isolation-harness artifact). Both converged on the same remaining lead:
every synthetic benchmark this project has ever validated against is either
this project's own old submissions (Submission C/G) or a small number of
reconstructed SINGLE-TRAJECTORY real replays (Phase 6's original 4
opponents, Crop Dusta's 2 episodes, the Larko-derived
`scripts/phase21/realistic_opponent.py`, the Sundar-derived
`scripts/phase34/sundar_archetype.py`) -- never a broad sample of the real
ladder's actual strategic diversity. This phase pulls a materially larger
real sample and characterizes what's actually out there.

MEASUREMENT ONLY. No agent built or modified.

REUSED, UNCHANGED: agents/phase6/replay_forensics.py::load_replay,
extract_episode_timelines -- this project's standard, already-verified real
replay parser. Not rebuilt.

OBSERVABILITY DISCIPLINE: every team in every episode here is read ONLY as
the "opponent" side of `extract_episode_timelines` (never as "self") --
concretely, for a 2-team episode, the function is called ONCE with
`our_name=team_A` (which returns team_B's PUBLIC-only opponent_timeline)
and ONCE with `our_name=team_B` (team_A's PUBLIC-only opponent_timeline).
This means neither team's shed, seeds, inventories, or submitted action is
EVER read for ANY of the 16 real episodes gathered here, including the 2
games this project's own team (shettynaisha / Submission I) played --
consistent with, and slightly stricter than, this project's own discipline
(Phase 19 populated an aggregate shed/seed total for whichever side it
called "self"; this phase never does, for any side, by construction).

EPISODES: pulled directly from the live Kaggle leaderboard (browser
session, no login required for the public replay.json endpoint) on
2026-09-04 -- 14 fresh episodes plus reuse of Phase 34/39's 2 existing
Crop Dusta episodes, spanning rank #1 (Crop Dusta) through the matchmaking
band around this project's own live rank (~5089/7587): keiz (#2) vs. Crop
Dusta/Jesse Bullard/Himanshu Kumar/AI是我的豆包 (4
episodes), plus Submission I's own 9 most recent real games (vs.
마짜MAZZANG, Kota Iizuka, Ryan Cheung, Reda HEDDAD, Vishal
Dhariwal, Shinzo Takayama, 宣城市机械电子职
业技术学院, Jonaid, Aidan Janish).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import load_replay, extract_episode_timelines  # noqa: E402

RAW_DIR = "results/phase41/raw_replays"
OUT_ROOT = "results/phase41"

# (episode_id, source_note) -- fresh pulls this phase, plus the 2 existing
# Crop Dusta episodes already downloaded and used by Phase 34/39/40.
EPISODES = [
    ("105444785", "keiz vs Crop Dusta"),
    ("105440807", "keiz vs Jesse Bullard"),
    ("105437334", "keiz vs Crop Dusta"),
    ("105395055", "keiz vs Himanshu Kumar"),
    ("105395067", "keiz vs AI是我的豆包"),
    ("105439708", "shettynaisha vs 마짜MAZZANG"),
    ("105429859", "shettynaisha vs Kota Iizuka"),
    ("105424362", "shettynaisha vs Ryan Cheung"),
    ("105407922", "shettynaisha vs Reda HEDDAD"),
    ("105407002", "shettynaisha vs Vishal Dhariwal"),
    ("105406092", "shettynaisha vs Shinzo Takayama"),
    ("105405153", "shettynaisha vs 宣城市机械电子职业技术学院"),
    ("105405216", "shettynaisha vs Jonaid"),
    ("105403450", "shettynaisha vs Aidan Janish"),
]
EXISTING_CROP_DUSTA = [
    ("results/phase34/raw_replays/105373474.json", "Crop Dusta (Phase 34/39)"),
    ("results/phase34/raw_replays/105341441.json", "Crop Dusta (Phase 34/39)"),
]


def extract_both_public(replay):
    """Both teams' PUBLIC-only trajectories -- see module docstring. Never
    populates shed/seeds/inventories/own_action for either team."""
    names = replay["info"]["TeamNames"]
    if len(names) != 2:
        raise ValueError(f"expected 2 teams, got {names}")
    _, _, opp_b = extract_episode_timelines(replay, our_name=names[0])
    _, _, opp_a = extract_episode_timelines(replay, our_name=names[1])
    return {names[0]: opp_a, names[1]: opp_b}


def team_features(name, timeline, episode_id, opponent_name):
    """Portfolio mix over time, scale trajectory, and rough commitment
    timing -- the same telemetry categories Phase 6 originally used."""
    if not timeline:
        return None
    days = sorted(timeline, key=lambda s: s.day)
    final = days[-1]
    final_crop_tiles = sum(final.crop_tile_counts.values())
    final_animals = sum(final.animal_tile_counts.values())

    first_land_day = next((s.day for s in days if s.land_quadrants > 1), None)
    first_animal_day = next((s.day for s in days if sum(s.animal_tile_counts.values()) > 0), None)
    first_land3_day = next((s.day for s in days if s.land_quadrants >= 3), None)
    max_hands_day = next((s.day for s in days if s.hands_count >= 10), None)

    # Dominant crop per day (by tile count) and the days it changes -- a
    # crude "pivot" trace, same idea Phase 6's own opponent characterization
    # used, not a new mechanic.
    dominant_seq = []
    for s in days:
        if not s.crop_tile_counts:
            continue
        dom = max(s.crop_tile_counts.items(), key=lambda kv: kv[1])
        if dom[1] <= 0:
            continue
        if not dominant_seq or dominant_seq[-1][1] != dom[0]:
            dominant_seq.append((s.day, dom[0], dom[1]))

    # Crop diversity: any crop that ever reaches >=5 tiles at some point.
    ever_crops = set()
    for s in days:
        for crop, ct in s.crop_tile_counts.items():
            if ct >= 5:
                ever_crops.add(crop)

    # Peak animal species mix (at the day of max total animals).
    peak_animal_day = max(days, key=lambda s: sum(s.animal_tile_counts.values()))

    return {
        "episode_id": episode_id, "opponent_name": opponent_name, "team_name": name,
        "n_days_observed": len(days), "final_day": final.day,
        "final_bank": final.bank, "final_land_quadrants": final.land_quadrants,
        "final_hands_count": final.hands_count,
        "final_crop_tiles": final_crop_tiles, "final_crop_mix": final.crop_tile_counts,
        "final_animal_count": final_animals,
        "peak_animal_day": peak_animal_day.day, "peak_animal_mix": peak_animal_day.animal_tile_counts,
        "first_land_expansion_day": first_land_day, "first_land3_day": first_land3_day,
        "first_animal_day": first_animal_day, "first_10hands_day": max_hands_day,
        "dominant_crop_sequence": dominant_seq, "crops_ever_at_scale": sorted(ever_crops),
    }


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    all_features = []

    for eid, note in EPISODES:
        path = os.path.join(RAW_DIR, f"{eid}.json")
        replay = load_replay(path)
        by_team = extract_both_public(replay)
        names = replay["info"]["TeamNames"]
        print(f"\n=== Episode {eid} ({note}): {names} ===")
        for name, timeline in by_team.items():
            feat = team_features(name, timeline, eid, [n for n in names if n != name][0])
            if feat is None:
                continue
            all_features.append(feat)
            print(f"  {name}: final_bank=${feat['final_bank']:,.0f} land={feat['final_land_quadrants']} "
                  f"hands={feat['final_hands_count']} crop_tiles={feat['final_crop_tiles']} "
                  f"animals={feat['final_animal_count']} crops_at_scale={feat['crops_ever_at_scale']} "
                  f"first_land_day={feat['first_land_expansion_day']} first_animal_day={feat['first_animal_day']}")

    for path, note in EXISTING_CROP_DUSTA:
        replay = load_replay(path)
        by_team = extract_both_public(replay)
        names = replay["info"]["TeamNames"]
        eid = replay["info"].get("EpisodeId")
        print(f"\n=== Episode {eid} ({note}): {names} ===")
        for name, timeline in by_team.items():
            if name != "Crop Dusta":
                continue  # already have the other side's data (Phase 6/34); avoid double-counting non-Crop-Dusta teams here
            feat = team_features(name, timeline, eid, [n for n in names if n != name][0])
            if feat is None:
                continue
            all_features.append(feat)
            print(f"  {name}: final_bank=${feat['final_bank']:,.0f} land={feat['final_land_quadrants']} "
                  f"hands={feat['final_hands_count']} crop_tiles={feat['final_crop_tiles']} "
                  f"animals={feat['final_animal_count']} crops_at_scale={feat['crops_ever_at_scale']} "
                  f"first_land_day={feat['first_land_expansion_day']} first_animal_day={feat['first_animal_day']}")

    with open(os.path.join(OUT_ROOT, "phase41_team_features.json"), "w") as f:
        json.dump(all_features, f, indent=2)
    print(f"\nWrote {len(all_features)} team-episode feature rows to {OUT_ROOT}/phase41_team_features.json")


if __name__ == "__main__":
    main()
