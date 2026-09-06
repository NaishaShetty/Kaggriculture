# Phase 52: Forensic Analysis of Our 3 Most Recent Real Losses

**Scope**: pure analysis, no agent code touched. New files: `scripts/phase52/loss_forensics.py`,
`results/phase52/raw_replays/*.json`, `results/phase52/phase52_loss_forensics.json`, this report.

## 0. Why this phase exists, and how the input was verified

A live check of our own team's 10 most recent real games this session found 7W-3L (70%) — a marked
improvement over Phase 41's earlier 4W-5L snapshot for Submission I. This phase forensically analyzes
the 3 losses directly, the same way Phase 41 first found the animal-count correlation and Phase 24/27
diagnosed real losses to find root causes.

**[VERIFIED]** All 3 target episodes were fetched via the public `GET
https://www.kaggle.com/competitions/episodes/<id>/replay.json` endpoint (no login) and their
final rewards matched the brief exactly:

| Episode | Opponent | Us | Them | Margin |
|---|---|---|---|---|
| 105750065 | Shawon Biswas | $66,091 | $74,844 | -$8,753 |
| 105745378 | yuki | $55,757 | $71,105 | -$15,348 |
| 105744439 | Sarthak Patel | $57,028 | $57,406 | -$378 |

Three comparison wins were fetched and confirmed as wins for `shettynaisha` (episode IDs from the
brief, team names/results independently confirmed, not assumed): 105757292 (vs. Eric Worrall, us
$64,133 / them $58,507), 105748242 (vs. Shuaib ayad Jasim Jasim, us $46,394 / them $19,551),
105746303 (vs. Moritz Huber, us $71,202 / them $25,593).

## 1. Method

`scripts/phase52/loss_forensics.py` is a thin wrapper (no modification to any frozen module) that
calls `agents/phase6/replay_forensics.py::extract_episode_timelines` ONCE per episode with
`our_name="shettynaisha"`, then runs `scripts/phase41/archetype_survey.py::team_features` — Phase
41's own unmodified feature vocabulary — on **both** the returned self-timeline and
opponent-timeline. This is the first time this project has run its forensics feature vocabulary on
its own team's real games. Public-state discipline is preserved: `team_features` only ever reads
`bank`, `hands_count`, `land_quadrants`, `crop_tile_counts`, `animal_tile_counts`, and `day` — all
public fields for both sides — and never touches the self-only `shed`/`seeds`/`inventories`/
`own_action` fields that `extract_episode_timelines` populates only for the "self" side. Full
per-episode feature dumps are in `results/phase52/phase52_loss_forensics.json`.

## 2. The 3 losses individually

**[OBSERVED]** (all figures are PUBLIC-only, final-day/day-29 snapshots unless noted)

**Loss 1 — vs. Shawon Biswas (105750065, margin -$8,753)**
Opponent: land=2, hands=7, crop_tiles=1 (essentially fully liquidated), **animals=18** (COW 13 /
SHEEP 5 peak), crops_ever_at_scale=[STRAWBERRY, TOMATO, WHEAT], first_land_expansion_day=13,
first_animal_day=3. Our side: standard shipped profile (land=3, hands=11, animals=7, MELON/
STRAWBERRY/WHEAT). This opponent ran a smaller land footprint than us but a much larger, earlier
animal operation — an **animal-heavy** profile, directly matching the animal-count lead Phase 41
already flagged (mean opponent animal count 16.4 in Submission I's losses vs. 7.0 in wins).

**Loss 2 — vs. yuki (105745378, margin -$15,348, our largest loss of the 3)**
Opponent: land=**4** (a full 4th-quadrant expansion), hands=10, crop_tiles=0 (fully liquidated),
animals=8, crops_ever_at_scale=[MELON, STRAWBERRY, WHEAT] — **the identical crop set we run**,
just at one more land quadrant. first_land_expansion_day=11 (later than our day 7), but they kept
expanding to a 4th quadrant we never take. This is a clean instance of Phase 41's flagged, never-yet-
tested **"whole-portfolio 4th-quadrant scale-up"** archetype: same strategy as ours, more of it.

**Loss 3 — vs. Sarthak Patel (105744439, margin -$378, essentially a coin flip)**
Opponent: land=**4**, hands=0 (at day 29 — they appear to have released all hands by game end,
unusual but plausible after full liquidation), crop_tiles=0, animals=10, crops_ever_at_scale=
[MELON, STRAWBERRY, WHEAT] — again our identical crop set, again at 4 quadrants instead of 3.
first_land_expansion_day=9. As flagged in the brief, this is a near-wash loss (0.7% margin) and its
profile is essentially the same shape as Loss 2 (same crops, one more land quadrant, slightly more
animals) — not a separately distinct mechanism, just a closer-run version of the same pattern.

## 3. Cross-loss comparison

**[OBSERVED]** All 3 losing opponents fully or near-fully liquidated their crop tiles by day 29
(crop_tiles = 1, 0, 0) — the same disciplined endgame our own shipped agent performs. **2 of 3**
(yuki, Sarthak Patel) ran the exact same three-crop portfolio we do (MELON/STRAWBERRY/WHEAT) but at
4 land quadrants instead of our 3 — a real, repeated instance of the 4th-quadrant scale-up archetype
Phase 41 identified but never built a validated benchmark for. The third (Shawon Biswas) instead
outscaled us on animals specifically (18 vs. our 7), a smaller land footprint (2 quadrants) but an
early, large animal operation — the animal-heavy archetype.

**[INFERRED]** These are two distinct mechanisms, not one shared cause: land-quadrant scale-up (2/3)
and animal-count scale-up (1/3). What they share is that **none of the 3 losing opponents represents
a novel or unrecognized archetype** — both map cleanly onto leads Phase 41 already surfaced from a
much larger sample (16 episodes) and never acted on. n=3 is too small to say which mechanism
dominates, but it is not too small to say "these are the same two already-identified levers showing
up again," which is itself useful confirmation.

## 4. Our own side: losses vs. wins

**[VERIFIED]** Our own team's PUBLIC trajectory is **essentially identical across all 6 games** —
3 losses and 3 wins alike:

| Episode | Result | Land | Hands | Crop tiles (final) | Animals | Crops | 1st land day |
|---|---|---|---|---|---|---|---|
| 105750065 | loss | 3 | 11 | 0 | 7 | M/S/W | 7 |
| 105745378 | loss | 3 | 11 | 0 | 7 | M/S/W | 7 |
| 105744439 | loss | 3 | 11 | 0 | 7 | M/S/W | 7 |
| 105757292 | win | 3 | 11 | 0 | 6 | M/S/W | 7 |
| 105748242 | win | 3 | 11 | 0 | 7 | M/S/W | 7 |
| 105746303 | win | 3 | 11 | 0 | 7 | M/S/W | 7 |

Land quadrants, hand count, crop mix, land-expansion timing, and animal-ramp timing (first_animal_day
= 0 in all 6) are all constant, and final animal count varies only within noise (6-7). **Our own side
shows no detectable difference in play between these 3 losses and these 3 wins** — the shipped
Submission K/I portfolio runs its fixed, opponent-blind schedule regardless of who it's facing, and
the win/loss outcome in this sample is fully explained by the *opponent's* scale, not any variation
in our own execution.

## 5. What separated the wins, for contrast

**[OBSERVED]** All 3 winning opponents, by contrast, left **large amounts of crop tiles unliquidated**
at day 29: Eric Worrall (31 tiles), Shuaib ayad Jasim Jasim (12 tiles), Moritz Huber (**92 tiles**,
running a much larger 4-crop portfolio that never got harvested down). Two of the three win-side
opponents also never reached our 3-quadrant scale at all (Eric Worrall: 2 quadrants; Shuaib ayad
Jasim Jasim: 1 quadrant, 0 animals, hands=0 by day 29). Moritz Huber DID reach 4 quadrants like two of
our losing opponents, but with **zero animals** and a much less efficient endgame (92 tiles left
standing) — the land scale-up without the clean liquidation discipline our losing opponents also
displayed.

**[INFERRED]** Endgame liquidation completeness (crop_tiles ≈ 0 at day 29 vs. crop_tiles in the
dozens) looks, in this small sample, like a real proxy for overall opponent competence: all 3 losses
came from opponents who liquidated cleanly like we do; all 3 wins came from opponents who did not.
This is consistent with, not contradictory to, the land/animal-scale findings above — a competent
opponent who also outscales us on land or animals beats us; a less competent opponent, even one who
reaches more land or grows more crop variety, does not, because they leave value on the table at the
end. n=6 is very small for this specific claim and it should be treated as suggestive, not confirmed.

## 6. Honest assessment of sample size

n=3 losses is small, and this phase found **two different mechanisms**, not one unifying cause:
land-quadrant scale-up (yuki, Sarthak Patel) and animal-count scale-up (Shawon Biswas). Both,
however, are mechanisms Phase 41 already flagged from a much larger sample and never followed up on
— so while this specific n=3 sample can't by itself prove either lever is "the" answer, it does not
introduce a new, unexplained pattern either. The liquidation-completeness observation (Section 5) is
the most novel finding of this phase, but at n=6 total games it is squarely in "worth watching,
not worth acting on yet" territory.

## 7. Conclusion and recommendation

**Do the 3 losses share a pattern?** Partially. Not one single archetype, but a shared *family*:
2 of 3 losses are cases of an opponent running our own exact crop portfolio at one additional land
quadrant (the 4th-quadrant scale-up archetype); the third is the animal-heavy archetype. Both were
already identified by Phase 41 on a larger sample and never built into a validated benchmark or
retest.

**Does our own side's play look different in losses vs. wins?** No. Our own team's PUBLIC trajectory
(land, hands, crop mix, timing, animal count) is statistically indistinguishable between the 3 losses
and 3 comparison wins in this sample — the shipped agent runs the same fixed schedule regardless of
opponent, and outcome variance here traces entirely to the opponent's own scale and competence, not
to any lapse in our own execution.

**What should a future phase investigate next?** The most concrete, already-partially-supported lead
is the still-untested **whole-portfolio 4th-quadrant scale-up benchmark** Phase 41 first flagged and
Phase 43's Jonaid-archetype reconstruction only partially addressed (that reconstruction used a
different opponent's raw target numbers and lost to Submission I — see Phase 43's finding that
blindly copying scale underperforms our own tuned 3-quadrant targets). This phase adds two more real,
fresh instances (yuki, Sarthak Patel) of a *same-crop-mix* opponent beating us specifically via a 4th
quadrant, strengthening the case that our own capped 3-quadrant land target — not crop selection — is
the more promising specific lever to examine, before any animal-count-driven change (which only
explains 1 of the 3 losses here). The liquidation-completeness observation (Section 5) is worth
tracking as an informal "opponent competence" heuristic in future forensics but is not yet actionable
on its own. No agent code change is recommended from this phase directly — per scope, this is
diagnosis only.
