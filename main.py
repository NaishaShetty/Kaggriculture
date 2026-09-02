"""
Kaggriculture competition submission entry point -- Submission C.

Canonical strategy: Competitive Agent V3 (Phase 3.8) =
  Economic Planner V1 (frozen)
  + Phase 3.3 Variant D market response (frozen, unmodified)
  + Phase 3.5 competitive scaling response (frozen, unmodified -- sets the
    hands target and a baseline animal target)
  + Phase 3.8 animal-specific response (new -- may raise the animal target
    further, in a small, bounded way, when the opponent's own animal count
    is materially above what Submission B's fixed baseline already handles)

Promoted from Submission B after Phase 3.7 identified, from real Submission
B competitive data, that opponent ANIMAL count (not hand count) cleanly
separates games the existing response wins from games it loses (mean 2.0
vs 9.2 across 9 real episodes where the response fired) -- Submission B's
hands target was already well-calibrated; only its animal target was
under-sized against the most animal-heavy real opponents. Phase 3.8
implemented a small, bounded, piecewise animal-target override on top of
B's unchanged stack (agents/phase3_8/animal_response.py), validated via:
  - 11/11 new regression tests, including a real-data replay validation
    against the actual moushun chen (Submission B) trajectory
  - 0/44 regressions across the full existing archetype battery
    (development + held-out seeds)
  - 1 measured improvement in the same battery (heavy_scaler: +$776 with
    the animal response confirmed firing)
See results/phase3_8/ for the complete implementation and validation
record, and results/phase3_5/ + results/phase3_6/ + results/phase3_7/ for
the research trail this promotion is grounded in.

This file remains a packaging/entry-point wrapper ONLY -- see
agents/phase3_8/adapters/competitive_v3_agent.py for the actual
architecture. The root-resolution logic below is UNCHANGED from
Submission B's main.py (same two verified Kaggle-loader defects it fixes:
__file__ is unavailable under Kaggle's exec()-based loading, and this
project's top-level `agents` package name collides with several unrelated
`agents.py` files bundled inside kaggle_environments itself).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase3_3/interventions.py, agents/phase3_5/response_policy.py, or
agents/phase3_8/animal_response.py (all frozen after their own
validation), or a new, separately-validated phase -- never here.
"""
import os
import sys


def _resolve_submission_root():
    if sys.path and os.path.isfile(os.path.join(sys.path[-1], "main.py")):
        return os.path.abspath(sys.path[-1])
    return os.path.dirname(os.path.abspath(__file__))


_ROOT = _resolve_submission_root()
if sys.path[:1] != [_ROOT]:
    sys.path.insert(0, _ROOT)
_ARTIFACT_PATH = os.path.join(_ROOT, "results", "phase3_3", "detector", "artifact.json")

from agents.phase3_8.adapters.competitive_v3_agent import make_competitive_v3_agent  # noqa: E402

_competitive_v3_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _competitive_v3_agent
    if _competitive_v3_agent is None or _new_episode(obs):
        _competitive_v3_agent = make_competitive_v3_agent(
            trace_path=None,
            artifact_path=_ARTIFACT_PATH,
        )
    return _competitive_v3_agent(obs)
