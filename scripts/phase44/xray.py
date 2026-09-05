"""
Phase 44: "X-ray" tool -- a reusable, re-runnable generalization of Phase
6/41's manual real-opponent-characterization pipeline, inspired by David
Estevez's public "X-ray your agent" notebook (this session's own research
find, real live rank #139). Given a target team and a list of their recent
episode IDs, this pulls those replays, extracts PUBLIC-only telemetry with
this project's own already-verified parser, and produces a structured
fingerprint report: win/loss ledger, strategy signature (Phase 41's own
feature vocabulary, reused not reinvented), opponent kinship/clone
detection against Phase 41's growing feature library, and an economy-shape
summary.

DISCOVERY-MECHANISM FINDING (per this phase's own Step 1 -- see the Phase
44 report Section 1 for the full account): "who currently holds rank #1"
and "their N most recent episode IDs" CANNOT be discovered by a plain
headless/scripted HTTP call without a Kaggle API token or login. The
leaderboard and Game-History-panel data are served by Kaggle's own internal
gRPC-web JSON API (`competitions.LeaderboardService/GetLeaderboard`, seen
directly in this session's own network traffic) which requires
session/CSRF context this environment cannot script blind -- a direct,
unauthenticated POST to it returns `403 PERMISSION_DENIED`. What DOES work
without any login, confirmed directly and reused unchanged from Phase
19/34/39/41: `GET https://www.kaggle.com/competitions/episodes/<id>/replay.json`,
once you already know the episode id. So this tool's boundary is exactly
there: discovering WHO is #1 and WHICH episode ids to pull is one small,
documented manual step (or, for an agentic session with browser access --
which is how every real-data phase in this project, including this one's
own demo run, has actually done it -- an automatable few-click step); every-
thing downstream of having a team name + episode id list is 100% scripted
and re-runnable with zero code changes.

USAGE:
  python scripts/phase44/xray.py                     # reads results/phase44/target_manifest.json
  python scripts/phase44/xray.py --team-name X --episode-ids 123,456,789
  python scripts/phase44/xray.py --manifest path/to/manifest.json

See the module docstring's DISCOVERY-MECHANISM section and the Phase 44
report for how to refresh target_manifest.json for a NEW target (e.g. a new
#1) before the next run.

REUSED, UNCHANGED:
  - agents/phase6/replay_forensics.py::load_replay, extract_episode_timelines
  - scripts/phase41/archetype_survey.py::extract_both_public, team_features
    (the exact feature vocabulary and PUBLIC-only extraction discipline --
    imported, not reimplemented)

OBSERVABILITY DISCIPLINE (identical to Phase 41's own, restated here since
this is the tool other phases will reuse): every team in every episode is
read ONLY as the "opponent" side of `extract_episode_timelines` -- for a
2-team episode, `extract_both_public` calls it once per team name, each
time treating that team as the non-viewer/opponent side, so shed contents,
seed inventories, carried inventories, and submitted actions are NEVER read
for ANY team, including the target team itself. This tool has no concept
of "us" at all -- it characterizes both sides of every pulled episode
exactly as if neither were ours.
"""
import argparse
import json
import math
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import load_replay  # noqa: E402
from scripts.phase41.archetype_survey import extract_both_public, team_features  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "phase44")
RAW_DIR = os.path.join(OUT_ROOT, "raw_replays")
DEFAULT_MANIFEST = os.path.join(OUT_ROOT, "target_manifest.json")
LIBRARY_PATH = os.path.join(OUT_ROOT, "phase44_xray_library.json")
PHASE41_LIBRARY_PATH = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "phase41",
                                     "phase41_team_features.json")
REPLAY_URL = "https://www.kaggle.com/competitions/episodes/{eid}/replay.json"


# ---------------------------------------------------------------------------
# Step 1/2: fetch (no login needed, once the episode id is known -- see
# module docstring for the discovery-mechanism boundary this does NOT cross)
# ---------------------------------------------------------------------------

def fetch_episode(episode_id, raw_dir=RAW_DIR, timeout=30):
    os.makedirs(raw_dir, exist_ok=True)
    path = os.path.join(raw_dir, f"{episode_id}.json")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    url = REPLAY_URL.format(eid=episode_id)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"failed to fetch episode {episode_id}: {e}") from e
    with open(path, "wb") as f:
        f.write(data)
    return path


# ---------------------------------------------------------------------------
# Step 3: win/loss ledger + strategy fingerprint (reuses Phase 41's own
# extract_both_public/team_features -- not reimplemented)
# ---------------------------------------------------------------------------

def analyze_episode(episode_id, target_name, raw_dir=RAW_DIR):
    path = fetch_episode(episode_id, raw_dir)
    replay = load_replay(path)
    names = replay["info"]["TeamNames"]
    if target_name not in names:
        return None
    opp_name = [n for n in names if n != target_name][0]
    by_team = extract_both_public(replay)
    target_timeline = by_team[target_name]
    feat = team_features(target_name, target_timeline, episode_id, opp_name)
    if feat is None:
        return None

    target_idx = names.index(target_name)
    rewards = replay.get("rewards") or [None, None]
    target_reward, opp_reward = rewards[target_idx], rewards[1 - target_idx]
    if target_reward is None or opp_reward is None:
        result = "unknown"
        margin = None
    elif target_reward > opp_reward:
        result = "win"
        margin = round(target_reward - opp_reward, 2)
    elif target_reward < opp_reward:
        result = "loss"
        margin = round(target_reward - opp_reward, 2)
    else:
        result = "tie"
        margin = 0.0

    feat["result"] = result
    feat["margin"] = margin
    feat["target_final_reward"] = target_reward
    feat["opponent_final_reward"] = opp_reward
    return feat


# ---------------------------------------------------------------------------
# Step 3 (kinship): a simple, explainable similarity metric against Phase
# 41's own growing feature library -- NEW logic, Phase 41 didn't build this.
# ---------------------------------------------------------------------------

_NUMERIC_FIELDS = [
    "final_land_quadrants", "final_hands_count", "final_crop_tiles", "final_animal_count",
]
_TIMING_FIELDS = ["first_land_expansion_day", "first_animal_day"]
_LATE_FILL = 30  # a team that never does X is treated as "did it very late" for distance purposes


def _numeric_vector(row):
    vec = [row.get(f) or 0 for f in _NUMERIC_FIELDS]
    vec += [row.get(f) if row.get(f) is not None else _LATE_FILL for f in _TIMING_FIELDS]
    return vec


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _jaccard(set_a, set_b):
    a, b = set(set_a), set(set_b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def kinship_score(row_a, row_b):
    """Blended similarity: 0.5 * cosine similarity of the numeric
    scale/timing vector (land/hands/crop-tiles/animals + first-land/
    first-animal day) + 0.5 * Jaccard similarity of each team's
    `crops_ever_at_scale` set. Chosen over a single metric because scale
    (numeric, continuous) and crop-portfolio SHAPE (categorical, set-valued)
    are different kinds of signal -- two teams at very different scale can
    still share an identical crop strategy, and vice versa; averaging both
    catches either kind of kinship, not just one."""
    num_sim = _cosine_similarity(_numeric_vector(row_a), _numeric_vector(row_b))
    crop_sim = _jaccard(row_a.get("crops_ever_at_scale", []), row_b.get("crops_ever_at_scale", []))
    return round(0.5 * num_sim + 0.5 * crop_sim, 4)


KINSHIP_THRESHOLD = 0.85


def find_kinship(target_row, library_rows, threshold=KINSHIP_THRESHOLD, exclude_team=None):
    matches = []
    for lib_row in library_rows:
        if exclude_team and lib_row.get("team_name") == exclude_team:
            continue
        score = kinship_score(target_row, lib_row)
        if score >= threshold:
            matches.append({
                "team_name": lib_row.get("team_name"), "episode_id": lib_row.get("episode_id"),
                "kinship_score": score,
            })
    matches.sort(key=lambda m: -m["kinship_score"])
    return matches


# ---------------------------------------------------------------------------
# Step 3 (economy shape): land timing / herd-crop scale / endgame
# liquidation -- reuses the CONCEPT from agents/phase21/liquidation.py
# (per-crop planting cutoffs mean a well-run farm should be near-fully
# liquidated, crop_tiles~0, by day 29) for REFERENCE ONLY; that module is
# never imported or modified here.
# ---------------------------------------------------------------------------

def economy_shape(row):
    fully_liquidated = row["final_crop_tiles"] == 0 and row["final_day"] >= 28
    return {
        "land_timing": {
            "first_expansion_day": row["first_land_expansion_day"],
            "reached_3_quadrants_day": row["first_land3_day"],
            "final_land_quadrants": row["final_land_quadrants"],
        },
        "herd_crop_scale": {
            "final_crop_tiles": row["final_crop_tiles"], "final_animal_count": row["final_animal_count"],
            "peak_animal_mix": row["peak_animal_mix"], "crop_diversity": len(row["crops_ever_at_scale"]),
        },
        "endgame_liquidation": {
            "fully_liquidated_by_final_day": fully_liquidated,
            "final_crop_tiles_remaining": row["final_crop_tiles"],
        },
    }


# ---------------------------------------------------------------------------
# Step 4: growing library (append, dedupe by episode_id+team_name)
# ---------------------------------------------------------------------------

def load_library(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def append_to_library(path, new_rows):
    lib = load_library(path)
    seen = {(r.get("episode_id"), r.get("team_name")) for r in lib}
    added = 0
    for row in new_rows:
        key = (row.get("episode_id"), row.get("team_name"))
        if key in seen:
            continue
        lib.append(row)
        seen.add(key)
        added += 1
    with open(path, "w") as f:
        json.dump(lib, f, indent=2)
    return added


def load_manifest(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(team_name, episode_ids, out_root=OUT_ROOT, raw_dir=RAW_DIR):
    os.makedirs(out_root, exist_ok=True)
    print(f"=== X-ray: {team_name} ({len(episode_ids)} episodes) ===")

    rows = []
    for eid in episode_ids:
        try:
            row = analyze_episode(eid, team_name, raw_dir)
        except Exception as e:  # noqa: BLE001 -- report and continue, one bad episode shouldn't kill the run
            print(f"  episode {eid}: FAILED ({e})")
            continue
        if row is None:
            print(f"  episode {eid}: target team not found in this replay, skipped")
            continue
        rows.append(row)
        print(f"  episode {eid}: {row['result'].upper():4s} margin=${row['margin']:,.2f}  "
              f"land={row['final_land_quadrants']} hands={row['final_hands_count']} "
              f"crop_tiles={row['final_crop_tiles']} animals={row['final_animal_count']} "
              f"crops={row['crops_ever_at_scale']}")

    if not rows:
        print("No episodes successfully analyzed.")
        return None

    # Win/loss ledger, in play order (episode ids are Kaggle-sequential --
    # larger id == later game, same convention every prior phase has used).
    ledger = sorted(rows, key=lambda r: int(r["episode_id"]))
    wins = sum(1 for r in ledger if r["result"] == "win")
    losses = sum(1 for r in ledger if r["result"] == "loss")
    ties = sum(1 for r in ledger if r["result"] == "tie")
    mean_margin = sum(r["margin"] for r in ledger if r["margin"] is not None) / len(ledger)

    # Kinship against Phase 41's original library PLUS every team this tool
    # has already profiled in a prior run (this file's own growing
    # library, loaded here BEFORE this run's rows are appended below) --
    # so kinship detection gets more powerful the more this tool is used,
    # not just a fixed one-time comparison set. Excludes the target's own
    # name so a team isn't matched against its own prior games.
    comparison_pool = load_library(PHASE41_LIBRARY_PATH) + load_library(LIBRARY_PATH)
    kinship_by_episode = {}
    for row in rows:
        kinship_by_episode[row["episode_id"]] = find_kinship(row, comparison_pool, exclude_team=team_name)

    report = {
        "team_name": team_name, "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_episodes": len(rows),
        "win_loss_ledger": [{"episode_id": r["episode_id"], "opponent": r["opponent_name"],
                              "result": r["result"], "margin": r["margin"]} for r in ledger],
        "record": {"wins": wins, "losses": losses, "ties": ties, "mean_margin": round(mean_margin, 2)},
        "strategy_fingerprint": rows,
        "economy_shape_by_episode": {r["episode_id"]: economy_shape(r) for r in rows},
        "kinship_matches_by_episode": kinship_by_episode,
    }

    print(f"\nRecord: {wins}W-{losses}L-{ties}T over {len(rows)} episodes, mean margin ${mean_margin:,.2f}")
    any_kinship = {eid: m for eid, m in kinship_by_episode.items() if m}
    if any_kinship:
        print("Kinship matches found (>= {:.2f} blended similarity):".format(KINSHIP_THRESHOLD))
        for eid, matches in any_kinship.items():
            for m in matches[:3]:
                print(f"  episode {eid} ~ {m['team_name']} (episode {m['episode_id']}): score={m['kinship_score']}")
    else:
        print(f"No kinship matches >= {KINSHIP_THRESHOLD} against the {len(phase41_lib)}-row Phase 41 library.")

    safe_name = "".join(c if c.isalnum() else "_" for c in team_name)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(out_root, f"phase44_xray_{safe_name}_{stamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nWrote report to {out_path}")

    added = append_to_library(LIBRARY_PATH, rows)
    print(f"Appended {added} new row(s) to the growing library ({LIBRARY_PATH}), "
          f"skipped {len(rows) - added} already-present (episode_id, team_name) duplicates.")

    return report


def main():
    parser = argparse.ArgumentParser(description="Phase 44 X-ray tool")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--team-name", default=None)
    parser.add_argument("--episode-ids", default=None, help="comma-separated episode ids")
    args = parser.parse_args()

    if args.team_name and args.episode_ids:
        team_name = args.team_name
        episode_ids = [e.strip() for e in args.episode_ids.split(",") if e.strip()]
    else:
        manifest = load_manifest(args.manifest)
        team_name = manifest["team_name"]
        episode_ids = manifest["episode_ids"]
        print(f"(loaded target from {args.manifest}: team={team_name!r}, "
              f"discovered_at={manifest.get('discovered_at')}, rank={manifest.get('rank')})")

    run(team_name, episode_ids)


if __name__ == "__main__":
    main()
