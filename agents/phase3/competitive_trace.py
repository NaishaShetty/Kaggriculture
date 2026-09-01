"""
Phase 3.1 competitive trace -- extends the Phase 2.6 decision trace schema
with competitive context (brief section 24). Phase 3.1 populates every
field it can (economic_state, competitive_state, market/opponent
observations, selected_strategy from the stub selector) but leaves
`inferred_regime`/`strategy_confidence` as explicit None/placeholder,
since no regime inference exists yet (Phase 3.2 concern) -- the SCHEMA
supports them, per the brief's instruction, without fabricating values.
"""
import json
import os


class CompetitiveTraceWriter:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._f = open(path, "a")

    def record(self, turn, day, economic_state_summary, competitive_state_summary,
               market_observation_record, opponent_observation_record,
               planner_decision_record, strategy_decision, inferred_regime=None, strategy_confidence=None,
               expected_value=None, actual_outcome=None):
        record = {
            "turn": turn, "day": day,
            "economic_state": economic_state_summary,
            "competitive_state": competitive_state_summary,
            "market_observation": market_observation_record,
            "opponent_observation": opponent_observation_record,
            "inferred_regime": inferred_regime,          # ALWAYS None in Phase 3.1 -- schema placeholder only
            "selected_strategy": {
                "mode": strategy_decision.mode.value, "switched": strategy_decision.switched,
                "reason": strategy_decision.reason,
            },
            "strategy_confidence": strategy_confidence,   # ALWAYS None in Phase 3.1
            "planner_decision": planner_decision_record,
            "expected_value": expected_value, "actual_outcome": actual_outcome,
        }
        self._f.write(json.dumps(record, default=str) + "\n")
        self._f.flush()
        return record

    def close(self):
        self._f.close()
