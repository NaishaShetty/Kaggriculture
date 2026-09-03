# A Fresh Read on Kaggriculture — First Principles, Not Prior Phases

Written after re-reading `vendor_kaggriculture/kaggriculture.py` (the actual engine
source, not any summary of it) and the official overview page directly, deliberately
setting aside everything built in Phases 1-20. The goal: what would an agent look
like if designed from these mechanics up, rather than from patching forward?

## The one fact that reframes everything: the market is shared and adversarial

Every crop/animal has a price curve `price(inv) = base ± amp·f(|inv-I0|)`, and `inv`
is **one shared pool per resource across both players** — not per-player. Every
phase so far analyzed crop economics in isolation (Phase 8 explicitly: single
player, no opponent) or measured opponent behavior passively (Phase 6: read their
public tiles, never modeled the market as a battlefield). But the market is the
one piece of the game state that is **literally the same number for both players,
every turn.** Whatever the opponent sells moves the price I sell into next, and
vice versa. This has never been treated as a lever — only as noise to minimize.

### Why MELON is a trap at scale, mechanically, not just empirically

Look at the actual glut curves, not just revenue-per-tile-day:

| Resource | Above-glut function | Price at 1×T oversupply | Price at 2×T oversupply |
|---|---|---|---|
| MELON | `sq` (quadratic), target 3.60 | $1 (floor) | $1 (floor) |
| STRAWBERRY | `linear`, target 1.60 | $1 (floor) | $1 (floor) |
| WOOL | `sq`, target 3.20 | $1 (floor) | $1 (floor) |
| CARROT | `sqrt`, target 0.70 | $10 | $1 (floor) |
| TOMATO | `sqrt`, target 0.60 | $24 | $9 |
| **WHEAT** | **`log`**, target 0.20 | **$20** | **$19** |
| **EGG** | **`log`**, target 0.20 | **$40** | **$39** |

WHEAT and EGG are the *only* two products that don't collapse to the $1 floor
under oversupply — both use the `log` shape, the flattest curve in the game, and
both have low `above_target` multipliers. Every other product (including
STRAWBERRY, MELON, WOOL, milk) crashes to the floor once combined two-player
production clears one T-width of oversupply — genuinely easy to hit once both
sides are producing at real scale, since T is calibrated against *one player's*
25-tile field over 24 days, and two competing players producing the same crop
will clear that threshold fast.

**This mechanically explains something Phase 6 could only observe as an
unexplained pattern and Phase 8 could not resolve**: real top players (confirmed
directly this session from live Kaggle replays — Larko, Milan Leonard) start on
MELON+WHEAT, then abandon MELON and converge on a large WHEAT-anchored footprint
by day 25. Phase 8 proved MELON has better *isolated* production economics —
correctly, for a single player with no rival draining the same pool. But MELON's
glut curve is the single harshest in the entire game (`sq`, 3.60 — worse than even
WOOL). It's a fine **opening** crop (no competition yet, high per-tile value while
the market is still near I0) and a bad **sustained** crop once two real producers
are both drawing it down. WHEAT's reward-per-tile-day is *lower* per the README
table (0.80 vs MELON's 0.55 — actually WHEAT is higher!) but more importantly its
market can absorb enormous combined two-player volume without collapsing. Every
agent this project has ever built (C through F) reasons about crop choice as a
single-player revenue-maximization problem. None of them reason about it as
"whichever crop I sink real scale into, so does my opponent eventually — which one
can the *shared* market actually hold?"

### GOOSE/EGG: a real, unexploited opportunity, not a Phase 1-20 finding

Nobody in this project — and neither of the two real top players observed live
this session — uses GOOSE at all. Every top player runs COW+SHEEP exclusively.
But EGG shares WHEAT's glut-resistant `log` curve, and GOOSE has the *fastest*
production interval of any animal (daily, vs. COW's every-2-days and SHEEP's
every-3-days — see `ANIMALS` in the engine source). Its base price ($50) is lower
than MILK ($160) or WOOL ($200), so it's plausible real players have already
implicitly priced in that GOOSE isn't worth it per-unit — but nobody in this
project has actually tested that at real combined two-player production scale,
where COW/SHEEP's `linear`/`sq`+high-target glut curves (1.60 and 3.20) might be
quietly capping real returns the same way MELON's does for crops. This is a real,
concrete, testable hypothesis this project has never checked, not a guess dressed
up as one.

## Second reframe: the score doesn't care how much you win by

Kaggle's evaluation (confirmed directly from the Overview page, §Evaluation): Elo
rating, win/loss/tie only, **coin margin does NOT affect rating change**. Every
phase so far — Phase 9 through 19 — optimized for final money as the primary
metric, with win-rate checked as a secondary validation step. That's backwards for
what actually determines rank. A strategy that wins 70% of games by $1 is
rating-superior to one that wins 60% of games by $100,000. This project already
knows this intellectually (`docs/LEADERBOARD_DIAGNOSTIC.md` cites it directly) but
no agent has actually been *designed* around it — every design (Planner v1 through
the Phase 15 macro-controller) is a money-maximizer that gets checked for win-rate
afterward, not a win-rate-maximizer from the start.

What would actually change if win-rate were the design target from day one, not
money:
- **The opponent's public farm state becomes a first-class input, not passive
  telemetry.** Both players' tiles are fully visible (`obs["farms"]` is shared and
  public — confirmed directly in the engine's observation format). An agent
  designed to win, not just earn, should actively watch what the opponent is
  committing to and **deliberately avoid stacking into the same glut-prone
  resource they're already scaling** — not out of politeness, but because it's a
  shared pool and their volume plus mine hits the crash threshold sooner than
  either of us alone would.
- **A close game late is worth defending, not just growing.** If the score is
  close on day 25, a design that reasons in win/loss terms should ask "what
  sequence of actions makes me MORE LIKELY to have more money than them at day 29"
  — which is a different optimization than "what sequence maximizes my own
  expected money." These coincide most of the time, but not always: e.g., a
  slightly-lower-EV action that reduces variance is correct once you're already
  ahead and money-margin stops mattering; a higher-variance action is correct once
  you're behind and only overtaking wins. No agent in this project reasons about
  its own trailing/leading state as a lever — Phase 4's threat/strategy scaffolding
  came close (NORMAL/COUNTER/DEFEND/RECOVER/ENDGAME modes) but was built on top of
  Submission C and never promoted; its core idea (mode switches keyed to relative
  score, not absolute money) is worth reviving, not from C's small-scale baseline,
  but as the organizing principle for a new design.

## Third reframe: nobody has modeled the market as a weapon

Because both players' orders for the same resource process in the same per-unit
lockstep loop against the same shared inventory (confirmed directly in
`_process_market`'s per-unit loop over `order_states` for both players
simultaneously), **selling a resource I don't need, purely to depress its price
right as the opponent is trying to cash out a large position in it, is a legal,
mechanically real lever this project has never once considered.** Every economic
model built so far (`economic_model/model.py`, the market simulator in
`agents/phase4/market_model.py`) treats market impact purely as a *cost to
minimize for your own sells* — never as leverage against the opponent's. This is
speculative — untested, and it would need real evidence before trusting it as a
strategy, not just an intriguing mechanical possibility — but it's a genuinely
unexplored dimension of this specific game, and worth at least an isolated
feasibility check before dismissing it.

## What a genuinely fresh agent design would prioritize, in order

1. **A portfolio chosen for shared-market durability, not isolated yield** — WHEAT
   as the durable backbone (not a starter crop to graduate away from), MELON as a
   deliberately time-boxed opening-only crop (harvested before the opponent's own
   MELON commitment matures), STRAWBERRY as a mid-game addition sized to what the
   market can still absorb given what the opponent is visibly also producing — and
   a real, tested check on whether GOOSE/EGG's glut-resistance makes it
   underrated versus COW/SHEEP at true combined scale.
2. **Win-probability as the literal objective function**, not money with a
   win-rate check bolted on afterward — meaning the agent's own relative
   score position (ahead/behind/close) should change its risk posture, the way a
   human competitive player would, not just its resource targets.
3. **Active opponent-aware portfolio differentiation** — read the opponent's
   public tile state continuously (not just as a scaling-detector trigger, the way
   every phase since 3.3 has used it) and steer away from whatever glut-prone
   resource they're already committing hardest to.
4. **Land/hand/animal targets set from real observed ceiling data (Phase 19
   already did this correctly) PLUS an explicit cash-safety floor from day one**
   (Phase 20 is already addressing this) — but built as one coherent design, not
   assembled as five sequential patches the way agents/phase15/ currently is.

## What I'd explicitly NOT carry forward from Phases 1-20

- The entire fixed-threshold response-layer architecture (Variant D, the scaling
  response, the animal response) — proven, repeatedly, to have a low ceiling
  because it's reactive and capped, not proportional.
- Validating primarily against Submission C/E — already agreed, and confirmed
  independently this session via live Kaggle data, that this was misleading.
- Treating money as the design target — it's an instrumental output, not the
  thing Kaggle actually scores.

## What I'd explicitly keep

- The evidentiary discipline itself (real data over assumption, honest negative
  results, verified mechanisms over guesses) — that's not slowing this project
  down, it's the only reason we know any of the above.
- The already-verified, reusable infrastructure: the market simulator
  (`agents/phase4/market_model.py`), the real-replay forensics pipeline
  (`agents/phase6/replay_forensics.py`), and the fresh top-ladder data already
  pulled this session.
