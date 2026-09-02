"""
Phase 3.5 Competitive Agent V2 adapter.

Architecture (as specified in the Phase 3.5 kickoff, section 16):
    Economic Planner V1 (frozen, unmodified)
    + validated market response          (Phase 3.3 Variant D -- crop substitution)
    + validated competitive scaling response (Phase 3.5 -- labor/animal scaling)

Exactly the same "call planner(obs) first, unmodified; THEN mutate its
OWN current_config in place for the tactical layer to pick up" pattern
Phase 3.1/3.3 established (agents/phase3_3/adapters/intervention_agent.py)
-- neither Planner v1 nor Variant D's own intervention function is
modified by this file. The two response layers touch DISJOINT config keys
("crops" vs "n_hands"/"animals") and are applied sequentially, so they
cannot conflict with each other.

`market_response_fn=None` and/or `scaling_response_enabled=False` let
regression/ablation tests isolate each layer independently (Planner v1
alone / +market response only / +scaling response only / both together).
"""
import os

from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3_3.expansion_detector import ExpansionDetector, DEFAULT_THRESHOLD
from agents.phase3_3.interventions import variant_d_production_substitution
from agents.phase3_5.response_policy import competitive_scaling_response


def make_competitive_v2_agent(market_response_fn=variant_d_production_substitution,
                               scaling_response_enabled=True,
                               market_threshold=DEFAULT_THRESHOLD,
                               trace_path=None, artifact_path=None):
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    market_detector = (ExpansionDetector(threshold=market_threshold, artifact_path=artifact_path)
                       if artifact_path is not None else ExpansionDetector(threshold=market_threshold))
    state_ref = {"market_activations": 0, "scaling_activations": 0}

    def agent(obs):
        opp_snap = opponent_logger.observe(obs)
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

        # --- layer 2: competitive scaling response (Phase 3.5, disjoint config keys) ---
        if scaling_response_enabled and len(opponent_logger.history) >= 1:
            new_config, scaling_detection = competitive_scaling_response(
                config, None, opponent_logger.history, obs["day"])
            if new_config != config:
                state_ref["scaling_activations"] += 1
                config.clear()
                config.update(new_config)

        return action

    agent._planner = planner
    agent._opponent_logger = opponent_logger
    agent._market_detector = market_detector
    agent._state_ref = state_ref
    return agent
