"""
Phase 34 Part B, Steps 6-8: CARROT as a late-game market-rotation crop,
tested the REALISTIC way -- 25 days of actual prior WHEAT/STRAWBERRY selling
pressure (agents/phase21/'s own current portfolio playing out normally
against a real opponent, not a fresh isolated market), then two
continuations compared from day 25 onward.

Step 6 (confirmed directly from both downloaded gold-tier replays, not
trusted from the prompt -- see results/phase34/phase34_trajectory_gold_*.json
and the Phase 34 report):
  - 105373474 (Crop Dusta vs. Jesse Bullard): CARROT surges from day 21 (17
    tiles) to a peak of 49 (day 25-26), fully liquidated to 2 by day 29.
    STRAWBERRY's market price crashes hard in the days just before/during the
    switch (day15 $192 -> day19 $105 -> day20 $45 -> day21 $1) -- a REAL,
    visible glut. WHEAT stays flat (~$35) throughout.
  - 105341441 (Crop Dusta vs. Knight of Favonius): CARROT surge is much
    smaller (starts day 26, only 6 tiles, never grows further), liquidated
    by day 29. STRAWBERRY's price does NOT crash here (stays $194-242
    throughout) -- the rotation still happens, just smaller, suggesting
    endgame tile-availability (STRAWBERRY's own planting cutoff freeing
    tiles) matters at least as much as price depression.

Step 7: agents/phase21/portfolio.py::portfolio_targets is reused UNCHANGED
for days 0-24 in BOTH conditions (same seed, same opponent -- the first 25
days play out identically, generating the SAME real prior selling pressure
in both). From day 25 (matching the earlier gold episode's actual rotation
start) through CARROT's own planting_cutoff_day (agents/phase21/liquidation.py
::planting_cutoff_day("CARROT"), COMPUTED not assumed), condition (b)
redirects ALL newly-vacant tile allocation to CARROT; condition (a) is the
unmodified baseline (agents/phase21/portfolio.py's own day>=20 all-WHEAT
default). Both conditions run through the real engine against
agents/phase15/'s Submission G (make_macro_agent, as shipped) for the same
real market pressure this project's standard validation uses.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase21.execution import make_execution_agent  # noqa: E402
from agents.phase21.liquidation import planting_cutoff_day  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase34"

CARROT_ROTATION_START_DAY = 25
CARROT_CUTOFF = planting_cutoff_day("CARROT")
print(f"CARROT planting_cutoff_day (computed, not assumed) = {CARROT_CUTOFF}")


def carrot_rotation_targets(day, obs, opponent_history=None):
    t = portfolio_targets(day, obs, opponent_history)
    if CARROT_ROTATION_START_DAY <= day <= CARROT_CUTOFF:
        t = dict(t)
        t["crop_fractions"] = {"CARROT": 1.0}
    return t


def make_agent(target_fn):
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_execution_agent(target_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_condition(label, target_fn):
    rows = []
    for seed in DEV_SEEDS:
        agent = make_agent(target_fn)
        opp = make_macro_agent()
        replay, meta = run_episode(agent, opp, STEPS, seed, None)
        o, t = replay["rewards"][0], replay["rewards"][1]
        rows.append({"seed": seed, "phase21": o, "submission_g": t, "winner": "phase21" if o > t else ("tie" if o == t else "submission_g")})
        print(f"  [{label}] seed={seed}: phase21=${o:,.2f}  submission_g=${t:,.2f}  winner={rows[-1]['winner']}", flush=True)
    wins = sum(1 for r in rows if r["winner"] == "phase21")
    mean_ours = sum(r["phase21"] for r in rows) / len(rows)
    print(f"  [{label}] Record: {wins}/{len(rows)}  Mean phase21=${mean_ours:,.2f}\n")
    return {"label": label, "rows": rows, "wins": wins, "mean_phase21": mean_ours}


def main():
    print("=== Condition (a): baseline, unmodified agents/phase21/ (Submission H) ===")
    results_a = run_condition("baseline", portfolio_targets)

    print("=== Condition (b): CARROT rotation from day 25 through day", CARROT_CUTOFF, "===")
    results_b = run_condition("carrot_rotation", carrot_rotation_targets)

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase34_carrot_rotation_results.json"), "w") as f:
        json.dump({"baseline": results_a, "carrot_rotation": results_b, "carrot_cutoff_day": CARROT_CUTOFF}, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase34_carrot_rotation_results.json")

    print(f"\n=== SUMMARY ===")
    print(f"  baseline:        {results_a['wins']}/4  mean=${results_a['mean_phase21']:,.2f}")
    print(f"  carrot_rotation: {results_b['wins']}/4  mean=${results_b['mean_phase21']:,.2f}")
    delta = results_b['mean_phase21'] - results_a['mean_phase21']
    print(f"  delta: ${delta:+,.2f} ({delta / results_a['mean_phase21'] * 100:+.1f}%)")


if __name__ == "__main__":
    main()
