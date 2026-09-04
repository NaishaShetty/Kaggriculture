# Phase 37: Packaging and Validating Submission I

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py` — the repo root `main.py` is unmodified and still builds Submission C/E). `agents/phase21/` was **not modified** by this phase, confirmed directly (Section 1). `agents/phase15/` (Submission G) was not touched.

## Executive Summary

**[VERIFIED] Submission I is built, packaged, and validated: `kaggriculture_phase37_submission_I.tar.gz`, SHA-256 `6a60947b2e3d8dd94679de01a81cf91807c1a2cad04f9902ccc232be86441848`, 42,061 bytes (41.1 KB), 14 files.**

- **[VERIFIED] Step 1's direct-read check found the premise needed correcting**: `agents/phase21/`'s own files are byte-identical to Submission H's shipped state — Phase 36's BUY_ANIMAL cash-reserve fix was built and validated entirely as new, separate code (`scripts/phase36/paced_execution.py`), never merged into `agents/phase21/execution.py` itself. Nothing else in `agents/phase21/` changed unexpectedly. This phase packages what Phase 36 actually validated, exactly where it lives, per this phase's own explicit constraint not to modify `agents/phase21/`'s own files.
- **Full existing regression suite**: 128/133 passing — identical to the state this project has held since Phase 20, same 5 pre-existing stale-`frozen_file_hashes.txt`/control-integrity failures, nothing new broken.
- **Cold-process test**: the package extracted to `C:/tmp/phase37_coldtest` (outside the repo), loaded via `exec()` with `__file__` deliberately unset (matching Kaggle's own loading mechanism), ran a full 720-turn episode to `DONE`/`DONE` status with a real final-money result ($71,377 vs. a random opponent's $0).
- **Re-confirmed head-to-head behavior on the PACKAGED artifact itself** (not just the in-repo module) against the in-repo Submission G: results on the 4 development seeds matched Phase 36's most recent in-repo validation **exactly, to the dollar, on every seed**.
- **Dependency-closure integrity**: all 13 non-`main.py` files in the package are byte-for-byte identical (SHA-256-verified) to their repo source files.

**This report documents that the package is correctly built and rigorously validated — the promotion basis (Phase 36's own 10/15 and 15/15 figures) is reused, not re-derived, per this phase's explicit scope.**

## 1. Confirming Phase 36's Fix Is Where It Actually Lives (Step 1)

**[VERIFIED, by direct read]** `agents/phase21/execution.py` contains NO `BUY_ANIMAL` reserve logic beyond `buy_n = min(still_needed, int(money // cost))` — the exact, unpaced state Submission H shipped. A direct listing of `agents/phase21/` confirms only `__init__.py`, `adapters/`, `execution.py`, `liquidation.py`, `portfolio.py`, `risk_posture.py` — no `paced_execution.py` or any other new file. **This confirms the task's premise needed a correction, not an assumption**: Phase 36's fix (the cash-reserve gate on `BUY_ANIMAL`) exists only in `scripts/phase36/paced_execution.py`, a standalone module Phase 36 built and validated separately, per that phase's own report ("No frozen file, `agents/phase21/`, or `agents/phase15/` was touched" — `results/phase36/PHASE36_ADAPTIVE_PACING_REPORT.md`).

Per this phase's own explicit constraint ("Do not modify `agents/phase21/`'s own files in this phase — package what Phase 36 already validated, don't tune anything further"), this package ships `scripts/phase36/paced_execution.py` **exactly where it already lives, unchanged**, wired to `agents/phase21/portfolio.py`'s own unmodified targets via a new, additive-only adapter (`scripts/phase37/paced_portfolio_agent.py`) that mirrors `agents/phase21/adapters/portfolio_agent.py`'s own structure exactly — same `OpponentObservationLogger` wiring, same `set_opponent_history` lifecycle, only the execution-layer factory differs (`make_paced_execution_agent` instead of `make_execution_agent`). An initial attempt to relocate `paced_execution.py` into `agents/phase21/` was intentionally abandoned in favor of this approach, since it would have meant adding a new file directly into that directory — the more conservative, literal reading of "do not modify `agents/phase21/`'s own files" was followed instead.

**[VERIFIED, by direct sanity check before proceeding]** The new adapter reproduces Phase 36's exact seed-700000 result before any packaging work began: `phase21(paced)=$55,204.00`, `submission_g=$51,182.00` — matching Phase 36's own reported figures for that seed exactly.

## 2. Dependency Closure

Traced directly from `scripts/phase37/paced_portfolio_agent.py`'s own import statements, transitively, by reading each imported module's own import block (not assumed):

```
scripts/phase37/paced_portfolio_agent.py
 ├─ agents/phase3/opponent_observation.py         (stdlib only: dataclasses, typing)
 ├─ agents/phase21/portfolio.py                    (UNCHANGED from Submission H)
 │    ├─ agents/phase21/execution.py               (UNCHANGED -- see below)
 │    └─ agents/phase21/liquidation.py              (UNCHANGED -- see below)
 └─ scripts/phase36/paced_execution.py             (Phase 36's validated fix, shipped unchanged)
      ├─ vendor_kaggriculture/kaggriculture.py     (CROPS, ANIMALS, LAND_PRICES)
      ├─ agents/phase21/risk_posture.py             (stdlib only -- no imports of its own)
      ├─ agents/phase21/liquidation.py
      │    └─ vendor_kaggriculture/kaggriculture.py (CROPS)
      ├─ agents/phase21/execution.py                (reuses bounded_multi_crop_tile_pool_assignment only)
      └─ agents/phase2_3/common.py
           └─ vendor_kaggriculture/kaggriculture.py (same file, same symbols)
```

**[VERIFIED] Does NOT import `agents/phase21/adapters/portfolio_agent.py`** (Submission H's own entry point) at all — the paced adapter is a separate, parallel entry point; `agents/phase21/adapters/` is not shipped in this package. **[VERIFIED] `agents/phase2_3/` and `vendor_kaggriculture/` are namespace packages** (no `__init__.py` in either, confirmed by direct directory listing, same as every prior submission). **[VERIFIED] `scripts/`, `scripts/phase36/`, and `scripts/phase37/` are ALSO namespace packages** (confirmed: none of the three has an `__init__.py`) — Python 3's PEP 420 namespace-package resolution needs none, provided the directories exist under a `sys.path` entry, the same mechanism `agents/phase2_3/` and `vendor_kaggriculture/` already rely on; the cold-process test (Section 5b) and cross-root reconfirmation (Section 5c) both directly confirm this resolves correctly, not just in theory. **`agents/phase3/` DOES have an (empty) `__init__.py`** that must still ship.

Final file list (`scripts/phase37_build_submission.py::FILES`, plus the package-local `main.py` this script writes): 13 dependency files + `main.py` = **14 files total**.

## 3. The Package's Own `main.py`

`scripts/phase37_build_submission.py` writes a NEW `main.py` content string to a temp file and adds it to the tarball with `arcname="main.py"` — **the repo root's own `main.py` is never read, modified, or used as a template file on disk**; the root-resolution logic was read directly from `scripts/phase29_build_submission.py` and replicated verbatim:

```python
def _resolve_submission_root():
    if sys.path and os.path.isfile(os.path.join(sys.path[-1], "main.py")):
        return os.path.abspath(sys.path[-1])
    return os.path.dirname(os.path.abspath(__file__))
```

The package's `agent(obs)` builds `scripts.phase37.paced_portfolio_agent.make_paced_portfolio_agent()` (no arguments), matching the same "build once per episode, keyed on `day==0, hour==0`" lifecycle every prior submission's `main.py` uses.

## 4. Submission Letter

**[VERIFIED, by direct listing of every existing `kaggriculture_*.tar.gz` in the repo root before choosing]**:

| Letter | Package | Phase |
|---|---|---|
| A | `kaggriculture_phase3_4_variantD_submission_A.tar.gz` | 3.4 |
| B | `kaggriculture_phase3_5_competitive_v2_submission_B.tar.gz` | 3.5 |
| C | `kaggriculture_phase3_8_submission_C.tar.gz` | 3.8 |
| D | `kaggriculture_phase7_submission_D.tar.gz` | 7 |
| E | `kaggriculture_phase12_submission_E.tar.gz` | 12 |
| F | `kaggriculture_phase18_submission_F.tar.gz` | 18 |
| G | `kaggriculture_phase20_submission_G.tar.gz` | 20 |
| H | `kaggriculture_phase29_submission_H.tar.gz` | 29 |
| **I** | **`kaggriculture_phase37_submission_I.tar.gz`** | **37 (this phase)** |

**I confirmed correct** — not assumed.

## 5. Validation

### 5a. Full Regression Suite

| Suite | Result |
|---|---|
| `phase2_6_regression_tests.py` | 18/18 |
| `phase3_1_regression_tests.py` | 21/21 |
| `phase3_2_regression_tests.py` | 13/14 (pre-existing stale-hash-pin failure, documented since Phase 7) |
| `phase3_3_regression_tests.py` | 11/12 (same) |
| `phase3_4_regression_tests.py` | 13/14 (same) |
| `phase3_5_regression_tests.py` | 19/20 (same) |
| `phase3_8_regression_tests.py` | 12/13 (same) |
| `phase12_regression_tests.py` | 21/21 |
| **Total** | **128/133**, identical to every prior submission's packaging phase since 20 |

**[VERIFIED] Nothing new broken.** `git status --short` shows only pre-existing changes (`docs/BIG_SWING_PLAN.md`) that predate this phase, plus this phase's own new, additive `scripts/phase32/` through `scripts/phase37/` and `results/phase32/` through `results/phase37/` paths — no frozen path, `agents/phase21/`, or `agents/phase15/` appears as modified.

### 5b. Cold-Process Test

Extracted `kaggriculture_phase37_submission_I.tar.gz` to `C:/tmp/phase37_coldtest` (outside the repo, via Python's own `tarfile` module — `tar` itself misparsed the Windows path as a remote host, a tooling quirk noted here for anyone reproducing this, not a packaging issue). Loaded `main.py` via:

```python
sys.path.append(os.path.abspath('.'))  # matches Kaggle's own sys.path convention (appends, not inserts)
src = open('main.py').read()
ns = {'__name__': 'submission_i_main'}   # __file__ deliberately absent
exec(compile(src, '<string>', 'exec'), ns)
agent = ns['agent']
```

Ran a full 720-turn episode via `kaggle_environments.make('kaggriculture', ...)` against the environment's built-in `random` opponent:

| Check | Result |
|---|---|
| `agent` callable after exec | Yes |
| Episode status (both players) | `DONE`, `DONE` |
| Final money | $71,377.00 (ours) vs. $0.00 (random) |
| Dependency on anything outside the package | None (isolated directory, no repo path on `sys.path`) |

**[VERIFIED] The package is fully self-contained and loads correctly under Kaggle's actual loading mechanism**, including its namespace-package dependencies under `scripts/`.

### 5c. Re-Confirmed Win-Rate on the PACKAGED Artifact Itself (vs. In-Repo Submission G)

`scripts/phase37/reconfirm_packaged_head_to_head.py`: `sys.path` is pointed ONLY at the isolated extracted directory and `sys.modules` entries for `agents`/`vendor_kaggriculture`/`scripts`/`instrumentation` are cleared before importing `scripts.phase37.paced_portfolio_agent.make_paced_portfolio_agent` fresh — confirmed resolved from `C:\tmp/phase37_coldtest\scripts\phase37\paced_portfolio_agent.py`, not the repo. `sys.modules` is cleared again, `sys.path` repointed at the repo root, and Submission G's `make_macro_agent()` is imported fresh from there.

| Seed | Packaged Submission I | In-repo Submission G | Winner |
|---|---|---|---|
| 700000 | $55,204.00 | $51,182.00 | I |
| 700001 | $62,956.00 | $53,082.00 | I |
| 700002 | $52,762.00 | $48,047.00 | I |
| 700003 | $56,899.00 | $46,979.00 | I |
| **Mean** | **$56,955.25** | **$49,822.50** | — |

**[VERIFIED] Every one of these figures matches Phase 36's most recent in-repo validation (`results/phase36/phase36_vs_submission_g_results.json`) exactly, to the dollar, on every seed** — confirming packaging introduced no behavioral change (no stale import, no config default reverting, no silent transformation, and the `scripts/` namespace-package dependency resolves correctly from the packaged copy). This 4-seed sample (4 wins, 0 losses) is consistent with the full 15-seed set's own 10-5 (66.7%) record.

**Supporting check — dependency-file integrity**: all 13 non-`main.py` files in the package were SHA-256-compared against their repo source files; every one matched exactly (Section below).

### 5d. Dependency-File SHA-256 Verification

| File | Match |
|---|---|
| `vendor_kaggriculture/kaggriculture.py` | OK |
| `vendor_kaggriculture/kaggriculture.json` | OK |
| `agents/__init__.py` | OK |
| `agents/phase2_3/common.py` | OK |
| `agents/phase3/__init__.py` | OK |
| `agents/phase3/opponent_observation.py` | OK |
| `agents/phase21/__init__.py` | OK |
| `agents/phase21/portfolio.py` | OK |
| `agents/phase21/execution.py` | OK |
| `agents/phase21/liquidation.py` | OK |
| `agents/phase21/risk_posture.py` | OK |
| `scripts/phase36/paced_execution.py` | OK |
| `scripts/phase37/paced_portfolio_agent.py` | OK |

**All 13 match, byte-for-byte.**

### 5e. Package Manifest

| Property | Value |
|---|---|
| Filename | `kaggriculture_phase37_submission_I.tar.gz` |
| SHA-256 | `6a60947b2e3d8dd94679de01a81cf91807c1a2cad04f9902ccc232be86441848` |
| Size | 42,061 bytes (41.1 KB) |
| File count | 14 |

## 6. Promotion Basis (Reused from Phase 36, Not Re-Derived)

Per this phase's explicit scope, the economic and competitive case for promoting this agent was already made and is not re-argued here:

- **10/15 (66.7%) head-to-head win rate against Submission G** — up from Submission H's own shipped 9/15 (60.0%) — on the full development+validation+held-out seed set (n=15), confirmed by `results/phase36/PHASE36_ADAPTIVE_PACING_REPORT.md`.
- **15/15 (100%) head-to-head win rate against Submission C** — up from 14/15 (93.3%) — same seed set.
- The change is narrowly scoped (one purchase type's cash-reserve gating, everything else — targets, HIRE, BUY_LAND, task scheduling — byte-identical to Submission H) and directly traced to a real, confirmed architectural gap (`agents/phase21/execution.py`'s `BUY_ANIMAL` held zero cash reserve before this fix), not a speculative redesign.

## Changed Files

New, all additive:
- `scripts/phase37_build_submission.py`
- `scripts/phase37/paced_portfolio_agent.py`
- `scripts/phase37/reconfirm_packaged_head_to_head.py`
- `results/phase37/phase37_reconfirm_packaged_results.json`
- `results/phase37/PHASE37_SUBMISSION_I_PACKAGING_REPORT.md` (this file)
- `kaggriculture_phase37_submission_I.tar.gz` (repo root, the built package)

No existing file was modified by this phase. Repo root `main.py` still builds Submission C/E. `agents/phase21/` was not modified. `agents/phase15/` was not touched.
