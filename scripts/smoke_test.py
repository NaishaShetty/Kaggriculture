"""Phase 1 smoke test: verify the kaggriculture env installs and runs end to end."""
from kaggle_environments import make


def my_agent(obs):
    if obs.get("step", 0) == 0:
        return {"farmer": ["PASS"], "market": [["BUY_SEED", "WHEAT", 1]]}
    return {"farmer": ["PASS"], "market": []}


def main():
    env = make("kaggriculture", configuration={"episodeSteps": 50}, debug=True)
    print("Made env OK. name =", env.name)
    print("Config:", env.configuration)
    env.run([my_agent, "random"])
    final = env.steps[-1]
    for i, s in enumerate(final):
        print(f"Player {i}: reward={s.reward}, status={s.status}")
    print("Total steps recorded:", len(env.steps))
    print("First obs keys:", list(env.steps[0][0].observation.keys()))


if __name__ == "__main__":
    main()
