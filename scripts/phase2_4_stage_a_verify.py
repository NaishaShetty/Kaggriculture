"""
Phase 2.4 Stage A -- Market Mechanics Discovery.

Deliberately cheap: the price formula itself is already fully DOCUMENTED
(docs/00_official_overview_raw.md) and was already VERIFIED once, in Phase 1,
by direct source-code reading. Stage A's job is to re-confirm that
verification holds against real, freshly-generated Phase 2.4 gameplay (not
just re-cite Phase 1), and to add the one genuinely new empirical question
Phase 1/2.2/2.3 never isolated: whether price "recovery" after a player sale
is driven ENTIRELY by town consumption (the documented mechanic) with zero
unexplained drift, quantified per product.

Two parts:
  A1. Formula re-verification: run one fresh multi-resource episode (reuses
      the Phase 2.3 framework's own passive-selling agent, sell_policy
      irrelevant to this check), then recompute market_price(item, inv) from
      the OFFICIAL, documented, VERIFIED formula for every recorded
      (inventory, price) pair across the whole episode and diff against the
      observed price. Zero mismatches = formula VERIFIED (not just DOCUMENTED)
      against Phase 2.4-generated data specifically.
  A2. Town-driven recovery isolation: after an agent's LAST sale of a given
      item, track that item's price for the remainder of the episode and
      cross-reference every inventory change against the deterministic town
      consumption schedule (shop_sell_interval / center_sell_interval,
      VERIFIED in Phase 1) -- if the two account for 100% of the delta, the
      "recovery is entirely town-driven" hypothesis is a VALIDATED FINDING,
      not an assumption.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_4.common import make_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from vendor_kaggriculture.kaggriculture import market_price, MARKET_PARAMS, SHOPS  # noqa: E402

OUT_ROOT = "results/phase2_4"
STEPS = 720


def part_a1(record):
    mh = record["market_history"]
    checked = mismatches = 0
    for rec in mh:
        inv, prices = rec["inventory"], rec["prices"]
        for item in prices:
            predicted = market_price(item, inv[item])
            checked += 1
            if predicted != prices[item]:
                mismatches += 1
    return {"checked": checked, "mismatches": mismatches, "verified": mismatches == 0}


def part_a2(record, extracted, player=0):
    """For each product, after the agent's LAST SELL/BUY_PRODUCT turn, verify
    every subsequent inventory delta is exactly explained by town consumption."""
    mh = record["market_history"]
    th = record["town_history"]
    txns = record["players"][player]["financial_transactions"]

    last_player_turn = {}
    for t in txns:
        if t["type"] in ("SELL", "BUY_PRODUCT"):
            last_player_turn[t["item"]] = max(last_player_turn.get(t["item"], -1), t["turn"])

    town_by_turn = {rec["turn"]: rec["unlocked_shops"] for rec in th}
    results = {}
    for item in MARKET_PARAMS:
        last_turn = last_player_turn.get(item, -1)
        post = [rec for rec in mh if rec["turn"] > last_turn]
        if len(post) < 2:
            continue
        explained, total_checks, unexplained_examples = 0, 0, []
        for i in range(1, len(post)):
            prev_inv, cur_inv = post[i - 1]["inventory"][item], post[i]["inventory"][item]
            delta = cur_inv - prev_inv
            turn = post[i]["turn"]
            # `_town_consume(env, state, step)` fires using the engine's `step` counter BEFORE
            # this record's turn index is incremented (same steps[t]-stores-result-of-action-at-t
            # replay-indexing pattern documented in docs/PHASE2_1_ARCHITECTURE.md section 2) --
            # empirically confirmed here: every mismatch before this fix was exactly a turn-1 shift
            # (see the Stage A report section on this verification for the raw before/after evidence).
            check_turn = turn - 1
            shops = town_by_turn.get(check_turn, [])
            expected_town_delta = 0
            if check_turn % 4 == 0:  # townShopSellInterval default
                for shop in shops:
                    products = SHOPS[shop]
                    if item in products:
                        expected_town_delta -= 2 if len(products) == 1 else 1
            if check_turn % 24 == 0 and item != "FERTILIZER":  # townCenterSellInterval default
                expected_town_delta -= 1
            total_checks += 1
            if delta == expected_town_delta:
                explained += 1
            elif len(unexplained_examples) < 3:
                unexplained_examples.append({"turn": turn, "observed_delta": delta, "expected_town_delta": expected_town_delta})
        results[item] = {
            "last_player_txn_turn": last_turn, "turns_checked": total_checks,
            "fully_town_explained": explained, "unexplained_examples": unexplained_examples,
            "verified": explained == total_checks,
        }
    return results


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    agent = make_agent(crops={"WHEAT": 0.3, "MELON": 0.7}, n_hands=2, animals={"GOOSE": 1, "COW": 1},
                        animal_buy_day=0, sell_policy={"mode": "passive"})
    record, replay, extracted = run_and_analyze(agent, "pass", STEPS, 200001, "stageA", "verify")

    a1 = part_a1(record)
    a2 = part_a2(record, extracted)

    out = {"a1_formula_reverification": a1, "a2_town_driven_recovery": a2}
    with open(os.path.join(OUT_ROOT, "stage_a_verification.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)

    print("A1 (price formula):", a1)
    print("A2 (town-driven recovery), per product:")
    for item, r in a2.items():
        print(f"  {item}: {r['fully_town_explained']}/{r['turns_checked']} turns fully explained by town "
              f"consumption alone (verified={r['verified']})")


if __name__ == "__main__":
    main()
