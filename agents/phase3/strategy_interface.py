"""
Phase 3.1 strategy-switching interface -- a STUB/control interface per the
brief section 19. Supports the architectural SHAPE future strategy
switching needs (no-switch / one-switch / multiple-switches / forced /
adaptive), but every mode in Phase 3.1 either does nothing (NO_SWITCH) or
applies a single pre-declared forced configuration (FORCED) -- no adaptive
decision-making. Real adaptive selection is explicitly Phase 3.2+ scope.
"""
from dataclasses import dataclass
from enum import Enum


class SwitchMode(Enum):
    NO_SWITCH = "no_switch"          # always keep the planner's own chosen config (Phase 2.6 behavior, unmodified)
    FORCED = "forced"                 # apply one pre-declared config regardless of state (for controlled A/B tests)
    ADAPTIVE_STUB = "adaptive_stub"    # interface present, but returns NO_SWITCH every time in Phase 3.1


@dataclass
class StrategyDecision:
    mode: SwitchMode
    switched: bool
    new_config_override: dict = None
    reason: str = ""


class StrategySelector:
    """The future strategy selector's STABLE INTERFACE. `select()` is called
    once per planning cycle, after the Economic Planner has already produced
    its own `new_config` -- this class may OVERRIDE it (FORCED mode only, for
    controlled experiments) or pass it through unchanged (every other mode).
    No mode in Phase 3.1 makes an adaptive decision based on competitive_state."""

    def __init__(self, mode: SwitchMode = SwitchMode.NO_SWITCH, forced_config: dict = None):
        self.mode = mode
        self.forced_config = forced_config
        self.switch_count = 0

    def select(self, planner_proposed_config, competitive_state) -> StrategyDecision:
        if self.mode == SwitchMode.FORCED and self.forced_config is not None:
            self.switch_count += 1
            return StrategyDecision(mode=self.mode, switched=True, new_config_override=dict(self.forced_config),
                                     reason="FORCED mode: pre-declared config applied regardless of state "
                                            "(controlled-experiment use only)")
        # NO_SWITCH and ADAPTIVE_STUB both defer entirely to the planner's own decision in Phase 3.1.
        return StrategyDecision(mode=self.mode, switched=False, new_config_override=None,
                                 reason="Phase 3.1: no adaptive strategy selection implemented -- "
                                        "planner's own config passes through unchanged")
