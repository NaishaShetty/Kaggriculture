"""
Phase 26 Step 1: trace agents/phase21/'s close losses to Submission G
day-by-day, both sides, to confirm (or refute) the diagnosis that it has no
risk-posture awareness -- does it keep spending/investing the same way
whether it's ahead or behind on live money margin?

Reuses agents/phase6/replay_forensics.py::extract_episode_timelines
unchanged, same TeamNames-patch technique Phase 24 used for locally-run
synthetic episodes (which have no real TeamNames).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from agents.phase6.replay_forensics import extract_episode_timelines, to_day_row  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720

# Close losses (small margin) + one moderate loss for range, from
# results/phase23/phase23_vs_submission_g_results.json (current, post-Phase25).
SEEDS_TO_TRACE = {
    700002: "close loss (-3277)",
    702003: "close loss (-4196)",
    702002: "close loss (-4915)",
    702004: "close loss (-5280)",
    701002: "moderate loss (-8867, for range)",
}


def trace_seed(seed, label):
    print(f"\n{'='*100}\nSEED {seed} -- {label}\n{'='*100}")
    agent21 = make_portfolio_agent()
    agentG = make_macro_agent()
    replay, meta = run_episode(agent21, agentG, STEPS, seed, None)
    replay["info"] = dict(replay.get("info") or {})
    replay["info"]["TeamNames"] = ["phase21", "Submission_G"]

    _, self_tl_21, _ = extract_episode_timelines(replay, our_name="phase21")
    _, self_tl_g, _ = extract_episode_timelines(replay, our_name="Submission_G")
    rows21 = {r.day: to_day_row(r) for r in self_tl_21}
    rowsG = {r.day: to_day_row(r) for r in self_tl_g}

    print(f"{'day':<5}{'P21 cash':<11}{'G cash':<11}{'margin':<11}{'P21 hands':<11}{'P21 land':<9}"
          f"{'P21 crop':<9}{'P21 seed_spend?':<10}")
    prev_margin = None
    for day in sorted(set(rows21) | set(rowsG)):
        r21, rg = rows21.get(day), rowsG.get(day)
        c21 = r21['bank'] if r21 else None
        cg = rg['bank'] if rg else None
        margin = (c21 - cg) if (c21 is not None and cg is not None) else None
        flip = ""
        if margin is not None and prev_margin is not None and (margin >= 0) != (prev_margin >= 0):
            flip = "  <-- LEAD FLIPS"
        prev_margin = margin if margin is not None else prev_margin
        h21 = r21['hands_count'] if r21 else '?'
        l21 = r21['land_quadrants'] if r21 else '?'
        ct21 = r21['total_crop_tiles'] if r21 else '?'
        print(f"{day:<5}${c21:<10.0f}${cg:<10.0f}{margin:<+11.0f}{h21:<11}{l21:<9}{ct21:<9}{flip}")

    final21, finalg = replay["rewards"][0], replay["rewards"][1]
    print(f"\nFinal: phase21=${final21:.0f}  Submission_G=${finalg:.0f}  margin=${final21-finalg:+.0f}")


def main():
    for seed, label in SEEDS_TO_TRACE.items():
        trace_seed(seed, label)


if __name__ == "__main__":
    main()
