# File: gen_app/config.py
"""
Configuration management for the project generator.

Loads configuration from a JSON file with sensible defaults.
"""

import json
import os

DEFAULT_CONFIG_PATH = "~/.gen_app/config.json"
DEFAULT_CONFIG = {
    # "default_model": "mistral-nemo:12b-instruct-2407-q8_0",
    "default_model": "qwq",
    "max_concurrency": 5,
    "templates_dir": "~/.gen_app/templates",
    "format_code": True,
    "setup_virtualenv": False,
    "auto_install_tools": False,
    "retry_attempts": 3,
    "backoff_factor": 1.5,
}


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """
    Load configuration from file.

    Parameters
    ----------
    config_path : str, optional
        Path to the configuration file, defaults to "~/.gen_app/config.json"

    Returns
    -------
    dict
        Configuration dictionary with defaults merged with user settings.
    """
    config_path = os.path.expanduser(config_path)
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
            config.update(user_config)
        except Exception:
            pass
    return config
