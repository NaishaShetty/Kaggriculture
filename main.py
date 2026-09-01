"""
Kaggriculture competition submission entry point.

Canonical strategy: Phase 3.3 Variant D ("production_substitution"), frozen
and validated through Phase 3.4 as the canonical Phase 3 adaptive strategy
(see docs/Kaggriculture_Documentation.docx, Phase 3.3/3.4 chapters, and
results/phase3_3/, results/phase3_4/ for the full validation record).

This file is a packaging/entry-point wrapper ONLY -- it contains no
strategy logic of its own. It:

  1. Resolves this submission's own root directory WITHOUT relying on
     `__file__` in this module. VERIFIED (this phase, via a real fresh-
     process smoke test) that Kaggle's own agent loader
     (kaggle_environments.agent.get_last_callable) reads a file-path
     submission's source as TEXT and runs it with `exec(code_object, {})`
     -- NOT a normal `import` -- so `__file__` is undefined here on the
     real Kaggle path, even though it works fine under `python main.py` or
     `import main`. That loader appends this file's own directory to the
     END of `sys.path` immediately before exec'ing it (so it is reliably
     `sys.path[-1]` at the moment this module's top-level code starts
     running), which we use as the root instead.
  2. Inserts that root at the FRONT of `sys.path` before importing anything
     from `agents.*`. VERIFIED (this phase, via a real cold-process smoke
     test replicating Kaggle's exact loading path) that `kaggle_environments`
     itself ships several bundled mini-environments with their OWN
     generically-named top-level `agents.py` files (e.g.
     `kaggle_environments/envs/lux_ai_s3/agents.py`) whose directories can
     already be present earlier in `sys.path` by the time this file's
     import runs -- a plain `import agents...` can resolve to one of THOSE
     unrelated files instead of this project's `agents/` package,
     depending on unpredictable environment-registry setup order. Since
     `sys.path` is scanned strictly in order and the first regular package
     found wins, putting our root first resolves this deterministically
     (this project's `agents/` directory has its own `__init__.py`, added
     for exactly this reason -- see agents/__init__.py).
  3. Passes the resolved ABSOLUTE path to the (frozen, unmodified in
     substance) Variant D stack via `make_intervention_agent`'s new
     `artifact_path` parameter -- see agents/phase3_3/adapters/
     intervention_agent.py -- rather than `os.chdir()`-ing the whole
     process, since `kaggle_environments.run([agent0, agent1])` executes
     both players' agent() calls in the SAME process: changing the process
     working directory from inside one player's agent would leak into the
     other player's turn.
  4. Constructs the exact, unmodified Phase 3.3 Variant D agent, using
     every other default (threshold, trace_path=None,
     intervention_log_path=None) exactly as used to produce every
     validated Phase 3.3/3.4 result -- no strategy parameter here was
     changed for submission.
  5. Rebuilds that agent at the first observation of every new episode
     (obs["day"] == 0 and obs["hour"] == 0) so no state can leak from one
     game into the next if this process is reused across multiple episodes
     -- a packaging-level safeguard, not a strategy change (within a single
     episode, the SAME agent closure is reused for every turn, exactly as
     validated).

Do not add strategy logic to this file. Any behavioral change belongs in
agents/phase3_3/interventions.py (frozen) or a new, separately-validated
phase -- never here.
"""
import os
import sys


def _resolve_submission_root():
    # Kaggle's real loader (kaggle_environments.agent.get_last_callable)
    # appends this file's own directory to sys.path immediately before
    # exec()-ing it, and nothing else runs in between -- so sys.path[-1]
    # is reliably our own directory at this exact point in that loading
    # path. Confirmed with `main.py` present there as a sanity check
    # rather than trusted blindly.
    if sys.path and os.path.isfile(os.path.join(sys.path[-1], "main.py")):
        return os.path.abspath(sys.path[-1])
    # Fallback for non-Kaggle-exec contexts: `python main.py`, `import
    # main`, or test harnesses that import this module normally.
    return os.path.dirname(os.path.abspath(__file__))


_ROOT = _resolve_submission_root()
if sys.path[:1] != [_ROOT]:
    sys.path.insert(0, _ROOT)
_ARTIFACT_PATH = os.path.join(_ROOT, "results", "phase3_3", "detector", "artifact.json")

from agents.phase3_3.adapters.intervention_agent import make_intervention_agent  # noqa: E402
from agents.phase3_3.interventions import variant_d_production_substitution  # noqa: E402

_variant_d_agent = None


def _new_episode(obs):
    return obs.get("day") == 0 and obs.get("hour") == 0


def agent(obs):
    global _variant_d_agent
    if _variant_d_agent is None or _new_episode(obs):
        _variant_d_agent = make_intervention_agent(
            intervention_fn=variant_d_production_substitution,
            trace_path=None,
            intervention_log_path=None,
            artifact_path=_ARTIFACT_PATH,
        )
    return _variant_d_agent(obs)
