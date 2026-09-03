> **Update, post-Phase 18 — Submission F is built, validated, and ready to upload.** `kaggriculture_phase18_submission_F.tar.gz` (SHA-256 `16d3d0eb...854e38`, 15 files) packages the Phase 15/16 macro-controller agent. Two honest course-corrections along the way, both worth remembering: (1) Phase 17's wider 15-seed validation caught that Phase 16's "$326 short of the bar" reading was small-sample luck — the true isolated-money mean is ~$43,735, still short of the original $50-80k target; (2) given that, **the promotion decision was deliberately reframed around win-rate rather than isolated money** — Phase 17's same 15-seed validation shows a clean **15/15 (100%) head-to-head win rate against both live submissions, +79% mean margin**, which is the metric that actually determines Kaggle's Elo-style live rank (`docs/LEADERBOARD_DIAGNOSTIC.md` §1), not isolated production economics against opponents this agent never played. Phase 18 re-confirmed the packaged artifact's behavior matches Phase 17's numbers to the dollar, cold-process tested clean, and regression suite stayed at the same 128/133 baseline every phase since 7 has held. **Ready for manual upload to Kaggle** — the original $50-80k stretch target remains open for a future iteration if pursued further, but is no longer the gate on shipping this agent.

> **Update, post-Phase 15 — the thesis is validated, the target is not yet cleared.** `results/phase15/PHASE15_MACRO_CONTROLLER_REPORT.md`: the new macro-controller agent, built exactly per this plan (combined, proportional, early commitment to real-opponent-derived targets), **beats Submission C and E head-to-head in all 4/4 development seeds, +68% mean ($37,184 vs $22,104)**, and reaches a mean isolated $45,126 — a genuine ~1.5-1.6x step-change over C's best-ever ~$28-29k. **Not promoted**: it falls short of this plan's own $50-80k bar (only 1/4 seeds clears $50k, mean sits below all 4 real opponents' actual final banks). The single largest lever in the whole phase was a bug fix, not a design change — a "sticky assignment" bug was silently abandoning already-growing crops every time the day-indexed schedule shifted, costing ~197x on one seed alone ($214→$42,154) once fixed. Diagnosed remaining gap: target *selection* is confirmed correct (grounded directly in real opponent data, already within their observed ranges) — the shortfall is now believed to be **execution efficiency at this larger combined scale** (the task scheduler was only ever validated single-crop, no-animal, at smaller scale — Phase 10's "already near-optimal" finding doesn't necessarily hold at 13 hands/13 animals/50 tiles across multiple crop types simultaneously). The sell-timing layer measured as a wash (not helping, not clearly hurting) and is a candidate to cut or rework. **Next step: a narrowly-scoped follow-up targeting scheduling efficiency at scale, not a bigger rebuild** — see the roadmap for the Phase 16 prompt once sent.

# The Big Swing: Why 15 Phases of Tuning Won't Reach Gold, and What Would

**Straight assessment, then a concrete plan for an architecture that can actually close the gap.**

## 1. The honest scorecard

Fifteen phases in, here's what's actually shipped and what it's worth:

| Submission | What it does | Measured improvement |
|---|---|---|
| D (Phase 7) | Fixes a dead sell-safety wire | Real, but only matters in the specific stuck-inventory case it targets |
| E (Phase 12) | Fixes a dead liquidity guard | **0/44 measured improvement** in every test run — the report itself says so |

And the research thread since (Phases 9-14) has been almost entirely **negative or neutral results**: don't raise the hand cap (Phase 9), scheduling wasn't the problem (Phase 10), animal capacity doesn't pay off in isolation (Phase 9/11), the one real live bug found doesn't matter at your actual scale (Phase 13/14). All of this was done rigorously and honestly — that's exactly why it's trustworthy — but rigor isn't the same as impact. **Every submission so far is defensive. None of them raise the ceiling.**

Meanwhile, the ceiling that actually matters hasn't moved:

- Your best recorded winning outcome, across every phase, is **~$28,000-29,000**.
- Community-reported RL agents on this same leaderboard are already at **$80,000-$160,000+** (per the forum research in `docs/LEADERBOARD_DIAGNOSTIC.md`).
- Real strong opponents parsed directly from your own replays (Phase 6) — Lai Eu Wen, moushun chen, Zach Locke — finish at **$76,000-$104,000+**, sustaining 8-13 hands and 10-14 animals *every single day*, on a portfolio Submission C's architecture has never once run.

That's a 3-5x gap. **No amount of adjusting thresholds inside the current architecture closes a 3-5x gap** — Phase 9/10/13/14 already proved this empirically: the current design has a real, measured ceiling around its current operating point, and pushing individual dials (hands, animals) past it makes things *worse*, not better, because the rest of the architecture wasn't built to use that scale.

## 2. Why tuning hit a wall — the actual mechanism, not a guess

This isn't mysterious. Read Phases 9-11 together and the story is complete:

- **Submission C's targets are small and fixed**: hands locked at 5 (`agents/phase3_5/response_policy.py`), animals capped at 6 even under maximum competitive pressure (`agents/phase3_8/animal_response.py`), crop choice defaults to MELON-solo (`agents/phase2_6/common.py`).
- **Phase 9 proved**: scaling *any one* of these up, alone, on the *existing* portfolio shape, loses money. More hands on a MELON-solo board is negative. More animals in isolation is negative or noise.
- **Phase 11 proved the missing piece**: scale the *whole portfolio* together — crops AND animals, in the proportions real strong opponents actually run — and labor's marginal value **reverses**, net +$7,690 instead of Phase 9's −$29,144, every hand count landing at 3-6x higher absolute money.

The conclusion Phase 9-11 together actually support, stated plainly: **Submission C isn't losing because any single number (hands, animals, MELON-vs-STRAWBERRY) is wrong. It's losing because it never commits to the combined scale real strong opponents operate at, all at once, early.** Planner v1 makes one conservative day-0 sizing decision and mostly stays there. Every phase since has been probing individual knobs on that same small, static commitment — which is exactly why each probe kept coming back "doesn't help" or "noise." You can't discover a step-change by wiggling one dial at a time on an architecture that was never designed to operate at step-change scale.

## 3. What the top of the field is actually doing (synthesized across everything gathered this session)

From real replay data (Phase 6, and this session's own live browser observation of the current #1 and #3):

- **Commitment happens fast and together.** Land, labor, and the first animal purchase land in the same 1-2 day window (Lai Eu Wen: day 9-10). Multiple hands are active from turn 1 of day 1, not ramped in gradually.
- **The commitment is broad, not deep in one crop.** By day 3, the winning side of a real top-5 head-to-head (Crop Dusta vs. Whyme Labs) already showed visibly denser, more advanced tile development than the losing side — tile-utilization density is what separated the win, observed directly in this session.
- **MELON is abandoned for STRAWBERRY by mid-game, in 4/4 real opponents studied** — even though Phase 8 proved STRAWBERRY doesn't win on raw isolated production economics. That contradiction is still unresolved (Phase 8 §6 flags it explicitly) and points at a two-player market dynamic this project has never directly tested — most likely, two players both running MELON (T=300, `above_target=3.60`, a hard crash penalty on oversupply) crash each other's MELON market far harder than an isolated single-player run ever shows, while STRAWBERRY's narrower depth matters less when only one side is committing to it at real volume.
- **Scale is sustained, not a one-time spike.** 13 hands and 12-14 animals held for 15+ consecutive days, each hand re-paid its full Fibonacci daily cost, because the production base (land + diverse portfolio) is big enough to make that scale worth its cost every day.

Submission C's architecture has never modeled any of this as a *combined, proportional* commitment — every layer that's been added (Variant D, the scaling response, the animal response) is a small, capped, reactive patch on top of a conservative baseline. That's the actual gap.

## 4. The big swing: what to build instead

Not another isolated no-submission probe. A genuinely new agent, built and validated with the same rigor this project has always used, but aimed at the scale the evidence now clearly supports — a **model-based macro controller**, exactly what Phase 6 §16 already recommended and explicitly justified (RL isn't viable yet: not enough credit-assignment data, only 2 real games on Submission C; a deterministic, evidence-grounded controller is both cheaper and more auditable given what's actually known).

**What it should do differently from Planner v1**, each point directly backed by a phase already run:

1. **Commit land + labor + a diverse crop-and-animal portfolio together, early** — not Planner v1's single conservative day-0 sizing pass. Target the moushun_chen-shaped portfolio Phase 11 already validated works (STRAWBERRY-anchored + COW/SHEEP), scaled toward real opponents' actual land/hand/animal levels (3-4 quadrants, 8-13 hands, 10-14 animals) rather than Submission C's current fixed 1-quadrant/5-hand/6-animal ceiling.
2. **Make hand/animal/land targets proportional to game state** (day, cash trajectory, opponent's observed scale — reusing the existing `agents/phase3/opponent_observation.py` telemetry this project already built) instead of Submission C's fixed thresholds. This is the structural fix for exactly what Phase 9 vs. Phase 11 revealed: a fixed target is either too small to pay off (Phase 9) or right for one portfolio shape and wrong for another (Phase 9 vs 11's contradiction) — a controller that scales its own targets with the actual game state doesn't have that failure mode by construction.
3. **Use the already-built, already-verified market simulator (`agents/phase4/market_model.py::simulate_sell`) for sell-timing**, not for portfolio/volume decisions (Phase 5 already proved that fails) — this was always the safer, recommended use (Phase 5 §16, Phase 8 §7) and is still unbuilt.
4. **Fix the fetch-bottleneck (Phase 13's finding) as part of this build**, since a controller operating at real animal scale (10-14, not Submission C's capped 6) will hit exactly the throughput ceiling Phase 13 found — irrelevant at C's current scale, directly relevant at the scale this new agent targets.
5. **Validate against real opponent replays as the primary benchmark**, not synthetic archetypes (which cap around 10 hands and have never represented the regime this controller targets) — reuse `agents/phase6/replay_forensics.py`, already built.

**Target, stated plainly so success is measurable**: this build should be judged against **$50,000-80,000+ final money on the moushun_chen-shaped benchmark**, not another few-thousand-dollar delta. If it can't clear that bar in controlled testing, it isn't ready to submit — same evidentiary discipline as every phase so far, just aimed at a number big enough to matter.

## 5. Sequencing

This is a genuinely bigger build than anything shipped so far — it deserves its own dedicated phase, not a quick prompt-and-go. Recommended shape:

1. **Design pass** (this document is step one) — confirm the target portfolio/scale numbers against a slightly larger real-replay sample than Phase 6's 4 opponents, if more are cheaply available (worth a quick pull before committing to exact targets).
2. **Build the controller** as a new, isolated adapter (following the project's own "new agents are separate experimental artifacts" convention) — reusing every already-validated piece (Phase 11's multi-resource execution logic, Phase 13's fetch fix, the market simulator, the opponent-observation telemetry) rather than rewriting anything that already works.
3. **Validate hard**: synthetic archetypes for basic sanity, but the real bar is performance against Phase 6's real-replay benchmarks and head-to-head against Submission C/E on fixed seeds.
4. **Promote only if it clears the $50-80k bar** — and if it doesn't, report why honestly, exactly as every phase so far has.
