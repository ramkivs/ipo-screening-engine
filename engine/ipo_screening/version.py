"""Version stamps for the IPO Screening Engine.

The engine version is part of the determinism contract: the same inputs,
source snapshots, configuration and engine version must produce the same
result hash (spec v1.5 s3.1, s27).
"""

from __future__ import annotations

ENGINE_VERSION = "1.5.0"
SPEC_VERSION = "1.5"
#: Version of the executable policy in config/ipo-config.v1.5.0.json
DEFAULT_CONFIG_VERSION = "1.5.0"
DEFAULT_CONFIG_PATH = "config/ipo-config.v1.5.0.json"
DEFAULT_SCHEMA_PATH = "schema/ipo-input.v1.5.schema.json"

__all__ = [
    "ENGINE_VERSION",
    "SPEC_VERSION",
    "DEFAULT_CONFIG_VERSION",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_SCHEMA_PATH",
]
