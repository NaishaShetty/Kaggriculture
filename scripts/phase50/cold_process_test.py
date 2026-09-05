"""
Phase 50, cold-process test -- mirrors Phase 47's own Section 5b exactly.
Loads the extracted package's main.py via exec() with __file__ deliberately
unset (matching Kaggle's own exec()-based loading mechanism), then runs a
full 720-turn episode via kaggle_environments against the environment's
built-in random opponent.
"""
import os
import sys

EXTRACTED_ROOT = "C:/tmp/phase50_coldtest"


def main():
    os.chdir(EXTRACTED_ROOT)
    sys.path.append(os.path.abspath('.'))
    src = open('main.py').read()
    ns = {'__name__': 'submission_k_main'}
    exec(compile(src, '<string>', 'exec'), ns)
    agent = ns['agent']
    print("agent callable after exec:", callable(agent))

    import kaggle_environments as ke
    env = ke.make("kaggriculture", debug=True)
    env.reset()
    env.run([agent, "random"])
    statuses = [s["status"] for s in env.steps[-1]]
    rewards = [s["reward"] for s in env.steps[-1]]
    print("statuses:", statuses)
    print("final rewards (ours vs random):", rewards)


if __name__ == "__main__":
    main()
