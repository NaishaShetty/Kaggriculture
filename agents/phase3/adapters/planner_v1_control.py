"""
Phase 3.1 frozen-control adapter. Wraps agents.phase2_6.common.make_agent
UNCHANGED (brief section 6/33.A: "Frozen Planner control wrapper. Runnable
independently.") and additionally attaches the Phase 3 observation loggers
(OpponentObservationLogger, MarketObservationLogger) and a CompetitiveTraceWriter
PURELY ADDITIVELY -- the loggers observe the same `obs` the planner already
receives, they never feed anything back into the planner's own decision
logic, and the planner's action output is passed through byte-for-byte
unmodified. This is what makes the "control reproduction" test meaningful:
if this adapter is truly inert, wrapping the frozen planner with it must
reproduce the exact same final money as calling agents.phase2_6.common.make_agent
directly (scripts/phase3_1_control_reproduction.py verifies this).
"""
import os

from agents.phase2_6.common import make_agent as make_planner_v1
from agents.phase3.opponent_observation import OpponentObservationLogger
from agents.phase3.market_observation import MarketObservationLogger
from agents.phase3.competitive_state import build_competitive_state, summarize as summarize_competitive
from agents.phase3.competitive_trace import CompetitiveTraceWriter
from agents.phase3.strategy import measure_snapshot
from agents.phase3.strategy_interface import StrategySelector, SwitchMode


def make_control_agent(trace_path=None, competitive_trace_path=None, strategy_mode=SwitchMode.NO_SWITCH,
                        forced_config=None):
    """Returns an agent(obs) function. `trace_path` is passed straight to
    the underlying Phase 2.6 planner (unchanged behavior). `competitive_trace_path`,
    if given, additionally records the Phase 3 competitive trace alongside it.
    `strategy_mode`/`forced_config` let a controlled experiment apply a FORCED
    override for ablation testing (brief section 20) -- NO_SWITCH (default)
    means this adapter is 100% inert and reproduces Phase 2.6 exactly."""
    planner = make_planner_v1(trace_path=trace_path)
    opponent_logger = OpponentObservationLogger()
    market_logger = MarketObservationLogger()
    selector = StrategySelector(mode=strategy_mode, forced_config=forced_config)
    ctrace = CompetitiveTraceWriter(competitive_trace_path) if competitive_trace_path else None

    def agent(obs):
        # 1. Observe (Phase 3 loggers) -- read-only, never mutates obs, never
        #    influences the planner call below.
        opp_snap = opponent_logger.observe(obs)
        market_snap = market_logger.observe(obs)  # own_transactions_this_turn intentionally omitted here
        #    (this control adapter does not have direct access to the planner's own txn ledger without
        #    re-deriving it from the trace; the resulting "unexplained delta" in this control config is
        #    therefore a conservative UPPER BOUND on opponent+self activity, not yet self-activity-corrected --
        #    documented limitation, see Phase 3.1 report section on market_observation).

        # 2. The planner makes its own decision, COMPLETELY UNCHANGED.
        action = planner(obs)

        # 3. Build the competitive state / strategy snapshot / trace PURELY FOR OBSERVATION.
        if ctrace is not None:
            config = planner._config
            cs = build_competitive_state(
                planner_state=_reconstruct_planner_state(obs), opponent_obs=opp_snap, market_obs=market_snap,
                opponent_history=opponent_logger.history, market_history=market_logger.history,
            )
            strategy_decision = selector.select(planner_proposed_config=config, competitive_state=cs)
            if strategy_decision.switched and strategy_decision.new_config_override:
                # FORCED-mode ablation only: override the config the NEXT tactical
                # turn will use. Never happens under NO_SWITCH (the default).
                config.clear()
                config.update(strategy_decision.new_config_override)
            snapshot = measure_snapshot(obs["day"], config, cs.own_economic_state.shed_total / 100.0)
            ctrace.record(
                turn=obs["day"] * 24 + obs.get("hour", 0), day=obs["day"],
                economic_state_summary={"cash": cs.own_economic_state.cash, "n_hands": cs.own_economic_state.n_hands},
                competitive_state_summary=summarize_competitive(cs),
                market_observation_record=market_logger.to_records()[-1],
                opponent_observation_record=opponent_logger.to_records()[-1],
                planner_decision_record={"config": {k: v for k, v in config.items() if not str(k).startswith("_")}},
                strategy_decision=strategy_decision,
                inferred_regime=None, strategy_confidence=None,
            )

        return action

    agent._planner = planner
    agent._opponent_logger = opponent_logger
    agent._market_logger = market_logger
    agent._selector = selector
    agent._ctrace = ctrace
    return agent


def _reconstruct_planner_state(obs):
    from agents.phase2_6.state import adapt
    return adapt(obs)
