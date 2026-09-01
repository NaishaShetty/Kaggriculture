# Architecture Map (Phase 1 Deliverable C)

## Agent -> Observation -> Decision -> Action -> Simulator -> New State -> Evaluation loop

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                kaggle_environments runner                │
                    │  (env.run([agent0, agent1])  /  Kaggle submission host)  │
                    └─────────────────────────────────────────────────────────┘
                                   │ calls agent(obs) each turn, per player
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ OBSERVATION  (per-player dict, built by kaggriculture.interpreter())  │
   │  player, day, hour, farms[0..1] (public), market (shared),            │
   │  town (shared), private (this player only: shed, seeds, inventories)  │
   └───────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ AGENT DECISION  (pure function: obs -> action dict)                   │
   │  agents/baseline_agent.py::agent(obs)  — stateless, scans obs each    │
   │  call; same call signature as built-in pass/random/starter agents     │
   │  defined inside kaggriculture.py itself.                              │
   └───────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ ACTION  {"farmer": [...], "hands": [[...],...], "market": [[...],...]}│
   └───────────────────────────────────────────────────────────────────────┘
                                   │ both players' actions collected
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ SIMULATOR STEP  kaggriculture.py::interpreter(state, env)             │
   │  1. Atomic PLANT-demand validation per player                         │
   │  2. Apply farmer action, then each hand's action (_apply_unit_action) │
   │  3. Process market queue (_process_market): HIRE/BUY_LAND atomic,     │
   │     then per-unit lockstep SELL/BUY_SEED/BUY_PRODUCT/BUY_ANIMAL       │
   │  4. Town consumption (_town_consume): shop + town-center draws        │
   │  5. Plant decay past max lifespan (_decay_plants), every turn         │
   │  6. If end of day: _end_of_day — daily plant/animal refresh, weed     │
   │     spawn (seeded RNG), inventory->shed drop, reset farmer/hands,     │
   │     possible new town-shop unlock                                    │
   │  7. Advance step/day/hour counters                                    │
   │  8. If final step: mark DONE, reward = farm money                     │
   └───────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ NEW STATE  — updated farms/market/town written back onto the shared   │
   │ observation object; both players' next `obs` reflects it (loop back   │
   │ to top for the next turn, x720)                                       │
   └───────────────────────────────────────────────────────────────────────┘
                                   │ after final turn
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ EVALUATION                                                            │
   │  Local: env.steps[-1][i].reward = final bank balance; harness/        │
   │  run_episodes.py aggregates across episodes/seeds into summary stats. │
   │  Kaggle ladder: episode outcome (win/loss/tie by final money) feeds   │
   │  an Elo-style skill rating; final leaderboard fit via Bradley-Terry   │
   │  tournament over post-deadline episodes.                              │
   └───────────────────────────────────────────────────────────────────────┘
```

## Component map (file/module level)

| Layer | Location |
|---|---|
| Env registration & runner | `kaggle_environments` package (PyPI, installed in `C:\kagvenv`) |
| Kaggriculture rules engine | `kaggle_environments/envs/kaggriculture/kaggriculture.py` (vendored copy: [../vendor_kaggriculture/kaggriculture.py](../vendor_kaggriculture/kaggriculture.py)) |
| Env spec/schema | `kaggle_environments/envs/kaggriculture/kaggriculture.json` |
| Official docs (agent-facing) | `kaggle_environments/envs/kaggriculture/{README.md,AGENTS.md}` — identical content to the Kaggle "Data" tab kit |
| Renderer / visualizer | `kaggle_environments/envs/kaggriculture/visualizer/{default,playable}` |
| Our agents | [../agents/baseline_agent.py](../agents/baseline_agent.py) (custom); `pass`/`random`/`starter` built into `kaggriculture.py` |
| Our evaluation harness | [../harness/run_episodes.py](../harness/run_episodes.py) |
| Raw + aggregated results | [../results/&lt;tag&gt;/{raw_episodes.json,raw_episodes.csv,summary.json}](../results/) |
| Beginner variant (found, unused) | `kaggle_environments/envs/kaggriculture_beginner/` — a second, presumably simplified registered env; not explored in Phase 1, flagged as an unknown for Phase 2 |

## Player perspective vs. shared state

- `farms`, `market`, `town` are **shared mutable objects** — both players' `obs` point at the exact
  same Python data during a local `env.run()`, always indexed `farms[0]`/`farms[1]` in stable player-id
  order (never re-indexed to "me"/"opponent"). `obs["player"]` is the only thing that tells an agent
  which index is itself.
- `private` is rebuilt per-player and never shared — this is the actual privacy boundary. Opponent shed
  contents, seed counts, and carried inventories are structurally absent from your observation, not just
  conventionally hidden.
