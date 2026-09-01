# Kaggriculture — Phase 1 Report

**Phase Status: PASS**

Date: 2026-08-15. All work under `C:\Kaggriculture`. See linked files for full detail — this
report is the executive summary tying deliverables A-H together.

---

## 1. Environment (Deliverable A)

- **Source of truth**: https://www.kaggle.com/competitions/kaggriculture (Overview/Data/Code/Rules
  tabs, all read directly via browser — see [docs/00_official_overview_raw.md](00_official_overview_raw.md)).
  Confirmed real, live, featured Kaggle simulation competition (host: Kaggle + Google; $50,000 prize
  pool, 10x $5,000; entry deadline 2026-09-23; 12,530 entrants at capture time).
- **Simulator**: not a separate download — it ships as a registered environment (`"kaggriculture"`)
  inside the `kaggle-environments` PyPI package. Installed version: **1.32.7**.
- **Install procedure** (reproducible):
  1. `python -m venv C:\kagvenv` — a **short-path venv was required**; installing into the default
     global site-packages (`AppData\Local\...\Python311`) or the `--user` site-packages
     (`AppData\Roaming\...`) both failed with Windows `MAX_PATH` errors while unpacking one
     dependency's (`orbax-checkpoint`) deeply-nested bundled test fixtures.
  2. `pip install --no-deps kaggle-environments` (avoids the problematic dep resolution order).
  3. `pip install Flask jsonschema numpy pygame pyjson5 termcolor requests tenacity google-auth pydantic kaggle`
     — installs everything `kaggle_environments` needs at import time, **skipping** the
     `jax`/`flax`/`gymnax`/`orbax-checkpoint`/`optax`/`chex`/`litellm`/`transformers` stack, which are
     dependencies for *other* bundled environments (an LLM/RL environment set that ships in the same
     package) and are not imported by the kaggriculture module itself.
  4. Verified via `import kaggle_environments` — succeeds cleanly (stderr noise about `open_spiel`
     game registration is unrelated startup logging, not an error).
- **Environment details**: Python 3.11.3 (venv), Windows 11, `kaggle-environments==1.32.7`,
  `kaggle==2.2.4` (CLI). Full pinned list not captured (Phase 1 used ad hoc installs); a `pip freeze`
  snapshot of `C:\kagvenv` should be taken before Phase 2 for full reproducibility.
- **Locating the simulator**: `kaggle_environments/envs/kaggriculture/kaggriculture.py` (1086 lines) —
  vendored into this project at [vendor_kaggriculture/kaggriculture.py](../vendor_kaggriculture/kaggriculture.py)
  for reference (not modified). A **second, unexplored** registered variant,
  `kaggriculture_beginner`, also exists in the package — flagged as a Phase 2 unknown, not
  investigated in Phase 1.
- **Running it**:
  ```python
  from kaggle_environments import make
  env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
  env.run([agent_or_name, agent_or_name])   # names: "pass" | "random" | "starter", or a .py path, or a callable
  ```
  Verified working end-to-end — see [scripts/smoke_test.py](../scripts/smoke_test.py).
- **Kaggle CLI / submission**: `kaggle` CLI installed and functional. **Kaggle API authentication
  completed** (user-provided API token, saved to `~/.kaggle/access_token`). Verified via
  `kaggle competitions list -s kaggriculture` and `kaggle competitions list --group entered` (user has
  already joined; team rank 0, 4,504 teams total at check time). Official Data-tab bundle downloaded:
  `kaggle competitions download kaggriculture -p kaggriculture-data` →
  [kaggriculture-data/](../kaggriculture-data/) (`README.md` + `AGENTS.md`, 39.43 kB, matches the
  Data-tab listing exactly). **`AGENTS.md` in the official download is byte-identical to the copy
  bundled inside the installed `kaggle-environments==1.32.7` package**
  ([vendor_kaggriculture/AGENTS.md](../vendor_kaggriculture/AGENTS.md)). **`README.md` in the official
  download is NOT identical** — it documents an older, non-`hinge` market pricing model for
  Carrot/Tomato/Egg; see Documentation Discrepancies below for the confirmed, officially-sourced
  diff (no longer just a web-page-vs-package comparison — this is Kaggle's own downloadable bundle
  disagreeing internally between its two files, and disagreeing with the actual running simulator).

## 2. Verified Mechanics (Deliverable B)

Full reference: [docs/01_mechanics_reference.md](01_mechanics_reference.md). Everything in it is
tagged DOCUMENTED / VERIFIED / HYPOTHESIS. Headline VERIFIED (source-code-confirmed, not just
web-documented) facts:

- Action dict schema confirmed exactly: `{"farmer": [...], "hands": [[...],...], "market": [[...],...]}`.
- **BUY_ANIMAL deposits directly into the shed**, not into field inventory — an animal must be
  `PICKUP`'d from the shed before it can be `PLACE`'d on a coop/pasture. Not explicit on the web docs.
- **BUILD_COOP/BUILD_PASTURE have $0 monetary cost** — the documented "Action Cost: 1 + 1" refers to
  turn-actions (build, then place), not dollars.
- Exact turn-processing order confirmed line-by-line from `interpreter()` (validation → unit actions
  → market lockstep → town consumption → per-turn decay → end-of-day refresh only on day boundaries →
  counters → terminal reward).
- **Determinism confirmed empirically**: identical `seed` config + identical agents ⇒ byte-identical
  episode across two independent runs (only the run's random UUID differed) — see
  [scripts/determinism_check.py](../scripts/determinism_check.py).
- Plant decay ("every other turn" once past max lifespan) is genuinely turn-granular, not day-granular.
- A freshly-planted one-time crop already carries `yield_units = 1`, but `HARVEST` is a no-op until
  `day - planted_day >= first_yield_day` — this gap is what broke our first baseline draft (see
  Failure Analysis).

## 3. Architecture (Deliverable C)

See [docs/02_architecture_map.md](02_architecture_map.md) for the full Agent → Observation → Decision
→ Action → Simulator → New State → Evaluation diagram and component/file map.

## 4. Evaluation Harness (Deliverable D)

[harness/run_episodes.py](../harness/run_episodes.py) — runs N episodes of any two agents (built-in
name, `.py` file, or callable), with either fixed reproducible seeds (`seed_base + episode_index`) or
env-default seeding, and writes per run:
- `raw_episodes.json` / `.csv` — every episode's seed, final money for both players, winner, per-player
  status, wall-clock runtime. **Raw data always preserved, never only aggregates.**
- `summary.json` — win/loss/tie rate, per-player error count (non-`DONE` status), and
  mean/median/std/min/max of final money for both players.
- optional full replay JSON per episode (`--save-replays`).

## 5. Reference Agent Results (Deliverable E)

10 episodes per matchup, fixed distinct seed ranges (no cherry-picking), full 720-turn episodes.

| Matchup | P0 win% | P1 win% | Tie% | P0 mean $ | P1 mean $ | Errors |
|---|---|---|---|---|---|---|
| starter vs random | 100% | 0% | 0% | 3,586.6 (σ=127) | 25.0 (σ=54) | 0 / 0 |
| pass vs random | 100% | 0% | 0% | 3,000.0 (σ=0) | 0.0 (σ=0) | 0 / 0 |
| pass vs starter | 0% | 100% | 0% | 3,000.0 (σ=0) | 3,553.6 (σ=145) | 0 / 0 |

Raw: [results/starter_vs_random](../results/starter_vs_random), [results/pass_vs_random](../results/pass_vs_random), [results/pass_vs_starter](../results/pass_vs_starter).

**Key finding**: the built-in `random` agent is a **net money-loser** over a full season (mean final
$0-25 from a $3,000 start) — it reliably ends up broke or near-broke. `pass` (a pure no-op agent)
trivially preserves its starting $3,000 exactly every time (σ=0, as expected — nothing it does can
change its own money). `starter` (the built-in carrot-loop agent) reliably nets a modest profit
(+$550 mean). This ordering — starter > pass > random — is a sanity-check that basic, deliberate
farming beats both inaction and undirected action, and that undirected action is actively harmful
here (spending on seeds/hires without the follow-through to recoup them).

## 6. Our Baseline Agent (Deliverable F)

[agents/baseline_agent.py](../agents/baseline_agent.py) — a deterministic, stateless "Wheat
Patroller": each turn it scans the whole owned farm for the single highest-priority action
(harvest-ready > needs-water > plantable-if-holding-a-seed), moves greedily toward the nearest such
tile if not already on one, always sells any wheat sitting in the shed, keeps exactly one wheat seed
on hand when affordable, and (only once cash is 3x+ the next land price) buys additional land. Wheat
was chosen deliberately: cheapest seed ($10), best documented yield/tile/day (0.80), lowest downside
if a single market swing goes badly. No hired hands, no animals, no other crops, no market timing —
intentionally out of scope for a Phase 1 control-condition baseline per the task brief.

## 7. Baseline Evaluation (Deliverable G)

15 episodes per matchup, fixed distinct seed ranges, full 720 turns, no cherry-picking.

| Matchup | Baseline win% | Opponent win% | Baseline mean $ | Opponent mean $ | Errors |
|---|---|---|---|---|---|
| baseline vs pass | 100% | 0% | 5,124.3 (σ=564) | 3,000.0 (σ=0) | 0 / 0 |
| baseline vs random | 100% | 0% | 5,233.7 (σ=331) | 38.7 (σ=145) | 0 / 0 |
| baseline vs starter | 100% | 0% | 5,378.3 (σ=571) | 3,529.5 (σ=85) | 0 / 0 |

Raw: [results/baseline_vs_pass](../results/baseline_vs_pass), [results/baseline_vs_random](../results/baseline_vs_random), [results/baseline_vs_starter](../results/baseline_vs_starter).

**45/45 episodes won, 0 ties, 0 errors, across 3 different opponents and 3 disjoint seed ranges.**
Mean net profit vs. the $3,000 starting bank: **+$2,124 to +$2,378** over a season, roughly double the
built-in `starter` agent's own margin (+$530 mean vs `pass`/`random`). Variance is non-trivial
(σ≈$330-570 on ~$5,000 means, i.e. ~6-11% coefficient of variation) — worth flagging rather than
glossing over, consistent with the "report variance, don't cherry-pick" rule. It comes from weed-spawn
RNG and market-price drift interacting with a single-tile-at-a-time farmer with no hands, which we
did not attempt to reduce in Phase 1.

## 8. Major Discoveries

1. **Windows long-path install failure** is not a Kaggriculture issue but an artifact of
   `kaggle-environments`' unrelated bundled dependencies (`orbax-checkpoint`'s test fixtures) —
   worked around via a short-path venv + selective dependency install; anyone else setting this up on
   Windows will hit the same wall.
2. **BUY_ANIMAL → shed, not inventory.** Not stated plainly in the docs; confirmed only by reading
   `_commit_unit()`. Materially changes how an agent must sequence animal purchases (buy → walk to
   shed → pickup → walk to structure → place, minimum 2 extra turns beyond the purchase itself).
3. **Newly-planted one-time crops already show `yield_units=1`**, which is a trap for any agent using
   a naive "yield_units > 0 → harvest" check (see Failure Analysis below) — the correct gate is
   `day - planted_day >= first_yield_day`, which the sim enforces server-side as a silent no-op, not
   an error, so the bug it causes (crop weeds out from neglect) is easy to miss without a full-length
   smoke test.
4. **`random` agent is a reliable money sink**, not neutral. Anyone using `random` as a "control"
   baseline should not assume it behaves like a weak-but-sane player — it actively loses nearly its
   entire starting bank.
5. A **second registered environment, `kaggriculture_beginner`**, ships alongside the main one and was
   not explored — worth a look in Phase 2 in case it's a useful simplified training/debug target.

## 9. Documentation Discrepancies

| # | Documentation says | Implementation does | Evidence | Current interpretation | Affects later strategy? |
|---|---|---|---|---|---|
| 1 | **Officially downloaded** `kaggle competitions download kaggriculture` bundle's `README.md`: Carrot uses `log`/0.20 below `I0`, Tomato uses `linear`/0.40, Egg uses `linear`/0.40 for their scarcity-side price curve. This matches the live Overview web page exactly (table in [docs/00_official_overview_raw.md](00_official_overview_raw.md)). | The same official download's `AGENTS.md` (a *different file in the same zip*), the installed `kaggle-environments==1.32.7` package's `MARKET_PARAMS`, **and that same package's own bundled `README.md`/`AGENTS.md`** all agree with each other and use a `hinge` function for all three goods instead (Carrot `below_target=1.00`, Tomato/Egg `below_target=0.40` but `hinge`-shaped) — i.e. 3 of 4 independent sources agree with each other and disagree only with the official download's `README.md`. | Downloaded the real Data-tab bundle post-authentication (`kaggriculture-data/README.md`, `AGENTS.md`); diffed both files against the installed 1.32.7 wheel's copies. `README.md` differs (non-hinge); `AGENTS.md` is byte-identical (hinge). Computed scarcity price at `I0-T` differs materially for Carrot ($42 per the stale README vs $70 actual/consistent-elsewhere). | This is Kaggle's own **`README.md` lagging behind an update** that was correctly propagated to `AGENTS.md`, the PyPI package, and (presumably) the live matchmaking servers. The **installed package (and its `AGENTS.md`) is authoritative** for local testing and actual agent behavior. | **Yes — significant.** Any Phase 2 pricing-strategy work for carrot/tomato/egg must use the in-code `hinge` formula (`u=x/T`, price term `u + 8·max(0,u-1)²`, scaled), not the stale `README.md` table. **Use `AGENTS.md` or the installed package source, never the standalone `README.md`, as the pricing source of truth** until Kaggle syncs it. |

## 10. Remaining Unknowns

- `resolve_episode_seed()` internals (lives in `kaggle_environments.utils`, not inspected) — exact
  behavior when no seed is passed.
- `actTimeout`/`runTimeout` config values seen in a live env (`1s`/`1200s`) — not stress-tested against
  a deliberately slow agent; relevant to real submission risk, not yet characterized.
- `kaggriculture_beginner` — entirely unexplored second environment.
- Whether the Kaggle Data-tab download (once authenticated) matches the vendored package copy
  byte-for-byte, or reflects yet another version — not yet checked directly against Kaggle's servers.
- Full `pip freeze` of the working venv not yet captured for bulletproof reproducibility.
- Variance sources behind the ~6-11% CoV in baseline final-money across seeds — not decomposed (could
  be weed RNG, market drift, or something else); flagged, not explained.

## 11. Recommended Next Phase (Phase 2 scope — not started)

Priority economic questions Phase 2 should investigate, in the order they'd most change strategy:
1. **Multi-crop / multi-tile parallelism value**: is a single wheat-only farmer near the ceiling of
   what one unit can do, or does diversifying crops (tomato/strawberry's ongoing yields, melon's high
   unit price) meaningfully beat a wheat monoculture once tile-count is no longer the bottleneck?
2. **Hired-hand ROI**: at what farm size/cash level does `HIRE`'s fib-cost curve stop paying for
   itself, given the (now corrected) `hinge` pricing curves for several goods?
3. **Animal economics**: eggs/milk/wool were entirely untested in Phase 1 (baseline has zero animal
   logic) — first-yield delay (4-10 days) and ongoing/indefinite production make them a very different
   risk/reward profile from one-time crops; needs its own baseline before judging.
4. **Land-expansion timing**: our 3x-safety-margin BUY_LAND rule was arbitrary — a real sensitivity
   sweep on when quadrant expansion pays for itself (given the fixed $1k/$2k/$4k ladder) is needed.
5. **Head-to-head dynamics**: everything in Phase 1 was single-player-economics testing (agent vs.
   passive/random/simple opponents). Since the market is shared and orders are processed in lockstep,
   two aggressive sellers of the same good will crash each other's price — this interaction has not
   been tested at all and could matter more than any single-player optimization.
