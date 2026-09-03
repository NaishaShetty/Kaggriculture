"""
Phase 9 Experiment 4 (Phase 6 §17, Experiment 4): High-scale animal capacity
re-test, against Submission C's ACTUAL current cap.

Submission C's animal-response cap (agents/phase3_8/animal_response.py,
read directly, not assumed): `HIGH_RESPONSE_ANIMALS = {"COW": 3, "SHEEP": 3}`
-- 6 animals total, reached only when the opponent-scaling detector fires
with the opponent at/above `HIGH_ANIMAL_THRESHOLD = 12`. Real strong
opponents (Phase 6 §5/§12) sustain 10-14 animals simultaneously for most of
the game -- far above this 6-animal ceiling.

CONTROL ARM: mirrors Phase 2.3's a3_animal_lifecycle methodology
(scripts/phase2_3_configs.py STAGE_A["a3_animal_lifecycle"]: no crops, feed
bought via market -- isolates animal economics from crop-labor
competition) but as an ANIMAL-COUNT sweep (0-6, i.e. through and just past
Submission C's own cap) rather than a single-animal type comparison (which
is what Phase 2.3 originally tested -- it never swept animal COUNT at all,
only animal TYPE at count=1, so this is the closest faithful adaptation of
its methodology to the count-marginal-value question Phase 6 asks). 0
extra land quadrants (matches Phase 2.3's small-board regime), n_hands=6
fixed (ample and cheaply affordable at this scale -- `sum(fib(0..5))=20`/
day -- so labor is never the bottleneck; Experiment 2 already covers the
hand-count question separately). Animals split as evenly as possible
between COW and SHEEP (Submission C's own response never uses GOOSE --
agents/phase3_8/animal_response.py's BASELINE/MODERATE/HIGH targets are
COW+SHEEP only -- so this mirrors the actual composition being tested
against). Uses the UNMODIFIED agents/phase2_3/common.py::make_agent.

VARIABLE ARM: same structure, animal counts 6-14 (i.e. from Submission C's
current cap up through the 10-14 range Phase 6 observed), on a 3-extra-
quadrant board (matches Experiment 2's choice, itself matching Lai Eu Wen's
observed max land count), n_hands=10 fixed (ample, matching the labor scale
real strong opponents pair with high animal counts -- not itself testing
the hand-count question). Uses scripts/phase9/common.py::
make_high_scale_agent with the same disclosed $30,000 starting-money
cushion as Experiment 2 (see that module's docstring for why), applied
identically across every cell in this arm so it cancels out of the
marginal comparison.

New code only. Does not modify agents/phase2_3/, agents/phase2_6/,
agents/phase3_3/, agents/phase3_5/, agents/phase3_8/, or main.py.
"""
import csv
import json
import os

from scripts.phase9.common import (
    DEVELOPMENT_SEEDS, HIGH_SCALE_STARTING_MONEY,
    make_control_agent, make_high_scale_agent, run_cell, mean_by_value, marginal_values,
)

OUT_ROOT = "results/phase9"

CONTROL_ANIMALS = [0, 1, 2, 3, 4, 5, 6]
VARIABLE_ANIMALS = [6, 7, 8, 9, 10, 11, 12, 13, 14]
CONTROL_HANDS = 6
VARIABLE_HANDS = 10
VARIABLE_LAND_QUADRANTS = 3

# Disclosed capital cushions -- see scripts/phase9/common.py's module docstring for
# the full rationale (separating "can this be bootstrapped from $3000" from "is
# animal N worth it at this scale"). $3000 default is enough for Phase 2.3's
# original a3_animal_lifecycle cells (which only ever tested a SINGLE animal), but
# buying 6 animals ($400-500 each) simultaneously on day 0 while also feeding all
# of them via BUY_PRODUCT before any product income exists (COW first_yield_day=8,
# SHEEP=6) is not affordable from $3000 -- confirmed by direct trace inspection
# (a raw $3000-start run of this exact control cell ends day-1 with $0 cash, only
# 3/6 animals ever placed, zero product ever sold). CONTROL_STARTING_MONEY is a
# SMALL, disclosed bump (still tiny relative to VARIABLE_STARTING_MONEY) applied
# uniformly across every count 0-6 in the control arm, so it cancels out of the
# marginal comparison exactly like the variable arm's larger cushion does.
CONTROL_STARTING_MONEY = 6000


def split_cow_sheep(n):
    n_cow = (n + 1) // 2
    n_sheep = n - n_cow
    return {"COW": n_cow, "SHEEP": n_sheep}


def run_control():
    rows = []
    for n in CONTROL_ANIMALS:
        animals = split_cow_sheep(n) if n > 0 else None
        agent = make_control_agent(
            crops=None, n_hands=CONTROL_HANDS, land_quadrants=0,
            animals=animals, animal_buy_day=0, feed_source="market",
        )
        for seed in DEVELOPMENT_SEEDS:
            result = run_cell(
                "phase9_animal_control", f"n{n}", seed, agent,
                extra_config={"startingMoney": CONTROL_STARTING_MONEY},
            )
            rows.append({"arm": "control", "n_animals": n, "seed": seed, **result})
            print(f"  [control n_animals={n}] seed={seed} final_money=${result['final_money']}", flush=True)
    return rows


def run_variable():
    rows = []
    for n in VARIABLE_ANIMALS:
        animals = split_cow_sheep(n) if n > 0 else None
        agent = make_high_scale_agent(
            crops=None, n_hands=VARIABLE_HANDS, land_quadrants=VARIABLE_LAND_QUADRANTS, land_buy_day=0,
            animals=animals, animal_buy_day=0, feed_source="market",
        )
        for seed in DEVELOPMENT_SEEDS:
            result = run_cell(
                "phase9_animal_variable", f"n{n}", seed, agent,
                extra_config={"startingMoney": HIGH_SCALE_STARTING_MONEY},
            )
            rows.append({"arm": "variable", "n_animals": n, "seed": seed, **result})
            print(f"  [variable n_animals={n} land={VARIABLE_LAND_QUADRANTS} hands={VARIABLE_HANDS}] "
                  f"seed={seed} final_money=${result['final_money']}", flush=True)
    return rows


def main():
    print("=== CONTROL ARM (no crops, market-fed, 0 extra land, 6 hands, animals 0-6, $3000 start) ===")
    control_rows = run_control()
    print("\n=== VARIABLE ARM (no crops, market-fed, 3 extra land, 10 hands, animals 6-14, $30000 start) ===")
    variable_rows = run_variable()

    all_rows = control_rows + variable_rows
    os.makedirs(OUT_ROOT, exist_ok=True)
    out_csv = os.path.join(OUT_ROOT, "phase9_animal_capacity_results.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"\nWrote {len(all_rows)} rows to {out_csv}")

    control_means = mean_by_value(control_rows, "n_animals")
    variable_means = mean_by_value(variable_rows, "n_animals")
    control_marginal = marginal_values(control_means)
    variable_marginal = marginal_values(variable_means)

    summary = {
        "control_means_by_n_animals": control_means,
        "control_marginal_by_n_animals": control_marginal,
        "variable_means_by_n_animals": variable_means,
        "variable_marginal_by_n_animals": variable_marginal,
    }
    out_json = os.path.join(OUT_ROOT, "phase9_animal_capacity_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")

    print("\nCONTROL marginal $/animal:", control_marginal)
    print("VARIABLE marginal $/animal:", variable_marginal)


if __name__ == "__main__":
    main()
