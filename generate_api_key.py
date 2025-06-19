#!/usr/bin/env python3
"""
API Key Generator Utility

This script helps generate secure API keys for the prompt-gateway application.
It generates cryptographically secure random keys and provides instructions
for setting them up as environment variables using JSON format.
"""

import secrets
import string
import json
import os
import logging
from pathlib import Path

# Configure basic logging for the script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def generate_api_key(length=32):
    """Generate a secure API key.

    Args:
        length (int): Length of the API key (default: 32)

    Returns:
        str: A secure random API key
    """
    # Use a combination of letters, digits, and symbols for security
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def load_existing_api_keys():
    """Load existing API keys from environment or .env file.

    Returns:
        list: List of existing API key dictionaries, or empty list if none found
    """
    # Try to get API keys from environment variable
    api_keys_env = os.getenv("API_KEYS")
    if api_keys_env:
        try:
            return json.loads(api_keys_env)
        except json.JSONDecodeError:
            logging.warning("Invalid JSON in API_KEYS environment variable")
            return []

    # Try to get API keys from .env file
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("API_KEYS="):
                        api_keys_str = line.split("=", 1)[1].strip()
                        # Remove quotes if present
                        if api_keys_str.startswith('"') and api_keys_str.endswith('"'):
                            api_keys_str = api_keys_str[1:-1]
                        elif api_keys_str.startswith("'") and api_keys_str.endswith(
                            "'"
                        ):
                            api_keys_str = api_keys_str[1:-1]
                        return json.loads(api_keys_str)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.warning("Could not parse API_KEYS from .env file: %s", e)
            return []

    return []


def get_or_create_api_keys():
    """Get existing API keys or create new ones if none exist.

    Returns:
        list: List of API key dictionaries
    """
    existing_keys = load_existing_api_keys()

    # Define default app names to ensure we have keys for
    default_apps = ["APP1", "WEBAPP", "MOBILE"]

    # Create a dictionary of existing keys for easy lookup
    existing_keys_dict = {
        key_obj["appname"]: key_obj["key"] for key_obj in existing_keys
    }

    # If no existing keys, create sample data
    if not existing_keys:
        logging.info("📝 No existing API keys found. Creating sample data...")
        api_keys_json = [
            {"appname": app, "key": generate_api_key()} for app in default_apps
        ]
        return api_keys_json

    # Preserve existing keys and add new ones for missing apps
    api_keys_json = []
    added_new_keys = False

    for app in default_apps:
        if app in existing_keys_dict and existing_keys_dict[app].strip():
            # Keep existing key
            api_keys_json.append({"appname": app, "key": existing_keys_dict[app]})
        else:
            # Add new key for missing or blank app
            api_keys_json.append({"appname": app, "key": generate_api_key()})
            added_new_keys = True

    # Add any additional existing keys that aren't in default apps
    for key_obj in existing_keys:
        if key_obj["appname"] not in default_apps:
            api_keys_json.append(key_obj)

    if added_new_keys:
        logging.info("📝 Added new API keys for missing or blank app names...")
    else:
        logging.info("✅ All required API keys already exist and are valid.")

    return api_keys_json


def main():
    """Main function to generate API keys and provide setup instructions."""
    logging.info("🔑 API Key Generator for Prompt Gateway")
    logging.info("=" * 50)

    # Get or create API keys
    api_keys_json = get_or_create_api_keys()

    logging.info("\n✅ Current API Keys:")
    for key_obj in api_keys_json:
        logging.info("   %s: %s", key_obj["appname"], key_obj["key"])

    logging.info("\n📋 Setup Instructions:")
    logging.info("-" * 30)

    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        logging.info("📁 Found existing .env file: %s", env_file.absolute())
        logging.info("\nUpdate your .env file with this line:")
        logging.info("API_KEYS=%s", json.dumps(api_keys_json))
    else:
        logging.info(
            "📁 No .env file found. You can create one or use system environment variables."
        )
        logging.info("\nOption 1 - Create .env file:")
        logging.info("Create a file named '.env' in %s with this content:", Path.cwd())
        logging.info("API_KEYS=%s", json.dumps(api_keys_json))

        logging.info("\nOption 2 - Use system environment variable:")
        logging.info("Set this environment variable:")
        logging.info("export API_KEYS='%s'", json.dumps(api_keys_json))

    logging.info("\n🔧 Usage:")
    logging.info("-" * 10)
    logging.info(
        "Include any of the tokens in your HTTP requests using the 'Authorization' header:"
    )
    logging.info("Authorization: Bearer %s", api_keys_json[0]["key"])

    logging.info("\n📝 Example curl command:")
    logging.info("-" * 25)
    logging.info('curl -X POST "http://your-server:5000/query" \\')
    logging.info('  -H "Content-Type: application/json" \\')
    logging.info('  -H "Authorization: Bearer %s" \\', api_keys_json[0]["key"])
    logging.info('  -d \'{"query": "Hello, how are you?"}\'')

    logging.info("\n🔒 Security Notes:")
    logging.info("-" * 15)
    logging.info("• Keep your API keys secure and don't share them")
    logging.info("• Use different keys for different applications")
    logging.info("• Rotate keys periodically for better security")
    logging.info("• Never commit API keys to version control")

    logging.info("\n🔄 To add more applications:")
    logging.info("-" * 30)
    logging.info("• Add new objects to the JSON array with unique appnames")
    logging.info("• Each key can be used by a different application")
    logging.info("• Example appnames: DESKTOP, API_CLIENT, BATCH_PROCESSOR")


if __name__ == "__main__":
    main()
