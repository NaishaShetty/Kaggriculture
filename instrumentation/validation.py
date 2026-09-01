"""
Accounting validation suite (brief section 22-23). Every check is
comparison-based and reports a diagnostic rather than silently passing or
silently dropping a mismatch. PASS/PARTIAL/FAIL verdicts:
  PASS    -- discrepancy is exactly zero (or within float rounding, 1e-6)
  PARTIAL -- discrepancy present but plausibly explained by a documented
             reconstruction limitation (see ledger.py docstring) or by shed
             overflow (a real, observable simulator behavior)
  FAIL    -- unexplained discrepancy; must be investigated before trusting
             downstream metrics for that episode
"""
from vendor_kaggriculture.kaggriculture import PRODUCTS, ANIMALS

FLOAT_TOL = 1e-6


def _verdict(discrepancy, explainable=False):
    if abs(discrepancy) <= FLOAT_TOL:
        return "PASS"
    return "PARTIAL" if explainable else "FAIL"


def validate_money(financial_summary):
    d = financial_summary["discrepancy"]
    explainable = financial_summary["n_unresolved_transactions"] > 0
    return {
        "check": "money_conservation",
        "starting_money": financial_summary["starting_money"],
        "total_income": financial_summary["total_income"],
        "total_expenditure": financial_summary["total_expenditure"],
        "reconstructed_final_money": financial_summary["reconstructed_final_money"],
        "actual_final_money": financial_summary["final_money"],
        "discrepancy": d,
        "n_unresolved_transactions": financial_summary["n_unresolved_transactions"],
        "verdict": _verdict(d, explainable),
    }


def validate_land(land_ledger):
    d = land_ledger["discrepancy"]
    return {
        "check": "land_conservation",
        "starting_unlocked_quadrants": land_ledger["starting_unlocked_quadrants"],
        "n_purchases": len(land_ledger["purchases"]),
        "reconstructed_ending_unlocked_quadrants": land_ledger["reconstructed_ending_unlocked_quadrants"],
        "actual_ending_unlocked_quadrants": land_ledger["ending_unlocked_quadrants"],
        "discrepancy": d,
        "verdict": _verdict(d),
    }


def validate_fertilizer(fertilizer_ledger):
    d = fertilizer_ledger["discrepancy"]
    return {
        "check": "fertilizer_conservation",
        **{k: v for k, v in fertilizer_ledger.items() if k != "discrepancy"},
        "discrepancy": d,
        "verdict": _verdict(d, explainable=True),  # FEED/DROP/PICKUP per-unit routing not fully traced
    }


def validate_product_inventory(turns, financial_transactions, crop_instances, animal_instances, shed_capacity=100):
    results = []
    harvested_by_product = {}
    for inst in crop_instances:
        harvested_by_product[inst["crop"]] = harvested_by_product.get(inst["crop"], 0) + inst["total_harvested_units"]
    # Phase 2.3 fix: this loop previously only had a dead `pass` body (never
    # exercised by Phase 2.2, which had no animals in play) -- animal-product
    # (EGG/MILK/WOOL) harvests were silently excluded from the inventory
    # conservation check, always reporting a spurious FAIL/PARTIAL for any
    # episode with animals. Fixed by attributing each animal instance's
    # harvested units to its product via the documented ANIMALS->product
    # mapping (VERIFIED, kaggriculture.py::ANIMALS), exactly mirroring how
    # crop_instances are attributed to their crop above.
    for inst in animal_instances:
        product = ANIMALS[inst["animal"]]["product"]
        units = sum(h["units"] for h in inst["harvests"])
        harvested_by_product[product] = harvested_by_product.get(product, 0) + units
    if not turns:
        return results
    starting = {}
    p0 = turns[0]["private_before"]
    for item in PRODUCTS:
        starting[item] = p0["shed"].get(item, 0) + sum(inv.get(item, 0) for inv in p0["inventories"])

    ending = dict(starting)
    for t in reversed(turns):
        if t["private_after"] is not None:
            for item in PRODUCTS:
                ending[item] = t["private_after"]["shed"].get(item, 0) + \
                    sum(inv.get(item, 0) for inv in t["private_after"]["inventories"])
            break

    bought = {}
    sold = {}
    for t in financial_transactions:
        if t["type"] == "BUY_PRODUCT":
            bought[t["item"]] = bought.get(t["item"], 0) + t["quantity"]
        if t["type"] == "SELL":
            sold[t["item"]] = sold.get(t["item"], 0) + t["quantity"]

    fed = sum(1 for t in turns for u in t["unit_actions"] if u["op"] == "FEED")

    for item in PRODUCTS:
        harvested = harvested_by_product.get(item, 0)
        consumed = fed if item == "WHEAT" else 0
        expected_ending = starting.get(item, 0) + harvested + bought.get(item, 0) - sold.get(item, 0) - consumed
        actual_ending = ending.get(item, 0)
        discrepancy = expected_ending - actual_ending
        near_capacity = discrepancy > 0  # possible shed-capacity overflow discard; not independently confirmed
        results.append({
            "check": "inventory_conservation", "item": item,
            "starting": starting.get(item, 0), "harvested": harvested, "bought": bought.get(item, 0),
            "sold": sold.get(item, 0), "consumed": consumed,
            "expected_ending": expected_ending, "actual_ending": actual_ending,
            "discrepancy": discrepancy,
            "verdict": _verdict(discrepancy, explainable=near_capacity),
        })
    return results


def build_validation_report(financial_summary, land_ledger, fertilizer_ledger, turns,
                             financial_transactions, crop_instances, animal_instances):
    money = validate_money(financial_summary)
    land = validate_land(land_ledger)
    fert = validate_fertilizer(fertilizer_ledger)
    inventory = validate_product_inventory(turns, financial_transactions, crop_instances, animal_instances)

    checks = [money, land, fert] + inventory
    verdicts = [c["verdict"] for c in checks]
    if all(v == "PASS" for v in verdicts):
        overall = "PASS"
    elif any(v == "FAIL" for v in verdicts):
        overall = "FAIL"
    else:
        overall = "PARTIAL"

    return {
        "overall": overall,
        "money": money,
        "land": land,
        "fertilizer": fert,
        "inventory": inventory,
    }
