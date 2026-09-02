"""
Phase 3.6 adaptive-response test harness adapter. Wraps the frozen Planner
v1 + frozen Variant D market response UNCHANGED (identical pattern to
agents/phase3_5/adapters/competitive_v2_agent.py, which remains untouched
and is still what main.py / Submission B actually run) and layers in a
SWITCHABLE Phase 3.6 scaling-response candidate (any function from
agents.phase3_6.response_policy_v2.CANDIDATES, selected by name).

This is a research/experimentation adapter, not a new production path --
nothing here is wired into main.py unless and until a candidate is
promoted (Phase 3.6-G).
"""
from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3_3.expansion_detector import ExpansionDetector, DEFAULT_THRESHOLD
from agents.phase3_3.interventions import variant_d_production_substitution
from agents.phase3_6.response_policy_v2 import CANDIDATES


def make_adaptive_agent(candidate_name="B0_fixed", market_response_fn=variant_d_production_substitution,
                         market_threshold=DEFAULT_THRESHOLD, trace_path=None, artifact_path=None,
                         trace_log_path=None):
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    market_detector = (ExpansionDetector(threshold=market_threshold, artifact_path=artifact_path)
                       if artifact_path is not None else ExpansionDetector(threshold=market_threshold))
    response_fn = CANDIDATES[candidate_name]
    state_ref = {"market_activations": 0, "scaling_activations": 0, "first_scaling_activation_turn": None}
    trace_f = open(trace_log_path, "a") if trace_log_path else None

    def agent(obs):
        opponent_logger.observe(obs)
        action = planner(obs)  # Planner v1's own decision, always computed first, unmodified

        turn = obs["day"] * 24 + obs.get("hour", 0)
        config = planner._config

        if market_response_fn is not None and len(opponent_logger.history) >= 1:
            market_detection = market_detector.check(opponent_logger.history, turn)
            if market_detection["active"]:
                from agents.phase2_6.state import adapt
                planner_state = adapt(obs)
                new_config = market_response_fn(config, planner_state, market_detection)
                if new_config != config:
                    state_ref["market_activations"] += 1
                    config.clear()
                    config.update(new_config)

        if len(opponent_logger.history) >= 1:
            new_config, scaling_detection = response_fn(config, obs, opponent_logger.history, obs["day"])
            if new_config != config:
                state_ref["scaling_activations"] += 1
                if state_ref["first_scaling_activation_turn"] is None:
                    state_ref["first_scaling_activation_turn"] = turn
                if trace_f:
                    import json
                    trace_f.write(json.dumps({
                        "turn": turn, "day": obs["day"], "candidate": candidate_name,
                        "trigger": scaling_detection.reason, "opponent_hands_recent": scaling_detection.opponent_hands_recent,
                        "opponent_animals_recent": scaling_detection.opponent_animals_recent,
                        "old_n_hands": config.get("n_hands"), "new_n_hands": new_config.get("n_hands"),
                        "old_animals": config.get("animals"), "new_animals": new_config.get("animals"),
                        "our_cash_at_trigger": obs["farms"][obs["player"]]["money"],
                    }) + "\n")
                    trace_f.flush()
                config.clear()
                config.update(new_config)

        return action

    agent._planner = planner
    agent._opponent_logger = opponent_logger
    agent._market_detector = market_detector
    agent._state_ref = state_ref
    agent._trace_f = trace_f
    return agent
