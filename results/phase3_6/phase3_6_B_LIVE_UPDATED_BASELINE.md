# Phase 3.6 Live Submission B Baseline (Updated)

Recursive re-scan of `COMPETITION RESULTS\SUBMISSION B` found **13 completed episodes** (up from 4 at the prior audit): 26 JSON files (13 full replays + 13 execution logs) + 13 videos, **0 parse errors**, all statuses `DONE`. One additional in-progress/deleted-account game seen in a prior video sidebar snapshot did NOT appear as a completed file this round and is correctly excluded (no data exists for it). One of the 13 completed games (episode 104768895) is itself against a `[Deleted]` account but has full, complete replay data (status=DONE, valid rewards) — included as a legitimate completed episode, distinct from the still-incomplete deleted-account game noted previously.

## Updated Baseline (n=13)

| Metric | Value |
|---|---|
| Total games | 13 |
| Wins | 4 |
| Losses | 9 |
| Win rate | 30.8% |
| Mean final money | $21,842 |
| Median final money | $22,335 |
| Mean margin | -$12,456 |
| Median margin | -$10,967 |
| Worst loss | moushun chen, -$48,162 |
| Largest win | cheesama, +$18,606 |

**Explicit caveat, per standing project instruction**: this win rate (30.8%) must NOT be read as "Submission B is a weak agent" or compared directly against Submission A's win rate to conclude one submission is globally better/worse. Both samples are small, opponent pools differ, and rating systems carry high early variance. This baseline exists for **mechanism-level evidence**, not an overall competitive verdict.

## Mechanism-Level Findings From the Expanded Sample

- **F-001 is now confirmed in 5 of 9 real B losses** (was 2 of 3): zixma13, moushun chen, the deleted-account game, iBooNDK, and Safin all show the detector triggering and the response firing against large hands+animals commitments, with the loss NOT prevented in every one of these 5 cases except Safin (a near-miss, -$1,617 only).
- **3 real wins occurred WITH the detector triggering and response firing** (cheesama: opponent 10 hands/0 animals; Thivvin Raj: 7 hands/6 animals; TinkerBotics: 10 hands/0 animals) — the response CAN and DOES work against high-labor opponents when the opponent's animal/land commitment stays low. This meaningfully refines the Phase 3.6 finding "matching scale doesn't help" — it appears MORE nuanced: the response is sufficient against labor-only scaling, but not against combined labor+animal+land scaling.
- **F-003 confirmed recurring**: a second real instance (kyunyoung, -$2,987, detector never triggers, opponent modest at 3 hands/2 animals) joins the original Vishwanath N Iyer case.
- **Two entirely new mechanisms discovered** this round: NEW-F-005 (a catastrophic $0 death-spiral loss with no scaling signature at all) and NEW-F-006 (a large loss from a land+animal-heavy, hands-modest opponent that the response only partially addresses, since it never touches land). See `phase3_6_C_WEAKNESS_COVERAGE_MATRIX.md` for full detail.

Full per-episode data: `phase3_6_B_LIVE_UPDATED_BASELINE.json`.
