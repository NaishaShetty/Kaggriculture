# Phase 49: Combined Execution Layer Sanity Check — Stopped Before CARROT/TOMATO

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`,
`agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`,
`agents/phase2_4/common.py`, `agents/phase15/`). `agents/phase21/` was
**not modified**. `scripts/phase45/seed_paced_execution.py` and
`scripts/phase46/feed_priority_execution.py` were read-for-reference and
imported-from only, never edited. All new code lives under
`scripts/phase49/`, all new results/report under `results/phase49/`.

## Executive Summary

**[VERIFIED] Per this phase's own explicit stop-rule, this phase stops at
Step 1.** The combined execution layer (`scripts/phase49/
combined_execution.py`, layering Phase 45's BUY_SEED reserve-gate and Phase
46's FEED tier-0.5 fix onto Phase 36's base pacer, run with Submission I's
existing, unmodified crop fractions and NO CARROT/TOMATO slice) was
sanity-checked on the mandatory 4-seed isolated-economy screen exactly as
instructed, **before** any new-crop design work began. **Result: a real,
non-trivial negative interaction.** Mean final money **-9.47%** vs. shipped
Submission I ($59,144.50 → $53,543.75) — clearly worse than *either* fix
alone (Phase 45's BUY_SEED pacer alone: -0.41%; Phase 46's FEED tier-0.5 fix
alone, i.e. Submission J: **+0.72%**). On 3 of the 4 development seeds
(700001, 700002, 700003), the combined candidate underperforms **both**
individual fixes, not just the worse of the two — the two validated,
individually-safe changes do not simply add or cancel when run together;
they interact unfavorably. **Per the brief's own explicit instruction
("report it plainly and stop rather than proceeding to layer a CARROT/
TOMATO slice on top of a broken combination"), Steps 2-5 (the cash-gated
slice design, the 4-seed screen, full 15-seed validation, and the
positive-result trace) were correctly NOT attempted.**

**Answering the phase's three framing questions directly: the combined
execution layer does NOT work cleanly on its own (a real interaction was
found); no cash-gated/smaller CARROT/TOMATO slice was built or tested,
because the prerequisite layer it would have run on failed its own sanity
check first; and nothing from this phase is ready to package. Submission I
remains the current best, unchanged. Submission J (Phase 46's FEED-priority
fix alone, already built and validated) remains the correct next upload
candidate — this phase found no reason to prefer the combined layer over
it.**

## 1. What Was Built (Step 1)

`scripts/phase49/combined_execution.py::make_combined_execution_agent`
reproduces Phase 36's base pacer verbatim (HIRE, BUY_LAND, BUY_ANIMAL
pacing, BUY_PRODUCT, worker/task-assignment scheduling — all byte-for-byte
identical across Phase 36/45/46's own three versions, confirmed by direct
comparison of all three source files before writing this one) and applies
BOTH previously-validated, non-overlapping changes at once:

1. **Phase 45's BUY_SEED reserve gate** (verbatim from `scripts/phase45/
   seed_paced_execution.py`): each crop's `BUY_SEED` purchase is gated,
   per-crop-type, against the posture-aware `land_purchase_reserve`
   (`agents/phase21/risk_posture.py`), applied against a running in-turn
   `money` variable.
2. **Phase 46's FEED tier-0.5 reprioritization** (verbatim from
   `scripts/phase46/feed_priority_execution.py`): the FEED task's priority
   tuple changes from `(1, ...)` (tied with WATER) to `(0.5, ...)` (strictly
   ahead of WATER, never contesting HARVEST/HARVEST_ANIMAL's tier 0).

These two changes touch different, non-adjacent lines of the same
monolithic `agent(obs)` closure (the BUY_SEED loop vs. one priority-tuple
literal in task scheduling) and had never been run together before this
phase. `scripts/phase49/combined_portfolio_agent.py` wires this execution
layer to Submission I's own unmodified `agents/phase21/portfolio.py::
portfolio_targets` — the same adapter shape Phase 37/45/46 already
established, with no CARROT/TOMATO slice and no other change.

## 2. Sanity Check: Isolated Economy (4-Seed Screen)

`scripts/phase49/sanity_check_isolated.py`, dev seeds 700000-700003, vs.
"pass":

| Candidate | Mean final money | Δ vs. shipped |
|---|---|---|
| `shipped` (Submission I, unmodified) | $59,144.50 | — |
| `seed_paced` (Phase 45's fix alone) | $58,900.00 | -0.41% |
| `feed_priority` (Phase 46's fix alone = Submission J) | $59,569.75 | **+0.72%** |
| `combined` (both fixes together, this phase) | **$53,543.75** | **-9.47%** |

Per-seed detail (`results/phase49/phase49_sanity_isolated_4seed.json`):

| Seed | shipped | seed_paced | feed_priority | combined |
|---|---|---|---|---|
| 700000 | $44,258 | $37,011 | $70,049 | $59,720 |
| 700001 | $76,683 | $64,178 | $64,409 | $55,908 |
| 700002 | $64,197 | $75,142 | $48,424 | $47,771 |
| 700003 | $51,440 | $59,269 | $55,397 | $50,776 |

**[VERIFIED]** On seed 700000, `combined` ($59,720) sits between `shipped`
and `feed_priority` — plausible if the two fixes were simply "the weaker of
the two" on that seed. But on **700001, 700002, and 700003** — three of the
four development seeds — `combined` is the *worst* of all four candidates,
below shipped and below **both** individual fixes, not just below the
better one. This is the signature of a genuine negative interaction, not
sampling noise or "combined just inherits whichever fix is worse on a given
seed": if that were the mechanism, `combined` should track the minimum of
`seed_paced` and `feed_priority` per seed, and on 700001 it does not
(`combined` $55,908 is 12.9% below `seed_paced`'s own $64,178, the lower of
the two individual fixes on that seed).

## 3. Sanity Check: Head-to-Head (4-Seed Screen)

`scripts/phase49/sanity_check_h2h.py`, dev seeds, `shipped` vs. `combined`
against all three required opponents:

| Candidate | vs. Submission G | vs. Submission C | vs. Jonaid |
|---|---|---|---|
| shipped | 4/4, margin +$7,133 | 4/4, margin +$21,355 | 4/4, margin +$24,318 |
| combined | 4/4, margin **+$3,711** | 4/4, margin **+$17,820** | 4/4, margin +$28,336 |

**[VERIFIED]** Win/loss record held at 4/4 for `combined` against all three
opponents on this small screen — no outright losses appeared. But margin
fell against the two opponents where Submission I's advantage is smallest
and most informative (Submission G: -48% margin; Submission C: -16.5%
margin), while margin rose against Jonaid (+16.5%), an opponent Submission I
already beats by a wide, saturating margin where a few thousand dollars of
noise doesn't change the qualitative picture. **This is consistent with,
not contradictory to, the isolated-economy finding**: a real economic
regression can coexist with an unchanged win/loss record on a 4-seed screen
against opponents Submission I already beats comfortably — the margin
erosion is the more sensitive signal here, and it points the same direction
as Section 2.

## 4. Diagnosis: Why the Interaction Is Negative (Direct Trace)

`scripts/phase49/trace_combined_interaction.py`, seed 700001 (the seed
where `combined` underperforms both individual fixes by the widest margin):

| Metric | shipped | seed_paced | feed_priority | combined |
|---|---|---|---|---|
| Final money | $76,683 | $64,178 | $64,409 | $55,908 |
| BUY_LAND days | 7, 11 | 8, 11 | 7, 11 | **6, 11** |
| Seeds purchased, day 2-9 (units) | 44 | 27 | 40 | 29 |
| idle_fraction | 0.0901 | 0.0895 | 0.0765 | **0.0745** |
| crop_fraction | 0.2346 | 0.2145 | 0.2272 | 0.2132 |
| animals purchased / escaped / net | 13 / 9 / 4 | 14 / 7 / **7** | 9 / 5 / 4 | 11 / 4 / **7** |

**[VERIFIED, by direct trace]** the two fixes' own individually-diagnosed
mechanisms are each still working correctly inside the combined layer: land
timing is not delayed (3rd/2nd quadrant purchases land on schedule, if
anything a day earlier than shipped), and the animal-escape mechanism Phase
45 diagnosed is genuinely improved (net purchased-minus-escaped = 7, tied
with `seed_paced` alone for the best of all four candidates, and better than
`shipped`'s 4). Worker-attention metrics (`idle_fraction`, `crop_fraction`)
are also not worse in `combined` than in either individual fix — if
anything `idle_fraction` is the lowest of the four. **None of the metrics
this project's prior traces (Phase 42/45/46) used to diagnose their own
collisions show an obvious smoking gun here** — no land-timing delay, no
increased idle time, no reduced crop-tile share, no worse animal economics.

**[HYPOTHESIS]** the regression is real but diffuse, in the same sense
Phase 45's own report described its BUY_SEED-paced CARROT/TOMATO retest
("a smaller, more diffuse cash-competition effect... not concentrated in
one traceable purchase-delay event the way Phase 42's version was"). The
early seed-purchase pattern (day 2-9 total: 29 for `combined`, close to
`seed_paced` alone's 27, well below `shipped`'s 44 and `feed_priority`
alone's 40) shows the BUY_SEED reserve gate is doing roughly the same thing
whether or not FEED's tier is also changed — but the two changes'
downstream cash consequences apparently compound rather than average when
applied together: BUY_SEED's reserve gate reduces early cash *outflow*,
while FEED's reprioritization redirects worker-turns away from WATER, and
the combination of "fewer, later crop tiles" (from the seed gate) with "less
worker attention on watering the tiles that do exist" (from FEED
outranking WATER) may compress the same, already-scarce early crop
production from two directions at once in a way neither fix does alone.
This is stated as a hypothesis, not confirmed by a further isolating
experiment (e.g. running the FEED-tier change alone but forcing `seed_paced`'s
exact seed-purchase trace, or vice versa) — per the phase's own stop
instruction, that further isolation work was not undertaken, since the
practical conclusion (don't combine these two fixes as currently
implemented) does not depend on fully resolving the mechanism.

**This is exactly the class of self-defeating coupling the brief warned to
watch for** (citing Phase 36's own prior finding that coupling HIRE to the
animal feed-buffer term caused a self-defeating feedback loop) — two
individually-safe, individually-validated changes to *different* resources
(cash reserve vs. worker-turn priority) still interact negatively when
stacked, even though neither change touches the other's own code path
directly. The lesson generalizes: validating two execution-layer changes
independently does not certify their combination, even when they appear to
target orthogonal mechanisms.

## 5. Steps 2-5: Not Attempted, By Design

Per the phase's own explicit instruction — *"If combining the two fixes
produces any unexpected interaction..., report it plainly and stop rather
than proceeding to layer a CARROT/TOMATO slice on top of a broken
combination"* — the cash-surplus-gated CARROT/TOMATO design (Step 2), the
4-seed screen (Step 3), full 15-seed validation (Step 4), and the
positive-result mechanism trace (Step 5) were **not attempted**. Building a
new-crop slice on top of an execution layer that already shows a
-9.47% unexplained regression on its own, unmodified portfolio would
confound any CARROT/TOMATO-specific result with this pre-existing
interaction, making the result uninterpretable either way — exactly the
"broken combination" scenario the brief anticipated.

## 6. Recommendation

**Not ready to package. Do not combine Phase 45's BUY_SEED pacer with Phase
46's FEED tier-0.5 fix as currently implemented.** Each fix should continue
to be evaluated and shipped independently:

- **Submission J** (Phase 46's FEED-priority fix alone, `feed_priority_execution.py`
  composed with `feed_priority_portfolio_agent.py`, already packaged as
  `kaggriculture_phase47_submission_J.tar.gz`) remains a real, validated win
  in its own right (+0.72% isolated on this phase's own re-confirmation,
  matching Phase 46/47's own numbers) and **this phase found no reason to
  prefer the combined layer over it** — if anything, this phase reinforces
  that Submission J should be uploaded as-is, not held back for a combined
  variant that turned out worse.
- **Phase 45's BUY_SEED pacer** remains real, working infrastructure for its
  own diagnosed problem (the land-timing collision under a day-0 CARROT/
  TOMATO slice) but, per this phase's finding, should not be casually
  stacked with other execution-layer changes without its own dedicated
  interaction check — a genuinely useful process lesson for any future
  phase that wants to compose two validated fixes.
- **The cash-gated/smaller CARROT/TOMATO idea itself remains untested by
  this phase** — neither confirmed nor refuted. Phase 41's real-data premise
  and Phase 42/45's finding that CARROT/TOMATO sell at healthy, non-crashed
  prices whenever planted are both still standing, unchanged. A future
  phase could still pursue a cash-gated slice, but should run it on top of
  a SINGLE validated execution fix (most naturally Phase 45's BUY_SEED
  pacer alone, since that is the one whose own diagnosed collision the
  slice would otherwise re-trigger) rather than a combined layer, unless
  and until a future phase specifically diagnoses and resolves this
  phase's found interaction.

Submission I remains the current best, unchanged. No new submission is
created this phase.

## Changed Files

New, all additive, none touching `agents/phase21/`, `scripts/phase36/`,
`scripts/phase45/`, or `scripts/phase46/`:
- `scripts/phase49/combined_execution.py`
- `scripts/phase49/combined_portfolio_agent.py`
- `scripts/phase49/sanity_check_isolated.py`
- `scripts/phase49/sanity_check_h2h.py`
- `scripts/phase49/trace_combined_interaction.py`
- `results/phase49/phase49_sanity_isolated_4seed.json`
- `results/phase49/phase49_sanity_h2h_4seed_dev.json`
- `results/phase49/PHASE49_CASH_GATED_CARROT_TOMATO_REPORT.md` (this file)

`agents/phase21/` was not modified. No submission is created.
