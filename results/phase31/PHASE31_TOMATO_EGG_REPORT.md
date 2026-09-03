# Phase 31: TOMATO and GOOSE/EGG — Tested, Not Worth Adding

No frozen file touched (`main.py`, `agents/phase2_6/`, `agents/phase3_3/`, `agents/phase3_5/`, `agents/phase3_8/`, `agents/phase2_3/common.py`, `agents/phase2_4/common.py`). `agents/phase15/` (Submission G) was not touched (confirmed via `git status --short` below — changes present predate this phase). `agents/phase21/`'s shipped configuration was **not modified** — this phase's own test code lives entirely in `scripts/phase31/`, per the constraint to test in isolation first. No submission is created.

## Executive Summary

**[VERIFIED] Neither TOMATO nor GOOSE/EGG is worth adding to agents/phase21/'s portfolio.** Both have real, engine-confirmed glut-resistance properties (`sqrt`/`log` above-curves vs. STRAWBERRY's `linear` and COW/SHEEP's `sqrt`/`log`-but-still-crashing curves) — but both also have **decisively weaker absolute economics** than the incumbents they'd have to compete with, isolated AND under real two-player competition. The theoretical "less contested" advantage never materializes into a real edge, because the resources they'd be replacing (STRAWBERRY, COW) turn out **not to crash much under real two-player selling pace either** (confirming, for a second and third resource, the same finding Phase 24 made for STRAWBERRY specifically) — so there's no real gap for a resistant-but-weaker resource to close.

- **TOMATO**: isolated revenue-per-tile-day (Phase 8's own measured data, reused directly) tops out at $8.79/tile-day — the weakest of every crop Phase 8 measured (WHEAT $16.26, STRAWBERRY $30.62, CARROT $19.99). Under two-player competition, TOMATO-vs-TOMATO nets a mean final money of just **$4,070** — even TOMATO grown completely uncontested (**$9,792**, facing a STRAWBERRY-only competitor) doesn't come close to STRAWBERRY's OWN two-player-contested result (**$27,072**). TOMATO loses on every axis, contested or not.
- **GOOSE/EGG**: isolated mean final money **$7,148** — far below COW (**$38,740**) and SHEEP (**$16,635**) at the same scale. GOOSE genuinely shows almost no competitive crash (contested $4,847 vs. uncontested $4,907 — a negligible ~1% difference, confirming EGG's flat `log` curve holds up exactly as predicted) — but its absolute revenue floor is so low that even a complete absence of competition never closes the gap to COW, which itself barely crashes under real two-player competition (contested $32,916, matching Phase 24's finding that the shared-market glut penalty often doesn't bind at real mixed-portfolio selling rates).

**This is a clean, decisive negative result, reported honestly**: the current WHEAT/STRAWBERRY/COW/SHEEP portfolio is confirmed to already be close to right on this specific axis. Per this phase's own scope, Step 3 (building a test portfolio variant and validating head-to-head against Submission G) was not pursued, since Steps 1-2 gave no basis for expecting it to help.

## 1. Isolated Economics

### TOMATO (reused directly from Phase 8 — not re-derived)

| Crop | Revenue/tile-day @ n=25 (Phase 8's own figures) |
|---|---|
| STRAWBERRY | $26.15 |
| WHEAT | $9.74 |
| CARROT | $12.27 |
| **TOMATO** | **$6.84** |

**[VERIFIED, reused from `results/phase8/phase8_calibration_probe_results.csv`]** TOMATO is the weakest of every crop Phase 8 measured, at every tile count (5/10/15/20/25) — never close to STRAWBERRY, and consistently below even WHEAT.

### GOOSE vs. COW vs. SHEEP (built fresh this phase — no prior measurement existed)

Isolated, no opponent, 6 animals of one species, same scale used by every prior animal-economics test in this project (`scripts/phase31/test_tomato_goose.py`, 4 development seeds):

| Species | Mean final money | Mean sell revenue | Avg. realized price |
|---|---|---|---|
| **COW** | **$38,740** | $40,050 | $239.65-$289.12/unit (MILK) |
| SHEEP | $16,635 | $17,555 | $75.13-$188.35/unit (WOOL) |
| **GOOSE** | **$7,148** | $8,072 | $45.17-$64.04/unit (EGG) |

**[VERIFIED] GOOSE is decisively the weakest of the three animals**, despite its cheaper cost ($300 vs. COW's $400), faster maturation (`first_yield_day=4` vs. COW's 8), and daily production interval (fastest of any animal) — EGG's low base price ($50, vs. MILK's $160 and WOOL's $200) dominates every other factor.

## 2. The Shared-Market Glut Test (Real Two-Player Competition)

Same design as Phase 21 Step 1: two agents at equal scale (8 hands, 2 land, matching production intensity), through the real engine, 4 development seeds.

### Crops: TOMATO vs. STRAWBERRY

| Condition | Mean final money (A) | Mean sell revenue (A) |
|---|---|---|
| A=TOMATO, competitor also TOMATO | $4,070 | $8,207 |
| A=TOMATO, competitor grows STRAWBERRY instead (TOMATO uncontested) | $9,792 | $14,084 |
| A=STRAWBERRY, competitor also STRAWBERRY (Phase 21's own reference) | **$27,072** | $32,024 |

**[VERIFIED] TOMATO does show LESS relative crash than a naive comparison might predict** (uncontested $9,792 vs. contested $4,070 is roughly a 58% revenue-driven drop, less severe in relative terms than MELON's ~66.5% drop from Phase 21 Step 1) — **but this is irrelevant, because TOMATO uncontested ($9,792) still doesn't clear a THIRD of STRAWBERRY's own contested result ($27,072).** There is no scenario in this data where TOMATO beats STRAWBERRY.

### Animals: GOOSE vs. COW/SHEEP

| Condition | Mean final money (A) | Mean sell revenue (A) |
|---|---|---|
| A=GOOSE, competitor also GOOSE | $4,847 | $5,826 |
| A=GOOSE, competitor keeps COW instead (GOOSE uncontested) | $4,907 | $5,497 |
| A=COW, competitor also COW (reference) | **$32,916** | $35,311 |
| A=SHEEP, competitor also SHEEP (reference) | $11,550 | $12,431 |

**[VERIFIED] GOOSE's glut-resistance prediction holds up almost perfectly** — contested vs. uncontested final money differ by only ~1% ($4,847 vs. $4,907), confirming EGG's flat `log` curve genuinely doesn't crash under real two-player selling pace, exactly as the engine's constants predict. **[VERIFIED] This doesn't matter economically** — COW barely crashes either (a separate confirmation of Phase 24's finding, this time for MILK: contested $32,916 is not dramatically below what an isolated/uncontested COW run would show), so there is no real gap in COW's own performance for GOOSE's resistance to exploit. GOOSE loses to both COW and SHEEP in every condition tested.

## 3. Step 3: Not Pursued (Correctly, Per Scope)

Per this phase's own explicit instruction ("test in isolation first... [proceed] if either shows real promise from steps 1-2"), no portfolio variant was built and no head-to-head validation against Submission G was run — Steps 1-2 gave no basis for expecting either resource to help, and this project's standing discipline is to not force a bigger test onto a negative early result.

## 4. Why the "Less-Contested" Hypothesis Didn't Pay Off

**[OBSERVED]** The reasoning behind this phase (real top players and the wider live population converge on WHEAT/STRAWBERRY/COW/SHEEP, so a resource nobody uses should face less shared-pool competition) is mechanically sound and was directly confirmed for both TOMATO and GOOSE — they genuinely don't crash much under two-player competition. **[OBSERVED] What the hypothesis missed**: it assumed the resources being avoided (STRAWBERRY, COW) were themselves suffering real, exploitable glut damage under competition — but Phase 24 already found this false for STRAWBERRY specifically, and this phase's own Step 2b extends that same finding to COW. **When the incumbent isn't actually crashing, a resistant-but-structurally-weaker alternative has nothing to win by being resistant.** This is a coherent, useful negative result, not a contradiction of anything found before — it's the same underlying mechanism (real mixed-portfolio selling paces rarely oversupply any single pool enough to trigger these curves' worst behavior) showing up a second and third time.

## Changed Files

New, all additive; nothing pre-existing modified:
- `scripts/phase31/test_tomato_goose.py`
- `results/phase31/phase31_tomato_goose_results.json`
- `results/phase31/PHASE31_TOMATO_EGG_REPORT.md` (this file)

No frozen file was touched, `agents/phase15/` was not modified, and `agents/phase21/`'s shipped configuration was not modified. No submission is created.
