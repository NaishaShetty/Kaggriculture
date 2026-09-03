"""
Phase 12: reproduce BOTH real F-005 forensic cases synthetically -- once on
UNPATCHED code (liquidity_guard_enabled=False, or equivalently the guard's
pre-Phase-12 CHECK_DAY=2-only behavior) to confirm the guard does not fire
(matching documented reality), then on PATCHED code (widened CHECK_DAYS,
wired into make_competitive_v3_agent) to confirm it DOES fire and that the
crop-footprint reduction lands before the tiles that caused each episode's
death spiral are planted.

Case 1: Phase 3.7-C's reconstructed death-spiral seed (852025866) -- documented
    cash of $572 at day==2 (above the old $200/day==2-only checkpoint), crisis
    not visible until day 4-6, ~21-22 tiles already planted by then.
Case 2: Lai Eu Wen-style FAST collapse (Phase 6 report Section 11, our own
    side of episode 104797306: $630 at day==1, $0 by day==3). The real
    episode's own seed is not recoverable (Kaggle's real-match seed is not
    recorded in the downloaded replay -- `configuration.seed` is null), so
    this case is reproduced by scanning synthetic seeds for one exhibiting
    the same qualitative pattern (a fast collapse to near-zero cash by
    day 3), not by replaying the literal game.

Run: python -m scripts.phase12.repro_forensic_cases
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent
from agents.phase3.opponent_classes import OPPONENT_CLASSES
from instrumentation.collector import run_episode

DEATH_SPIRAL_SEED = 852025866
EPISODE_STEPS = 720


def _own_tile_kind_counts(farm):
    n = 0
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                n += 1
    return n


def _daily_trace(replay, player=0):
    """One row per (day, hour==0) turn: cash and planted-crop-tile count."""
    rows = []
    seen_days = set()
    for step in replay["steps"]:
        obs = step[0]["observation"]  # shared public observation; farms[] holds both players
        day = obs["day"]
        if obs.get("hour", 0) != 0 or day in seen_days:
            continue
        seen_days.add(day)
        farm = obs["farms"][player]
        rows.append({"day": day, "cash": farm["money"], "planted_tiles": _own_tile_kind_counts(farm)})
    return rows


def run_case(label, seed, opponent_key, liquidity_guard_enabled):
    agent = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=liquidity_guard_enabled)
    opponent = OPPONENT_CLASSES[opponent_key]()
    replay, meta = run_episode(agent, opponent, EPISODE_STEPS, seed, None)
    trace = _daily_trace(replay)
    fired = agent._state_ref["liquidity_guard_triggered"]
    fired_day = None
    if fired:
        for row in trace:
            if row["cash"] < 200.0:
                fired_day = row["day"]
                break
    print(f"\n=== {label} (seed={seed}, opponent={opponent_key}, guard_enabled={liquidity_guard_enabled}) ===")
    for row in trace[:10]:
        print(f"  day {row['day']:2d}: cash=${row['cash']:.2f}  planted_tiles={row['planted_tiles']}")
    print(f"  guard fired: {fired}  (activations={agent._state_ref['liquidity_guard_activations']})")
    return trace, fired, fired_day


def find_fast_collapse_seed(candidate_seeds, opponent_key="passive"):
    """Scan candidate seeds (unpatched-behavior run, guard disabled) for one
    where cash collapses to near-zero by day 3, matching the Lai Eu Wen
    pattern (Phase 6 report Sec. 11: $630 day1 -> $0 day3)."""
    for seed in candidate_seeds:
        agent = make_competitive_v3_agent(trace_path=None, liquidity_guard_enabled=False)
        opponent = OPPONENT_CLASSES[opponent_key]()
        replay, _ = run_episode(agent, opponent, EPISODE_STEPS, seed, None)
        trace = _daily_trace(replay)
        by_day = {r["day"]: r["cash"] for r in trace}
        if by_day.get(3, 9999) < 50.0 and by_day.get(1, 0) > 100.0:
            print(f"  candidate seed {seed}: day1=${by_day.get(1):.2f} day3=${by_day.get(3):.2f}  <- MATCH")
            return seed, trace
        print(f"  candidate seed {seed}: day1=${by_day.get(1, float('nan')):.2f} "
              f"day3=${by_day.get(3, float('nan')):.2f}")
    return None, None


def main():
    print("#" * 70)
    print("CASE 1: Phase 3.7-C reconstructed death-spiral seed (852025866)")
    print("#" * 70)
    trace_unpatched, fired_unpatched, _ = run_case(
        "Case 1 -- UNPATCHED (guard disabled == old dead-trigger behavior)",
        DEATH_SPIRAL_SEED, "passive", liquidity_guard_enabled=False)
    trace_patched, fired_patched, fired_day1 = run_case(
        "Case 1 -- PATCHED (widened CHECK_DAYS, wired in)",
        DEATH_SPIRAL_SEED, "passive", liquidity_guard_enabled=True)

    day2_cash = next((r["cash"] for r in trace_unpatched if r["day"] == 2), None)
    print(f"\nCase 1 summary: day==2 cash was ${day2_cash:.2f} (Phase 3.7-C documented $572 -- "
          f"{'MATCHES' if day2_cash and abs(day2_cash - 572) < 50 else 'differs, see note'} prior finding).")
    print(f"  Unpatched: guard fired = {fired_unpatched} (expected False, matching current reality)")
    print(f"  Patched:   guard fired = {fired_patched} on day {fired_day1}")
    if fired_patched and fired_day1 is not None:
        planted_at_fire = next(r["planted_tiles"] for r in trace_patched if r["day"] == fired_day1)
        planted_final = trace_patched[-1]["planted_tiles"] if trace_patched else None
        print(f"  Tiles planted at fire-day ({fired_day1}): {planted_at_fire}; "
              f"final planted-tile count in this run: {planted_final}")

    print("\n" + "#" * 70)
    print("CASE 2: Lai Eu Wen-style fast collapse (searching for a matching synthetic seed)")
    print("#" * 70)
    candidate_seeds = [852025867, 852025868, 852025870, 852025900, 852030000,
                       111222333, 222333444, 333444555, 444555666, 555666777]
    fast_seed, trace_fast_unpatched = find_fast_collapse_seed(candidate_seeds)
    if fast_seed is None:
        print("\nNo candidate seed matched the fast-collapse pattern (day1>$100, day3<$50). "
              "Case 2 could not be reproduced synthetically with the tried seed pool -- reporting honestly.")
        return

    print(f"\nUsing seed {fast_seed} for Case 2.")
    trace_unpatched2, fired_unpatched2, _ = run_case(
        "Case 2 -- UNPATCHED", fast_seed, "passive", liquidity_guard_enabled=False)
    trace_patched2, fired_patched2, fired_day2 = run_case(
        "Case 2 -- PATCHED", fast_seed, "passive", liquidity_guard_enabled=True)
    print(f"\nCase 2 summary: guard fired unpatched={fired_unpatched2}, patched={fired_patched2} on day {fired_day2}")
    if fired_patched2 and fired_day2 is not None:
        planted_at_fire = next(r["planted_tiles"] for r in trace_patched2 if r["day"] == fired_day2)
        planted_final = trace_patched2[-1]["planted_tiles"] if trace_patched2 else None
        print(f"  Tiles planted at fire-day ({fired_day2}): {planted_at_fire}; "
              f"final planted-tile count in this run: {planted_final}")


if __name__ == "__main__":
    main()
