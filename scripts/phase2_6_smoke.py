"""
Phase 2.6 planner smoke test (brief section 33.19). Verifies the full path:
environment -> state adapter -> economic model -> candidate generation ->
evaluation -> decision -> execution -> state verification -> trace, end to
end, on one short episode, before any larger evaluation is attempted.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_6.common import make_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

TRACE_PATH = "results/phase2_6/planner_v1/traces/smoke_test.jsonl"
os.makedirs(os.path.dirname(TRACE_PATH), exist_ok=True)
if os.path.exists(TRACE_PATH):
    os.remove(TRACE_PATH)

agent = make_agent(trace_path=TRACE_PATH)
record, replay, extracted = run_and_analyze(agent, "pass", 240, 999001, "smoke26", "ep000")
agent._tracer.close()

print("final_money:", record["outcome"]["final_money"])
print("validation:", record["players"][0]["validation"]["overall"])

with open(TRACE_PATH) as f:
    lines = [json.loads(l) for l in f]
print(f"\n{len(lines)} planning cycles recorded")
for rec in lines[:3]:
    print(f"day={rec['day']} n_candidates={rec['n_candidates']} n_selected={len(rec['selected_decisions'])}")
    for sel in rec["selected_decisions"]:
        print(f"    SELECTED: {sel['candidate']['description']} "
              f"(net_expected_value={sel['net_expected_value']}, confidence={sel['expected_value']['confidence']})")
    if rec["prior_cycle_verification"]:
        print(f"    prior-cycle verification: {rec['prior_cycle_verification']}")

assert record["players"][0]["validation"]["overall"] in ("PASS", "PARTIAL"), "smoke test: validation FAILed"
assert len(lines) >= 5, "smoke test: too few planning cycles recorded"
print("\nSMOKE TEST PASSED")
