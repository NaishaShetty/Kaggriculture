"""
Phase 33 Part B, Step 4: direct-trace confirmation that the strictly
opportunistic fertilizer configuration (scripts/phase33/
fert_execution_opportunistic.py, FERTILIZE tier 4 / COLLECT_FERTILIZER
tier 5) never displaces a tier-0-through-3 task -- not assumed from the tier
numbers, verified turn-by-turn against the real engine.

For every turn, at the moment tier-4 processing begins, records:
  - unmatched_le3_at_tier4_start: how many tier<=3 entries are still sitting
    unassigned in the combined entry pool
  - eligible_le3_pairs_at_tier4_start: of those, how many are actually
    eligible for some worker that is STILL UNCLAIMED at that exact moment
    (i.e. a worker about to receive a fertilizer assignment)

Non-preemption holds if and only if eligible_le3_pairs_at_tier4_start is 0 on
EVERY turn that also assigns a fertilizer task -- if it's ever >0, that would
mean a worker took a fertilizer task while a tier<=3 task it could have done
went unaddressed, i.e. real preemption despite the tier number.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402
from agents.phase3.opponent_observation import OpponentObservationLogger  # noqa: E402
from scripts.phase33.fert_execution_opportunistic import make_fert_execution_agent  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720
SEEDS = [700000, 700001, 700002, 700003]


def run_traced(seed):
    trace_sink = []
    opponent_logger = OpponentObservationLogger()
    execution_agent = make_fert_execution_agent(portfolio_targets, fertilize=True, trace_sink=trace_sink)

    def agent(obs):
        opponent_logger.observe(obs)
        execution_agent.set_opponent_history(opponent_logger.history)
        return execution_agent(obs)

    replay, meta = run_episode(agent, "pass", STEPS, seed, None)
    return trace_sink, replay


def main():
    total_turns = 0
    total_fert_actions = 0
    total_violations = 0
    worst_violation = None

    for seed in SEEDS:
        trace_sink, replay = run_traced(seed)
        n_fert_actions_seed = 0
        n_violations_seed = 0
        for row in trace_sink:
            total_turns += 1
            fert_assignments = [a for a in row["assignments"] if a["tier"] >= 4]
            n_fert_actions_seed += len(fert_assignments)
            if fert_assignments and row["eligible_le3_pairs_at_tier4_start"]:
                n_violations_seed += 1
                if worst_violation is None:
                    worst_violation = {"seed": seed, "day": row["day"],
                                        "eligible_le3_pairs": row["eligible_le3_pairs_at_tier4_start"],
                                        "n_fert_assignments": len(fert_assignments)}
        total_fert_actions += n_fert_actions_seed
        total_violations += n_violations_seed
        print(f"  seed={seed}: turns={len(trace_sink)} fertilizer_actions={n_fert_actions_seed} "
              f"preemption_violations={n_violations_seed}", flush=True)

    print(f"\nTOTAL across {len(SEEDS)} seeds: {total_turns} turns, {total_fert_actions} fertilizer-tier actions, "
          f"{total_violations} turns with a fertilizer action AND an eligible unmatched tier<=3 entry")
    if total_violations == 0:
        print("[VERIFIED] Zero preemption violations -- the strictly-opportunistic configuration never took a "
              "worker-turn that a tier<=3 task could have used, confirmed by direct trace, not just tier numbering.")
    else:
        print(f"[VERIFIED] {total_violations} preemption violations found -- example: {worst_violation}")


if __name__ == "__main__":
    main()
