"""Quick sanity smoke test for agents/phase2_3/common.py -- not part of the
formal experiment campaign. Prints final money for a handful of configs so
obvious bugs (crashes, zero production, runaway spend) surface fast."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_3.common import make_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402

CASES = [
    ("wheat_solo_0hands", make_agent(crops="WHEAT")),
    ("wheat_solo_2hands", make_agent(crops="WHEAT", n_hands=2)),
    ("melon_solo_0hands", make_agent(crops="MELON")),
    ("melon_solo_2hands_1land", make_agent(crops="MELON", n_hands=2, land_quadrants=1, land_buy_day=0)),
    ("wheat_goose_pair", make_agent(crops="WHEAT", n_hands=1, animals={"GOOSE": 1}, animal_buy_day=0)),
    ("melon_goose_fert", make_agent(crops={"MELON": 1.0}, n_hands=2, animals={"GOOSE": 2}, animal_buy_day=0,
                                     collect_fertilizer=True, fertilizer_apply=True)),
]

STEPS = 300  # ~12.5 days -- enough to see hires/land/animals/first harvests, cheap to iterate on
for name, agent in CASES:
    record, replay, extracted = run_and_analyze(agent, "pass", STEPS, 999, "smoke", name)
    fin = record["players"][0]["financial_summary"]
    val = record["players"][0]["validation"]["overall"]
    crop_m = record["players"][0]["crop_metrics"]
    animal_m = record["players"][0]["animal_metrics"]
    print(f"{name:32s} final_money={fin['final_money']:>10.1f} valid={val:8s} "
          f"crops={ {k: v.get('total_harvested_units') for k, v in crop_m.items()} } "
          f"animals={ {k: v.get('total_product_units') for k, v in animal_m.items()} }")
