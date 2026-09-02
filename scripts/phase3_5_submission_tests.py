"""
Phase 3.5 submission-packaging regression tests. Run:
    python scripts/phase3_5_submission_tests.py

Covers the packaging-only changes made to prepare the first Kaggle
submission: the additive `artifact_path` parameter on
`make_intervention_agent`, `main.py`'s root-resolution logic (must work
without `__file__`, matching Kaggle's real exec()-based loader), the
episode-boundary reset, and an end-to-end smoke test of `main.py` itself
via `kaggle_environments`. Does NOT re-check strategy correctness (that is
Phase 3.3/3.4's job, covered by their own regression suites) -- only that
packaging did not change behavior and that the entry point actually runs.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase3_3.adapters.intervention_agent import make_intervention_agent
from agents.phase3_3.interventions import variant_d_production_substitution
from agents.phase3.opponent_classes import OPPONENT_CLASSES
from instrumentation.pipeline import run_and_analyze

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
PASS_COUNT = 0
FAIL_COUNT = 0


def check(name, cond):
    global PASS_COUNT, FAIL_COUNT
    if cond:
        PASS_COUNT += 1
        print(f"  PASS  {name}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL  {name}")


def test_artifact_path_override_is_backward_compatible():
    print("artifact_path override backward-compatibility:")
    seed = 700002
    default_agent = make_intervention_agent(intervention_fn=variant_d_production_substitution, trace_path=None)
    explicit_path = os.path.abspath("results/phase3_3/detector/artifact.json")
    explicit_agent = make_intervention_agent(intervention_fn=variant_d_production_substitution, trace_path=None,
                                              artifact_path=explicit_path)
    r1, _, _ = run_and_analyze(default_agent, OPPONENT_CLASSES["expansion_oriented"](), 720, seed,
                                "phase3_5_test", "default_path")
    r2, _, _ = run_and_analyze(explicit_agent, OPPONENT_CLASSES["expansion_oriented"](), 720, seed,
                                "phase3_5_test", "explicit_path")
    check("explicit absolute artifact_path produces IDENTICAL outcome to the default relative path",
          r1["outcome"]["final_money"] == r2["outcome"]["final_money"])
    check("explicit-path run still reproduces the known Phase 3.3 reference value ($19,367)",
          r2["outcome"]["final_money"][0] == 19367.0)


def test_main_py_importable_and_correct_agent():
    print("main.py importability and agent identity:")
    import importlib
    spec = importlib.util.spec_from_file_location("submission_main", os.path.join(ROOT, "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    check("main.py exposes a callable named 'agent'", callable(getattr(mod, "agent", None)))
    # NOTE: main.py is overwritten on each promotion (Submission A -> B -> C -> ...), same as
    # every prior phase. This check is deliberately promotion-agnostic (it does not hardcode
    # which phase's agent-builder main.py currently imports) so it does not go stale the next
    # time a new submission is promoted -- see scripts/phase3_8_regression_tests.py for the
    # Submission-C-specific check that main.py builds make_competitive_v3_agent.
    builder_names = [n for n in dir(mod) if n.startswith("make_competitive_v") and n.endswith("_agent")]
    check("main.py builds its agent via some make_competitive_vN_agent constructor",
          any(getattr(mod, n) is not None for n in builder_names))


def test_episode_boundary_reset():
    print("episode-boundary reset logic:")
    import importlib
    spec = importlib.util.spec_from_file_location("submission_main2", os.path.join(ROOT, "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fake_obs_day0 = {"day": 0, "hour": 0}
    fake_obs_mid = {"day": 5, "hour": 3}
    check("day=0,hour=0 is treated as a new episode", mod._new_episode(fake_obs_day0))
    check("day=5,hour=3 is NOT treated as a new episode", not mod._new_episode(fake_obs_mid))


def test_end_to_end_smoke_via_kaggle_environments():
    print("end-to-end smoke test (kaggle_environments, main.py as a file path, vs. built-in 'random'):")
    script = f"""
import sys
sys.path.insert(0, r"{ROOT}")
from kaggle_environments import make
env = make("kaggriculture", configuration={{"episodeSteps": 240}}, debug=False)
env.run([r"{os.path.join(ROOT, 'main.py')}", "random"])
last = env.steps[-1][0].observation
print("OK", last["farms"][0]["money"], last["farms"][1]["money"], len(env.steps))
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd="C:\\Users",
                             timeout=120)
    ok = result.returncode == 0 and "OK" in result.stdout
    check("main.py runs a full smoke episode via kaggle_environments' own file-loading path "
          "(exec()-based, no __file__) with cwd deliberately set OUTSIDE the repo", ok)
    if not ok:
        print("    STDOUT:", result.stdout[-2000:])
        print("    STDERR:", result.stderr[-2000:])


def main():
    test_artifact_path_override_is_backward_compatible()
    test_main_py_importable_and_correct_agent()
    test_episode_boundary_reset()
    test_end_to_end_smoke_via_kaggle_environments()
    print(f"\n{PASS_COUNT} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT:
        sys.exit(1)


if __name__ == "__main__":
    main()
