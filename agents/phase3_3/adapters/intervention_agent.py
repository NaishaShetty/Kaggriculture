"""
Phase 3.3 intervention agent adapter. Extends the Phase 3.1 control-adapter
pattern (agents/phase3/adapters/planner_v1_control.py): wraps
agents.phase2_6.common.make_agent UNCHANGED, runs the Phase 3.3
ExpansionDetector every planning cycle, and -- ONLY if `intervention_fn` is
given and the detector is active -- overrides the planner's own chosen
`current_config` before the tactical layer (agents/phase2_4/common.py) acts
on it. Planner v1's own source code is never touched; this is a strictly
external wrapper, exactly like Phase 3.1's control adapter.

`intervention_fn=None` reproduces Variant B (detection-only, zero behavioral
change) -- verified by regression test to be economically identical to the
raw frozen planner, the same discipline Phase 3.1 used to prove its own
control adapter was inert.

`artifact_path` (Phase 3.5 submission-packaging addition, purely additive):
optional override for the detector's persisted artifact file location,
passed straight through to `ExpansionDetector`. Defaults to `None`, which
preserves the EXACT prior behavior (falls back to
`ExpansionDetector`'s own `ARTIFACT_PATH` default, a path relative to the
process's current working directory) for every existing caller/test -- this
does not change what gets loaded or how detection behaves, only where a
caller may explicitly point it, needed because Kaggle's own agent loader
executes submission files via `exec()` rather than `import`, so a
submission entry point has no reliable relative-path/CWD assumption to
lean on (see main.py).
"""
import os

from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3_3.expansion_detector import ExpansionDetector, DEFAULT_THRESHOLD


def make_intervention_agent(intervention_fn=None, threshold=DEFAULT_THRESHOLD, trace_path=None,
                             intervention_log_path=None, artifact_path=None):
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    detector = (ExpansionDetector(threshold=threshold, artifact_path=artifact_path)
                if artifact_path is not None else ExpansionDetector(threshold=threshold))
    log_f = open(intervention_log_path, "a") if intervention_log_path else None
    state_ref = {"n_activations": 0, "first_activation_turn": None}

    def agent(obs):
        # ORDERING NOTE (documented, not hidden): `planner(obs)` is called
        # BEFORE any override, so on a day-boundary (replanning) turn, that
        # turn's OWN action still reflects Planner v1's un-intervened choice
        # -- the override below only takes effect starting the NEXT turn
        # (and persists for the rest of that in-game day, since Planner v1
        # only recomputes `config` from scratch once per day). This is a
        # deliberate, minimal-footprint design (never patches Planner v1's
        # own replanning logic) with a documented ~1-turn/day lag, not an
        # attempt to intervene before the planner has even decided anything.
        opp_snap = opponent_logger.observe(obs)
        action = planner(obs)  # Planner v1's own decision, always computed first, unmodified

        turn = obs["day"] * 24 + obs.get("hour", 0)
        if len(opponent_logger.history) >= 1:
            detection = detector.check(opponent_logger.history, turn)
        else:
            detection = {"active": False, "predicted_class": None, "confidence": 0.0, "checkpoint_used": None}

        if intervention_fn is not None and detection["active"]:
            from agents.phase2_6.state import adapt
            planner_state = adapt(obs)
            config = planner._config
            new_config = intervention_fn(config, planner_state, detection)
            if new_config != config:
                state_ref["n_activations"] += 1
                if state_ref["first_activation_turn"] is None:
                    state_ref["first_activation_turn"] = turn
                config.clear()
                config.update(new_config)

        if log_f:
            import json
            log_f.write(json.dumps({"turn": turn, "detection": detection,
                                     "n_activations": state_ref["n_activations"]}) + "\n")
            log_f.flush()

        return action

    agent._planner = planner
    agent._opponent_logger = opponent_logger
    agent._detector = detector
    agent._state_ref = state_ref
    agent._log_f = log_f
    return agent
