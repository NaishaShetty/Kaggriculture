"""
Phase 38: market-as-weapon feasibility experiment (docs/FRESH_STRATEGY.md
Reframe 3) -- a controlled, real-engine, two-agent test of whether
deliberately timing a sell to crash a price right before an opponent's
inferred sell actually produces a positive RELATIVE-MARGIN edge, under
PERFECT information about the opponent's sell timing (this phase does not
attempt inference -- see the report's own honest scoping note).

MECHANISM, confirmed by direct read of vendor_kaggriculture/kaggriculture.py
::_process_market (not assumed):
  - Both players' market orders are processed per QUEUE INDEX i (their i-th
    submitted order interleaves with the opponent's i-th order), and for
    SELL/BUY orders at the same index, price is re-quoted UNIT BY UNIT.
  - The code's own comment confirms it directly: "Both players see the same
    pre-commit inventory for this unit" -- within one unit-round, BOTH
    players' current-unit price is quoted from the SAME starting inventory,
    THEN both commit. This means if A and B submit an equal-sized SELL order
    for the SAME item in the SAME turn (both landing at queue-index 0, their
    only market order that turn), they experience an IDENTICAL price
    sequence, unit for unit -- a same-turn, same-size mutual crash should be
    close to a wash BY CONSTRUCTION, not a win for either side. This is a
    concrete, testable prediction, not an assumption.
  - market["inventory"][item] does NOT decay or reset between turns on its
    own (confirmed: the only mutations found via direct grep for
    `"inventory"]` are SELL/BUY commits and a small periodic town-shop/
    town-center consumption trickle, `_town_consume`, every 4-24 steps) --
    a price crash PERSISTS across turns until either side's future BUY
    activity or the slow town trickle erodes it. This means a PRE-EMPTIVE
    sell (a turn before the target's own sell) should carry its crash
    forward largely intact, unlike a same-turn simultaneous sell.

EXPERIMENT DESIGN: two single-crop STRAWBERRY producers (matching Phase 21
Step 1 / Phase 31's own glut-experiment scale: 8 hands, 2 land quadrants;
crop_tile_target reduced to 20 here, not 40, specifically to keep
accumulated shed inventory comfortably under the 100-unit shed cap during
the deliberate holding window this experiment needs -- STRAWBERRY chosen
because it is the most glut-sensitive crop this project's own market
constants show, T=100, the smallest depth parameter of any crop, giving the
clearest possible signal for this test).

Agent A (the "target"): grows normally, but its execution layer's own SELL
order for STRAWBERRY is EXTERNALLY GATED -- suppressed every turn before a
fixed, known DUMP_TURN, then allowed through unmodified from DUMP_TURN
onward (the underlying execution layer already emits a SELL order for its
FULL held shed stock every turn it has any -- gating just controls WHEN that
order is allowed to fire, not what it contains). This is what "a PREDICTABLE
harvest/sell schedule you control directly" means here -- A's dump turn is
fixed by this script, not inferred.

Agent B (the "attacker" under test) -- three variants, same gating
mechanism, same production scale as A:
  - CONTROL: dump_turn=0 (i.e. never held -- sells naturally/continuously
    from turn 0, the standard, uncoordinated behavior every agent in this
    project already uses).
  - ATTACK_SAME_TURN: dump_turn = A's own DUMP_TURN (simultaneous lump sell,
    same queue index -- tests the "should be a wash" prediction above).
  - ATTACK_PREEMPT: dump_turn = A's DUMP_TURN minus 24 turns (one full day
    earlier) -- B's batch clears at the UNCRASHED price, then A's identical
    batch sells into the market B already pushed up.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.execution import make_execution_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]

CROP = "STRAWBERRY"
N_HANDS = 8
LAND_QUADRANTS = 2
CROP_TILE_TARGET = 20  # reduced from Phase 21/31's 40 -- keeps held inventory under the 100-unit shed cap

A_DUMP_DAY = 18
A_DUMP_TURN = A_DUMP_DAY * 24 + 12  # mid-day, turn 444
PREEMPT_TURN = A_DUMP_TURN - 24  # exactly one day earlier, turn 420

OUT_ROOT = "results/phase38"


def make_gated_single_crop_agent(dump_turn):
    """dump_turn=0 means "never gated" (sells naturally from turn 0, i.e.
    CONTROL). Otherwise: strips any SELL order for CROP on turns before
    dump_turn (letting shed inventory accumulate); from dump_turn onward,
    the underlying agent's own SELL-full-shed behavior is left unmodified."""
    def targets(day, obs, opponent_history):
        return {
            "n_hands": N_HANDS, "land_quadrants": LAND_QUADRANTS, "animals": {},
            "crop_tile_target": CROP_TILE_TARGET, "crop_fractions": {CROP: 1.0},
        }
    base_agent = make_execution_agent(targets)

    def agent(obs):
        action = base_agent(obs)
        turn = obs["day"] * 24 + obs.get("hour", 0)
        if dump_turn > 0 and turn < dump_turn:
            action["market"] = [o for o in action["market"] if not (isinstance(o, list) and len(o) > 1 and o[0] == "SELL" and o[1] == CROP)]
        return action
    return agent


def run_condition(label, b_dump_turn):
    rows = []
    for seed in DEV_SEEDS:
        agent_a = make_gated_single_crop_agent(A_DUMP_TURN)
        agent_b = make_gated_single_crop_agent(b_dump_turn)
        record, replay, extracted = run_and_analyze(agent_a, agent_b, STEPS, seed, "phase38_market_weapon", f"{label}_seed{seed}")
        a_money = record["outcome"]["final_money"][0]
        b_money = record["outcome"]["final_money"][1]
        txn_a = record["players"][0]["market_transaction_summary"].get(f"SELL:{CROP}", {})
        txn_b = record["players"][1]["market_transaction_summary"].get(f"SELL:{CROP}", {})
        rows.append({
            "seed": seed, "a_final_money": a_money, "b_final_money": b_money,
            "margin_a_minus_b": a_money - b_money,
            "a_sell_revenue": txn_a.get("total_value", 0.0), "a_sell_qty": txn_a.get("total_quantity", 0),
            "a_avg_price": txn_a.get("avg_realized_price"),
            "b_sell_revenue": txn_b.get("total_value", 0.0), "b_sell_qty": txn_b.get("total_quantity", 0),
            "b_avg_price": txn_b.get("avg_realized_price"),
        })
        print(f"  [{label}] seed={seed}: A=${a_money:,.0f} (qty={txn_a.get('total_quantity',0)}, avg=${txn_a.get('avg_realized_price')}) "
              f"B=${b_money:,.0f} (qty={txn_b.get('total_quantity',0)}, avg=${txn_b.get('avg_realized_price')}) "
              f"margin(A-B)=${a_money-b_money:,.0f}", flush=True)
    mean_a = sum(r["a_final_money"] for r in rows) / len(rows)
    mean_b = sum(r["b_final_money"] for r in rows) / len(rows)
    mean_margin = sum(r["margin_a_minus_b"] for r in rows) / len(rows)
    print(f"  [{label}] MEAN A=${mean_a:,.2f}  MEAN B=${mean_b:,.2f}  MEAN margin(A-B)=${mean_margin:,.2f}\n")
    return {"label": label, "rows": rows, "mean_a": mean_a, "mean_b": mean_b, "mean_margin_a_minus_b": mean_margin}


def main():
    print(f"A always dumps at turn {A_DUMP_TURN} (day {A_DUMP_DAY}). "
          f"Preempt turn = {PREEMPT_TURN} (day {PREEMPT_TURN // 24}).\n")

    results = {}
    print("=== CONTROL: B sells naturally (no coordination with A's dump) ===")
    results["control"] = run_condition("control", 0)

    print("=== ATTACK_SAME_TURN: B dumps on the SAME turn as A ===")
    results["attack_same_turn"] = run_condition("attack_same_turn", A_DUMP_TURN)

    print("=== ATTACK_PREEMPT: B dumps ONE DAY BEFORE A ===")
    results["attack_preempt"] = run_condition("attack_preempt", PREEMPT_TURN)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase38_market_weapon_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {OUT_ROOT}/phase38_market_weapon_results.json")

    print("\n=== SUMMARY ===")
    control_margin = results["control"]["mean_margin_a_minus_b"]
    for label in ["control", "attack_same_turn", "attack_preempt"]:
        r = results[label]
        delta_margin_for_b = -(r["mean_margin_a_minus_b"] - control_margin)  # positive = B relatively better off than in control
        print(f"  {label}: mean A=${r['mean_a']:,.2f}  mean B=${r['mean_b']:,.2f}  margin(A-B)=${r['mean_margin_a_minus_b']:,.2f}  "
              f"[B's relative-margin gain vs. control: ${delta_margin_for_b:+,.2f}]")


if __name__ == "__main__":
    main()
