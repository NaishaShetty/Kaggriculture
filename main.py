"""
Kaggriculture competition submission entry point -- Submission B.

Canonical strategy: Competitive Agent V2 (Phase 3.5) =
  Economic Planner V1 (frozen)
  + Phase 3.3 Variant D market response (frozen, unmodified -- crop
    substitution when an expansion_oriented-style MELON-flooding opponent
    is detected)
  + Phase 3.5 competitive scaling response (new -- raises our own labor/
    animal targets when a real-competition-motivated pattern is detected:
    the opponent sustains a much larger labor+animal base than we do).

Promoted from Submission A (Phase 3.4 Variant D alone) after real-
competition forensics on 18 actual Kaggle episodes
(results/phase3_5/competition_results_inventory.json) found that 6 of 10
real losses shared a mechanism no prior synthetic archetype represented:
a sustained, large opponent labor/animal commitment our static ~2-hands
strategy never matches. The new response layer was validated via a
controlled synthetic archetype (agents/phase3_5/opponent_classes_extended
.heavy_scaler) across disjoint development/validation/held-out seeds
(15/15 positive, zero side effects against the other 6 archetypes or
expansion_oriented) before being promoted here -- see
results/phase3_5/ for the full evidence trail.

This file remains a packaging/entry-point wrapper ONLY -- see
agents/phase3_5/adapters/competitive_v2_agent.py for the actual (frozen-
Planner-v1 + two response layers) architecture. The root-resolution logic
below is UNCHANGED from Submission A's main.py and must stay that way --
it fixes two real, verified Kaggle-loader defects (see
results/phase3_5/submission_manifest.json's
defects_found_and_fixed_during_packaging for the full writeup):
  1. Kaggle's real agent loader (kaggle_environments.agent.get_last_callable)
     executes a file-path submission via exec(code_object, {}), not a
     normal `import` -- `__file__` is undefined in that context, so the
     root is instead recovered from sys.path[-1] (reliably this
     submission's own directory at that exact point in Kaggle's loading
     sequence -- it appends exec_dir to sys.path immediately before
     exec'ing, and nothing runs in between).
  2. kaggle_environments itself bundles several unrelated mini-environments
     with their OWN generically-named `agents.py` files (lux_ai_s3,
     lux_ai_2021, crawl, mab, rps, word_art, word_association). A cold-
     process `import agents...` can resolve to one of THOSE instead of this
     project's `agents/` package depending on unpredictable sys.path
     ordering from kaggle_environments' own environment-registry setup --
     reproduced and confirmed via an actual crash during Phase 3.5
     packaging. Fixed by making `agents` a regular package (agents/
     __init__.py) and inserting this resolved root at the FRONT of
     sys.path before any `agents.*` import is attempted.

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase3_3/interventions.py, agents/phase3_5/response_policy.py
(both frozen after their own validation), or a new, separately-validated
phase -- never here.
"""
import os
import sys


def _resolve_submission_root():
    # Kaggle's real loader appends this file's own directory to sys.path
    # immediately before exec()-ing it, and nothing else runs in between --
    # so sys.path[-1] is reliably our own directory at this exact point in
    # that loading path. Confirmed with main.py present there as a sanity
    # check rather than trusted blindly.
    if sys.path and os.path.isfile(os.path.join(sys.path[-1], "main.py")):
        return os.path.abspath(sys.path[-1])
    # Fallback for non-Kaggle-exec contexts: `python main.py`, `import
    # main`, or test harnesses that import this module normally.
    return os.path.dirname(os.path.abspath(__file__))


_ROOT = _resolve_submission_root()
if sys.path[:1] != [_ROOT]:
    sys.path.insert(0, _ROOT)  # MUST happen before any `agents.*` import -- see module docstring, defect 2
_ARTIFACT_PATH = os.path.join(_ROOT, "results", "phase3_3", "detector", "artifact.json")

from agents.phase3_5.adapters.competitive_v2_agent import make_competitive_v2_agent  # noqa: E402

_competitive_v2_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _competitive_v2_agent
    if _competitive_v2_agent is None or _new_episode(obs):
        _competitive_v2_agent = make_competitive_v2_agent(
            trace_path=None,
            artifact_path=_ARTIFACT_PATH,
        )
    return _competitive_v2_agent(obs)
