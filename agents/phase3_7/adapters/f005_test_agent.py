"""Phase 3.7-C test harness: Submission B's exact stack + the switchable
F-005 liquidity guard layered on top, disjoint from the market/scaling
config keys those layers already use (touches "crops" only, same as
Variant D, applied at a fixed early checkpoint independent of Variant D's
own detector)."""
from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3_3.expansion_detector import ExpansionDetector, DEFAULT_THRESHOLD
from agents.phase3_3.interventions import variant_d_production_substitution
from agents.phase3_5.response_policy import competitive_scaling_response
from agents.phase3_7.f005_liquidity_guard import f005_liquidity_guard


def make_f005_test_agent(guard_enabled=True, trace_path=None):
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    market_detector = ExpansionDetector(threshold=DEFAULT_THRESHOLD)
    state_ref = {"market_activations": 0, "scaling_activations": 0, "guard_triggered": False}

    def agent(obs):
        opponent_logger.observe(obs)
        action = planner(obs)
        turn = obs["day"] * 24 + obs.get("hour", 0)
        config = planner._config

        if len(opponent_logger.history) >= 1:
            market_detection = market_detector.check(opponent_logger.history, turn)
            if market_detection["active"]:
                from agents.phase2_6.state import adapt
                planner_state = adapt(obs)
                new_config = variant_d_production_substitution(config, planner_state, market_detection)
                if new_config != config:
                    state_ref["market_activations"] += 1
                    config.clear()
                    config.update(new_config)

        if len(opponent_logger.history) >= 1:
            new_config, _ = competitive_scaling_response(config, None, opponent_logger.history, obs["day"])
            if new_config != config:
                state_ref["scaling_activations"] += 1
                config.clear()
                config.update(new_config)

        if guard_enabled:
            new_config, triggered = f005_liquidity_guard(config, obs, state_ref["guard_triggered"])
            if triggered and not state_ref["guard_triggered"]:
                state_ref["guard_triggered"] = True
                config.clear()
                config.update(new_config)

        return action

    agent._planner = planner
    agent._state_ref = state_ref
    return agent
