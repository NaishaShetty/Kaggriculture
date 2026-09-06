"""
Phase 52: forensic analysis of our own team's 3 most recent real losses.

WHY THIS PHASE EXISTS: a live leaderboard check this session found our
team's 10 most recent real games are 7W-3L (70%), a marked improvement over
Phase 41's earlier 4W-5L snapshot for Submission I. The 3 real losses are
sitting right there, freshly identified -- this project's own standing
discipline (Phase 24, 27, 41) says to look at real losses directly rather
than assume they're noise, the same way Phase 41 first found the
animal-count correlation.

MEASUREMENT ONLY. No agent built or modified.

REUSED, UNCHANGED:
  - agents/phase6/replay_forensics.py::load_replay, extract_episode_timelines
  - scripts/phase41/archetype_survey.py::team_features (the exact feature
    vocabulary Phase 41/44 already use)

WHAT'S NEW HERE (a thin wrapper only): Phase 41/44's `extract_both_public`
always treats the target team as the "opponent" side of
`extract_episode_timelines` -- fine when characterizing someone else, but
this is the first phase to run the pipeline on OUR OWN team's real games,
where we legitimately want both:
  (a) our own side's PUBLIC-only trajectory (same public-state discipline,
      just also computing team_features on the "self" timeline this
      module already builds), and
  (b) the opponent's PUBLIC-only trajectory (unchanged from Phase 41/44).

`extract_our_and_opponent_public` below calls `extract_episode_timelines`
ONCE per episode with our_name="shettynaisha" and computes `team_features`
on BOTH returned timelines. This is safe under the SAME public-state
discipline Phase 41/44 already documented: `extract_episode_timelines`
never populates shed/seeds/inventories/own_action on the opponent
timeline (see replay_forensics.py's own module docstring), and while it
DOES populate those self-only fields on OUR OWN timeline, `team_features`
(reused unchanged from Phase 41) never reads any of those fields -- it
only reads bank, hands_count, land_quadrants, crop_tile_counts,
animal_tile_counts, and day, all of which are public for both sides. So
even though the underlying snapshot object carries our own private shed/
seed data, this analysis simply never looks at it, preserving Phase 41's
public-only comparison standard for both sides.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import load_replay, extract_episode_timelines  # noqa: E402
from scripts.phase41.archetype_survey import team_features  # noqa: E402

OUR_NAME = "shettynaisha"
RAW_DIR = "results/phase52/raw_replays"
OUT_ROOT = "results/phase52"

LOSSES = [
    ("105750065", "Shawon Biswas"),
    ("105745378", "yuki"),
    ("105744439", "Sarthak Patel"),
]
WINS = [
    ("105757292", "Eric Worrall"),
    ("105748242", "Shuaib ayad Jasim Jasim"),
    ("105746303", "Moritz Huber"),
]


def extract_our_and_opponent_public(replay):
    """Returns (our_features, opp_features) using team_features (Phase 41's
    unmodified feature vocabulary) on BOTH sides of ONE call to
    extract_episode_timelines -- see module docstring for why this stays
    within Phase 41/44's public-state discipline."""
    meta, self_timeline, opp_timeline = extract_episode_timelines(replay, our_name=OUR_NAME)
    eid = meta["episode_id"]
    opp_name = meta["opponent_name"]
    our_feat = team_features(OUR_NAME, self_timeline, eid, opp_name)
    opp_feat = team_features(opp_name, opp_timeline, eid, OUR_NAME)
    return meta, our_feat, opp_feat


def analyze(episode_id, expected_opponent, label):
    path = os.path.join(RAW_DIR, f"{episode_id}.json")
    replay = load_replay(path)
    names = replay["info"]["TeamNames"]
    rewards = replay.get("rewards") or [None, None]
    our_idx = names.index(OUR_NAME)
    our_reward, opp_reward = rewards[our_idx], rewards[1 - our_idx]
    meta, our_feat, opp_feat = extract_our_and_opponent_public(replay)
    assert meta["opponent_name"] == expected_opponent, (
        f"episode {episode_id}: expected opponent {expected_opponent!r}, got {meta['opponent_name']!r}"
    )
    result = "win" if our_reward > opp_reward else ("loss" if our_reward < opp_reward else "tie")
    assert result == label, f"episode {episode_id}: expected {label}, got {result} (${our_reward} vs ${opp_reward})"
    return {
        "episode_id": episode_id, "label": label,
        "our_final_bank": our_reward, "opponent_final_bank": opp_reward,
        "margin": round(our_reward - opp_reward, 2),
        "our_features": our_feat, "opponent_features": opp_feat,
    }


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    results = {"losses": [], "wins": []}

    print("=== 3 recent real LOSSES ===")
    for eid, opp in LOSSES:
        row = analyze(eid, opp, "loss")
        results["losses"].append(row)
        print(f"  {eid} vs {opp}: us=${row['our_final_bank']:,.0f} them=${row['opponent_final_bank']:,.0f} "
              f"margin=${row['margin']:,.2f}")
        print(f"    OURS : land={row['our_features']['final_land_quadrants']} "
              f"hands={row['our_features']['final_hands_count']} "
              f"crop_tiles={row['our_features']['final_crop_tiles']} "
              f"animals={row['our_features']['final_animal_count']} "
              f"crops={row['our_features']['crops_ever_at_scale']} "
              f"first_land_day={row['our_features']['first_land_expansion_day']} "
              f"first_animal_day={row['our_features']['first_animal_day']}")
        print(f"    OPP  : land={row['opponent_features']['final_land_quadrants']} "
              f"hands={row['opponent_features']['final_hands_count']} "
              f"crop_tiles={row['opponent_features']['final_crop_tiles']} "
              f"animals={row['opponent_features']['final_animal_count']} "
              f"crops={row['opponent_features']['crops_ever_at_scale']} "
              f"first_land_day={row['opponent_features']['first_land_expansion_day']} "
              f"first_animal_day={row['opponent_features']['first_animal_day']}")

    print("\n=== 3 comparison real WINS ===")
    for eid, opp in WINS:
        row = analyze(eid, opp, "win")
        results["wins"].append(row)
        print(f"  {eid} vs {opp}: us=${row['our_final_bank']:,.0f} them=${row['opponent_final_bank']:,.0f} "
              f"margin=${row['margin']:,.2f}")
        print(f"    OURS : land={row['our_features']['final_land_quadrants']} "
              f"hands={row['our_features']['final_hands_count']} "
              f"crop_tiles={row['our_features']['final_crop_tiles']} "
              f"animals={row['our_features']['final_animal_count']} "
              f"crops={row['our_features']['crops_ever_at_scale']} "
              f"first_land_day={row['our_features']['first_land_expansion_day']} "
              f"first_animal_day={row['our_features']['first_animal_day']}")
        print(f"    OPP  : land={row['opponent_features']['final_land_quadrants']} "
              f"hands={row['opponent_features']['final_hands_count']} "
              f"crop_tiles={row['opponent_features']['final_crop_tiles']} "
              f"animals={row['opponent_features']['final_animal_count']} "
              f"crops={row['opponent_features']['crops_ever_at_scale']} "
              f"first_land_day={row['opponent_features']['first_land_expansion_day']} "
              f"first_animal_day={row['opponent_features']['first_animal_day']}")

    out_path = os.path.join(OUT_ROOT, "phase52_loss_forensics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
