"""
Phase 4 final-bank forecast.

HONEST SCOPE NOTE: this is a deliberately SIMPLE, interpretable linear
extrapolation, not a full production-simulation model. A rigorous
"remaining crop yields + future animal production + feed costs" forecast
for OUR OWN farm is achievable in principle (we have full private state),
but a comparably rigorous forecast for the OPPONENT is NOT, because their
crop ages, feed schedule, and inventory are private/unobservable -- only
their bank trajectory and visible footprint are legitimate signals. Rather
than build an asymmetric model (precise for us, invented for them) that
would silently violate the project's own "do not use hidden state" rule,
this module uses the SAME simple method (recent velocity x remaining
days) for both sides, explicitly labeled as a coarse proxy with
uncertainty, not a claim of precision.
"""
from dataclasses import dataclass

TOTAL_DAYS = 30


@dataclass
class BankForecast:
    projected_bank: float
    uncertainty: float  # +/- range, a coarse heuristic (see below), not a statistical CI
    basis: str


def forecast_self(current_cash, cash_velocity_recent, remaining_days):
    """OUR OWN forecast can additionally use the fact that we KNOW our own
    committed portfolio (crops/animals) and can defer to
    economic_model.crop_production_value / animal_production_value for a
    more grounded remaining-yield estimate where available -- callers
    should prefer that when a concrete portfolio is known. This function
    is the FALLBACK / general-purpose path (also used for the opponent)."""
    projected = current_cash + cash_velocity_recent * remaining_days
    uncertainty = abs(cash_velocity_recent) * remaining_days * 0.5  # coarse: half the extrapolated delta
    return BankForecast(projected_bank=projected, uncertainty=uncertainty,
                         basis="linear extrapolation of recent bank velocity -- HYPOTHESIS-level precision")


def forecast_opponent(current_bank, bank_velocity_recent, remaining_days, regime_confidence="HYPOTHESIS"):
    """Same method as forecast_self -- deliberately, per the module
    docstring. `regime_confidence` is carried through only for tracing,
    not used to adjust the number itself (adjusting the forecast based on
    an unvalidated regime label would manufacture false precision)."""
    projected = current_bank + bank_velocity_recent * remaining_days
    uncertainty = abs(bank_velocity_recent) * remaining_days * 0.5
    return BankForecast(projected_bank=projected, uncertainty=uncertainty,
                         basis=f"linear extrapolation of observed bank velocity ({regime_confidence})")


def projected_gap(self_forecast: BankForecast, opponent_forecast: BankForecast):
    """Returns (gap, combined_uncertainty). gap > 0 means we are projected
    ahead. Combined uncertainty is the simple sum of both sides' coarse
    ranges -- not a rigorous propagation, deliberately conservative
    (wider) rather than falsely precise."""
    gap = self_forecast.projected_bank - opponent_forecast.projected_bank
    combined_uncertainty = self_forecast.uncertainty + opponent_forecast.uncertainty
    return gap, combined_uncertainty
