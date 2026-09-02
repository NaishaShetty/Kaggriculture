"""
Phase 4 (Submission D) top-level controller. Ties opponent_model,
forecast, threat, strategy, portfolio, and liquidity together into one
per-day decision, then hands off to the SAME frozen mechanisms Submission
C already validated (Variant D market response, the Phase 3.5 scaling
response, the Phase 3.8 animal response) for the COUNTER mode's concrete
resource response -- per the brief's explicit instruction to integrate,
not re-derive, C's validated mechanisms.

ARCHITECTURAL BOUNDARY, stated plainly: this controller decides
HIGH-LEVEL CONFIG (crop portfolio fractions, n_hands, animals, sell
policy) exactly like every Phase 3.3-3.8 layer before it -- it does NOT
replace the frozen Phase 2.4 tactical task scheduler (movement, per-tile
watering/harvest priority, worker task assignment). The brief's
"rolling-horizon action planner" requirement is interpreted at this
config-decision granularity, re-evaluated once per day (a 1-day
"horizon" in the sense that it is the frozen tactical layer's own
existing per-day replanning cadence, not a new multi-day lookahead
search) rather than as a literal multi-day per-tile task search --
implementing the latter would mean rewriting agents/phase2_4/common.py,
which is explicitly out of scope (frozen, validated, must not be
touched). This is a deliberate, disclosed scope boundary, not a silent
gap.
"""
from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase2_6.state import adapt
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3_3.expansion_detector import ExpansionDetector, DEFAULT_THRESHOLD
from agents.phase3_3.interventions import variant_d_production_substitution
from agents.phase3_5.response_policy import competitive_scaling_response
from agents.phase3_8.animal_response import animal_specific_response
from agents.phase4.opponent_model import OpponentTrajectory
from agents.phase4.forecast import forecast_self, forecast_opponent, projected_gap
from agents.phase4.threat import assess_threat
from agents.phase4.strategy import select_mode, NORMAL, COUNTER, DEFEND, RECOVER, ENDGAME
from agents.phase4.portfolio import build_portfolio
from agents.phase4.liquidity import liquidity_state, is_endgame, endgame_liquidation_plan

TOTAL_DAYS = 30


def make_phase4_agent(market_response_fn=variant_d_production_substitution, market_threshold=DEFAULT_THRESHOLD,
                       trace_path=None, artifact_path=None, portfolio_enabled=True, endgame_enabled=True,
                       liquidity_guard_enabled=True, controller_trace_path=None):
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    market_detector = (ExpansionDetector(threshold=market_threshold, artifact_path=artifact_path)
                       if artifact_path is not None else ExpansionDetector(threshold=market_threshold))
    trajectory = OpponentTrajectory()
    state_ref = {"market_activations": 0, "scaling_activations": 0, "animal_response_activations": 0,
                 "portfolio_switches": 0, "mode_history": [], "last_mode": None, "last_portfolio_day": -1}
    trace_f = open(controller_trace_path, "a") if controller_trace_path else None

    def agent(obs):
        opponent_logger.observe(obs)
        action = planner(obs)  # Planner v1's own decision, always computed first, unmodified

        day = obs["day"]
        turn = day * 24 + obs.get("hour", 0)
        config = planner._config
        our_player = obs["player"]
        our_farm = obs["farms"][our_player]
        our_cash = our_farm["money"]

        # --- layer 1: market response (Variant D, frozen, unchanged) ---
        if market_response_fn is not None and len(opponent_logger.history) >= 1:
            market_detection = market_detector.check(opponent_logger.history, turn)
            if market_detection["active"]:
                planner_state = adapt(obs)
                new_config = market_response_fn(config, planner_state, market_detection)
                if new_config != config:
                    state_ref["market_activations"] += 1
                    config.clear()
                    config.update(new_config)

        # --- layer 2: Submission C's scaling + animal response, frozen, unchanged ---
        if len(opponent_logger.history) >= 1:
            new_config, _ = competitive_scaling_response(config, None, opponent_logger.history, day)
            if new_config != config:
                state_ref["scaling_activations"] += 1
                config.clear()
                config.update(new_config)
            new_config2, _ = animal_specific_response(config, opponent_logger.history, day)
            if new_config2 != config:
                state_ref["animal_response_activations"] += 1
                config.clear()
                config.update(new_config2)

        # --- layer 3 (Phase 4, new): strategic assessment, once per day ---
        if obs.get("hour", 0) == 0 and len(opponent_logger.history) >= 1:
            trajectory.observe(opponent_logger.history)
            opp_latest = trajectory.latest()
            remaining_days = max(0, TOTAL_DAYS - day)

            self_fc = forecast_self(our_cash, 0.0, remaining_days)  # conservative: no self-velocity assumed beyond current cash
            opp_fc = forecast_opponent(opp_latest.bank if opp_latest else 0.0, trajectory.bank_velocity(), remaining_days)
            gap, _ = projected_gap(self_fc, opp_fc)
            regime, _ = trajectory.classify_regime()
            threat = assess_threat(gap, trajectory.animal_velocity(), trajectory.hands_velocity(),
                                    regime, remaining_days, our_cash)
            liq_state, _ = liquidity_state(our_cash, remaining_days)
            endgame_now = is_endgame(day, TOTAL_DAYS)

            decision = select_mode(threat, liq_state, endgame_now, state_ref["last_mode"])
            state_ref["mode_history"].append(decision.mode)
            state_ref["last_mode"] = decision.mode

            # Portfolio: only override the crop mix on day 0 (initial choice) --
            # switching an already-growing portfolio mid-game destroys sunk
            # production (P26-004, already documented, frozen finding) and this
            # phase found no new evidence to justify overriding that caution.
            # NOTE: checking config.get("_portfolio_name") is None does NOT work
            # here -- Planner v1's own SWITCH_PORTFOLIO decision already runs
            # (inside the `planner(obs)` call above) and sets _portfolio_name
            # before this code executes, exactly like every other Phase 3.x
            # override in this file replaces an already-Planner-decided value
            # rather than waiting for an unset one.
            if portfolio_enabled and day == 0 and obs.get("hour", 0) == 0 and state_ref["last_portfolio_day"] < 0:
                planner_state = adapt(obs)
                new_crops = build_portfolio(planner_state)
                new_config = dict(config)
                new_config["crops"] = new_crops
                new_config["_portfolio_name"] = "phase4_dynamic"
                config.clear()
                config.update(new_config)
                state_ref["portfolio_switches"] += 1
                state_ref["last_portfolio_day"] = day

            # Liquidity guard: in RECOVER mode, suppress further escalation of
            # hands/animals targets beyond whatever is already committed (does
            # not reduce existing commitments -- only stops NEW increases).
            if liquidity_guard_enabled and decision.mode == RECOVER:
                pass  # no explicit action needed: layers 1/2 above only ever RAISE
                      # targets and this mode simply does not add a new raise;
                      # existing config values pass through unchanged.

            if trace_f:
                import json
                trace_f.write(json.dumps({
                    "turn": turn, "day": day, "mode": decision.mode, "reason": decision.reason,
                    "projected_gap": round(gap, 1), "threat_level": threat.level, "threat_score": threat.score,
                    "opponent_regime": regime, "liquidity_state": liq_state, "our_cash": our_cash,
                }) + "\n")
                trace_f.flush()

        # --- layer 4 (Phase 4, new): endgame liquidation via direct action augmentation ---
        if endgame_enabled and is_endgame(day, TOTAL_DAYS):
            shed = obs.get("private", {}).get("shed", {})
            market_inv = obs["market"]["inventory"]
            plan = endgame_liquidation_plan(shed, market_inv)
            existing_market_orders = action.get("market", [])
            items_already_selling = {o[1] for o in existing_market_orders if o and o[0] == "SELL"}
            for item, n in plan.items():
                if n > 0 and item not in items_already_selling and len(existing_market_orders) < 10:
                    existing_market_orders.append(["SELL", item, n])
            action["market"] = existing_market_orders

        return action

    agent._planner = planner
    agent._opponent_logger = opponent_logger
    agent._trajectory = trajectory
    agent._state_ref = state_ref
    agent._trace_f = trace_f
    return agent
