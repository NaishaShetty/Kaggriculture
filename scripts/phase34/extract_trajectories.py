"""
Phase 34 Step 1 (Part A) / Step 6 (Part B): extract full day-by-day
trajectories from the real downloaded episodes using
agents/phase6/replay_forensics.py::extract_episode_timelines, REUSED
UNCHANGED (no new parsing logic) -- confirms the prompt's summary directly
from the raw data before anything is built.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import load_replay, extract_episode_timelines, to_day_row  # noqa: E402

OUT_ROOT = "results/phase34"


def dump_timeline(path, our_name, label):
    replay = load_replay(path)
    meta, self_tl, opp_tl = extract_episode_timelines(replay, our_name=our_name)
    print(f"\n=== {label} ({path}) ===")
    print(f"  meta: {meta}")
    rows_self = [to_day_row(s) for s in self_tl]
    rows_opp = [to_day_row(s) for s in opp_tl]
    for r in rows_self:
        crops = {k[6:]: v for k, v in r.items() if k.startswith("tiles_") and v > 0}
        animals = {k[8:]: v for k, v in r.items() if k.startswith("animals_") and v > 0}
        print(f"  [SELF={our_name}] day={r['day']:2d} bank=${r['bank']:>10,.0f} hands={r['hands_count']:2d} "
              f"land={r['land_quadrants']} crops={crops} animals={animals}")
    for r in rows_opp:
        crops = {k[6:]: v for k, v in r.items() if k.startswith("tiles_") and v > 0}
        animals = {k[8:]: v for k, v in r.items() if k.startswith("animals_") and v > 0}
        print(f"  [OPP]              day={r['day']:2d} bank=${r['bank']:>10,.0f} hands={r['hands_count']:2d} "
              f"land={r['land_quadrants']} crops={crops} animals={animals}")

    os.makedirs(OUT_ROOT, exist_ok=True)
    out = {"meta": meta, "self_rows": rows_self, "opp_rows": rows_opp}
    fname = os.path.join(OUT_ROOT, f"phase34_trajectory_{label}.json")
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"  Wrote {fname}")
    return meta, rows_self, rows_opp


def main():
    dump_timeline("results/phase34/raw_replays/105208327_worstloss.json", "shettynaisha", "sundar_worstloss")
    dump_timeline("results/phase34/raw_replays/105373474.json", "Crop Dusta", "gold_105373474")
    dump_timeline("results/phase34/raw_replays/105341441.json", "Crop Dusta", "gold_105341441")


if __name__ == "__main__":
    main()
