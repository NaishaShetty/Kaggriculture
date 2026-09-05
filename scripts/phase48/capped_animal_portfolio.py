"""
Phase 48 Part C, step 8: a capacity-aware wrapper around
agents/phase21/portfolio.py::portfolio_targets (imported unmodified, per the
Phase 42/45 composition pattern) that caps the ANIMAL target at a realistic
sustainable ceiling instead of letting it escalate to _ANIMAL_SPECIES_RUNGS's
own final rung (17 by day 11) -- grounded directly in this phase's own
steady-state measurement (scripts/phase48/animal_ceiling_probe.py), which
found owned-animal count actually EQUILIBRATES around 7-9 (mean steady-state
8.00 isolated / 7.18 vs. Submission G, days 20-29) regardless of the 17
target, because purchases and chronic feed-related escapes roughly balance
out well below the target rung.

Only the "animals" field of portfolio_targets' own output is touched here;
everything else (land, hands, crop_tile_target, crop_fractions) passes
through byte-for-byte unchanged, matching the Phase 45 Part B / Phase 42
"wrap portfolio_targets, don't modify it" convention exactly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.phase21.portfolio import portfolio_targets  # noqa: E402


def make_capped_animal_target_fn(cap_total=8, base_target_fn=portfolio_targets):
    """Caps the TOTAL animal count in `targets["animals"]` at `cap_total`,
    proportionally shrinking each species' rung value to preserve the
    existing COW:SHEEP ratio (rather than hard-capping one species to zero
    while leaving the other at its rung value)."""

    def target_fn(day, obs, opponent_history=None):
        targets = base_target_fn(day, obs, opponent_history)
        animals = dict(targets["animals"])
        total = sum(animals.values())
        if total > cap_total and total > 0:
            scale = cap_total / total
            scaled = {k: int(v * scale) for k, v in animals.items()}
            # Distribute any rounding-down remainder to the largest species
            # first (deterministic, avoids ever exceeding cap_total).
            remainder = cap_total - sum(scaled.values())
            if remainder > 0:
                for k in sorted(animals, key=lambda k: -animals[k]):
                    if remainder <= 0:
                        break
                    scaled[k] += 1
                    remainder -= 1
            animals = scaled
        targets = dict(targets)
        targets["animals"] = animals
        return targets

    return target_fn
