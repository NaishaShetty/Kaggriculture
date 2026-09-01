"""
Phase 3.4 candidate adaptive mechanisms, built AFTER failure forensics on
Variant D's (Phase 3.3) 5 remaining losses out of 15 against
expansion_oriented (results/phase3_4/failure_analysis/).

ROOT CAUSE DIAGNOSED (not assumed), from direct trace/financial-transaction
inspection of the 5 losing episodes vs. the 10 winning ones: every loss
showed nearly IDENTICAL substitute-crop (STRAWBERRY) production volume to
the wins (roughly 96-110 units), but a wildly different average REALIZED
STRAWBERRY sell price ($126-204 in losses vs. $259-279 in wins). This is NOT
an opponent-driven effect -- expansion_oriented (per Phase 3.2/3.3) only
ever grows MELON, never STRAWBERRY -- but a SELF-INFLICTED price crash.
Confirmed mechanistically via `vendor_kaggriculture.kaggriculture.MARKET_PARAMS`:
STRAWBERRY has market depth T=100, the SMALLEST of any of the 5 crops
(WHEAT=400, CARROT=450, TOMATO=200, MELON=300) -- its price is the MOST
sensitive to selling volume of any crop. Variant D's `crop_production_value()`
-based ranking (Phase 2.2's ISOLATED revenue/tile-day calibration) has no
awareness of market depth at all, so it always concentrates 100% of MELON's
freed portfolio share into whichever single crop that isolated calibration
ranks highest -- currently STRAWBERRY -- regardless of how much volume that
market can absorb before the price collapses.

TWO CANDIDATE FIXES WERE DESIGNED AND TESTED AGAINST THIS DIAGNOSIS. BOTH
WERE STAGE-1-SCREENED ON THE FULL 15-SEED expansion_oriented BATTERY AND
BOTH UNDERPERFORMED VARIANT D. See results/phase3_4/candidate_experiments/
for the raw per-seed results this conclusion is based on.
"""
from economic_model.model import crop_production_value

NON_MELON_CANDIDATES = ["WHEAT", "STRAWBERRY", "CARROT", "TOMATO"]


def _redistribute_diversified(crops: dict, top_crops: list):
    if not crops or "MELON" not in crops:
        return dict(crops or {})
    melon_frac = crops["MELON"]
    remaining = {c: f for c, f in crops.items() if c != "MELON"}
    if not top_crops:
        return remaining or {"WHEAT": 1.0}
    share = melon_frac / len(top_crops)
    for c in top_crops:
        remaining[c] = remaining.get(c, 0.0) + share
    return remaining


def candidate_c_diversified_substitution(config, state, detector_result, n_substitutes=2):
    """
    TRIGGER: expansion_oriented detected (same Phase 3.2/3.3 detector, same threshold).
    INTERVENTION: MELON's freed portfolio share is split evenly across the
      TOP `n_substitutes` (default 2) non-MELON crops ranked by
      economic_model.crop_production_value(), instead of Variant D's 100%-
      into-the-single-best-crop allocation.
    MECHANISM: reduces per-crop selling VOLUME into any one market, directly
      addressing the diagnosed self-inflicted-price-crash failure mode
      (STRAWBERRY's T=100 market depth is the smallest of any crop) without
      changing total freed capacity or inventing a new valuation model.
    EXPECTED BENEFIT: should reduce the variance/downside of Variant D's
      remaining losses (each substitute crop sees roughly half the selling
      pressure it would under D alone).
    EXPECTED DOWNSIDE: if the #2-ranked crop is meaningfully worse than #1,
      diversifying could reduce mean revenue even if it reduces variance.
    EVIDENCE (results/phase3_4/candidate_experiments/candidate_c_full15.json):
      REJECTED. 0/15 wins vs Variant D's 10/15 on the identical 15-seed
      battery. Root cause: economic_model.crop_production_value() ranks
      TOMATO (the #2 non-MELON crop) at roughly 1421 vs STRAWBERRY's ~6718 --
      a ~4.7x intrinsic-value gap -- so halving allocation into a crop worth
      ~1/5 as much per unit costs far more in foregone revenue than the
      reduced price-impact variance recovers. Diversification only helps
      when the substitutes are comparably valuable; here they are not.
    """
    if not detector_result["active"]:
        return config
    ranked = []
    for candidate in NON_MELON_CANDIDATES:
        est = crop_production_value(candidate, state, n_tiles=10)
        if est.value is not None:
            ranked.append((candidate, est.value))
    ranked.sort(key=lambda x: -x[1])
    top_crops = [c for c, _ in ranked[:n_substitutes]]
    new_config = dict(config)
    new_config["crops"] = _redistribute_diversified(config.get("crops") or {}, top_crops)
    return new_config


def candidate_e_partial_melon_retention(config, state, detector_result, melon_frac=0.5):
    """
    TRIGGER: expansion_oriented detected (same detector/threshold as Variant D).
    INTERVENTION: instead of fully vacating MELON (Variant D redirects 100%
      of MELON's portfolio share to the best-ranked substitute), retain a
      fixed `melon_frac` (default 0.5) of MELON and send the rest to
      STRAWBERRY -- a hard-coded 50/50 MELON+STRAWBERRY split, not a
      model-derived allocation.
    MECHANISM (HYPOTHESIS, not validated a priori): reduces STRAWBERRY
      selling volume (addressing the diagnosed price-crash risk) by
      producing less of it in the first place, rather than by diversifying
      into a weaker crop. Side effect noted during testing: continued MELON
      production/selling by the protagonist ALSO further depresses the
      shared MELON market, which measurably reduced the opponent's own
      final money too (observed opponent final money ~$16,659-17,274 under
      this candidate vs. ~$21,894-22,340 for Variant D on the same 5 seeds)
      -- a real market-interaction side effect, not by design.
    EVIDENCE (results/phase3_4/candidate_experiments/candidate_e_full15.json):
      REJECTED. Tested first on the 5 known Variant-D-losing seeds (1/5 wins,
      seed 702001 only) then on the full 15-seed battery. Overall win rate
      did not exceed Variant D's 10/15, and on the 10 seeds Variant D already
      wins, partial MELON retention reintroduces MELON oversupply exposure
      Variant D had already eliminated -- net effect: no improvement over
      Variant D, confirmed on the full battery, not just the losing subset.
    """
    if not detector_result["active"]:
        return config
    new_config = dict(config)
    new_config["crops"] = {"MELON": melon_frac, "STRAWBERRY": 1.0 - melon_frac}
    return new_config


CANDIDATES = {
    "C_diversified_substitution": candidate_c_diversified_substitution,
    "E_partial_melon_retention": candidate_e_partial_melon_retention,
}
