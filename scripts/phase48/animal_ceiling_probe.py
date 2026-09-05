"""
Phase 48 Part C: extends Phase 46's capacity_probe.py-style instrumentation
(reused pattern, not rebuilt from scratch -- same imported primitives, same
composition idea of wrapping the ALREADY-VALIDATED execution layer with a
pure-measurement `turn_log`) to measure the STEADY-STATE sustainable animal
count under Submission J's own execution layer (scripts/phase46/
feed_priority_execution.py + agents/phase21/portfolio.py::portfolio_targets,
unmodified -- exactly what's packaged for Submission J), not just the final
day-29 count Phase 41/45 already looked at.

METHOD: track owned-animal count (tiles with an "animal" key -- the same
direct-state check capacity_probe.py and Phase 33 Section 10 both already
use) at the END of every day, for the full 30-day episode, isolated (vs.
"pass") and vs. Submission G. "Steady state" is defined as the mean owned
count over the LAST 10 days (day 20-29 inclusive) -- late enough that the
target rungs have all fully kicked in (the last rung fires day 11) and any
early-game purchase ramp-up transient has settled, but not just the single
final-day snapshot Phase 41 flagged as an open question. Cumulative
purchases (summed BUY_ANIMAL quantities from the agent's own emitted market
actions) and cumulative escapes (inferred as
max(0, cumulative_purchases - owned_count_now) at each day boundary, i.e.
every animal not currently owned and not explained by a still-pending
in-flight purchase must have escaped, since this engine has no other animal
"exit" -- no SELL for live animals, only their products) are also tracked so
purchases-vs-escapes equilibrium is visible directly, not just inferred from
a flat owned-count line.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets, _ANIMAL_SPECIES_RUNGS  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from scripts.phase46.feed_priority_execution import make_feed_priority_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
TURNS_PER_DAY = 24
DEV_SEEDS = [700000, 700001, 700002, 700003]
OUT_ROOT = "results/phase48"


def owned_animal_counts(obs):
    tiles = obs["farms"][0]["tiles"]
    counts = {}
    for row in tiles:
        for tt in row:
            if isinstance(tt, dict) and "animal" in tt:
                a = tt["animal"]
                counts[a] = counts.get(a, 0) + 1
    return counts


def run_one_with_perday_purchases(seed, opponent_label):
    """Same as run_one but tracks purchases with the day they happened, so
    cumulative-at-day-N purchases and escapes-at-day-N can both be computed."""
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_feed_priority_execution_agent(portfolio_targets)
    purchase_events = []  # (day, species, qty)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        result = execution_agent(obs)
        for entry in result.get("market", []):
            if entry and entry[0] == "BUY_ANIMAL":
                purchase_events.append((obs["day"], entry[1], entry[2]))
        return result

    opponent = "pass" if opponent_label == "pass" else make_macro_agent()
    replay, meta = run_episode(agent, opponent, STEPS, seed, None)

    daily = []
    for day in range(30):
        t = day * TURNS_PER_DAY + (TURNS_PER_DAY - 1)
        if t >= len(replay["steps"]):
            break
        # accumulate all purchases with day <= this day (recomputed fresh each iteration
        # is wasteful but STEPS/30 is small; clarity over micro-efficiency here)
        cum_by_species = {}
        for d2, species, qty in purchase_events:
            if d2 <= day:
                cum_by_species[species] = cum_by_species.get(species, 0) + qty
        obs = replay["steps"][t][0]["observation"]
        counts = owned_animal_counts(obs)
        total_owned = sum(counts.values())
        total_purchased = sum(cum_by_species.values())
        escaped_est = max(0, total_purchased - total_owned)
        daily.append({
            "day": day, "counts": dict(counts), "total_owned": total_owned,
            "cum_purchased_by_species": dict(cum_by_species), "total_purchased": total_purchased,
            "escaped_est": escaped_est,
        })
    return daily


def summarize_condition(label, opponent_label, seeds=DEV_SEEDS):
    all_rows = []
    for seed in seeds:
        daily = run_one_with_perday_purchases(seed, opponent_label)
        final_owned = daily[-1]["total_owned"] if daily else 0
        steady_days = [d for d in daily if 20 <= d["day"] <= 29]
        steady_mean = sum(d["total_owned"] for d in steady_days) / len(steady_days) if steady_days else 0.0
        final_purchased = daily[-1]["total_purchased"] if daily else 0
        final_escaped = daily[-1]["escaped_est"] if daily else 0
        row = {
            "seed": seed, "final_owned": final_owned, "steady_state_mean_owned": round(steady_mean, 2),
            "final_cum_purchased": final_purchased, "final_cum_escaped_est": final_escaped,
            "daily": daily,
        }
        all_rows.append(row)
        print(f"  [{label}] seed={seed}: final_owned={final_owned} steady_state_mean={steady_mean:.2f} "
              f"cum_purchased={final_purchased} cum_escaped_est={final_escaped}", flush=True)
    mean_final = sum(r["final_owned"] for r in all_rows) / len(all_rows)
    mean_steady = sum(r["steady_state_mean_owned"] for r in all_rows) / len(all_rows)
    mean_purchased = sum(r["final_cum_purchased"] for r in all_rows) / len(all_rows)
    mean_escaped = sum(r["final_cum_escaped_est"] for r in all_rows) / len(all_rows)
    print(f"  [{label}] MEAN final_owned={mean_final:.2f}  MEAN steady_state={mean_steady:.2f}  "
          f"MEAN cum_purchased={mean_purchased:.2f}  MEAN cum_escaped_est={mean_escaped:.2f}\n")
    return {
        "label": label, "rows": all_rows, "mean_final_owned": mean_final,
        "mean_steady_state_owned": mean_steady, "mean_cum_purchased": mean_purchased,
        "mean_cum_escaped_est": mean_escaped,
    }


def main():
    print(f"_ANIMAL_SPECIES_RUNGS target ladder (agents/phase21/portfolio.py, unmodified): {_ANIMAL_SPECIES_RUNGS}")
    print(f"Final target: {sum(_ANIMAL_SPECIES_RUNGS[-1][1].values())} animals by day {_ANIMAL_SPECIES_RUNGS[-1][0]}\n")

    results = {}
    print("=== Isolated (vs. 'pass'), Submission J's execution layer, unmodified targets ===")
    results["isolated"] = summarize_condition("isolated", "pass")

    print("=== vs. Submission G, Submission J's execution layer, unmodified targets ===")
    results["vs_submission_g"] = summarize_condition("vs_submission_g", "submission_g")

    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(os.path.join(OUT_ROOT, "phase48_animal_ceiling_probe_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUT_ROOT}/phase48_animal_ceiling_probe_results.json")


if __name__ == "__main__":
    main()
