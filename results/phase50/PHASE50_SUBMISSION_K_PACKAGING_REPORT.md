# Phase 50: Submission K Packaging — Phase 48's Capped-Animal-Target Fix

No frozen file touched (`main.py` at repo root, `agents/phase2_6/`,
`agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`,
`agents/phase2_3/common.py`, `agents/phase2_4/common.py`, `agents/phase15/`,
`agents/phase21/` itself). All new code lives in `scripts/phase50_build_submission.py`
and `scripts/phase50/`; all new results in `results/phase50/`. The repo root
`main.py` is untouched and continues to build Submission C/E exactly as
before. `agents/phase21/portfolio.py::portfolio_targets` is imported
unmodified throughout, exactly as Phase 48 built it.

## Executive Summary

**[VERIFIED] `kaggriculture_phase50_submission_K.tar.gz` (SHA-256
`22a48aecee99c0d69b11151011558326de9208ae8102311b70e533271796cb3c`) is ready
to upload.** Packaging surfaced **no discrepancy of any kind** — the
dependency closure was clean on the first attempt, the cold-process test
passed clean, the regression suite held at the same 128/133 baseline every
submission since Phase 20 has carried, and the packaged artifact's
re-confirmed 15-seed head-to-head numbers matched Phase 48's own in-repo
Part C validation **exactly, to the dollar, on all 45 seed×opponent data
points** (15/15 vs. Submission G, margin $14,842.73; 15/15 vs. Submission C,
margin $43,501.13; 15/15 vs. the Phase 43 Jonaid archetype, margin
$36,256.73 — every one identical to the numbers in
`results/phase48/PHASE48_FERTILIZER_LAND_ANIMAL_TARGET_RETEST_REPORT.md`
Section 4). This is the same clean-packaging outcome Phase 47 had for
Submission J, this time genuinely with zero bugs found in either the
packaged strategy or this phase's own new validation tooling.

## 1. Confirming the Exact Factory Chain to Ship (Not Assumed)

Read directly, not assumed, per this phase's own instruction:

- `scripts/phase48/capped_animal_portfolio_agent.py::make_capped_animal_portfolio_agent`
  is the packaging-style adapter. Its own source (`CAP_TOTAL = 8` at module
  level, `def make_capped_animal_portfolio_agent(cap_total=CAP_TOTAL)`)
  **[VERIFIED] confirms `cap_total`'s default is 8** — the exact value
  Phase 48's own screen (Section 4 of that report) validated as strictly
  better than cap=9 and every uncapped baseline on all 4 development seeds.
  This phase packages that default unchanged; no other value was
  substituted.
- It composes `scripts/phase48/capped_animal_portfolio.py::make_capped_animal_target_fn(cap_total=8, base_target_fn=portfolio_targets)`,
  which itself imports `agents/phase21/portfolio.py::portfolio_targets`
  **unmodified** (confirmed by direct read: `from agents.phase21.portfolio
  import portfolio_targets` — only the `"animals"` field of its returned
  dict is touched; `land`, `hands`, `crop_tile_target`, `crop_fractions`
  pass through byte-for-byte unchanged).
- It composes `scripts/phase46/feed_priority_execution.py::make_feed_priority_execution_agent` —
  **[VERIFIED] byte-for-byte identical to Submission J's own shipped
  execution layer** (confirmed directly: the dependency-closure check in
  Section 3 below hashes this exact file against the repo source and it
  matches; it is imported directly, not copied or modified, by
  `capped_animal_portfolio_agent.py`).
- `agents/phase3/opponent_observation.py::OpponentObservationLogger` is
  wired in the same way Phase 46/47's own adapter
  (`scripts/phase46/feed_priority_portfolio_agent.py`) does it.

This is the exact chain Phase 48's Section 4/"Changed Files" list describes
and the exact chain this phase packages — no substitution, no different
default.

## 2. Confirming the Submission Letter

**[VERIFIED]** Listed every `kaggriculture_*.tar.gz` in the repo root before
choosing a letter (per this phase's own instruction, not assuming "K" is
correct without checking):

```
kaggriculture_phase12_submission_E.tar.gz
kaggriculture_phase18_submission_F.tar.gz
kaggriculture_phase20_submission_G.tar.gz
kaggriculture_phase29_submission_H.tar.gz
kaggriculture_phase37_submission_I.tar.gz
kaggriculture_phase3_4_variantD_submission_A.tar.gz
kaggriculture_phase3_5_competitive_v2_submission_B.tar.gz
kaggriculture_phase3_8_submission_C.tar.gz
kaggriculture_phase47_submission_J.tar.gz
kaggriculture_phase7_submission_D.tar.gz
```

A-J are all taken (Variant D "A", competitive_v2 "B", phase3_8 "C",
sell-safety fix "D", F-005 fix "E", macro-controller "F", macro-controller +
liquidity guard "G", shared-market portfolio agent "H", cash-pacer "I", FEED
tier-0.5 fix "J"). **K is confirmed free and is the letter used.**

## 3. Packaging Script and Dependency Closure

`scripts/phase50_build_submission.py` follows `scripts/phase47_build_submission.py`'s
exact structure: a package-local `main.py` (embedded as a string constant,
never the repo root's `main.py`) with the identical Kaggle-compatible
root-resolution fallback (`_resolve_submission_root()`, unchanged from
Phase 37/47's own verbatim logic — `sys.path[-1]`-based, handling
`exec()`-based loading with no `__file__`), wiring in the Phase 48 factory
chain confirmed in Section 1.

**FILES list** (14 non-`main.py` files, one more than Phase 47's 13 — the
two new Phase 48 wrapper files replace Phase 46's single adapter file):

```
vendor_kaggriculture/kaggriculture.py
vendor_kaggriculture/kaggriculture.json
agents/__init__.py
agents/phase2_3/common.py
agents/phase3/__init__.py
agents/phase3/opponent_observation.py
agents/phase21/__init__.py
agents/phase21/portfolio.py
agents/phase21/execution.py
agents/phase21/liquidation.py
agents/phase21/risk_posture.py
scripts/phase46/feed_priority_execution.py
scripts/phase48/capped_animal_portfolio.py
scripts/phase48/capped_animal_portfolio_agent.py
```

Traced by direct import reading (confirmed via `grep` of every file's own
`import`/`from` lines, Section "dependency closure" comment in the script
itself): `capped_animal_portfolio_agent.py` → `agents.phase3.opponent_observation`
+ `scripts.phase46.feed_priority_execution` (→ `vendor_kaggriculture.kaggriculture`,
`agents.phase21.risk_posture`, `agents.phase21.liquidation`,
`agents.phase21.execution`, `agents.phase2_3.common`) + `scripts.phase48.capped_animal_portfolio`
(→ `agents.phase21.portfolio` → `agents.phase21.execution` + `agents.phase21.liquidation`).
Confirmed directly: does **not** import `agents/phase21/adapters/portfolio_agent.py`
(Submission H/I's entry point) nor `scripts/phase46/feed_priority_portfolio_agent.py`
(Submission J's own adapter — a structurally identical but separate wiring
file, not itself imported by the Phase 48 adapter). `scripts/`,
`scripts/phase46/`, and `scripts/phase48/` are confirmed namespace packages
(no `__init__.py` in any of the three); `agents/phase3/` and
`agents/phase21/` do have `__init__.py` and both ship.

**Tarball built**: `kaggriculture_phase50_submission_K.tar.gz`, 45,013 bytes
(44.0 KB), 15 files (14 dependency files + package-local `main.py`), SHA-256
`22a48aecee99c0d69b11151011558326de9208ae8102311b70e533271796cb3c`.

### 3a. Dependency-Closure Check — [VERIFIED] Clean

`scripts/phase50/dependency_closure_check.py` performed a byte-for-byte
SHA-256 comparison of all 14 non-`main.py` packaged files against their repo
sources:

```
All 14 packaged files are byte-for-byte identical to their repo sources. Clean.
```

Every one of the 14 files matched on the first run — no discrepancy found,
no fix needed.

## 4. Cold-Process Test — [VERIFIED] Clean

`scripts/phase50/cold_process_test.py` extracted the tarball to
`C:/tmp/phase50_coldtest` (outside the repo), then loaded `main.py` via
`exec()` with `__file__` deliberately unset (matching Kaggle's own loading
mechanism), and ran a full 720-turn episode via `kaggle_environments`
against the environment's built-in random opponent:

```
agent callable after exec: True
statuses: ['DONE', 'DONE']
final rewards (ours vs random): [70724.0, 0.0]
```

(The OpenSpiel "Unknown game" warnings preceding this output are unrelated
import-time noise from an unrelated dependency inside `kaggle_environments`
itself, not specific to this package — the same noise every prior phase's
cold-process test has also emitted.) Both statuses `DONE`, our agent
$70,724.00 vs. random's $0.00 — clean, no crash, no exception.

## 5. Full Regression Suite — [VERIFIED] Unchanged at 128/133

Ran all 8 canonical regression scripts from the repo root (confirmed this is
the correct invocation — no `pytest`/`tox`/`setup.cfg` config exists in the
repo; each script is a standalone hand-rolled `check()` counter, and "133"
is the sum of all 8 scripts' individual check counts):

| Script | Passed | Failed |
|---|---|---|
| `phase2_6_regression_tests.py` | 18 | 0 |
| `phase3_1_regression_tests.py` | 21 | 0 |
| `phase3_2_regression_tests.py` | 13 | 1 |
| `phase3_3_regression_tests.py` | 11 | 1 |
| `phase3_4_regression_tests.py` | 13 | 1 |
| `phase3_5_regression_tests.py` | 19 | 1 |
| `phase3_8_regression_tests.py` | 12 | 1 |
| `phase12_regression_tests.py` | 21 | 0 |
| **Total** | **128** | **5** |

**[VERIFIED] 128/133, the identical count and the identical 5 failing
checks every submission since Phase 7/20 has carried** — each of the 5
failures is the same pre-existing "frozen Planner v1 remains byte-for-byte
unchanged" stale-hash-pin assertion (in `phase3_2`, `phase3_3`, `phase3_4`,
`phase3_5`, `phase3_8`'s own "control integrity" check), comparing current
files against `results/phase3_1/control_reproduction/frozen_file_hashes.txt`,
known stale since Phase 7 and never a real regression. **The count did not
change** — no new failure, no fewer failures than expected.

## 6. Packaged-Artifact Re-Confirmation — [VERIFIED] Matches Phase 48 Exactly, to the Dollar

`scripts/phase50/reconfirm_packaged_head_to_head.py` was built using Phase
47's own `scripts/phase47/reconfirm_packaged_head_to_head.py` as a direct
template, per this phase's instruction. Both of Phase 47's own previously-
found pitfalls were checked directly rather than assumed to be already
fixed by copying the template:

**Pitfall 1 — REPO_ROOT dirname()-count off-by-one.** This script sits at
`scripts/phase50/reconfirm_packaged_head_to_head.py`, the identical
directory depth below the repo root as Phase 47's own script
(`scripts/phase47/...`) — both are exactly two directories below the root,
so the same three chained `os.path.dirname()` calls apply. Rather than
assume this transfers automatically, the script asserts directly at runtime
that `REPO_ROOT` contains `main.py`, `agents/`, `scripts/`, and
`vendor_kaggriculture/` before doing anything else — confirmed at actual
run time:

```
REPO_ROOT resolved to: C:\Kaggriculture (verified: contains main.py, agents/,
scripts/, vendor_kaggriculture/ -- not scripts/ or scripts/phase50/)
```

**Pitfall 2 — missing `importlib.invalidate_caches()`.** Included in the
same place Phase 47's fixed version puts it: immediately after `sys.path` is
repointed back to the repo root and `sys.modules` is cleared, before
importing `agents.phase15`/`agents.phase3_8`/`scripts.phase43` fresh from
the repo. The script also asserts directly (not just via the docstring
claim) that the packaged agent resolves from under `EXTRACTED_ROOT` and that
the opponents/engine resolve from under `REPO_ROOT` — both assertions passed
silently (no `AssertionError`), confirmed by the printed resolution paths:

```
packaged make_capped_animal_portfolio_agent resolved from: scripts.phase48.capped_animal_portfolio_agent (C:\tmp/phase50_coldtest\scripts\phase48\capped_animal_portfolio_agent.py)
opponents/engine resolved from repo root: C:\Kaggriculture (verified via make_macro_agent's module file)
```

**Result — full 15-seed set (development + validation + held-out), packaged
artifact only:**

| Matchup | Packaged artifact (this phase) | Phase 48 in-repo (Section 4) | Match? |
|---|---|---|---|
| vs. Submission G | 15/15, mean margin $14,842.73 | 15/15, mean margin $14,842.73 | **[VERIFIED] Exact** |
| vs. Submission C | 15/15, mean margin $43,501.13 | 15/15, mean margin $43,501.13 | **[VERIFIED] Exact** |
| vs. Jonaid | 15/15, mean margin $36,256.73 | 15/15, mean margin $36,256.73 | **[VERIFIED] Exact** |

All three mean margins match Phase 48's own in-repo numbers to the cent, and
every individual per-seed value in `results/phase50/phase50_reconfirm_packaged_h2h_15seed_full.json`
matches the corresponding row in Phase 48's own
`results/phase48/phase48_animal_cap_h2h_15seed_full.json` (`capped_animal_8`
condition) exactly — **zero mismatches across all 45 seed×opponent data
points.** No discrepancy was found in this re-confirmation; no fix was
required.

## 7. Summary Table

| Validation step | Result |
|---|---|
| Factory chain confirmed (Section 1) | `make_capped_animal_portfolio_agent(cap_total=8 default)` → `make_capped_animal_target_fn` (wraps `portfolio_targets` unmodified) + `make_feed_priority_execution_agent` (byte-identical to Submission J's) |
| Submission letter confirmed (Section 2) | K (A-J taken, confirmed by listing repo root) |
| Dependency-closure check | **Clean** — 14/14 files byte-for-byte identical to repo sources |
| Cold-process test | **Clean** — `DONE`/`DONE`, $70,724.00 vs. random's $0.00 |
| Regression suite | **Unchanged, 128/133** — same 5 pre-existing stale-hash-pin failures |
| Packaged-artifact re-confirmation | **Exact match to Phase 48**, all 45 seed×opponent data points, zero mismatches |

## 8. Ready-to-Upload Confirmation

**No discrepancy of any kind was found at any validation step.** The
packaged strategy, the dependency closure, the cold-process behavior, the
regression suite, and the packaged-artifact's head-to-head numbers all
checked out clean on the first attempt — a genuinely uneventful packaging
phase, reported honestly as such (unlike Phase 47, which found and fixed two
real bugs in its own new tooling; this phase's own new tooling, built
directly against Phase 47's template with both known pitfalls explicitly
checked via runtime assertions rather than assumed fixed, needed no
after-the-fact correction).

**`kaggriculture_phase50_submission_K.tar.gz` (SHA-256
`22a48aecee99c0d69b11151011558326de9208ae8102311b70e533271796cb3c`) is ready
to upload.**

## Changed Files

New, additive only (no frozen file touched, `agents/phase21/` and
`agents/phase15/` untouched, repo root `main.py` untouched):

- `scripts/phase50_build_submission.py` (packaging script)
- `scripts/phase50/dependency_closure_check.py` (Section 3a)
- `scripts/phase50/cold_process_test.py` (Section 4)
- `scripts/phase50/reconfirm_packaged_head_to_head.py` (Section 6)
- `results/phase50/phase50_reconfirm_packaged_h2h_15seed_full.json`
- `results/phase50/PHASE50_SUBMISSION_K_PACKAGING_REPORT.md` (this file)
- `kaggriculture_phase50_submission_K.tar.gz` (repo root — the submission artifact itself)
