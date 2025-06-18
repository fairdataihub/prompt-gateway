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


def main():
    """Main function to generate API keys and provide setup instructions."""
    print("🔑 API Key Generator for Prompt Gateway")
    print("=" * 50)

    # Generate API keys for different applications
    api_keys_json = [
        {"appname": "APP1", "key": generate_api_key()},
        {"appname": "WEBAPP", "key": generate_api_key()},
        {"appname": "MOBILE", "key": generate_api_key()},
    ]

    print("\n✅ Generated API Keys:")
    for key_obj in api_keys_json:
        print(f"   {key_obj['appname']}: {key_obj['key']}")

    print("\n📋 Setup Instructions:")
    print("-" * 30)

    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"📁 Found existing .env file: {env_file.absolute()}")
        print("\nAdd this line to your .env file:")
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
