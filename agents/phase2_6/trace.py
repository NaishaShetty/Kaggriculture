"""
Phase 2.6 decision trace system. Every planning cycle (once per in-game day)
appends one JSON record to a JSONL trace file -- machine-readable, per the
brief section 33.10. Also records post-action verification results appended
retroactively (matched by day) once the NEXT cycle observes the outcome.
"""
import json
import os


class TraceWriter:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._f = open(path, "a")

    def _estimate_to_dict(self, est):
        if est is None:
            return None
        return {"value": est.value, "low": est.low, "high": est.high,
                "confidence": est.confidence, "basis": est.basis, "notes": est.notes}

    def record_cycle(self, turn, day, state_summary, all_evaluated, selected, rejected,
                      expected_state_delta, prior_cycle_verification=None):
        def ec_to_dict(ec):
            ev = ec["evaluated"]
            return {
                "candidate": ev["candidate"],
                "direct_cost": ev["direct_cost"],
                "expected_value": self._estimate_to_dict(ev["expected_value"]),
                "net_expected_value": ev["net_expected_value"],
                "model_function_used": ev["model_function_used"],
                "model_status": ev["model_status"],
                "classification": ec["classification"],
                "rejection_reason": ec.get("rejection_reason"),
            }

        record = {
            "turn": turn, "day": day,
            "state_summary": state_summary,
            "candidate_opportunities": [ec_to_dict(ec) for ec in all_evaluated],
            "n_candidates": len(all_evaluated),
            "selected_decisions": [ec_to_dict(ec) for ec in selected],
            "rejected_decisions": [ec_to_dict(ec) for ec in rejected],
            "expected_state_delta": expected_state_delta,
            "prior_cycle_verification": prior_cycle_verification,
        }
        self._f.write(json.dumps(record, default=str) + "\n")
        self._f.flush()
        return record

    def close(self):
        self._f.close()
