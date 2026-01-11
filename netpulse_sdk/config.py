"""
Configuration file support for NetPulse SDK

Supports:
- netpulse.yaml in current directory
- ~/.netpulse/config.yaml
- Environment variable substitution (${VAR_NAME})
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import logging

log = logging.getLogger(__name__)

# Default config file locations (in order of priority)
CONFIG_PATHS = [
    Path("netpulse.yaml"),
    Path("netpulse.yml"),
    Path.home() / ".netpulse" / "config.yaml",
    Path.home() / ".netpulse" / "config.yml",
]


def _substitute_env_vars(value: Any) -> Any:
    """Substitute ${VAR_NAME} with environment variable values"""
    if isinstance(value, str):
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, value)
        for var_name in matches:
            env_value = os.environ.get(var_name, "")
            value = value.replace(f"${{{var_name}}}", env_value)
        return value
    elif isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


def load_config(
    config_path: Optional[str] = None,
    profile: Optional[str] = None,
) -> Dict[str, Any]:
    """Load configuration from YAML file

    Args:
        config_path: Explicit config file path (optional)
        profile: Profile name to use (optional, defaults to 'default')

    Returns:
        Configuration dictionary with keys:
            - base_url: API base URL
            - api_key: API key
            - driver: Default driver
            - connection_args: Default connection arguments
            - timeout: HTTP timeout
            - pool_connections: Connection pool size
            - pool_maxsize: Max connections per pool
            - max_retries: Retry count
    """
    try:
        import yaml
    except ImportError:
        log.debug("PyYAML not installed, config file support disabled")
        return {}

    # Find config file
    config_file = None
    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            log.warning(f"Config file not found: {config_path}")
            return {}
    else:
        for path in CONFIG_PATHS:
            if path.exists():
                config_file = path
                break

    if not config_file:
        log.debug("No config file found")
        return {}

    log.debug(f"Loading config from: {config_file}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f) or {}
    except Exception as e:
        log.warning(f"Failed to load config file: {e}")
        return {}

    # Get profile config
    profile_name = profile or "default"

    # Merge default + profile
    config = {}

    # First load 'default' profile
    if "default" in raw_config:
        config.update(raw_config["default"])

    # Then overlay specific profile if different from default
    if profile_name != "default" and "profiles" in raw_config:
        if profile_name in raw_config["profiles"]:
            profile_config = raw_config["profiles"][profile_name]
            # Deep merge connection_args
            if "connection_args" in profile_config and "connection_args" in config:
                config["connection_args"].update(profile_config.pop("connection_args", {}))
            config.update(profile_config)
        else:
            log.warning(f"Profile '{profile_name}' not found in config")

    # Substitute environment variables
    config = _substitute_env_vars(config)

    return config


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a value from config with environment variable fallback"""
    value = config.get(key)
    if value is None or value == "":
        return default
    return value
