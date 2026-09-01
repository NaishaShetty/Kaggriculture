# Phase 1 Freeze Manifest

**Freeze tag**: `phase1-frozen` (no git repository present — see Git Freeze section below for how
this tag is represented instead)
**Freeze date**: 2026-08-16
**Phase 1 status carried into this freeze**: PASS
**Phase 2.0 (this gate) status**: see [../docs/PHASE2_0_REPORT.md](../docs/PHASE2_0_REPORT.md)

## Project state at freeze time

- Not a git repository (`git status` → `fatal: not a git repository`). No branches, no tags exist
  because there is no repository. See §Git Freeze Point below.
- Python: 3.11.3, venv at `C:\kagvenv` (short-path, required — see `environment.txt`).
- `kaggle-environments`: **1.32.7**, registered env `"kaggriculture"`.
- Kaggle CLI: **2.2.4** (inside `C:\kagvenv`).
- OS: Windows 11 Home, build 10.0.26200, x86_64.

## File hashes (SHA-256)

Full machine-readable list: [hashes.txt](hashes.txt). Summary of what's covered:

| Category | File | SHA-256 |
|---|---|---|
| Simulator (installed = vendored, verified identical) | `vendor_kaggriculture/kaggriculture.py` | `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e` |
| Simulator spec | `vendor_kaggriculture/kaggriculture.json` | `a82c89c1a2315b93f39775d8e025471a01b738647c9772658368ee6b1b6f4867` |
| Package's own README (⚠ hinge pricing, current) | `vendor_kaggriculture/README.md` | `3081e52baf8eb2da5d861acc63a3636ce29425f6bdb79a67036ba234ac4ade00` |
| Package's own AGENTS.md | `vendor_kaggriculture/AGENTS.md` | `e1a80501a7b02a212eaac9370ada4129a64e0ee6cb3cbc790f3d77d22863fe22` |
| Official downloaded README (⚠ stale, non-hinge — see discrepancy log) | `kaggriculture-data/README.md` | `63d0497ca655ea1857a96a3226bed6664a2fa98506d76d1fa14ce9101c5f1d34` |
| Official downloaded AGENTS.md (matches package) | `kaggriculture-data/AGENTS.md` | `e1a80501a7b02a212eaac9370ada4129a64e0ee6cb3cbc790f3d77d22863fe22` |
| Official downloaded zip | `kaggriculture-data/kaggriculture.zip` | `1e0ab343e7c959954095926e18030c21d9be40946ab814ca6b2ce6cb8a94a32f` |
| **Frozen baseline agent** | `agents/baseline_agent.py` | `d007f1ed0c025f6fc90d9914c371e49cf2e49ac4f6183fb6c9554079847ecefd` |
| **Frozen evaluation harness** | `harness/run_episodes.py` | `099ef1a01d38eb3019b3365bcbe757155dd3c574aeeda5199c08862c8104319e` |
| Smoke test script | `scripts/smoke_test.py` | `f7c757082f86e93b325db563da03cb2b9ce477f7050bea1bdc0ca0781dda40b2` |
| Determinism check script | `scripts/determinism_check.py` | `92e640073745c8892446859348ee67126d9abe611f3003ee39ed3f4d31b7205c` |
| Overview capture | `docs/00_official_overview_raw.md` | `cf216a18bd0afac35919e27d45a8621fb4692c1f5f61dd31ecef54308dcbb1de` |
| Mechanics reference | `docs/01_mechanics_reference.md` | `fb916b46242967e7220ec4baafb6571191ba60608deead20873cae4ead382dfd` |
| Architecture map | `docs/02_architecture_map.md` | `f72658d4d36b2d335d58429ad704aee3775f4c4e55aa16450c86541191d340a7` |
| Phase 1 report | `docs/PHASE1_REPORT.md` | `fa5d7b24829f3f6409c0ff435dd06c65db12fe09731acbc7d2a675649afb486f` |

**Confirmed match**: installed simulator source (`C:\kagvenv\...\kaggriculture.py`) and the vendored
copy used throughout Phase 1 are byte-identical (same hash). Same for the spec JSON and package's own
README/AGENTS.md. This confirms Phase 1's experiments ran against exactly the source code preserved
in this repository.

## Experiment references (historical, immutable — Phase 1)

| Directory | Matchup | Episodes | Seed range |
|---|---|---|---|
| `results/starter_vs_random` | starter vs random | 10 | 1000-1009 |
| `results/pass_vs_random` | pass vs random | 10 | 2000-2009 |
| `results/pass_vs_starter` | pass vs starter | 10 | 3000-3009 |
| `results/determinism_check_starter_v_starter` | starter vs starter | 3 | 500-502 |
| `results/baseline_vs_pass` | baseline vs pass | 15 | 100-114 |
| `results/baseline_vs_random` | baseline vs random | 15 | 200-214 |
| `results/baseline_vs_starter` | baseline vs starter | 15 | 300-314 |
| `results/smoke_baseline_vs_starter*` | early dev smoke tests (baseline agent under development, incl. the pre-fix losing-money version) | 2-3 each | 9000+ |

**None of these were modified, deleted, or regenerated during this freeze.**

## New artifacts from this freeze (Phase 2.0), kept separate from Phase 1 history

| Directory | Purpose |
|---|---|
| `phase1_freeze/reproducibility_results/repro_baseline_vs_{pass,random,starter}` | Re-run of the exact three baseline benchmarks, same seed ranges, for reproducibility comparison |
| `phase1_freeze/reproducibility_results/sanity_pass_vs_pass` | Sanity check: PASS vs PASS |
| `phase1_freeze/reproducibility_results/sanity_pass_vs_starter` | Sanity check: PASS vs STARTER |
| `phase1_freeze/reproducibility_results/sanity_baseline_vs_pass` | Sanity check: baseline vs PASS |
| `phase1_freeze/reproducibility_results/determinism_rerun.txt` | Re-run of the seed-42 starter-vs-starter determinism check |
| `phase1_freeze/pip_freeze.txt` | Full dependency snapshot |
| `phase1_freeze/environment.txt` | Human-readable environment/reproduction procedure |
| `phase1_freeze/hashes.txt` | Machine-readable SHA-256 manifest |

## Reproduction commands

```bash
# 1. Create/activate the environment (short path required on Windows, see environment.txt)
python -m venv C:\kagvenv
C:\kagvenv\Scripts\python.exe -m pip install --no-deps kaggle-environments
C:\kagvenv\Scripts\python.exe -m pip install Flask jsonschema numpy pygame pyjson5 termcolor requests tenacity google-auth pydantic kaggle

# 2. Simulator smoke test
C:\kagvenv\Scripts\python.exe scripts/smoke_test.py

# 3. Determinism check
C:\kagvenv\Scripts\python.exe scripts/determinism_check.py

# 4. Evaluation harness (example: baseline vs starter, 15 episodes, fixed seeds)
cd harness
C:\kagvenv\Scripts\python.exe run_episodes.py --p0 ../agents/baseline_agent.py --p1 starter \
  --episodes 15 --steps 720 --seed-base 300 --out ../results --tag baseline_vs_starter

# 5. Baseline benchmark battery (all three opponents)
C:\kagvenv\Scripts\python.exe run_episodes.py --p0 ../agents/baseline_agent.py --p1 pass    --episodes 15 --steps 720 --seed-base 100 --out ../results --tag baseline_vs_pass
C:\kagvenv\Scripts\python.exe run_episodes.py --p0 ../agents/baseline_agent.py --p1 random  --episodes 15 --steps 720 --seed-base 200 --out ../results --tag baseline_vs_random
C:\kagvenv\Scripts\python.exe run_episodes.py --p0 ../agents/baseline_agent.py --p1 starter --episodes 15 --steps 720 --seed-base 300 --out ../results --tag baseline_vs_starter
```

Verify hashes with: `sha256sum -c phase1_freeze/hashes.txt` (from the project root, after adjusting
path separators if run under native Windows rather than Git Bash).
