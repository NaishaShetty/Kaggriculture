"""
Phase 3.8 Submission C adapter: Submission B's exact, frozen stack
(Planner v1 + Variant D market response + the existing fixed hands/animals
scaling response) with ONE additional, switchable layer applied on top:
agents.phase3_8.animal_response.animal_specific_response, which may raise
the ANIMAL target further for high/extreme opponent animal counts. The
hands target is NEVER touched by this file or by the new layer -- it is
set exactly once, by Submission B's own frozen response_policy, and passed
through unchanged.

This is a new file. agents/phase3_5/adapters/competitive_v2_agent.py
(Submission B's actual production adapter) is NOT modified -- Submission B
remains completely available, unchanged, and independently runnable as the
control. `main.py` is NOT changed by this file either; wiring a promoted
candidate into main.py happens only if/when promotion is confirmed.
"""
from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3_3.expansion_detector import ExpansionDetector, DEFAULT_THRESHOLD
from agents.phase3_3.interventions import variant_d_production_substitution
from agents.phase3_5.response_policy import competitive_scaling_response
from agents.phase3_8.animal_response import animal_specific_response


def make_competitive_v3_agent(animal_response_enabled=True, market_response_fn=variant_d_production_substitution,
                               market_threshold=DEFAULT_THRESHOLD, trace_path=None, artifact_path=None):
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    market_detector = (ExpansionDetector(threshold=market_threshold, artifact_path=artifact_path)
                       if artifact_path is not None else ExpansionDetector(threshold=market_threshold))
    state_ref = {"market_activations": 0, "scaling_activations": 0, "animal_response_activations": 0}

    def agent(obs):
        opponent_logger.observe(obs)
        action = planner(obs)  # Planner v1's own decision, always computed first, unmodified

        turn = obs["day"] * 24 + obs.get("hour", 0)
        config = planner._config

        # --- layer 1: market response (Variant D, frozen logic reused unchanged) ---
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

        # --- layer 2: Submission B's existing scaling response, UNCHANGED -- this is what
        # sets n_hands; it also sets a baseline animal target, which layer 3 may then raise. ---
        if len(opponent_logger.history) >= 1:
            new_config, _ = competitive_scaling_response(config, None, opponent_logger.history, obs["day"])
            if new_config != config:
                state_ref["scaling_activations"] += 1
                config.clear()
                config.update(new_config)

        # --- layer 3 (Phase 3.8, Submission C only): animal-specific override. Never touches
        # n_hands. Only raises 'animals' further for opponents above the Phase 3.7-derived
        # thresholds; otherwise leaves whatever layer 2 already set (B's baseline) untouched. ---
        if animal_response_enabled and len(opponent_logger.history) >= 1:
            new_config, _ = animal_specific_response(config, opponent_logger.history, obs["day"])
            if new_config != config:
                state_ref["animal_response_activations"] += 1
                config.clear()
                config.update(new_config)

        return action

    agent._planner = planner
    agent._opponent_logger = opponent_logger
    agent._market_detector = market_detector
    agent._state_ref = state_ref
    return agent
