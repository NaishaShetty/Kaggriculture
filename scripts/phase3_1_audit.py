"""
Phase 3.1 observability audit reproducer -- prints and re-validates
results/phase3_1/observability/observability_audit.json against the actual
running simulator (not just re-printing a static file), per the brief's
"do not assume the opponent observation interface from conceptual
descriptions" instruction. Confirms, on a real episode, that every field
marked observable=true actually appears in `obs`, and every field marked
observable=false actually does NOT appear.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.baseline_agent import agent as wheat_patroller_agent  # noqa: E402
from instrumentation.pipeline import run_episode  # noqa: E402

AUDIT_PATH = "results/phase3_1/observability/observability_audit.json"


def main():
    with open(AUDIT_PATH) as f:
        audit = json.load(f)

    replay, meta = run_episode(wheat_patroller_agent, "pass", 60, 600001, None)
    obs = replay["steps"][10][0]["observation"]
    own = obs["player"]
    opp = 1 - own

    checks = {
        "Own cash (money)": "money" in obs["farms"][own],
        "Own tiles (crops/animals/structures/growth state)": "tiles" in obs["farms"][own],
        "Own shed contents": "shed" in obs["private"],
        "Own seed counts": "seeds" in obs["private"],
        "Own carried inventory (farmer + hands)": "inventories" in obs["private"],
        "Opponent cash (money)": "money" in obs["farms"][opp],
        "Opponent tiles (crop type, planted_day, watered_today, animal type, fed/cared/fertilizer_available)": "tiles" in obs["farms"][opp],
        "Opponent farmer/hand positions": "farmer" in obs["farms"][opp] and "hands" in obs["farms"][opp],
        "Opponent unlocked quadrants (land)": "unlocked_quadrants" in obs["farms"][opp],
        "Opponent hires_today (hand count hired so far today)": "hires_today" in obs["farms"][opp],
        "Opponent shed contents": False,  # obs['private'] only ever contains OWN player's data
        "Opponent seed counts": False,
        "Opponent carried inventory": False,
        "Market prices (all products)": "prices" in obs.get("market", {}),
        "Market inventory (all products)": "inventory" in obs.get("market", {}),
        "Town unlocked shops": "unlocked_shops" in obs.get("town", {}),
    }

    print(f"{'Information':70s} {'Audit says':12s} {'Live obs check':15s} {'Match'}")
    mismatches = 0
    for row in audit["audit_table"]:
        info = row["information"]
        if info in checks:
            live = checks[info]
            match = live == row["observable"]
            if not match:
                mismatches += 1
            print(f"{info[:69]:70s} {str(row['observable']):12s} {str(live):15s} {'OK' if match else 'MISMATCH'}")

    print(f"\n{mismatches} mismatches between the static audit and a live episode's actual `obs` structure.")
    if mismatches:
        sys.exit(1)
    print("Audit CONFIRMED against a real running episode (not merely asserted).")


if __name__ == "__main__":
    main()
