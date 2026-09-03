"""
Phase 28: trace agents/phase21/'s CURRENT losses to Submission G (post-Phase-27),
day-by-day, both sides. Reuses agents/phase6/replay_forensics.py
::extract_episode_timelines unchanged, same TeamNames-patch technique every
diagnostic phase since 24 has used for locally-run synthetic episodes.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase15.adapters.macro_agent import make_macro_agent  # noqa: E402
from agents.phase21.adapters.portfolio_agent import make_portfolio_agent  # noqa: E402
from agents.phase6.replay_forensics import extract_episode_timelines, to_day_row  # noqa: E402
from instrumentation.collector import run_episode  # noqa: E402

STEPS = 720

# Current losses (results/phase23/phase23_vs_submission_g_results.json, post-Phase-27), by margin.
SEEDS_TO_TRACE = {
    700000: "-32005 (huge outlier)",
    702001: "-4902",
    701002: "-4857 (previously flagged, Phase 25/27)",
    700001: "-2940",
    702000: "-458 (close)",
    702003: "-71 (near-tie)",
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

    print(f"{'day':<5}{'P21 cash':<11}{'G cash':<11}{'margin':<11}{'P21 h':<7}{'P21 l':<6}{'P21 crop':<9}"
          f"{'G h':<6}{'G l':<6}{'G crop':<8}")
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
        hg = rg['hands_count'] if rg else '?'
        lg = rg['land_quadrants'] if rg else '?'
        ctg = rg['total_crop_tiles'] if rg else '?'
        print(f"{day:<5}${c21:<10.0f}${cg:<10.0f}{margin:<+11.0f}{h21:<7}{l21:<6}{ct21:<9}{hg:<6}{lg:<6}{ctg:<8}{flip}")

    final21, finalg = replay["rewards"][0], replay["rewards"][1]
    print(f"\nFinal: phase21=${final21:.0f}  Submission_G=${finalg:.0f}  margin=${final21-finalg:+.0f}")

    # crop mix snapshots
    for day in [5, 10, 15, 20, 25, 27, 28, 29]:
        r21, rg = rows21.get(day), rowsG.get(day)
        if r21:
            c = {k[6:]: v for k, v in r21.items() if k.startswith("tiles_") and v}
            print(f"  day {day} P21 crop mix: {c}")
        if rg:
            c = {k[6:]: v for k, v in rg.items() if k.startswith("tiles_") and v}
            print(f"  day {day} G   crop mix: {c}")


def main():
    for seed, label in SEEDS_TO_TRACE.items():
        trace_seed(seed, label)


if __name__ == "__main__":
    main()
