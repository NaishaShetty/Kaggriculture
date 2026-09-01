"""
Telemetry schema version and static classification tables.

Increment TELEMETRY_SCHEMA_VERSION on any change to the shape/meaning of
emitted records; never silently reinterpret older telemetry under a new
version. See docs/PHASE2_1_TELEMETRY_SCHEMA.md for the full field-by-field
documentation (raw/derived/public/private/diagnostic classification).
"""

TELEMETRY_SCHEMA_VERSION = "2.3.0"

# ---------------------------------------------------------------------------
# Action classification (brief section 8)
# ---------------------------------------------------------------------------
MOVEMENT_OPS = {"NORTH", "SOUTH", "EAST", "WEST"}
CROP_OPS = {"PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG"}
ANIMAL_OPS = {"FEED", "CARE", "PLACE", "COLLECT_FERTILIZER"}  # HARVEST shared with crop ops, resolved by target
FARM_OPS = {"BUILD_COOP", "BUILD_PASTURE", "PICKUP", "DROP"}
IDLE_OPS = {"PASS"}
# unit-op HARVEST is ambiguous (crop vs animal) until resolved against the tile it targeted.

MARKET_OPS = {"BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "SELL"}
ECONOMY_OPS = {"HIRE", "BUY_LAND"}  # also submitted via the market order queue

ALL_UNIT_OPS = MOVEMENT_OPS | CROP_OPS | ANIMAL_OPS | FARM_OPS | IDLE_OPS


def classify_unit_op(op, tile_before=None):
    """Classify a single farmer/hand op. HARVEST is disambiguated using the
    tile the unit stood on before acting, when available."""
    if op in MOVEMENT_OPS:
        return "MOVEMENT"
    if op == "HARVEST":
        if isinstance(tile_before, dict) and "animal" in tile_before:
            return "ANIMAL"
        return "CROP"
    if op in CROP_OPS:
        return "CROP"
    if op in ANIMAL_OPS:
        return "ANIMAL"
    if op in FARM_OPS:
        return "FARM"
    if op in IDLE_OPS:
        return "IDLE"
    return "UNKNOWN"


def classify_market_op(op):
    if op in ECONOMY_OPS:
        return "ECONOMY"
    if op in MARKET_OPS:
        return "MARKET"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Info-boundary policy (brief section 19 / 7)
# ---------------------------------------------------------------------------
# Fields inside a player's own `observation` payload that are PUBLIC (visible
# to both agents in the live game, since obs.farms/market/town/day/hour are
# the same shared object handed to every player -- confirmed by reading
# vendor_kaggriculture/kaggriculture.py `interpreter()`/`_initialize()`).
PUBLIC_OBSERVATION_KEYS = {"farms", "market", "town", "day", "hour", "step"}

# Fields that are PRIVATE to the player who received them -- never copied into
# an opponent-telemetry record, never used to inform a decision boundary.
PRIVATE_OBSERVATION_KEYS = {"private"}  # shed, seeds, per-unit carried inventories
