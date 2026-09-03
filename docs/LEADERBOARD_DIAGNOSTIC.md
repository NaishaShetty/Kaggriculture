# The Gap to Gold

**Why the Kaggriculture agent sits at rank 6044/7305, and what it will take to close the gap.**

Rank 6044 of 7305 isn't a fluke of a young submission — all three submitted agents converge to nearly the same losing score. This report covers what the live Kaggle data, the project's own prior phase reports, and the competition's Discussion forum say about why, and what actually needs to change.

| | |
|---|---|
| **Current rank** | 6,044 / 7,305 (bottom ~17th percentile) |
| **Live score** | 385.3 — Elo-style rating, starts at 600 |
| **Leader's score** | 2,913.0 (MtN, rank #1) |
| **Your 3 submissions** | 376–385, all clustered together |

---

## 1. The leaderboard isn't measuring your bank balance

This is the first misunderstanding worth clearing up, because it reframes everything else: the number next to your name is not your farm's income. It's a win/loss rating.

Kaggriculture's live leaderboard runs an Elo-style rating: every submission starts at **600**, plays episodes against opponents near its current rating, and moves up or down based only on **win/loss/tie** — margin of victory (how much money you had versus your opponent) never enters the calculation. A confirmed community fit puts the update factor at roughly `K ≈ 200·e^(−n/26)`: huge for your first ~10 games, nearly flat by game 80. That's why a rating needs 100+ games and roughly a day of wall-clock time before it means anything — early swings are opponent-draw noise, not skill signal.

More importantly, per Kaggle staff's own pinned post: **the live leaderboard is not the final one.** After the submission deadline, episodes keep running for two more weeks, and a single **Bradley-Terry tournament** over just that window produces the final ranking. Only your **two most recently active submissions** at that point are eligible — a third submission retires the oldest slot, and every new submission restarts at 600. Everything your live rating did before the deadline is discarded.

> **What this changes about how you should work:** stop judging a variant by its money total in your own test battery, and stop resubmitting near-identical builds to "re-roll" a better-looking live number — it buys a nicer screen for a few days and changes nothing about the final tournament. The only two things that matter at the deadline are which two builds sit in your two active slots, and whether they actually beat the live population's current skill level.

---

## 2. What a score of 385 actually tells you

If this were just early-submission noise, your three architecturally different agents wouldn't land within 9 points of each other.

| Submission | Architecture | Age | Live score |
|---|---|---|---|
| `submission_A` | Planner v1 + Variant D substitution | 21h | 382.6 |
| `submission_B` | A + fixed scaling response | 5h | 376.5 |
| `submission_C` (current) | B + animal-count-aware response | 2h | 385.3 |

```
You (C)                    385   [███░░░░░░░░░░░░░░░░░░░]
New-submission baseline    600   [████░░░░░░░░░░░░░░░░░░]
Leader (MtN)              2913   [██████████████████████]
```

A brand-new submission starts at 600 and drifts based on results. Landing at 385 — **215 points below the starting line** — and doing so independently for three different builds — is not "still converging." It's a converged signal that this lineage loses more often than it wins against whatever the live matchmaking pool currently looks like near this rating band. Submission C is only 2 hours old (~60–80% converged per the community's own measured convergence curve), so its exact number will still move, but it's very unlikely to jump the ~2,500-point gap to the leaderboard's top tier — that gap is architectural, not noise.

---

## 3. Root causes, from your own prior audits

You don't need to guess at this — five phases of forensic replay analysis in this repo already diagnosed most of it. Nothing below is new; it's what's been sitting unresolved in the weakness matrix.

### Known weaknesses, never closed

| ID | Issue | Severity | Status |
|---|---|---|---|
| F-001 | Scaling response fires, but its magnitude is fixed and too small against large real opponents | **Critical** | 6 of 9 firing episodes still lost |
| F-003 | Market-exit timing — bulk-selling into a price you've already crashed instead of spacing sales | High | mechanism identified, no fix built |
| F-005 | "Death spiral" — a liquidity guard exists in code but its trigger condition never fires in practice | **Critical** | worst-outcome bug, unaddressed |
| F-002 / F-004 | Scaling-within-tolerance and low-footprint-opponent cases | Unknown | insufficient evidence either way |

### The ceiling is architectural, not tactical

The single clearest data point in the whole project: a real opponent (`moushun chen`) fielding 10 hired hands, 14 animals, and 3 land quadrants beat Submission B by **$48,162**. Your own synthetic testing tool goes bankrupt trying to simulate any archetype past ~10 hands — meaning **you cannot even locally reproduce the scale of opponent that's already beating you live.** Every "0 regressions across 44 comparisons" result in your validation history is true and real, but it was measured against archetypes capped well below where competitive play actually happens.

Your best recorded winning outcome across every phase is around **$28,000–29,000** in final money. Phase 4 built a genuinely new, verified market-impact simulator (`agents/phase4/market_model.py`) — but it was never wired into an actual sell-sizing decision that got tested. It's real, correct capability sitting unused.

> **The uncomfortable number:** per the competition's own discussion forum, players running pure RL self-play are already reaching **$80,000–$160,000+** terminal cash — 3 to 5× your own best winning outcome. That gap can't be closed by re-tuning thresholds inside the current architecture; see §5.

---

## 4. What everyone else is actually doing

Pulled directly from the competition's live Discussion tab. Four distinct approaches are visible in public threads, each with a real, load-bearing tradeoff.

**Pure reinforcement learning** (e.g. Mark Schatza, JAX + PPO, self-play)
10k steps/sec throughput, billions of training steps, 75%-sales / 25%-terminal-cash reward shaping with an exploration bonus per product sold (otherwise it collapses to a melon monoculture). Reached ~$80k cash, then hit a hard wall — exploration collapse, credit assignment across 720 turns is brutal. Reportedly some players are past $160k this way, but the compute and engineering cost is severe.

**Offline search, online distillation** (Beam search / genetic algorithm)
Finds $40k+ solutions offline with unlimited compute, but the live Kaggle server gives you a 1-second-per-turn budget on CPU only — deep search doesn't fit, so it degrades to a shallow, locally-optimal rollout online unless distilled into something fast first.

**Rule-based / heuristic — this is you** (fixed-threshold detectors + response layers)
Fast, deterministic, cheap to validate — and exactly where you are. The community's own consensus on it, independently echoed by other posters: it "works well but easily gets outplayed in the late game when market elasticity drops. It feels too rigid." That's F-003 and F-001 in different words.

**Hybrid: heuristic executor + macro "CEO" layer** (community-recommended breakthrough direction)
Keep a deterministic layer for movement, legality, and logistics (the part you've already solved well), and let a smarter macro layer — search-based or learned, doesn't have to be full RL — own only the expensive decisions: crop portfolio, land timing, sell sizing/timing. Frees the hard optimization problem from also having to learn how to not walk into walls.

One more forum data point worth naming directly: there's active discussion (and a "Daily Top Episodes Dataset" resource, plus an open rules question on Rule 3.14.a) about extracting build orders and farm geometries straight from top players' public replays — described by one poster as the dominant public-leaderboard meta right now. Kaggle staff have also posted a standalone warning about scammers soliciting source code. Treat both as signal about the environment you're competing in, not as something to imitate uncritically.

---

## 5. Live replay evidence from top-ranked play

Discussion posts describe what top players say they're doing; watching actual replays shows what's happening on the board. Two episodes were inspected directly via the Kaggle replay viewer (logged-in session, no source code involved — only the rendered game state).

### Yuan800 (#1, score ~2,930) — self-play validation episode, seed 618269597

This is Yuan800's own submission playing itself (Kaggle runs a validation episode against the agent's own prior copy on upload), so both farms shown are the same underlying agent:

- **Turn ~20 of day 1**: multiple hands already hired and a pasture already built — nearly the entire $3,000 starting bank spent same-day (down to $27 by day 1's last turn).
- **Day 7-8**: a second land quadrant (NE) already purchased; both quadrants (50 tiles) nearly fully planted, with almost no idle tiles.
- **Day 9**: sheep flock grown to 8+ — well above the 5-6 ceiling your own animal-response layer currently targets.
- Replanting was continuous day over day — dense fields of freshly-tilled dirt every day, implying several hands cycling water → harvest → replant in parallel rather than one farmer working serially.

### Crop Dusta (#3) vs. Whyme Labs (#2) — real head-to-head, seed 215620170

More useful than the self-play game: a genuine match between two different top-5 teams, where one clearly separated from the other early.

- **Day 2**: both sides already had a sheep pasture built and multiple hands active — confirms the day-1/day-2 animal-infrastructure pattern isn't unique to Yuan800.
- **Day 3**: the two farms visibly diverged. **Crop Dusta's** tiles were mostly showing stacked yield counts of 2-3 per tile — dense, advanced production. **Whyme Labs'** tiles were still mostly single units, with several still empty.
- **Result**: Whyme Labs lost this game ("[Loss] Whyme Labs 2906 (-5)" shown in the replay header).

The second replay is the more important finding: **tile-utilization density by day 3 was the visible difference between a win and a loss, between two teams that are both already in the gold band.** This isn't just a gap between you and the top — it's the same variable that separates 2nd place from 3rd.

### What this corroborates

Both replays point at the same thing your own Phase 2-4 reports kept deferring as out of scope: a **rolling-horizon, tile-level task planner** that keeps every owned tile continuously in a water/harvest/replant cycle across several simultaneous hands, rather than fixed per-archetype thresholds. The self-play game shows what "fully utilized" looks like at the top (near-zero idle tiles, land bought by day 7, animal counts past your current caps); the head-to-head shows that *falling behind on exactly that metric*, even slightly, is enough to lose to another top-5 team.

---

## 6. Path to gold, in priority order

Ordered by leverage, not by how interesting each item is to build.

### P0 · Fix, don't rebuild
**Make F-005's liquidity guard actually fire, and stop the F-003 bulk-sell crashes.**
You already have a diagnosed root cause for both. F-005's countermeasure exists but its trigger never activates under real conditions — that's a detection bug, cheap to fix relative to its severity (it's your worst-outcome failure mode). F-003 has an exact, quantified case: a single 95-unit dump landed at the crash floor and cost ~$25,650 versus spacing the same units across the price recovery. Wire the already-built `market_model.py` into your actual SELL sizing so it never happens again — this is real, tested capability you built and shelved.

### P1 · Raise the ceiling, not the floor
**Build a benchmark that can represent opponents who are already beating you.**
Your synthetic archetypes go bankrupt past ~10 hands, while real opponents run 10 hands / 14 animals / 3 land and win by tens of thousands. Stop validating exclusively against synthetic archetypes and start replaying real public top episodes (the Daily Top Episodes Dataset the community already assembled) as regression benchmarks. You cannot fix what you cannot reproduce locally.

### P2 · Architecture
**Move from fixed-threshold response layers to the hybrid pattern.**
F-001's core diagnosis — a correct detector paired with a response magnitude that's fixed regardless of how far behind you are — is a structural property of threshold-based logic, not a tuning error. The field's own consensus direction is a deterministic executor (which you've already validated well through Phases 2–3) topped with a macro layer that makes portfolio, land-timing, and sell-timing decisions proportionally to the actual gap and actual remaining time — search-based or learned, not necessarily full RL. This is the step-change the $28k → $80k+ gap requires; no amount of re-tuning your two existing scaling constants gets there.

### P3 · Evaluation discipline
**Optimize win-rate against strong opponents, not mean coin totals against weak ones.**
Every promotion in this project so far has been justified by "0 regressions across N archetypes" — true, but those archetypes are mostly weak (passive, conservative, market_selling) and the win margins there don't matter at all to your rating. Score every future candidate by win/loss against your hardest replayed opponents on fixed seeds, exactly the way the live Bradley-Terry tournament will.

### P4 · Submission hygiene
**Stop spending submission slots on near-duplicates.**
A, B, and C are all live right now within 9 points of each other — that's three architecturally distinct ideas correctly tested, which is good practice. Going forward: only your two most recent submissions matter at deadline, and each new one restarts at 600 and needs ~a day to mean anything. Reserve submissions for genuine architectural changes (per P2), not incremental threshold tweaks.

---

**Sources:** live Kaggle leaderboard, submissions history, and Discussion tab (kaggle.com/competitions/kaggriculture) read directly this session under the user's logged-in account; internal phase reports `results/phase3_6/`, `results/phase3_7/phase3_7_WEAKNESS_COVERAGE_MATRIX.md`, `results/phase3_8/`, and `results/phase4/phase4_FINAL_REPORT.md` from this repository.
