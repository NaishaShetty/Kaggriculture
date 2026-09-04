"""
Phase 34 Part A, Step 3: sanity-check the synthetic Sundar archetype in
isolation (vs. "pass"), then run agents/phase21/'s CURRENT shipped portfolio
agent (Submission H, unmodified) head-to-head against it on the 4 development
seeds -- does the real loss reproduce against a synthetic stand-in?
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from scripts.phase34.sundar_archetype import make_sundar_archetype  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402
from instrumentation.pipeline import analyze_replay  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase34"


def isolated_check():
    print("=== Isolated sanity check: Sundar archetype vs. 'pass' ===")
    rows = []
    for seed in DEV_SEEDS:
        agent = make_sundar_archetype()
        replay, meta = run_episode(agent, "pass", STEPS, seed, None)
        record, extracted = analyze_replay(replay, meta, "phase34_sundar_isolated", f"seed{seed}")
        final_money = record["outcome"]["final_money"][0]
        rows.append({"seed": seed, "final_money": final_money})
        print(f"  seed={seed}: final_money=${final_money}", flush=True)
    mean_final = sum(r["final_money"] for r in rows) / len(rows)
    print(f"  MEAN final_money=${mean_final:.2f}  (real Sundar game reached $97,246 in real 2-player competition)\n")
    return rows


def head_to_head():
    print("=== agents/phase21/ (Submission H, unmodified) vs. synthetic Sundar archetype ===")
    rows = []
    for seed in DEV_SEEDS:
        agent21 = make_portfolio_agent()
        sundar = make_sundar_archetype()
        replay, meta = run_episode(agent21, sundar, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        winner = "phase21" if o > t else ("tie" if o == t else "sundar_archetype")
        rows.append({"seed": seed, "phase21": o, "sundar_archetype": t, "winner": winner})
        print(f"  seed={seed}: phase21=${o:,.2f}  sundar_archetype=${t:,.2f}  winner={winner}", flush=True)
    wins = sum(1 for r in rows if r["winner"] == "phase21")
    print(f"\n  Record: {wins}W-{len(rows)-wins}L (win rate {wins}/{len(rows)})")
    mean_ours = sum(r["phase21"] for r in rows) / len(rows)
    mean_theirs = sum(r["sundar_archetype"] for r in rows) / len(rows)
    print(f"  Mean: phase21=${mean_ours:,.2f}  sundar_archetype=${mean_theirs:,.2f}")
    return rows


def main():
    iso_rows = isolated_check()
    h2h_rows = head_to_head()
    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase34_sundar_headtohead_results.json"), "w") as f:
        json.dump({"isolated": iso_rows, "head_to_head": h2h_rows}, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase34_sundar_headtohead_results.json")


if __name__ == "__main__":
    main()
