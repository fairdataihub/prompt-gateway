"""Configuration for the application.

This module handles environment variable configuration for the application.
It supports loading configuration from both a local .env file and system environment variables.
"""

import json
import logging
from os import environ
from pathlib import Path
from dotenv import dotenv_values

# Check if `.env` file exists in the current directory
# This allows the app to work with or without a .env file
env_path = Path(".") / ".env"

# Flag to indicate whether a local .env file is present
LOCAL_ENV_FILE = env_path.exists()

# Load environment variables from .env file if it exists
# dotenv_values() returns a dictionary of key-value pairs from the .env file
# If .env doesn't exist, this will be an empty dictionary
config = dotenv_values(".env")


def get_env(key):
    """Return environment variable from .env or native environment.

    This function provides a unified way to access environment variables.
    It first checks the local .env file (if it exists), then falls back
    to system environment variables.

    Args:
        key (str): The environment variable key to retrieve

    Returns:
        str or None: The value of the environment variable, or None if not found
    """
    # If .env file exists, try to get value from it first
    # Otherwise, get value directly from system environment
    return config.get(key) if LOCAL_ENV_FILE else environ.get(key)


def get_api_keys():
    """Get all API keys from environment variables.

    This function expects a single environment variable 'API_KEYS' containing
    a JSON array of objects with 'appname' and 'key' properties.

    Returns:
        dict: Dictionary of API key names to their values
    """
    api_keys = {}

    # Get all environment variables
    env_vars = config if LOCAL_ENV_FILE else environ

    # Get API keys from JSON format
    api_keys_json = env_vars.get("API_KEYS")
    if api_keys_json:
        try:
            # Parse the JSON array of objects
            keys_array = json.loads(api_keys_json)
            if isinstance(keys_array, list):
                for key_obj in keys_array:
                    if (
                        isinstance(key_obj, dict)
                        and "appname" in key_obj
                        and "key" in key_obj
                    ):
                        api_keys[key_obj["appname"]] = key_obj["key"]
        except (json.JSONDecodeError, TypeError) as e:
            # Log the error
            logging.error("Could not parse API_KEYS JSON: %s", e)

    return api_keys


def validate_api_key(api_key):
    """Validate an API key against the configured keys.

    Args:
        api_key (str): The API key to validate

    Returns:
        bool: True if the API key is valid, False otherwise
    """
    if not api_key:
        return False

    valid_keys = get_api_keys()
    return api_key in valid_keys.values()
