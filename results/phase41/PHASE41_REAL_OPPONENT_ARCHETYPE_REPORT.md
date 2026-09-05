# Phase 41: Real Opponent Archetype Report

## Executive Summary

**[VERIFIED]** Pulled 14 fresh real episodes (spanning rank #1 through the
matchmaking band around this project's own live rank, ~5089/7587) plus
reuse of Phase 34/39's 2 existing Crop Dusta episodes — 16 real episodes,
30 team-trajectories total, extracted with Phase 6's own unmodified parser.
**[OBSERVED]** The real ladder is not one archetype. Five identifiable
clusters emerge from this sample (Section 2), and two of them have **no
synthetic counterpart this project has ever validated against in the form
they actually appear**: (1) a broader crop portfolio including CARROT
and/or TOMATO at sustained (≥5-tile) scale, seen in **12 of 30 (40%)**
sampled trajectories, including gold-tier opponents Crop Dusta and keiz —
Submission I has never grown either crop; (2) a genuine 4th-land-quadrant
expansion, seen in 3 of 30 trajectories across this sample and Phase 34's
prior data (Sundar, Jonaid, Alden Jenish S) — Submission I is hard-capped
at 3 quadrants and has never been validated against this archetype in the
form real players actually run it (a portfolio-wide scale-up, not a
dedicated side-crop on isolated new land, which is the only way this
project has tested a 4th quadrant so far — Phase 33 Part C, and that test
found something different and much narrower than what real land-4 players
do).

**[OBSERVED]** Submission I's own 9 most recent real games (4W-5L, roughly
matching the reported ~50% live win rate) show a **suggestive but noisy**
split by opponent animal count: mean opponent animal count in the 5 losses
is 16.4, vs. 7.0 in the 4 wins — but one win (vs. a 4th-quadrant, 13-animal
opponent) and one loss (vs. a 9-animal opponent) both break the pattern.
Reported as an honest, small-sample observation, not a causal claim.

**Recommendation**: this phase does not build anything (per its own scope).
The concrete, actionable recommendation for a future phase is to (1) test
CARROT and TOMATO as a **minor diversification slice within Submission I's
existing portfolio** (5-15 tiles alongside the current MELON/STRAWBERRY/
WHEAT mix, not as a monocrop replacement — Phase 33 Part A only tested the
latter and correctly rejected it, a different question), and (2) build and
validate against a 4th-quadrant benchmark that scales the *entire*
portfolio proportionally (more of everything already being grown, the way
Sundar/Jonaid/Alden Jenish S actually do it), not Phase 33 Part C's
narrower "dedicated new land for one new crop" framing, which found a real
but different failure mode (Fibonacci hire cost resetting daily, not
portfolio economics).

## 1. Method

**Episode sourcing [VERIFIED]**: pulled via the Kaggle live leaderboard
(browser, no login required) on 2026-09-04. `keiz` (rank #2)'s game history
supplied 5 episodes against 4 distinct top-tier opponents (Crop Dusta x2,
Jesse Bullard, Himanshu Kumar, AI是我的豆包). This
project's own team (`shettynaisha`, live rank 5089/7587, rating 543) supplied
its own 9 most recent real games, against 9 distinct opponents in the
matchmaking band near that rank. All 14 episode JSONs were downloaded
directly via `GET https://www.kaggle.com/competitions/episodes/<id>/replay.json`
(no login required for this endpoint, confirmed directly — same endpoint
Phase 19 already established) into `results/phase41/raw_replays/`. Combined
with Phase 34/39's existing 2 Crop Dusta episodes, this gives **16 real
episodes / up to 30 team-trajectories**, spanning ranks #1 (Crop Dusta,
score ~3011) down to whatever band this project's own current live rating
(543) gets matched against — a materially wider rank spread than any prior
phase's real sample (Phase 6: 4 opponents from 2 episodes; Phase 19: 4
episodes, top-of-ladder only; Phase 34/39: Crop Dusta only, 2 episodes).

**Extraction [VERIFIED]**: `agents/phase6/replay_forensics.py::
extract_episode_timelines` and `load_replay`, reused completely unchanged —
no new parser. `scripts/phase41/archetype_survey.py` is new, additive code
only (feature aggregation on top of the parser's own output).

**Observability discipline [VERIFIED]**: every one of the 30 team-
trajectories in this report — including the 9 games this project's own
team played — was read strictly as the "opponent" side of
`extract_episode_timelines`. For each 2-team episode, the function was
called once with `our_name=team_A` (returning team_B's PUBLIC-only
`opponent_timeline`) and once with `our_name=team_B` (team_A's PUBLIC-only
`opponent_timeline`). This means shed contents, seed inventories, carried
inventories, and submitted actions were **never read for any team in any
episode in this report** — stricter than Phase 19's own precedent (which
populated an aggregate shed/seed total for whichever side it happened to
call "self"). Every field in Section 2/3 below (crop-tile counts by type,
land quadrants, hand count, animal counts by species, bank) is a directly
public field of `obs["farms"][idx]`, per `agents/phase6/replay_forensics.py`'s
own documented boundary.

## 2. Archetype Taxonomy

Five identifiable clusters, all from **directly observed** final-day (or
near-final-day) portfolio state — not forced onto a taxonomy the data
doesn't support. Full per-team feature table: `results/phase41/
phase41_team_features.json` (30 rows).

### A. Gold-tier full-scale, diversified crop mix
Crop Dusta (x4 rows), keiz (x4), Jesse Bullard, Himanshu Kumar, AI是
我的豆包 — 9 rows. Land 3, hands 10-12, animals 8-18 (wide spread),
first land expansion day 5-6. **Crop mix regularly includes CARROT and/or
TOMATO at ≥5-tile scale** (6 of 9 rows) alongside MELON/STRAWBERRY/WHEAT —
this is the specific, concrete gap named in the Executive Summary.

### B. 4th-quadrant expansion
Jonaid (land 4, hands 11, animals **24** — the highest animal count in the
whole sample), Alden Jenish S (land 4, hands 12, animals 13), plus Phase
34's previously-characterized Sundar trajectory (land 4 by day 15, ~19
SHEEP). **[OBSERVED]** all three scale the *entire* portfolio up when they
take the 4th quadrant (more animals, not a new isolated crop) — different
from what Phase 33 Part C tested (a 4th quadrant dedicated solely to
TOMATO/GOOSE via new hands, everything else untouched).

### C. Animal-heavy, land-light
마짱MAZZANG (land 2, hands 10, animals 17, MELON/WHEAT only — no
STRAWBERRY), Reda HEDDAD (land 2, hands 6, animals **19**, WHEAT-only crop
mix). Both trade land/crop diversity for a larger animal footprint on a
smaller base. **[OBSERVED]** both of Submission I's games against this
archetype were losses (Section 4).

### D. Small-scale / conservative
Kota Iizuka (land 1, hands **0** — never hired anyone, ran only on starting
hands — crop_tiles 13, animals 0), Shinzo Takayama (land 1, hands 8,
WHEAT-only, never expanded land at all). **[OBSERVED]** this archetype is
reasonably close to Phase 3.1's existing `conservative`/`passive` synthetic
archetypes already in this project's benchmark set — Submission I beat both
real examples of it comfortably (Section 4).

### E. Delayed-ramp mid-scale
Ryan Cheung (land 3, hands 10, animals 13, but first land expansion at
**day 12**, not day 5-7 like every other full-scale row), Vishal Dhariwal
(land 3, hands 8, first land expansion day 10, still holding 10 unliquidated
crop tiles at day 29 — the only opponent row in this sample that didn't
fully liquidate). A "reaches the same rough scale, slower and later" shape,
distinct from both the fast gold-tier ramp (Archetype A) and the never-
expands conservative shape (Archetype D).

## 3. Cross-Reference Against This Project's Existing Synthetic Benchmark Set

This project's synthetic/benchmark validation has only ever consisted of:

1. **Phase 3.1's 7 controlled archetypes** (`agents/phase3/opponent_classes.py`
   — passive, production_heavy, market_selling, expansion_oriented,
   animal_oriented, conservative, aggressive_investment): small scale (0-4
   hands, 1-3 land, MELON/STRAWBERRY/WHEAT/GOOSE/COW only), built in Phase
   3.1 as "experimental archetypes for future adaptation experiments, not
   claims about real Kaggle competitors" (the module's own docstring).
   **[OBSERVED]** reasonably represents Archetype D above; does not
   represent A, B, C, or E.
2. **`scripts/phase21/realistic_opponent.py`** (Larko-derived, one real
   trajectory): land 3 by day 11, hands 11 by day 10, ~58-tile crop
   ceiling — this is what Submission I's own `_LAND_RUNGS`/`_HANDS_RUNGS`/
   `_CROP_TILE_RUNGS` were themselves built from. **Never grows CARROT or
   TOMATO.** Never reaches a 4th quadrant.
3. **`scripts/phase34/sundar_archetype.py`** (Sundar-derived, one real
   trajectory, the only prior attempt at Archetype B): land 4 by day 15,
   19 SHEEP, STRAWBERRY+MELON sustained. Built and isolation-sanity-checked
   in Phase 34, but **[VERIFIED]** never became an ongoing validation
   benchmark — no later phase (35-40) head-to-head-tests Submission I
   against it. This is the one archetype this project came closest to
   covering, and then didn't follow through on.
4. **Submission C / Submission G as opponents** — this project's own prior
   work, not independent real data.

**[OBSERVED] Concrete gap #1 — CARROT/TOMATO diversification.** Phase 33
Part A tested CARROT, but only as a monocrop replacement for STRAWBERRY
(CARROT-vs-CARROT, CARROT-vs-STRAWBERRY-uncontested) — a different question
from what real opponents actually do. In this sample, no real opponent runs
CARROT as their dominant crop; it appears as a **minor slice** (a handful to
~15 tiles) alongside a MELON/STRAWBERRY/WHEAT-anchored portfolio otherwise
similar in scale to Submission I's own. Phase 33's decisive rejection
(CARROT nets $330 as a monocrop, two orders of magnitude below STRAWBERRY)
does not actually test whether a small CARROT/TOMATO slice adds anything on
top of an otherwise-STRAWBERRY-anchored portfolio — that specific
configuration has never been tried.

**[OBSERVED] Concrete gap #2 — 4th-quadrant, whole-portfolio scale-up.**
Phase 33 Part C tested a 4th quadrant, but only as dedicated new land for
one new crop (TOMATO or GOOSE) serviced by newly-hired hands, with the
existing WHEAT/STRAWBERRY/COW/SHEEP footprint left completely untouched —
and found a real, but narrow, failure mode (hands reset to zero every day
in this engine, so `n_dedicated_hands` extra hands pay their full Fibonacci
hire cost fresh every single day — not a portfolio-economics finding at
all). Sundar (Phase 34), Jonaid, and Alden Jenish S (this phase) all take a
4th quadrant as an extension of hands/animals/crops already being grown,
not a separate side-venture — a meaningfully different configuration Phase
33 Part C never tested, and which the abandoned Sundar archetype (Phase 34)
was the only prior attempt to approximate, never carried into an ongoing
benchmark.

**[OBSERVED] Not a gap** — Archetypes D (small-scale/conservative) and, to
a reasonable approximation, C (animal-heavy/land-light) are already close
to what Phase 3.1's `conservative`/`passive`/`animal_oriented` synthetic
archetypes represent, even though those were built without real-data
grounding. Submission I's real record against Archetype D in this sample
(2 wins, 0 losses) is consistent with that existing synthetic coverage
being adequate for the low end of the ladder.

## 4. Informal Loss-Pattern Check (Submission I's Own Real Games)

**[OBSERVED], small sample (n=9), not a causal claim.** Submission I's 9
most recent real games: 4 wins (vs. Kota Iizuka, Vishal Dhariwal, Shinzo
Takayama, Alden Jenish S), 5 losses (vs. 마짱MAZZANG, Ryan Cheung,
Reda HEDDAD, 宣城市机械电子职业技术学院,
Jonaid) — roughly consistent with the ~50% live win rate already reported.

| Opponent | Result | Opponent archetype | Opponent final animals | Opponent land |
|---|---|---|---|---|
| 마짱MAZZANG | Loss | C (animal-heavy) | 17 | 2 |
| Ryan Cheung | Loss | E (delayed-ramp) | 13 | 3 |
| Reda HEDDAD | Loss | C (animal-heavy) | 19 | 2 |
| 宣城市机械电子职业技术学院 | Loss | A-adjacent | 9 | 3 |
| Jonaid | Loss | B (4th-quadrant) | 24 | 4 |
| Kota Iizuka | Win | D (conservative) | 0 | 1 |
| Vishal Dhariwal | Win | A-adjacent, slow | 5 | 3 |
| Shinzo Takayama | Win | D (conservative) | 10 | 1 |
| Alden Jenish S | Win | B (4th-quadrant) | 13 | 4 |

Mean opponent final animal count: **16.4 in the 5 losses vs. 7.0 in the 4
wins** — a real split in the mean, but not a clean per-game rule (the
宣城市 loss came against a 9-animal opponent, and the Alden
Jenish S win came against a 13-animal, 4th-quadrant opponent). Submission
I's own final animal count is stable at 7-9 across every one of these 9
games (never varies much despite `agents/phase21/portfolio.py`'s target
rungs reaching considerably higher) — worth naming as a loose thread for a
future phase (is our own animal count under-shooting its own target under
real competitive cash pressure, separately from anything Phase 39/40
measured?), but this phase did not trace it further; it is a candidate
question, not a finding.

**[HYPOTHESIS, not established]** if real losses do skew toward
animal-heavier opponents, that would be a different lead from the
crop-diversification/4th-quadrant gaps in Section 3 — worth a dedicated,
better-powered check in a future phase (more games, ideally with a
synthetic animal-heavy control to isolate the effect from confounds like
land quadrant count or overall opponent strength), not concluded here.

## 5. Recommendation

Per this phase's own scope, no agent or benchmark script was built. For a
future phase, in priority order:

1. **Test a CARROT/TOMATO minor-diversification slice** (5-15 tiles) added
   on top of Submission I's existing MELON/STRAWBERRY/WHEAT mix — not a
   monocrop test (already done, Phase 33 Part A, correctly rejected).
2. **Build and validate a whole-portfolio 4th-quadrant benchmark** —
   scaling existing crops/hands/animals into a 4th quadrant the way Sundar/
   Jonaid/Alden Jenish S actually do it, reusing Phase 34's abandoned Sundar
   archetype as a starting point rather than Phase 33 Part C's narrower
   dedicated-new-crop framing — then head-to-head Submission I against it,
   the same rigor `scripts/phase23/vs_submission_g.py` already established.
3. **A dedicated, better-powered version of Section 4's loss-pattern check**
   once more real games accumulate, specifically isolating opponent animal
   count as a variable (ideally with a synthetic control, not just real-game
   correlation) before treating it as more than a lead.

No submission is created from this phase.
