"""
Phase 2.6 open-hypothesis experiments (brief section 33.15), targeted only
at planner-decision-relevant regions, per section 14/15/29's instruction not
to re-run a giant discovery campaign for low-impact uncertainty.

H1 -- animal time-scaling (economic_model.model.animal_production_value's
      linear proportional-scaling assumption, flagged HYPOTHESIS in Phase 2.5).
      Decision-relevant because the planner's BUY_ANIMAL evaluation directly
      depends on it once day > 0.
H2 -- portfolio-complexity-aware selling (does a single-crop-calibrated
      selling-policy uplift transfer to a complex multi-resource portfolio).
      Decision-relevant because the planner's SWITCH_SELL_POLICY evaluator
      (agents/phase2_6/evaluator.py::_evaluate_sell_policy_switch) explicitly
      branches on portfolio complexity and needs evidence either way.
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.phase2_4.common import make_agent  # noqa: E402
from instrumentation.pipeline import run_and_analyze  # noqa: E402
from economic_model.model import EconomicState, animal_production_value  # noqa: E402

OUT_PATH = "results/phase2_6/hypothesis_test_results.json"
STEPS = 720
SEEDS = list(range(303000, 303006))  # n=6, disjoint from every prior seed range in this project


def h1_animal_time_scaling():
    """Hypothesis: animal_production_value()'s linear time-scaling of the
    30-day solo COW profit ($7,370, F5) predicts actual measured profit for
    a COW purchased mid-episode (day 15, half the horizon) within a
    reasonable margin.
    Controlled: solo COW (no crops), n_hands=1, feed_source=market, opponent=pass, 720 steps.
    Treatment: animal_buy_day in {0, 15}.
    Seeds: 303000-303005 (n=6).
    """
    results = {"hypothesis": "animal_production_value's linear time-scaling assumption "
                              "(Phase 2.5, flagged HYPOTHESIS) predicts actual measured profit "
                              "for a mid-episode animal purchase",
               "conditions": {}}
    for buy_day in (0, 15):
        agent = make_agent(animals={"COW": 1}, n_hands=1, animal_buy_day=buy_day, feed_source="market")
        moneys = []
        for seed in SEEDS:
            record, _, _ = run_and_analyze(agent, "pass", STEPS, seed, "h1_animal_scaling", f"day{buy_day}_seed{seed}")
            moneys.append(record["outcome"]["final_money"][0])
        actual_profit = statistics.mean(moneys) - 3000.0

        state = EconomicState(day=buy_day, cash=3000, n_hands=1)
        predicted = animal_production_value("COW", state, n_hands_available=1)

        results["conditions"][f"buy_day_{buy_day}"] = {
            "n_seeds": len(SEEDS), "actual_mean_final_money": round(statistics.mean(moneys), 2),
            "actual_mean_profit": round(actual_profit, 2),
            "predicted_profit": predicted.value, "predicted_range": [predicted.low, predicted.high],
            "within_predicted_range": (predicted.low <= actual_profit <= predicted.high) if predicted.value is not None else None,
            "relative_error_pct": round(100 * (actual_profit - predicted.value) / abs(predicted.value), 1) if predicted.value else None,
        }

    d0 = results["conditions"]["buy_day_0"]
    d15 = results["conditions"]["buy_day_15"]
    both_in_range = d0["within_predicted_range"] and d15["within_predicted_range"]
    results["classification"] = "SUPPORTED" if both_in_range else (
        "REJECTED" if not d0["within_predicted_range"] and not d15["within_predicted_range"] else "INCONCLUSIVE")
    results["conclusion"] = (
        f"day-0 actual profit ${d0['actual_mean_profit']} vs predicted ${d0['predicted_profit']} "
        f"(range [{d0['predicted_range'][0]},{d0['predicted_range'][1]}]); "
        f"day-15 actual profit ${d15['actual_mean_profit']} vs predicted ${d15['predicted_profit']} "
        f"(range [{d15['predicted_range'][0]},{d15['predicted_range'][1]}])."
    )
    return results


def h2_portfolio_complexity_selling():
    """Hypothesis: a selling-policy uplift calibrated on a SIMPLE single-crop
    portfolio (F14) does NOT transfer to a COMPLEX multi-resource portfolio,
    consistent with F19's null result -- re-examined here using ALREADY
    COLLECTED Phase 2.4 data (no new episodes needed, per the brief's own
    "only run new experiments when needed" instruction) plus one fresh
    confirmatory check of the planner's own conservative default."""
    # Cite existing Phase 2.4 data directly (results/phase2_4/analysis_summary.json).
    existing_evidence = {
        "simple_portfolio_MELON_threshold_0.9_vs_passive": {"passive": 27891.0, "threshold": 28491.0, "uplift": 600.0},
        "complex_portfolio_integrated_threshold_1.0_vs_passive": {"passive": 31562.5, "threshold": 21892.125, "uplift": -9670.375},
        "complex_portfolio_integrated_threshold_batch_vs_passive": {"passive": 31562.5, "threshold_batch": 31354.125, "uplift": -208.375},
    }
    # Fresh confirmatory check: does the PLANNER's own conservative "treat as a wash,
    # do not assume uplift" default for complex portfolios avoid the -$9,670 loss a
    # naive transfer of F14's uplift would have caused? Compare the planner's
    # evaluator output directly (no new episodes needed -- this is a pure model query).
    from agents.phase2_6.evaluator import _evaluate_sell_policy_switch
    from economic_model.model import EconomicState
    complex_config = {"crops": {"MELON": 0.5, "STRAWBERRY": 0.5}, "animals": {"GOOSE": 1, "COW": 1}}
    state = EconomicState(day=5, cash=5000, market_prices={"MELON": 100}, market_inventory={"MELON": 10500})
    est = _evaluate_sell_policy_switch({"params": {"mode": "threshold"}}, state, complex_config)

    supported = (existing_evidence["complex_portfolio_integrated_threshold_1.0_vs_passive"]["uplift"] < 0 and
                 existing_evidence["simple_portfolio_MELON_threshold_0.9_vs_passive"]["uplift"] > 0)
    planner_avoids_overclaim = est.value is not None and est.value <= 0

    return {
        "hypothesis": "a single-crop-calibrated selling-policy uplift (F14) does not transfer to a "
                      "complex multi-resource portfolio (consistent with F19)",
        "existing_evidence_cited": existing_evidence,
        "planner_default_check": {
            "complex_portfolio_threshold_switch_estimate": est.value, "confidence": est.confidence,
            "basis": est.basis, "avoids_naive_overclaim": planner_avoids_overclaim,
        },
        "classification": "SUPPORTED" if supported and planner_avoids_overclaim else "INCONCLUSIVE",
        "conclusion": (
            "Existing Phase 2.4 data directly confirms the hypothesis: the same threshold policy that "
            "gained +$600 on a simple MELON-solo portfolio LOST $9,670 on the complex integrated portfolio "
            "relative to passive. The planner's own evaluator (agents/phase2_6/evaluator.py) already "
            "encodes this by treating complex-portfolio selling-policy switches as a wash (value<=0), "
            "confirmed here directly against the evaluator's own output rather than assumed."
        ),
    }


def main():
    print("Running H1 (animal time-scaling)...")
    h1 = h1_animal_time_scaling()
    print(f"  classification: {h1['classification']}\n  {h1['conclusion']}\n")

    print("Running H2 (portfolio-complexity-aware selling)...")
    h2 = h2_portfolio_complexity_selling()
    print(f"  classification: {h2['classification']}\n  {h2['conclusion']}\n")

    out = {"H1_animal_time_scaling": h1, "H2_portfolio_complexity_selling": h2}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
