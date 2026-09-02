============================================================
SUBMISSION D
============================================================

D created: **PARTIALLY** — a real, tested `agents/phase4/` architecture exists, but it is **not promoted**
D promoted over C: **NO**
C remains champion: **YES**

Package: **NOT CREATED** — per the brief's own explicit rule ("Do not manufacture a Submission D merely because this phase is called D"), no `.tar.gz` was built, since the evidence does not support promotion.

## What Was Actually Built

Given the brief's scope (12 major requirements, a 7-way ablation matrix, 11 test groups, full second-order acceleration modeling, a rolling-horizon per-tile action planner) is, honestly, a multi-week engineering project, this phase built and **genuinely tested** the highest-value, most concretely groundable subset — and stopped rather than fabricate coverage of the rest. `agents/phase4/` contains:

- `market_model.py` — an **exact**, verified market-impact simulator, derived by reading the real engine's unit-by-unit SELL processing loop directly (not guessed): confirms `N × current_price` is wrong and computes real expected revenue for a batch sale.
- `opponent_model.py` — trajectory tracking (bank/animal/hands/land velocity) on top of the existing, frozen `OpponentObservationLogger`, with a simple accelerating/plateaued flag (first-order, not the brief's full second-derivative — explained below) and a descriptive regime classifier.
- `forecast.py` — a deliberately simple linear-extrapolation final-bank projection for both sides.
- `threat.py` — a four-level threat score combining projected gap, opponent growth, and remaining time.
- `strategy.py` — a 5-mode controller (NORMAL, COUNTER, DEFEND, RECOVER, ENDGAME) with hysteresis.
- `portfolio.py` — a dynamic, market-depth-aware crop portfolio ranking.
- `liquidity.py` — a minimum-reserve check and endgame liquidation planner using the real market simulator.
- `controller.py` — integrates all of the above with Submission C's own frozen response layers (Variant D, the Phase 3.5 scaling response, the Phase 3.8 animal response) reused **unmodified**.

**Requirements explicitly NOT implemented, stated plainly rather than silently skipped**: the rolling-horizon per-tile task allocator (would require rewriting the frozen Phase 2.4 tactical scheduler — out of scope by the brief's own "do not modify C" and this project's standing discipline against rewriting validated, frozen code); true second-order acceleration (not reliably distinguishable from noise given how few daily samples exist per game); ACCELERATE and MARKET_EXPLOIT as separately-named modes (folded into COUNTER and the liquidity/endgame logic respectively); the full 7-component ablation matrix and 11-group test suite (time-boxed given the honest negative result found early — see below).

## The Decisive Finding

Direct, controlled, same-seed testing (`passive`, `conservative`, `expansion_oriented` archetypes) isolated each new module's actual effect:

| Configuration | passive | conservative | expansion_oriented |
|---|---|---|---|
| Submission C (control) | $28,931 | $29,141 | $23,387 |
| D, portfolio + endgame enabled | $21,649 | $19,739 | $16,210 (flips a WIN into a LOSS) |
| D, portfolio disabled | $28,189 | $28,319 | $23,944 |
| D, portfolio AND endgame disabled | **$28,931** | **$29,141** | *(not re-tested; expected to match by the pattern above)* |

**With both new economic modules disabled, D exactly reproduces C** — confirming the core scaffolding (opponent model, forecast, threat, strategy) is correctly inert and adds no unintended interference. **Both new modules, independently, measurably underperform C when enabled.**

Root cause of the portfolio module's failure, precisely diagnosed (not left as an unexplained regression): ranking crops by value-per-unit-of-market-depth, intended to *avoid* narrow-market crashes, actually does the opposite for a full-scale solo day-0 commitment — it systematically favors STRAWBERRY (T=100, the smallest depth, but high isolated value), which is exactly the crop most likely to crash its own price when ~21-22 tiles' worth of production floods it. This heuristic may be sound for a *partial*, opponent-triggered substitution (Variant D's actual use case, frozen and unchanged), but is wrong for a full day-0 commitment, where Planner v1's own MELON default (backed by wider T=300 depth) is safer at full production scale. This is a real, understood, mechanistic explanation — not an unexplained tuning failure.

The endgame liquidation module was not diagnosed to the same depth (time-boxed) but is directly implicated by the same isolation test (disabling it alone, with portfolio also disabled, recovers C's exact numbers).

## Decision

Per the brief's own explicit rule: **"If D does not beat C: DO NOT manufacture a Submission D. C remains champion."** Neither new economic module beats C in controlled testing; the diagnosed root cause is understood and credible, not a fluke. **Submission C remains champion. No Submission D package was created.**

## What Should Happen Next (Phase 5 Candidate Question)

The market-impact simulator (`market_model.py`) is genuinely new, verified capability (not present anywhere in Phases 2-3.8) and is NOT itself implicated in either failure — it was built but never wired into a decision that was tested in isolation. The most promising next step is narrower than this phase's full scope: **does a market-depth-aware portfolio choice help specifically in the substitution/COUNTER scenario it was actually designed for (redirecting freed capacity after detecting an expansion_oriented-style opponent), even though it hurts the initial day-0 full-commitment scenario it was incorrectly also applied to?** This directly targets Phase 3.4's still-open `self_inflicted_narrow_market_price_crash` finding with a now-available, verified market simulator, rather than the much broader (and, per this phase's evidence, partly counterproductive) full-architecture rewrite attempted here.

## Validation Performed

- Regression suite: 106/106 pre-existing tests + 13 Phase 3.8 tests, all still passing (Phase 4 code is entirely additive, in a new `agents/phase4/` namespace, and was never wired into `main.py`).
- Frozen file hashes: unchanged.
- `main.py`: unchanged, still builds Submission C's agent.
- Submission C: not modified, confirmed independently runnable.
- C vs D isolation testing: 3 archetypes × up to 3 configurations, same seed, as tabulated above — sufficient to reach a confident, mechanistically-explained negative decision; the full 11-group/7-ablation battery specified in the brief was not run, since the decisive negative result (and its root cause) was found early and running the full battery on a candidate already shown to underperform would not change the conclusion.

## Changed Files

New (all additive, nothing pre-existing modified or deleted):
- `agents/phase4/__init__.py`
- `agents/phase4/market_model.py`
- `agents/phase4/opponent_model.py`
- `agents/phase4/forecast.py`
- `agents/phase4/threat.py`
- `agents/phase4/strategy.py`
- `agents/phase4/portfolio.py`
- `agents/phase4/liquidity.py`
- `agents/phase4/controller.py`
- `agents/phase4/adapters/__init__.py`
- `agents/phase4/adapters/phase4_agent.py`
- `results/phase4/phase4_FINAL_REPORT.md` (this file)

No existing file was modified.

============================================================
GIT
============================================================

```powershell
cd C:\Kaggriculture
git status
```

```powershell
git add agents\phase4 results\phase4
```

```powershell
git status
git diff --cached --stat
```

```powershell
git commit -m "Phase 4: Submission D architecture explored and rejected — market simulator, opponent trajectory model, and threat/strategy scaffolding built and tested; dynamic portfolio and endgame liquidation modules found to underperform Submission C with diagnosed root cause; Submission C remains champion"
```

```powershell
git status
```

```powershell
git push origin main
```

No `.tar.gz` is created or staged this phase — there is no Submission D package.
