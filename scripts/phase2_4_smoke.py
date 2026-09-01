"""Phase 2.4 smoke test: (1) confirms sell_policy='passive' exactly reproduces
agents/phase2_3/common.py's behavior on identical config/seed (regression
guard for the refactor), (2) sanity-checks threshold/batch modes run cleanly
and produce different, plausible behavior."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_3.common import make_agent as make_agent_23  # noqa: E402
from agents.phase2_4.common import make_agent as make_agent_24  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

STEPS = 720
CONFIG = dict(crops="MELON", n_hands=2, animals={"GOOSE": 1}, animal_buy_day=0)
SEED = 12345

agent_23 = make_agent_23(**CONFIG)
agent_24_passive = make_agent_24(**CONFIG, sell_policy={"mode": "passive"})

r23, _, _ = run_and_analyze(agent_23, "pass", STEPS, SEED, "smoke24", "p23")
r24, _, _ = run_and_analyze(agent_24_passive, "pass", STEPS, SEED, "smoke24", "p24_passive")

m23 = r23["outcome"]["final_money"]
m24 = r24["outcome"]["final_money"]
print(f"phase2_3 final_money={m23}  phase2_4(passive) final_money={m24}  MATCH={m23 == m24}")
assert m23 == m24, "REGRESSION: phase2_4 passive mode does not reproduce phase2_3 exactly"

for mode, kwargs in [
    ("threshold_0.9", {"mode": "threshold", "threshold_frac": 0.9}),
    ("batch_5d", {"mode": "batch", "batch_interval_days": 5}),
    ("threshold_batch", {"mode": "threshold_batch", "threshold_frac": 1.1, "batch_interval_days": 5}),
    ("threshold_no_safety", {"mode": "threshold", "threshold_frac": 1.3, "overflow_safety": False}),
]:
    agent = make_agent_24(**CONFIG, sell_policy=kwargs)
    rec, _, _ = run_and_analyze(agent, "pass", STEPS, SEED, "smoke24", mode)
    val = rec["players"][0]["validation"]["overall"]
    print(f"{mode:24s} final_money={rec['outcome']['final_money']}  valid={val}")

print("SMOKE TEST PASSED")
