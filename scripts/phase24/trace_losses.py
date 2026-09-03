"""
Phase 24: trace agents/phase21/'s worst head-to-head losses to Submission G
(agents/phase15/), plus one win for contrast, day-by-day, both sides.

Reuses agents/phase6/replay_forensics.py::extract_episode_timelines UNCHANGED
for the extraction. That function reads `replay["info"]["TeamNames"]` to pick
a viewer index -- locally-run synthetic episodes (instrumentation.collector
.run_episode) don't set TeamNames (it's None), so this script sets it to
["phase21", "Submission_G"] before calling the function, once per replay --
a legitimate, minimal use of the function exactly as designed (index lookup
by name), not a modification of the function itself.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from agents.phase6.replay_forensics import extract_episode_timelines, to_day_row  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720

# Worst 4 losses (from results/phase23/phase23_vs_submission_g_results.json,
# sorted by margin) + 1 win for contrast.
SEEDS_TO_TRACE = {
    700001: "loss (-18904, worst)",
    701002: "loss (-17269)",
    700002: "loss (-14948)",
    701001: "loss (-13413)",
    701000: "win (+2386, contrast)",
}


def trace_seed(seed, label):
    print(f"\n{'='*90}\nSEED {seed} -- {label}\n{'='*90}")
    agent21 = make_portfolio_agent()
    agentG = make_macro_agent()
    replay, meta = run_episode(agent21, agentG, STEPS, seed, None)
    replay["info"] = dict(replay.get("info") or {})
    replay["info"]["TeamNames"] = ["phase21", "Submission_G"]

    _, self_tl_21, opp_tl_21_view = extract_episode_timelines(replay, our_name="phase21")
    # self_tl_21 is phase21's own full row (day, bank, hands, land, crop tiles, animals)
    _, self_tl_g, _ = extract_episode_timelines(replay, our_name="Submission_G")

    rows21 = {r.day: to_day_row(r) for r in self_tl_21}
    rowsG = {r.day: to_day_row(r) for r in self_tl_g}

    print(f"{'day':<5}{'P21 cash':<12}{'P21 hands':<11}{'P21 land':<10}{'P21 crop':<10}{'P21 anim':<10}"
          f"|{'G cash':<12}{'G hands':<10}{'G land':<9}{'G crop':<9}{'G anim':<9}")
    for day in sorted(set(rows21) | set(rowsG)):
        r21 = rows21.get(day)
        rg = rowsG.get(day)

        def fmt(r):
            if r is None:
                return "?", "?", "?", "?", "?"
            return (f"${r['bank']:.0f}", r['hands_count'], r['land_quadrants'],
                    r['total_crop_tiles'], r['total_animal_count'])

        c21, h21, l21, ct21, a21 = fmt(r21)
        cg, hg, lg, ctg, ag = fmt(rg)
        print(f"{day:<5}{c21:<12}{h21:<11}{l21:<10}{ct21:<10}{a21:<10}|{cg:<12}{hg:<10}{lg:<9}{ctg:<9}{ag:<9}")

    final21 = replay["rewards"][0]
    finalG = replay["rewards"][1]
    print(f"\nFinal: phase21=${final21:.0f}  Submission_G=${finalG:.0f}")

    # Crop-mix snapshot at a few key days for both sides.
    for day in [5, 10, 15, 20, 25]:
        r21 = rows21.get(day)
        rg = rowsG.get(day)
        if r21:
            crops21 = {k[6:]: v for k, v in r21.items() if k.startswith("tiles_") and v}
            print(f"  day {day} P21 crop mix: {crops21}")
        if rg:
            cropsg = {k[6:]: v for k, v in rg.items() if k.startswith("tiles_") and v}
            print(f"  day {day} G   crop mix: {cropsg}")


def main():
    for seed, label in SEEDS_TO_TRACE.items():
        trace_seed(seed, label)


if __name__ == "__main__":
    main()
