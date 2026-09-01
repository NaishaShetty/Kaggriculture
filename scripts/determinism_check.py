"""Run the exact same seed+agents twice and diff the full replay to confirm determinism."""
import json
from kaggle_environments import make

def run(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 200, "seed": seed}, debug=False)
    env.run(["starter", "starter"])
    return env.toJSON()

a = run(42)
b = run(42)

a_str = json.dumps(a, sort_keys=True)
b_str = json.dumps(b, sort_keys=True)

print("Identical replay JSON:", a_str == b_str)
if a_str != b_str:
    # find first differing step
    for i, (sa, sb) in enumerate(zip(a["steps"], b["steps"])):
        if json.dumps(sa, sort_keys=True) != json.dumps(sb, sort_keys=True):
            print("First differing step index:", i)
            break
else:
    print("Confirmed: identical seed -> bit-identical episode (given identical deterministic agents).")

final_a = a["steps"][-1]
final_b = b["steps"][-1]
print("Run A final rewards:", [s["reward"] for s in final_a])
print("Run B final rewards:", [s["reward"] for s in final_b])
