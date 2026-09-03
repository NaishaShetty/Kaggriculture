"""Phase 6 replay forensics pipeline tests.
Run: python scripts/phase6/phase6_regression_tests.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase6.replay_forensics import (  # noqa: E402
    load_replay, viewer_index_for_us, extract_episode_timelines, to_day_row,
    infer_sell_events_own, velocities, PlayerDaySnapshot,
)

PASS_COUNT = 0
FAIL_COUNT = 0
REPLAY_PATH = "COMPETITION RESULTS/SUBMISSION C/104797306.json"


def check(name, cond):
    global PASS_COUNT, FAIL_COUNT
    if cond:
        PASS_COUNT += 1
        print(f"  PASS  {name}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL  {name}")


def test_replay_parsing():
    print("replay parsing:")
    replay = load_replay(REPLAY_PATH)
    check("has steps", len(replay["steps"]) > 0)
    check("has 720 steps (30 days x 24h)", len(replay["steps"]) == 720)
    check("has info.TeamNames", len(replay["info"]["TeamNames"]) == 2)


def test_player_separation():
    print("player separation:")
    replay = load_replay(REPLAY_PATH)
    us, opp, opp_name = viewer_index_for_us(replay, "shettynaisha")
    check("us index in {0,1}", us in (0, 1))
    check("opponent index is the other one", opp == 1 - us)
    check("opponent name is not our own name", opp_name != "shettynaisha")


def test_day_aggregation():
    print("day aggregation:")
    replay = load_replay(REPLAY_PATH)
    meta, self_tl, opp_tl = extract_episode_timelines(replay)
    check("30 days extracted", meta["n_days"] == 30)
    check("self and opponent timelines same length", len(self_tl) == len(opp_tl))
    days = [s.day for s in self_tl]
    check("days strictly increasing", days == sorted(set(days)) and len(days) == len(set(days)))
    check("last day is 29", days[-1] == 29)


def test_market_extraction():
    print("market extraction:")
    replay = load_replay(REPLAY_PATH)
    _, self_tl, _ = extract_episode_timelines(replay)
    snap = self_tl[10]
    check("market_inventory has WHEAT", "WHEAT" in snap.market_inventory)
    check("market_prices has MELON", "MELON" in snap.market_prices)
    check("market price is a positive number", snap.market_prices["MELON"] > 0)


def test_worker_extraction():
    print("worker (hands) extraction:")
    replay = load_replay(REPLAY_PATH)
    _, self_tl, opp_tl = extract_episode_timelines(replay)
    check("self hands_count is non-negative for every day", all(s.hands_count >= 0 for s in self_tl))
    check("opponent hands_count is non-negative for every day", all(s.hands_count >= 0 for s in opp_tl))
    # VERIFIED_MECHANIC (vendor_kaggriculture.kaggriculture._end_of_day: farm["hands"] = []
    # every day): hands are NOT persistent hires -- they reset to zero every in-game day and
    # must be re-hired daily (agents/phase2_4/common.py's own HIRE logic already accounts for
    # this, comment: "hands reset daily"). A day-over-day DECREASE in hands_count is therefore
    # expected and legal, not a parsing bug -- this test only asserts hands_count stays within
    # the mechanically possible range, never that it is monotonic.
    check("hands_count never exceeds a plausible daily cap (<=30)",
          all(s.hands_count <= 30 for s in opp_tl))


def test_animal_extraction():
    print("animal extraction:")
    replay = load_replay(REPLAY_PATH)
    _, self_tl, opp_tl = extract_episode_timelines(replay)
    total_animals_over_time = [sum(s.animal_tile_counts.values()) for s in opp_tl]
    check("animal counts are non-negative", all(n >= 0 for n in total_animals_over_time))
    check("animal_tile_counts keys are valid species",
          all(k in ("COW", "SHEEP", "GOOSE") for s in opp_tl for k in s.animal_tile_counts))


def test_crop_extraction():
    print("crop extraction:")
    replay = load_replay(REPLAY_PATH)
    _, self_tl, opp_tl = extract_episode_timelines(replay)
    check("crop_tile_counts keys are valid crops",
          all(k in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON") for s in opp_tl for k in s.crop_tile_counts))
    row = to_day_row(self_tl[15])
    check("to_day_row flattens per-crop tile columns", "tiles_MELON" in row)


def test_no_private_leakage():
    print("no private-state leakage:")
    replay = load_replay(REPLAY_PATH)
    _, self_tl, opp_tl = extract_episode_timelines(replay)
    check("opponent snapshots never carry shed data", all(s.shed is None for s in opp_tl))
    check("opponent snapshots never carry seed data", all(s.seeds is None for s in opp_tl))
    check("opponent snapshots never carry inventory data", all(s.inventories is None for s in opp_tl))
    check("opponent snapshots never carry our own_action field", all(s.own_action is None for s in opp_tl))
    check("self snapshots DO carry private shed data (own side only)",
          all(s.shed is not None for s in self_tl))


def test_own_action_only_self():
    print("own-action extraction stays on our own side:")
    replay = load_replay(REPLAY_PATH)
    _, self_tl, _ = extract_episode_timelines(replay)
    events = infer_sell_events_own(self_tl)
    check("sell/market events extracted from our own actions", isinstance(events, list))
    check("every event has day/op/item/quantity keys",
          all(set(e.keys()) == {"day", "op", "item", "quantity"} for e in events))


def test_deterministic_analysis():
    print("deterministic analysis:")
    replay = load_replay(REPLAY_PATH)
    meta1, self1, opp1 = extract_episode_timelines(replay)
    meta2, self2, opp2 = extract_episode_timelines(replay)
    check("re-parsing the same replay yields identical day counts", meta1["n_days"] == meta2["n_days"])
    check("re-parsing yields identical bank trajectory",
          [s.bank for s in self1] == [s.bank for s in self2])

    rows = [to_day_row(s) for s in opp1]
    v1 = velocities(rows, ["bank", "hands_count"])
    v2 = velocities(rows, ["bank", "hands_count"])
    check("velocity computation is deterministic", v1 == v2)
    check("velocity output has one entry per day", len(v1) == len(rows))


def main():
    test_replay_parsing()
    test_player_separation()
    test_day_aggregation()
    test_market_extraction()
    test_worker_extraction()
    test_animal_extraction()
    test_crop_extraction()
    test_no_private_leakage()
    test_own_action_only_self()
    test_deterministic_analysis()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    return 0 if FAIL_COUNT == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
