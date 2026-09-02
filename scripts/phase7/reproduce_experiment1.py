"""
Phase 7, Experiment 1 (per results/phase6/PHASE6_COMPETITIVE_META_FORENSICS_REPORT.md
Section 17, item 1): reproduce the Lai Eu Wen freeze conditions -- an early,
sustained MELON market glut that pushes price below MELON's base ($250) and
keeps it there, while our own agent accumulates harvested MELON in its shed
under a threshold sell policy that never re-triggers -- and confirm whether
the fix (agents/phase2_6/common.py's import) changes the outcome.

DESIGN NOTE (why this is a fixed-config tactical-layer test, not a full
Submission C run): an earlier version of this script ran the FULL Submission
C stack (Planner v1's adaptive decision loop + Variant D + the scaling
response + the animal response) against a synthetic MELON-heavy opponent.
That reproduced 0 SELL orders, but for the WRONG reason -- the adaptive
planner's own response to that specific synthetic opponent drove our own
hands to 0 and cash to $0 by day 7 (a pre-existing early-collapse pattern,
matching NEW-F-005 from Phase 3.7, not the "harvest succeeds but selling
freezes" mechanism Phase 6 diagnosed). That is a DIFFERENT bug and would
have been a false-positive reproduction. This version instead calls
`agents.phase2_6.common`'s OWN `make_agent_24` symbol directly (whichever
module it currently resolves to -- agents.phase2_4.common on unpatched code,
agents.phase2_5.common after the Phase 7 fix -- so this script automatically
exercises exactly the code path the fix changes) with a FIXED, realistic
config (mirrors the config Phase 3.3's own code comments describe as
"Planner v1 already independently chooses ... for a simple MELON-solo
portfolio": threshold selling, threshold_frac=1.0, horizon_aware=True) that
guarantees hands are hired and MELON is harvested, isolating the ONE
mechanism this phase's fix targets.

Usage: python scripts/phase7/reproduce_experiment1.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import agents.phase2_6.common as p26  # noqa: E402 -- read make_agent_24 dynamically, see design note above
from agents.phase2_3.common import make_agent as make_agent_23  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

STEPS = 720
SEED = 900001  # disjoint from every seed range used elsewhere in this project (all below 900000)

FIXED_CONFIG = {
    "crops": {"MELON": 1.0}, "n_hands": 1, "land_quadrants": 1, "land_buy_day": 0,
    "plant_delay_day": 18,
    "sell_policy": {"mode": "threshold", "threshold_frac": 1.0, "horizon_aware": True},
}
# n_hands deliberately kept low (1): the Lai Eu Wen freeze accumulated only 54-59 shed
# units over the whole game, well under SHED_CAPACITY(100)*overflow_safety_frac(0.85)=85
# -- a faster-producing config (e.g. n_hands=2) hits that overflow valve and force-sells
# before ever reaching the specific "held indefinitely, safety net never fires" condition
# this experiment targets (confirmed: an n_hands=2 version of this script reached shed=100
# and force-sold twice via the EXISTING overflow_safety mechanism, not via horizon_aware --
# a different, already-working mitigation, not the one this phase's fix is about).


def our_agent():
    """Exactly what agents/phase2_6/common.py's own agent(obs) does at its
    tactical call site (line 139: `make_agent_24(**config)` then
    `tactical_agent(obs)`), but with a FIXED config instead of Planner v1's
    adaptive decision loop -- isolating the sell-safety mechanism alone."""
    tactical_agent = p26.make_agent_24(**FIXED_CONFIG)
    return tactical_agent


def melon_glut_opponent():
    """A synthetic opponent producing MELON at a scale that, combined with
    our own MELON production under the same fixed config, keeps the shared
    market price below MELON's $250 base for a sustained stretch --
    reusing an already-validated archetype-building tool
    (agents/phase2_3/common.py::make_agent), no new mechanic invented."""
    return make_agent_23(crops="MELON", n_hands=3, land_quadrants=1, land_buy_day=0)


def count_our_sell_orders(replay, our_player_index):
    steps = replay["steps"]
    sell_count = 0
    sell_log = []
    for step in steps:
        action = step[our_player_index].get("action") or {}
        for order in action.get("market", []) or []:
            if order and order[0] == "SELL":
                sell_count += 1
                obs = step[our_player_index]["observation"]
                sell_log.append({"day": obs["day"], "hour": obs.get("hour", 0), "order": order})
    return sell_count, sell_log


def main():
    protagonist = our_agent()
    opponent = melon_glut_opponent()

    record, replay, extracted = run_and_analyze(protagonist, opponent, STEPS, SEED,
                                                 "phase7_experiment1_reproduction", f"seed{SEED}")

    our_idx = 0
    sell_count, sell_log = count_our_sell_orders(replay, our_idx)

    final_obs = replay["steps"][-1][our_idx]["observation"]
    final_shed = final_obs["private"]["shed"]
    final_shed_total = sum(final_shed.values())
    final_money = final_obs["farms"][our_idx]["money"]
    opp_final_money = final_obs["farms"][1 - our_idx]["money"]

    max_shed_ever = 0
    max_shed_day = None
    for step in replay["steps"]:
        obs = step[our_idx]["observation"]
        shed_total = sum(obs["private"]["shed"].values())
        if shed_total > max_shed_ever:
            max_shed_ever = shed_total
            max_shed_day = obs["day"]

    melon_price_history = [(s[our_idx]["observation"]["day"], s[our_idx]["observation"]["market"]["prices"].get("MELON"))
                            for s in replay["steps"][::24]]

    print(f"agents.phase2_6.common.make_agent_24 currently resolves to: {p26.make_agent_24.__module__}")
    print(f"seed={SEED}")
    print(f"our SELL orders issued across all {STEPS} turns: {sell_count}")
    print(f"max shed inventory reached at any point: {max_shed_ever} (day {max_shed_day})")
    print(f"our final shed contents: {final_shed}")
    print(f"our final shed total (unsold units): {final_shed_total}")
    print(f"our final money: ${final_money}")
    print(f"opponent final money: ${opp_final_money}")
    print(f"MELON price by day (sampled every 24 turns): {melon_price_history}")
    if sell_log:
        print(f"first SELL order: {sell_log[0]}")
        print(f"last SELL order: {sell_log[-1]}")
    else:
        print("NO SELL orders issued at any point in the episode.")

    accumulated_but_stuck = max_shed_ever > 0 and sell_count == 0
    print(f"\nFREEZE REPRODUCED (production accumulated in shed, 0 sells ever): {accumulated_but_stuck}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
