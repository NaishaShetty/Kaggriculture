"""
Phase 2.5 stress-test agent: identical to agents/phase2_4/common.py (imported,
not duplicated) except the sell policy is wrapped with a horizon-safety
override sourced directly from economic_model.model.terminal_liquidation_deadline
-- a concrete test of whether the Economic Model v0.1's F16 formalization
("Latest Safe Sell Day") actually prevents the batch-stranding collapse it
was built to explain, not just describe after the fact.

`sell_policy["horizon_aware"] = True` adds exactly one rule on top of
whatever `mode` is chosen: once `day >= terminal_liquidation_deadline(...)`
under that mode's own parameters, sell EVERYTHING regardless of the mode's
normal trigger condition. This is the model's own liquidation-deadline
concept, wired into an actual agent decision, not a new invented mechanic.
"""
from agents.phase2_4.common import make_agent as make_agent_24, _sell_quantity as _sell_quantity_24
from economic_model.model import terminal_liquidation_deadline


def _sell_quantity_horizon_aware(item, held, price, day, policy, turn=None):
    base_qty = _sell_quantity_24(item, held, price, day, policy, turn=turn)
    if policy.get("horizon_aware") and held > 0:
        mode = policy.get("mode", "passive")
        deadline_info = terminal_liquidation_deadline(
            item, _FakeState(day), mode, batch_interval_days=policy.get("batch_interval_days"))
        if day >= deadline_info["latest_safe_sell_day"]:
            return held  # force full liquidation past the model's own safe-sell deadline
    return base_qty


class _FakeState:
    """terminal_liquidation_deadline only reads TOTAL_DAYS-relative day math
    from the state object in this codepath -- a minimal shim, not a real
    EconomicState, to avoid threading full farm state through the agent
    just for this one deadline lookup."""
    def __init__(self, day):
        self.day = day


def make_agent(**kwargs):
    """Same signature as agents/phase2_4/common.py::make_agent. `agent(obs)`
    (built once by make_agent_24) looks up `_sell_quantity` in
    agents.phase2_4.common's module namespace DYNAMICALLY, at each call --
    so the patch must be live at CALL time, not just at construction time
    (an earlier version of this wrapper patched only around the
    make_agent_24(**kwargs) call itself, which only builds the closure and
    never invokes it -- a real bug, caught before this was used in any
    experiment: the patch was already reverted by the time the simulator
    actually called agent(obs)). Fixed by patching/restoring on every turn,
    inside the returned wrapper itself."""
    import agents.phase2_4.common as p24
    agent_inner = make_agent_24(**kwargs)
    original = p24._sell_quantity

    def agent(obs):
        p24._sell_quantity = _sell_quantity_horizon_aware
        try:
            return agent_inner(obs)
        finally:
            p24._sell_quantity = original

    return agent
