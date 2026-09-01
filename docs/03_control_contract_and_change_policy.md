# Phase 1 Control Contract & Phase 2 Change-Control Policy

Established at the Phase 2.0 freeze gate (2026-08-16). Every Phase 2 experiment must be compared
against this control, and must follow the change-control rules below.

## The Phase 1 control condition

```
Simulator:
    kaggle-environments 1.32.7
    registered environment "kaggriculture"
    source SHA-256: bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e
    (see phase1_freeze/hashes.txt for the full manifest)

Agent (frozen control):
    "Wheat Patroller" — agents/baseline_agent.py
    SHA-256: d007f1ed0c025f6fc90d9914c371e49cf2e49ac4f6183fb6c9554079847ecefd

Evaluation:
    harness/run_episodes.py
    SHA-256: 099ef1a01d38eb3019b3365bcbe757155dd3c574aeeda5199c08862c8104319e
    fixed seeded episodes (--seed-base) where reproducibility is required

Historical controls (built into the simulator, not ours to modify):
    pass    — always PASS, no-op
    random  — NOTE: internally unseeded (random.Random() per call); not reproducible
              across runs even with a fixed episode seed. Use only for aggregate/
              statistical comparison, never for exact-value regression checks.
    starter — deterministic carrot loop

Primary evaluation:
    final bank balance (reward)
    win / loss / tie

Secondary diagnostics:
    variance (std, min/max across seeds)
    error count (non-DONE status)
    runtime
    action/resource behavior, where already surfaced by the harness
```

## Why "random" is excluded from strict reproducibility claims

Verified during this freeze (Phase 2.0 §11-12 reproduction exercise): re-running
`baseline vs pass` and `baseline vs starter` with the same seed ranges reproduced **identical final
money for every episode** (only wall-clock runtime differed). Re-running `baseline vs random` under
the same conditions did **not** reproduce identical values. Root cause, confirmed by source
inspection: `random_agent()` in `kaggriculture.py` constructs `rng = random.Random()` with no seed
argument, fresh on every call — this is disconnected from the episode's `configuration["seed"]`
entirely. This is a property of the built-in reference agent, not a simulator or harness defect.
**Implication for Phase 2**: any experiment that includes `random` as an opponent must use enough
episodes to be statistically meaningful and must not expect episode-level reproducibility; experiments
against `pass` or `starter` (or other deterministic agents) can and should be checked at the
episode-exact level.

## Change-control rules for Phase 2

1. **Do not modify the frozen baseline.** `agents/baseline_agent.py` (hash above) is immutable. If a
   genuine bug is found in it, fork it under `agents/phase2/` with a new name — never edit in place.
2. **Do not modify the simulator.** `vendor_kaggriculture/` is a reference copy, not a working copy —
   never edited. If a simulator version bump or behavioral discrepancy is found, vendor the new
   version under a separate, clearly versioned directory (e.g. `vendor_kaggriculture_v1_33_0/`) and
   document the diff; never overwrite the frozen copy.
3. **Do not overwrite historical experiments.** Every experiment — Phase 1's or Phase 2's — gets its
   own new directory under `results/` (or a Phase-2-specific results root) with a descriptive tag.
   Nothing in `results/` or `phase1_freeze/reproducibility_results/` gets deleted or regenerated
   in place.
4. **New agents are separate experimental artifacts**, organized e.g.:
   ```
   agents/
       baseline_agent.py          # frozen Phase 1 control — never edited
       phase2/
           crop_sweep_<name>.py
           market_<name>.py
           planner_v1_<name>.py
   ```
5. **Every experiment states a hypothesis before running**, in this shape:
   ```
   Hypothesis:
   Expected result:
   Independent variable:
   Dependent variables:
   Controls:
   Seeds:
   Opponent:
   Sample size:
   Success criterion:
   ```
6. **No seed tuning.** Seeds are for reproducibility and fair evaluation, never for cherry-picking a
   favorable outcome. A fixed, pre-declared seed range is chosen before results are seen.
7. **Preserve negative results.** A strategy that underperforms the frozen baseline is still evidence
   and gets written up and kept, not discarded.

## What Phase 2.0 explicitly did NOT do

Per the freeze-gate brief, no economic optimization, crop/market/hiring/land/animal tuning, opponent
modeling, RL, or evolutionary search was performed or mixed into this freeze. All work in this phase
was limited to: inventory, verification, hashing, reproduction of existing Phase 1 benchmarks under
identical conditions, and sanity checks of the existing harness. See
[../docs/PHASE2_0_REPORT.md](PHASE2_0_REPORT.md) for the full account.
