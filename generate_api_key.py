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
from pathlib import Path


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
            print("⚠️  Warning: Invalid JSON in API_KEYS environment variable")
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
            print(f"⚠️  Warning: Could not parse API_KEYS from .env file: {e}")
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
        print("📝 No existing API keys found. Creating sample data...")
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
        print("📝 Added new API keys for missing or blank app names...")
    else:
        print("✅ All required API keys already exist and are valid.")

    return api_keys_json


def main():
    """Main function to generate API keys and provide setup instructions."""
    print("🔑 API Key Generator for Prompt Gateway")
    print("=" * 50)

    # Get or create API keys
    api_keys_json = get_or_create_api_keys()

    print("\n✅ Current API Keys:")
    for key_obj in api_keys_json:
        print(f"   {key_obj['appname']}: {key_obj['key']}")

    print("\n📋 Setup Instructions:")
    print("-" * 30)

    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"📁 Found existing .env file: {env_file.absolute()}")
        print("\nUpdate your .env file with this line:")
        print(f"API_KEYS={json.dumps(api_keys_json)}")
    else:
        print(
            "📁 No .env file found. You can create one or use system environment variables."
        )
        print("\nOption 1 - Create .env file:")
        print(f"Create a file named '.env' in {Path.cwd()} with this content:")
        print(f"API_KEYS={json.dumps(api_keys_json)}")

        print("\nOption 2 - Use system environment variable:")
        print("Set this environment variable:")
        print(f"export API_KEYS='{json.dumps(api_keys_json)}'")

    print("\n🔧 Usage:")
    print("-" * 10)
    print(
        "Include any of the tokens in your HTTP requests using the 'Authorization' header:"
    )
    print(f"Authorization: Bearer {api_keys_json[0]['key']}")

    print("\n📝 Example curl command:")
    print("-" * 25)
    print('curl -X POST "http://your-server:5000/query" \\')
    print('  -H "Content-Type: application/json" \\')
    print(f'  -H "Authorization: Bearer {api_keys_json[0]["key"]}" \\')
    print('  -d \'{"query": "Hello, how are you?"}\'')

    print("\n🔒 Security Notes:")
    print("-" * 15)
    print("• Keep your API keys secure and don't share them")
    print("• Use different keys for different applications")
    print("• Rotate keys periodically for better security")
    print("• Never commit API keys to version control")

    print("\n🔄 To add more applications:")
    print("-" * 30)
    print("• Add new objects to the JSON array with unique appnames")
    print("• Each key can be used by a different application")
    print("• Example appnames: DESKTOP, API_CLIENT, BATCH_PROCESSOR")


if __name__ == "__main__":
    main()
