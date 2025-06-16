"""
config_loader.py

Handles importing and validating configuration for the Pi-hole control panel.

- Raises an error if a required config value is missing.
- Sets default values for optional config values if not provided.
- Retains provided values from config.py.
"""

import importlib

REQUIRED_CONFIG = [
    "PIHOLE_INSTANCES",
    "FLASK_SECRET_KEY"
]
OPTIONAL_CONFIG_DEFAULTS = {
    "BLOCKING_DISABLE_DURATION": None,
    "BLOCKING_ENABLE_DURATION": None
}

def load_config():
    """
    Import and validate configuration from config.py.

    This function:
        - Imports the config.py module.
        - Ensures all required configuration values are present and not empty.
        - Sets optional configuration values to their default if missing.
        - Returns a dictionary with all validated and finalized config values.

    Raises:
        RuntimeError: If config.py is missing or a required config value is absent.

    Returns:
        dict: Dictionary of configuration values ready for use in the app.
    """
    try:
        config = importlib.import_module("config")
    except ImportError as err:
        raise RuntimeError(
            "Could not import config.py. Please create one as described in the README."
        ) from err

    # Validate required config values
    for key in REQUIRED_CONFIG:
        if not hasattr(config, key) or getattr(config, key) in (None, '', {}):
            raise RuntimeError(f"Missing required config value '{key}' in config.py")

    # Gather all config values
    loaded_config = {key: getattr(config, key) for key in REQUIRED_CONFIG}
    for key, default in OPTIONAL_CONFIG_DEFAULTS.items():
        loaded_config[key] = getattr(config, key, default)
    return loaded_config
