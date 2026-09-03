"""
Phase 25: systematic sweep of agents/phase21/portfolio.py's day>=8
STRAWBERRY/WHEAT ratio (Phase 24 picked its ratios by inference from a
single trace, not a sweep -- exactly the mistake Phase 22 found and fixed
for the day<5 opening ratio). Measures HEAD-TO-HEAD performance against
Submission G directly (not isolated money -- this is a competitiveness
question, not a solo-economy one), same 4 development seeds Phase 22 used
for its own screening pass.

Sequential, not full-grid, per the brief's "somewhat independent" framing:
  Pass 1: sweep day 15+ STRAWBERRY fraction, holding day 8-14 fixed at
          Phase 24's own 0.65.
  Pass 2: sweep day 8-14 STRAWBERRY fraction, holding day 15+ fixed at
          Pass 1's winner.
Does NOT touch agents/phase21/portfolio.py directly during the sweep --
monkeypatches _base_crop_fractions via a fresh targets function per
candidate, same technique scripts/phase22/opening_ratio_sweep.py used.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import agents.phase21.portfolio as portfolio_mod  # noqa: E402
from agents.phase21.execution import make_execution_agent  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

DEV_SEEDS = [700000, 700001, 700002, 700003]
STEPS = 720

MELON_OPENING_END_DAY = portfolio_mod.MELON_OPENING_END_DAY


def make_targets_fn(mid_straw_frac, late_straw_frac):
    """Same as portfolio.portfolio_targets, except day 8-14 and day 15+ use
    the given STRAWBERRY fractions (WHEAT = 1 - straw_frac in each window)
    instead of the hardcoded 0.65 / 0.80."""

    def base_crop_fractions(day):
        if day < 5:
            return {"MELON": 0.5, "WHEAT": 0.5}
        if day < MELON_OPENING_END_DAY:
            return {"MELON": 0.35, "STRAWBERRY": 0.45, "WHEAT": 0.20}
        if day < 15:
            return {"STRAWBERRY": mid_straw_frac, "WHEAT": round(1 - mid_straw_frac, 4)}
        return {"STRAWBERRY": late_straw_frac, "WHEAT": round(1 - late_straw_frac, 4)}

    def targets(day, obs, opponent_history):
        crop_fractions = dict(base_crop_fractions(day))
        # opponent-aware shift left dormant during the sweep (threshold > 1.0,
        # unchanged from Phase 24) -- Step 3 checks separately whether to
        # re-enable it, not folded into this ratio sweep.
        t = {
            "n_hands": portfolio_mod._rung_value(day, portfolio_mod._HANDS_RUNGS),
            "land_quadrants": portfolio_mod._rung_value(day, portfolio_mod._LAND_RUNGS),
            "animals": dict(portfolio_mod._rung_value(day, portfolio_mod._ANIMAL_SPECIES_RUNGS)),
            "crop_tile_target": portfolio_mod._rung_value(day, portfolio_mod._CROP_TILE_RUNGS),
            "crop_fractions": crop_fractions,
        }
        if day >= portfolio_mod.LIQUIDATION_START_DAY:
            t["crop_tile_target"] = 0
        if day >= portfolio_mod.DIG_ONGOING_CROPS_DAY:
            t["digging_ongoing"] = True
        return t

    return targets


def make_candidate_agent(mid_frac, late_frac):
    targets_fn = make_targets_fn(mid_frac, late_frac)
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_execution_agent(targets_fn)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    return agent


def run_candidate_vs_g(mid_frac, late_frac, seed):
    agent21 = make_candidate_agent(mid_frac, late_frac)
    agentG = make_macro_agent()
    replay, meta = run_episode(agent21, agentG, STEPS, seed, None)
    return replay["rewards"][0], replay["rewards"][1]


def sweep(label, candidates):
    print(f"\n=== {label} ===")
    results = {}
    for mid_frac, late_frac in candidates:
        rows = []
        for seed in DEV_SEEDS:
            ours, theirs = run_candidate_vs_g(mid_frac, late_frac, seed)
            rows.append((seed, ours, theirs))
        wins = sum(1 for _, o, t in rows if o > t)
        mean_ours = sum(o for _, o, t in rows) / len(rows)
        mean_theirs = sum(t for _, o, t in rows) / len(rows)
        margin = mean_ours - mean_theirs
        results[(mid_frac, late_frac)] = {"rows": rows, "wins": wins, "mean_ours": mean_ours,
                                            "mean_theirs": mean_theirs, "margin": margin}
        print(f"  mid={mid_frac} late={late_frac}: wins={wins}/4  mean_ours=${mean_ours:.0f}  "
              f"mean_theirs=${mean_theirs:.0f}  margin=${margin:+.0f}")
        for seed, o, t in rows:
            print(f"    seed={seed}: ours=${o:.0f} theirs=${t:.0f} {'WIN' if o>t else 'loss'}")
    return results


def main():
    # Pass 1: sweep day 15+ STRAWBERRY fraction, mid (day 8-14) fixed at 0.65 (Phase 24's own).
    pass1_candidates = [(0.65, f) for f in [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]]
    pass1 = sweep("PASS 1: sweep day15+ STRAWBERRY fraction (mid fixed at 0.65)", pass1_candidates)
    best_late = max(pass1, key=lambda k: pass1[k]["margin"])[1]
    print(f"\nBest late-game fraction from Pass 1: {best_late} (margin=${pass1[(0.65, best_late)]['margin']:+.0f})")

    # Pass 2: sweep day 8-14 STRAWBERRY fraction, late fixed at Pass 1's winner.
    pass2_candidates = [(f, best_late) for f in [0.55, 0.60, 0.65, 0.70, 0.75]]
    pass2 = sweep(f"PASS 2: sweep day8-14 STRAWBERRY fraction (late fixed at {best_late})", pass2_candidates)
    best_mid = max(pass2, key=lambda k: pass2[k]["margin"])[0]
    print(f"\nBest mid-game fraction from Pass 2: {best_mid} (margin=${pass2[(best_mid, best_late)]['margin']:+.0f})")

    print(f"\n\n=== FINAL CHOICE: mid={best_mid}, late={best_late} ===")

    import json
    os.makedirs("results/phase25", exist_ok=True)
    out = {
        "pass1": {f"{k[0]}_{k[1]}": v for k, v in pass1.items()},
        "pass2": {f"{k[0]}_{k[1]}": v for k, v in pass2.items()},
        "chosen": {"mid": best_mid, "late": best_late},
    }
    with open("results/phase25/phase25_ratio_sweep.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nWrote results/phase25/phase25_ratio_sweep.json")


if __name__ == "__main__":
    main()
