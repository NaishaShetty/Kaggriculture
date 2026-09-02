"""
Phase 4 opponent trajectory model.

Extends (does not replace) the existing, frozen
agents.phase3.opponent_observation.OpponentObservationLogger -- reuses it
for the raw per-turn snapshot collection (unchanged), and adds VELOCITY
tracking (this phase's actual new contribution) on top: bank, animals,
hands, and land, each sampled at a STABLE daily checkpoint to avoid the
documented daily hands-reset artifact (same discipline as
agents.phase3_5.opponent_scaling_detector).

HONEST SCOPE NOTE: full second-order acceleration modeling (as sketched in
the Phase 4 brief) was simplified to first-order velocity (change per day
over a trailing window) plus a simple accelerating/plateaued/declining
flag -- a true second-derivative estimate from noisy, sparse daily
observations would not be reliably distinguishable from noise with only a
handful of data points per game, and a false precision here would violate
this project's own standing discipline against overclaiming. This is
EMPIRICAL FINDING-grounded (Phase 3.7's real-data animal/hands separation),
not HYPOTHESIS.

Regimes are a DESCRIPTIVE CONVENIENCE for tracing/debugging, not a
prediction target in themselves -- consistent with the brief's own
"classification is not the final objective" instruction.
"""
from dataclasses import dataclass, field

MIN_SAMPLE_HOUR = 18  # matches agents.phase3_5.opponent_scaling_detector's own discipline
VELOCITY_WINDOW_DAYS = 5


@dataclass
class OpponentSnapshot:
    day: int
    bank: float
    hands: int
    animals: int
    land: int
    crop_tiles: int


@dataclass
class OpponentTrajectory:
    daily_snapshots: list = field(default_factory=list)  # OpponentSnapshot, one per day (stable sample)

    def observe(self, history):
        """`history`: agents.phase3.opponent_observation.OpponentObservationLogger.history.
        Rebuilds the stable daily-sample list from the full per-turn history
        (cheap at this project's episode lengths -- 720 turns)."""
        by_day = {}
        for snap in history:
            if snap.hour >= MIN_SAMPLE_HOUR or snap.day not in by_day:
                by_day[snap.day] = snap
        self.daily_snapshots = [
            OpponentSnapshot(
                day=d, bank=s.visible_money, hands=len(s.visible_hand_positions),
                animals=sum(s.visible_animal_tile_counts.values()),
                land=s.visible_land_quadrants,
                crop_tiles=sum(s.visible_crop_tile_counts.values()),
            )
            for d, s in sorted(by_day.items())
        ]

    def _velocity(self, attr, window_days=VELOCITY_WINDOW_DAYS):
        if len(self.daily_snapshots) < 2:
            return 0.0
        recent = self.daily_snapshots[-1]
        window_start_day = max(0, recent.day - window_days)
        earlier = next((s for s in self.daily_snapshots if s.day >= window_start_day), self.daily_snapshots[0])
        days_elapsed = max(1, recent.day - earlier.day)
        return (getattr(recent, attr) - getattr(earlier, attr)) / days_elapsed

    def bank_velocity(self):
        return self._velocity("bank")

    def animal_velocity(self):
        return self._velocity("animals")

    def hands_velocity(self):
        return self._velocity("hands")

    def land_velocity(self):
        return self._velocity("land")

    def is_accelerating(self, attr, window_days=VELOCITY_WINDOW_DAYS):
        """Simple, honest proxy for 'still growing': compares the most
        recent window's velocity to the PRIOR window's velocity. Returns
        True only if there is enough history (>= 2 full windows) AND the
        recent window's growth rate is clearly higher (not noise-level)."""
        if len(self.daily_snapshots) < window_days * 2:
            return False
        recent = self.daily_snapshots[-1]
        mid = next((s for s in self.daily_snapshots if s.day >= recent.day - window_days), None)
        early = next((s for s in self.daily_snapshots if s.day >= recent.day - 2 * window_days), None)
        if mid is None or early is None:
            return False
        recent_v = (getattr(recent, attr) - getattr(mid, attr)) / max(1, recent.day - mid.day)
        prior_v = (getattr(mid, attr) - getattr(early, attr)) / max(1, mid.day - early.day)
        return recent_v > prior_v + 0.5  # +0.5/day margin -- avoid flagging noise as acceleration

    def latest(self):
        return self.daily_snapshots[-1] if self.daily_snapshots else None

    def classify_regime(self):
        """DESCRIPTIVE, not predictive -- see module docstring. Thresholds
        for animals reuse Phase 3.7's validated real-data finding
        (loss cluster >=8, win cluster <=6); hands/land thresholds are
        round-number extensions of the same logic, not independently
        validated to the same degree -- labeled HYPOTHESIS in the trace."""
        latest = self.latest()
        if latest is None:
            return "UNKNOWN", "insufficient_history"
        if latest.animals >= 8:
            return "ANIMAL_HEAVY", "EMPIRICAL_FINDING (Phase 3.7 real-data animal threshold)"
        if latest.hands >= 8 and latest.animals < 4:
            return "LABOR_HEAVY", "HYPOTHESIS (round-number extension of the animal threshold)"
        if latest.land >= 3 and latest.animals < 4 and latest.hands < 6:
            return "CAPITAL_ACCUMULATOR", "HYPOTHESIS (Phase 3.7-D found land alone is not independently causal)"
        if latest.crop_tiles >= 15 and latest.animals < 4 and latest.hands < 4:
            return "PRODUCTION_HEAVY", "HYPOTHESIS"
        if latest.hands <= 2 and latest.animals <= 2 and latest.land <= 1:
            return "BALANCED", "HYPOTHESIS (low-footprint default)"
        return "UNKNOWN", "does not match any established pattern"
