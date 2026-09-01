# Kaggriculture Phase 2.0 — Phase 1 Freeze & Reproducibility Gate

Date: 2026-08-16. Git repository: none exists for this project (documented, not forced — see §Git
Freeze below). All new artifacts under `phase1_freeze/`; nothing in Phase 1's original file set was
modified.

---

## 1. Inventory (before any changes)

Confirmed present and untouched at freeze start: `docs/{00_official_overview_raw,01_mechanics_reference,
02_architecture_map,PHASE1_REPORT}.md`, `vendor_kaggriculture/` (+ unused `vendor_kaggriculture_beginner/`),
`agents/baseline_agent.py`, `harness/run_episodes.py`, `scripts/{smoke_test,determinism_check}.py`,
`kaggriculture-data/{README.md,AGENTS.md,kaggriculture.zip}`, 10 `results/*` directories (7 from the
formal Phase 1 experiment set, 3 early dev smoke-test dirs). No git repository. Empty `logs/` and
`replays/` directories exist but were never populated (harness supports replay saving via
`--save-replays`, simply never invoked in Phase 1) — noted as non-blocking. Two unexplained files
(`README.md`, `AGENTS.md` at the project root, outside any subdirectory) were noted in the Phase 1
report as being of unknown provenance; they remain untouched and unused as a source for any claim in
this report or Phase 1's.

## 2. Artifact verification

All Deliverable-A-through-H Phase 1 artifacts listed in the brief were confirmed present, non-empty,
and internally consistent (cross-referenced against each other and against direct source-code reading).
Nothing missing; nothing fabricated.

## 3. Simulator freeze

`kaggle-environments==1.32.7` confirmed installed (`pip show`). Installed simulator source
(`kaggriculture.py`) hashed and compared against the Phase 1 vendored copy:

```
SHA-256 (installed): bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e
SHA-256 (vendored):  bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e
MATCH: yes
```

Also hash-matched: `kaggriculture.json` (spec), the package's own `README.md`/`AGENTS.md`. **The
vendored copy is confirmed to be the exact source Phase 1 experiments ran against.**

## 4. Official competition data — preserved, discrepancy re-confirmed via a stronger source

`kaggriculture-data/` (README.md, AGENTS.md, kaggriculture.zip) preserved exactly as downloaded in
Phase 1 (original file timestamps intact, 2026-08-09; not touched this session). Hash comparison:

- `kaggriculture-data/AGENTS.md` == `vendor_kaggriculture/AGENTS.md` (byte-identical — matches the
  currently-running simulator's own pricing documentation, i.e. the `hinge` curve).
- `kaggriculture-data/README.md` != `vendor_kaggriculture/README.md` (confirms Phase 1's finding: the
  officially-downloaded standalone README documents a stale, non-`hinge` pricing model for
  Carrot/Tomato/Egg). **Not corrected. Preserved exactly as downloaded**, per the freeze-gate
  instruction not to erase discrepancy evidence.

## 5. Reproducibility snapshot

- Python: 3.11.3, venv `C:\kagvenv` (short path — required workaround for a Windows `MAX_PATH`
  failure in an unrelated bundled dependency, `orbax-checkpoint`'s test fixtures; full procedure and
  rationale in [phase1_freeze/environment.txt](../phase1_freeze/environment.txt)).
- OS: Windows 11 Home, build 10.0.26200, x86_64.
- Kaggle CLI: 2.2.4.
- `pip freeze`: 125 packages, captured verbatim to
  [phase1_freeze/pip_freeze.txt](../phase1_freeze/pip_freeze.txt) — not hand-constructed.
  Intentionally-omitted heavy deps (`flax`, `gymnax`, `orbax-checkpoint`, `optax`, `chex`, `litellm`,
  `transformers`) confirmed absent; `jax` present as an incidental transitive install, confirmed
  harmless (no import-time dependency from `kaggriculture.py`).

## 6. Frozen control

- **Baseline agent** ("Wheat Patroller"), `agents/baseline_agent.py`:
  `SHA-256 d007f1ed0c025f6fc90d9914c371e49cf2e49ac4f6183fb6c9554079847ecefd`. Confirmed unchanged
  since the Phase 1 experiments that produced the results in `results/baseline_vs_*` (same file, no
  modifications made this session prior to hashing).
- **Evaluation harness**, `harness/run_episodes.py`:
  `SHA-256 099ef1a01d38eb3019b3365bcbe757155dd3c574aeeda5199c08862c8104319e`. Verified it still
  supports every capability required by the brief: built-in + custom-file agents, fixed/random seeds,
  multi-episode runs, raw JSON+CSV output, summaries, winner/status/error tracking, optional replays.
  No Phase 2 economic telemetry added.

## 7. Reproduction results

Re-ran the three formal baseline benchmarks with identical seed ranges into a new, separate directory
(`phase1_freeze/reproducibility_results/repro_baseline_vs_*`), Phase 1 originals untouched.

| Matchup | Money reproduced episode-exact? | Aggregate stats reproduced? |
|---|---|---|
| baseline vs pass | **Yes — 15/15 episodes identical** (only wall-clock runtime differs) | Yes, exactly |
| baseline vs starter | **Yes — 15/15 episodes identical** (only wall-clock runtime differs) | Yes, exactly |
| baseline vs random | **No** — per-episode money differs | Broadly consistent (100% baseline win rate both times; mean ~$5.2k both times) but not exact |

**Root-caused the `random` discrepancy**: `random_agent()` in `kaggriculture.py` builds
`rng = random.Random()` with no seed, fresh every call — disconnected from the episode's
`configuration["seed"]`. This is a property of that specific built-in agent, not a simulator, harness,
or baseline-agent defect. Confirmed by the fact that the two other matchups (both opponents fully
deterministic) reproduced perfectly under the identical procedure. Documented as a permanent caveat in
the control contract: never expect episode-exact reproducibility against `random`; use it only for
aggregate comparisons with adequate sample size.

## 8. Determinism reconfirmed

Re-ran `scripts/determinism_check.py` (seed 42, starter vs starter, 200 steps) — **identical final
rewards** to the original Phase 1 run ([3060.0, 3060.0] both times, matching Phase 1's own recorded
value). Re-verified programmatically that all 200 step trajectories are byte-identical between two
independent runs of the same seed; the only differing field across the full episode dump is the
run's random UUID (`id`), not game state.

## 9. Harness sanity checks

| Check | Expected | Observed |
|---|---|---|
| PASS vs PASS | tie, $3000/$3000, zero variance | **tie_rate=1.0**, both means $3000.00, std 0 — matches |
| PASS vs STARTER | starter generally outperforms pass | starter mean $3465 vs pass $3000 — matches |
| baseline vs PASS | baseline shows meaningful farming activity, outperforms pass | baseline mean $5763 vs pass $3000 — matches |

## 10. Historical results preservation

Confirmed: no file under `results/` was modified, deleted, or regenerated. All reruns and sanity
checks from this freeze were written to a new location,
`phase1_freeze/reproducibility_results/`, under new tags (`repro_*`, `sanity_*`).

## 11. Git freeze point

**No git repository exists for this project.** `git status` / `git log` / `git tag` all report
"not a git repository." Per the freeze-gate instructions, this is documented rather than forced —
git was not initialized, and no repository workflow was imposed. If a durable, taggable freeze point
is wanted going forward, the recommended next action (not performed here, pending explicit user
direction, since initializing version control is a standing infrastructure decision) is: `git init`,
add everything **except** `phase1_freeze/reproducibility_results/` scratch reruns if kept out of
history, verify no credentials are staged (`~/.kaggle/access_token` lives outside the project tree and
was confirmed absent from every file under `C:\Kaggriculture` via a repo-wide grep for the token
prefix), commit, and tag `phase1-frozen`.

## 12. Change-control policy

Established in full at [docs/03_control_contract_and_change_policy.md](03_control_contract_and_change_policy.md)
— control contract, the `random`-agent reproducibility caveat, and all 7 change-control rules from the
brief (no baseline edits, no simulator edits, no overwriting history, new-agents-as-new-files,
hypothesis-before-experiment, no seed tuning, preserve negative results).

## 13. Critical discrepancies

1. **Kaggle's own downloadable `README.md` is stale** relative to `AGENTS.md` in the same zip and the
   actual running simulator (non-`hinge` vs `hinge` pricing for Carrot/Tomato/Egg). Confirmed via
   direct hash/diff of the official download, not just the web page. Non-blocking for the freeze
   itself (doesn't affect anything frozen), but **load-bearing for Phase 2** pricing work — use
   `AGENTS.md`/package source, never the standalone README.
2. **`random` reference agent is not seed-reproducible.** Documented as a control-contract caveat, not
   a defect to fix (it's a property of the shipped reference agent, out of scope to modify).

## 14. Non-blocking issues

- `logs/`/`replays/` directories exist but are empty (harness capability unused, not broken).
- Two unexplained root-level `README.md`/`AGENTS.md` files of unknown provenance remain on disk,
  untouched, not used as a source for any claim.
- No git repository — infrastructure gap, not a data-integrity issue; documented, not remediated
  without explicit direction.
- Full `pip freeze` from the *original* Phase 1 session was never captured at the time (Phase 1 report
  flagged this as a remaining unknown); this freeze captures the *current* environment's `pip freeze`,
  which is consistent with Phase 1 in every way checked (same kaggle-environments version, same hash,
  same reproduced results) but is not a byte-for-byte historical artifact of the original install
  session.

## 15. Frozen artifacts (final list)

Simulator source + spec + docs (`vendor_kaggriculture/`), official data bundle
(`kaggriculture-data/`), baseline agent (`agents/baseline_agent.py`), evaluation harness
(`harness/run_episodes.py`), all Phase 1 documentation (`docs/00`-`02` + `PHASE1_REPORT.md`), all
Phase 1 result directories (`results/*`), all hashed and manifested in
[phase1_freeze/hashes.txt](../phase1_freeze/hashes.txt) and
[phase1_freeze/FREEZE_MANIFEST.md](../phase1_freeze/FREEZE_MANIFEST.md).

---

```text
KAGGRICULTURE PHASE 2.0
PHASE 1 FREEZE & REPRODUCIBILITY GATE

Status:
PASS WITH ISSUES

Simulator:
Version: kaggle-environments 1.32.7 ("kaggriculture")
Source hash: bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e

Python: 3.11.3 (C:\kagvenv)
OS: Windows 11 Home, build 10.0.26200, x86_64
Kaggle CLI: 2.2.4

Baseline:
Wheat Patroller
Source hash: d007f1ed0c025f6fc90d9914c371e49cf2e49ac4f6183fb6c9554079847ecefd

Harness:
Source hash: 099ef1a01d38eb3019b3365bcbe757155dd3c574aeeda5199c08862c8104319e

Determinism:
PASS  (seed 42, starter vs starter — byte-identical trajectory across two independent runs)

Phase 1 reproduction:
PARTIAL  (baseline vs pass: PASS, episode-exact. baseline vs starter: PASS, episode-exact.
          baseline vs random: root-caused non-reproducibility in the built-in "random" agent's
          own unseeded RNG — not a simulator/harness/baseline defect; aggregate behavior consistent.)

Historical results preserved:
YES

Git freeze:
Tag: none (no git repository exists; documented, not forced)
Commit: n/a

Critical discrepancies:
1. Kaggle's official downloadable README.md is stale vs. AGENTS.md/installed package (pricing model
   for Carrot/Tomato/Egg) — confirmed via official-download hash diff, not just the web page.
2. Built-in "random" reference agent is not seed-reproducible (unseeded internal RNG) — control
   contract updated to require aggregate-only comparison against it.

Non-blocking issues:
- Empty logs/ and replays/ directories (unused capability, not broken)
- Two unexplained root-level README.md/AGENTS.md files of unknown provenance, untouched, unused
- No git repository configured for this project
- Original Phase 1 session's exact pip freeze was never captured historically; current freeze's
  pip freeze is consistent with Phase 1 in every checked respect but isn't a historical artifact

Frozen artifacts:
vendor_kaggriculture/ (simulator source+spec+docs), kaggriculture-data/ (official bundle),
agents/baseline_agent.py, harness/run_episodes.py, docs/00-02 + PHASE1_REPORT.md, results/* (7 formal
+ 3 dev-smoke-test dirs), phase1_freeze/{FREEZE_MANIFEST.md,hashes.txt,pip_freeze.txt,environment.txt,
reproducibility_results/}, docs/03_control_contract_and_change_policy.md

Phase 2.0 conclusion:
The Phase 1 foundation is verified, hashed, and reproducible for every deterministic-agent matchup
tested; the one non-reproducing matchup (vs. the built-in "random" agent) has a fully identified,
non-blocking root cause external to anything Phase 1 built. No historical data was altered. No
credentials were exposed. The two open issues (stale official README, no git repo) are documented and
do not compromise the integrity of the frozen control. Status is PASS WITH ISSUES rather than a clean
PASS solely because of the missing git freeze point and the pre-existing unexplained root-level files
— neither affects correctness or reproducibility of the frozen environment itself.

Approved next step:
Phase 2.1 — Economic Instrumentation
```
