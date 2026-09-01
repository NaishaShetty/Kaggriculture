"""
Kaggriculture Phase 2.1 — Economic Instrumentation & Telemetry.

Entirely external / read-only with respect to the frozen simulator and frozen
baseline agent. Nothing in this package imports agents/baseline_agent.py or
mutates vendor_kaggriculture/kaggriculture.py. Game-rule constants (CROPS,
ANIMALS, market pricing formula, etc.) are imported read-only from the vendored
module as the single source of truth.

See docs/PHASE2_1_ARCHITECTURE.md and docs/PHASE2_1_TELEMETRY_SCHEMA.md.
"""
from .schema import TELEMETRY_SCHEMA_VERSION

__all__ = ["TELEMETRY_SCHEMA_VERSION"]
