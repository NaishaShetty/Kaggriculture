"""
Collector: runs one episode through the frozen, unmodified simulator and
returns the full replay (env.toJSON()) plus run metadata. Identical in every
respect to how harness/run_episodes.py drives the environment -- this module
adds no agent wrapping, no simulator patching, no extra actions. It is a
read-only consumer of the same public API (`kaggle_environments.make`,
`env.run`, `env.toJSON`).
"""
import time

from kaggle_environments import make

from .schema import TELEMETRY_SCHEMA_VERSION


def run_episode(p0, p1, episode_steps, seed=None, extra_config=None):
    config = {"episodeSteps": episode_steps}
    if seed is not None:
        config["seed"] = seed
    if extra_config:
        config.update(extra_config)

    env = make("kaggriculture", configuration=config, debug=False)

    t0 = time.time()
    env.run([p0, p1])
    runtime_s = time.time() - t0

    replay = env.toJSON()

    meta = {
        "instrumentation_schema_version": TELEMETRY_SCHEMA_VERSION,
        "simulator_version": replay.get("version") or replay.get("module_version"),
        "environment_name": replay.get("name"),
        "p0": p0 if isinstance(p0, str) else getattr(p0, "__name__", str(p0)),
        "p1": p1 if isinstance(p1, str) else getattr(p1, "__name__", str(p1)),
        "seed": seed,
        "episode_steps_requested": episode_steps,
        "n_steps_recorded": len(replay["steps"]),
        "runtime_s": runtime_s,
        "configuration": replay.get("configuration"),
    }
    return replay, meta
