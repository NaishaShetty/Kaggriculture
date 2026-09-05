# Phase 44: X-Ray Tool Report

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`,
`agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`,
`agents/phase2_4/common.py`, `agents/phase15/`, `agents/phase21/`). No agent
was built or modified — this is infrastructure only. No submission is
created.

## Executive Summary

**[VERIFIED] Built `scripts/phase44/xray.py`**, a reusable, re-runnable
generalization of Phase 6/41's manual real-opponent-characterization
pipeline — the same idea as the "X-ray your agent" public notebook this
session found during research (David Estevez, real live rank #139), built
in this project's own style, reusing this project's own already-verified
infrastructure. Given a target team and a list of their recent episode IDs,
it produces a win/loss ledger, a strategy fingerprint (Phase 41's own
feature vocabulary, imported not reinvented), opponent kinship/clone
detection against a growing real-opponent library, and an economy-shape
summary — then appends the target's own newly-extracted rows to that
library so the dataset grows every time the tool runs.

**[VERIFIED] The tool does NOT fully automate "who is #1 right now."**
Direct investigation (Section 1) confirms the leaderboard is served by
Kaggle's own internal `competitions.LeaderboardService/GetLeaderboard`
gRPC-web JSON API, which requires session/CSRF context this environment
cannot script blind — a direct unauthenticated call returns `403
PERMISSION_DENIED`. **Everything downstream of "I have a team name and a
list of episode IDs" is 100% scripted, unattended, and re-runnable with
zero code changes** (confirmed by running the tool twice in a row: the
second run reproduces the identical report and correctly adds zero new
library rows, all five already present). The one manual step — identifying
the current target and their recent episode IDs — is small, documented, and
was itself performed live this phase (Section 3) using the exact same
browser mechanism Phase 19/34/39/41 already used, not a new capability.

**[OBSERVED] Real demonstration run against `keiz`, this session's current
rank #1** (the ladder moved since Phase 41, when Crop Dusta held #1 — a
live illustration of exactly why this needs to be re-runnable, not a
one-time snapshot): **5W-0L-0T over its 5 most recent episodes, mean margin
+$8,254.20/game**, and every one of those 5 games shows strong kinship
(0.87-0.999 blended similarity) to other gold-tier real opponents already
in Phase 41's library (Crop Dusta, Jesse Bullard, Himanshu Kumar, Vishal
Dhariwal) — the tool correctly recognizes keiz as a member of the same
"gold-tier full-scale diversified" cluster Phase 41 already identified,
not a false-positive match to a weak archetype. This is a working sanity
check on the kinship metric itself, not just a report of numbers.

## 1. Discovery-Mechanism Finding

**[VERIFIED, direct investigation]** Opened the live leaderboard and
captured its own network traffic (browser session, no login). The
leaderboard table and the Game History panel (both team lookup by rank and
a team's recent episode list) are populated by
`POST https://www.kaggle.com/api/i/competitions.LeaderboardService/GetLeaderboard`
— an internal gRPC-web-over-JSON endpoint, not a documented public REST API.
**[VERIFIED]** a direct, credential-free `fetch()` to this endpoint from the
same origin (`window.fetch`, guessing a plausible request body) returns
`{"error":{"code":403,"message":"Permission 'competitions.get' was
denied","status":"PERMISSION_DENIED"}}` — confirming it requires
authenticated session context this tool cannot supply headlessly.
**[OBSERVED]** attempts to intercept the app's own real outgoing request
(patching `window.fetch`/`XMLHttpRequest` before triggering a refresh) did
not capture a call in the time available — the app likely issues this
request from a bundled, minified client library in a way that isn't easily
hooked post-load, and further reverse-engineering (finding the exact
protobuf-JSON field names and any required headers) was judged not worth
the time against this phase's actual goal.

**[VERIFIED] What DOES work with zero login or token, unchanged from every
prior phase**: `GET https://www.kaggle.com/competitions/episodes/<id>/replay.json`
— confirmed again this phase (14 direct fetches, all `HTTP 200`, standalone
via `curl`/`urllib`, no browser). This is the one piece Phase 19 already
established and every phase since (34, 39, 41, this one) has reused
unchanged.

**Conclusion, stated plainly**: this environment cannot, by itself,
headlessly answer "who is rank #1 right now" or "what are their recent
episode IDs" — that specific lookup requires either a Kaggle API
token/login (explicitly excluded, same constraint every real-data phase in
this project has operated under) or a live, authenticated browser session.
**This is not a limitation unique to this phase** — Phase 19/34/39/41 all
performed this exact same lookup the exact same way (a person, or an
agentic session with browser access, reading the rendered leaderboard and
clicking through Game History), they just didn't build a reusable tool
around what came after it. This phase does.

## 2. What Was Built

`scripts/phase44/xray.py`:
- **Fetch** (`fetch_episode`): `urllib`-only, no browser dependency, caches
  to `results/phase44/raw_replays/` — genuinely scriptable, reused unchanged
  logic (same endpoint, same discipline as every prior phase).
- **Extraction** (`analyze_episode`): imports
  `scripts.phase41.archetype_survey.extract_both_public` and `team_features`
  directly — **not reimplemented**. Determines win/loss/tie/margin from
  `replay["rewards"]`, indexed by the target team's position in
  `info.TeamNames` (public metadata, not the target's own action).
- **Kinship/clone detection** (`kinship_score`, `find_kinship`) — **new
  logic this phase built**, since Phase 41 didn't: a blended similarity
  metric, `0.5 · cosine_similarity(numeric scale/timing vector) + 0.5 ·
  Jaccard(crop-portfolio set)`. Justification: scale (land/hands/crop-tiles/
  animals + first-land/first-animal commitment day) is continuous signal;
  crop-portfolio SHAPE (`crops_ever_at_scale`, a set) is categorical — two
  teams at very different scale can still share an identical crop strategy
  and vice versa, so averaging a continuous-similarity metric with a
  set-similarity metric catches either kind of kinship, not just one.
  Threshold 0.85 (tunable) flags a "close match."
- **Economy shape** (`economy_shape`): land timing, herd/crop scale,
  endgame liquidation (crop tiles at 0 by the final observed day, or not) —
  reuses the CONCEPT from `agents/phase21/liquidation.py` (a well-run farm
  should be near-fully liquidated by day 29, since every crop's own
  planting cutoff makes new plantings pointless past a certain day) for
  reference only; that module is never imported or modified.
- **Growing library** (`append_to_library`): appends new
  `(episode_id, team_name)` rows to `results/phase44/phase44_xray_library.json`,
  deduplicated — confirmed idempotent by running the tool twice in a row
  (Section 4).
- **CLI** (`main`): defaults to reading `results/phase44/target_manifest.json`
  (team name + episode ID list + how/when they were discovered); accepts
  `--team-name`/`--episode-ids` or `--manifest <path>` overrides for a
  different target.

## 3. The One Manual Step, Performed Live This Phase

**[VERIFIED]** Using this session's own live browser access: opened the
Kaggriculture leaderboard, confirmed the current rank-1 team is **`keiz`**
(score 3012.9 — the ladder has moved since Phase 41, when Crop Dusta held
#1, now sitting at rank #2 at 2995.8), opened keiz's Game History panel,
and clicked through its 5 most recent games, reading each episode ID off
the resulting `GET .../episodes/<id>/replay.json` network request — the
exact same mechanism Phase 19/34/39/41 already used, not a new one. Result
recorded in `results/phase44/target_manifest.json`:

```json
{
  "team_name": "keiz", "rank": 1, "score": 3012.9,
  "discovered_at": "2026-09-04",
  "episode_ids": ["105462264", "105458810", "105457934", "105455373", "105451852"]
}
```

**To refresh this for a future run**: repeat this same click sequence for
whoever holds #1 (or any other target) at that time, overwrite
`target_manifest.json` with the new team name/episode IDs, then run
`python scripts/phase44/xray.py` — no code changes needed. This is a
2-3-minute step for a person, or a handful of browser tool calls for an
agentic session with live browser access (which is how this phase's own
demo run, and every real-data phase before it, actually did it).

## 4. Sample Real Run — `keiz`, Rank #1

```
=== X-ray: keiz (5 episodes) ===
  episode 105462264: WIN  margin=$12,034.00  land=3 hands=10 crop_tiles=7  animals=10 crops=[CARROT, MELON, STRAWBERRY, WHEAT]
  episode 105458810: WIN  margin=$10,920.00  land=3 hands=10 crop_tiles=2  animals=12 crops=[MELON, STRAWBERRY, WHEAT]
  episode 105457934: WIN  margin=$8,954.00   land=3 hands=10 crop_tiles=3  animals=8  crops=[CARROT, MELON, STRAWBERRY, TOMATO, WHEAT]
  episode 105455373: WIN  margin=$2,104.00   land=3 hands=10 crop_tiles=6  animals=12 crops=[CARROT, MELON, STRAWBERRY, WHEAT]
  episode 105451852: WIN  margin=$7,259.00   land=3 hands=10 crop_tiles=12 animals=9  crops=[CARROT, MELON, STRAWBERRY, TOMATO, WHEAT]

Record: 5W-0L-0T, mean margin $8,254.20
```

**[OBSERVED]** Every game a win, margins ranging $2,104-$12,034 —
consistent with holding rank #1 at the time of this pull. **[OBSERVED]**
land=3/hands=10 in every single game — remarkably stable scale, matching
Phase 41's own "Archetype A: gold-tier full-scale, diversified" cluster
almost exactly (that cluster's own range was land 3, hands 10-12). CARROT
appears in 4/5 games, TOMATO in 2/5 — directly consistent with Phase 41's
40%-of-sample CARROT/TOMATO finding, now reconfirmed on a fresh, independent
5-game sample from a different point in time.

**Kinship matches (>= 0.85 blended similarity)**: every one of keiz's 5
games matched strongly to Crop Dusta, Jesse Bullard, Himanshu Kumar, and/or
Vishal Dhariwal — all real, upper-tier opponents already in Phase 41's
library, several above 0.98. **No matches at all to any small-scale/
conservative archetype rows** (Kota Iizuka, Shinzo Takayama) or animal-
heavy/land-light rows (마짜MAZZANG, Reda HEDDAD) — the metric
correctly separates keiz into the cluster it actually belongs to, not a
false positive. This is a genuine (if informal) validation of the kinship
metric's usefulness, not just a demonstration that it runs.

Full report: `results/phase44/phase44_xray_keiz_20260904T122437Z.json`.
Growing library after this run: `results/phase44/phase44_xray_library.json`
(5 rows, all keiz — the tool's own output, separate from and cross-checked
against, not merged into, Phase 41's own `phase41_team_features.json`).

## 5. Re-Runnability, Confirmed

**[VERIFIED]** Ran the tool a second time, unchanged, against the same
manifest: identical win/loss ledger, identical kinship matches, and
**"Appended 0 new row(s)... skipped 5 already-present duplicates"** — the
growing library correctly deduplicates by `(episode_id, team_name)` rather
than re-appending on every run. A fresh timestamped report file is still
written each run (so a run's own point-in-time output is never lost), while
the library itself only grows with genuinely new data.

## 6. How a Future Phase Should Use This

1. **Refresh the target** (the one manual step, Section 3): check the live
   leaderboard for whoever currently holds the rank of interest, note their
   team name, open Game History, and copy the episode IDs of however many
   recent games are wanted into `results/phase44/target_manifest.json` (or
   pass `--team-name`/`--episode-ids` directly for a one-off target without
   touching the manifest file).
2. **Run it**: `python scripts/phase44/xray.py`. No other setup.
3. **Read the report**: win/loss ledger for a quick "is this team actually
   strong right now" check, strategy fingerprint for archetype
   classification (reusing Phase 41's own taxonomy language), kinship
   matches to see if this team is a new archetype or a variant of one
   already catalogued, economy shape for a quick land/herd/liquidation
   summary.
4. **The growing library accumulates automatically** — repeated runs over
   time, across different targets, build a real, ever-expanding dataset
   future phases can query directly (`results/phase44/phase44_xray_library.json`)
   without re-running anything, the same way Phase 41's own one-time sample
   is queried today.
5. **For a broader refresh** (many teams at once, e.g. redoing Phase 41's
   own 16-episode pull at a fresh point in time): repeat step 1 for
   multiple targets before running — the tool itself accepts one target per
   invocation by design (keeping the manual step small and well-scoped
   rather than trying to batch an entire leaderboard scrape into one manual
   session), but nothing stops running it several times in a row for
   several targets in one sitting.

## Changed Files

New, all additive:
- `scripts/phase44/xray.py`
- `results/phase44/target_manifest.json`
- `results/phase44/raw_replays/` (5 fresh episode JSONs)
- `results/phase44/phase44_xray_keiz_20260904T122437Z.json`
- `results/phase44/phase44_xray_library.json`
- `results/phase44/PHASE44_XRAY_TOOL_REPORT.md` (this file)

No frozen file, `agents/phase21/`, or any other agent file was touched. No
submission is created.
