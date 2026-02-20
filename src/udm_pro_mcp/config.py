"""Configuration loading and validation."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import ConfigError
from .models import UDMConfig

DEFAULT_CONFIG_DIR = Path.home() / ".udm-pro-mcp"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


def get_config_path() -> Path:
    """Return the config file path, respecting UDM_MCP_CONFIG env var."""
    env_path = os.environ.get("UDM_MCP_CONFIG")
    if env_path:
        return Path(env_path)
    return DEFAULT_CONFIG_FILE


def load_config() -> UDMConfig:
    """Load and validate configuration from disk."""
    path = get_config_path()

    if not path.exists():
        raise ConfigError(
            f"Config file not found at {path}. "
            f"Create it with your UDM Pro credentials or set UDM_MCP_CONFIG."
        )

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc

    try:
        return UDMConfig(**raw)
    except Exception as exc:
        raise ConfigError(f"Invalid config in {path}: {exc}") from exc
