#!/usr/bin/env python3
"""
Startup check script for Ollama availability in Docker container scenarios.
This script checks if Ollama is accessible from within a container.
"""

import sys
import time
import requests


def check_ollama_health():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get("http://host.docker.internal:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "Ollama is running and accessible"
        return False, f"Ollama responded with status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return (
            False,
            "Cannot connect to Ollama. Is it running on host.docker.internal:11434?",
        )
    except requests.exceptions.Timeout:
        return False, "Connection to Ollama timed out"
    except requests.exceptions.RequestException as e:
        return False, f"Request error checking Ollama health: {str(e)}"


def wait_for_ollama(max_retries=10, retry_delay=2):
    """Wait for Ollama to become available with retry logic"""
    print("🔍 Checking Ollama availability for Docker container...")
    print("Note: Ollama should be running outside the container on the host machine")

    for attempt in range(max_retries):
        is_healthy, message = check_ollama_health()
        if is_healthy:
            print(f"✅ {message}")
            print("🚀 Ollama is ready! The application can now start.")
            return True

        if attempt < max_retries - 1:  # Don't sleep on the last attempt
            print(
                f"❌ Ollama not available (attempt {attempt + 1}/{max_retries}): {message}"
            )
            print(f"⏳ Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(
                f"❌ Ollama health check failed after {max_retries} attempts: {message}"
            )
            print("\nTroubleshooting tips:")
            print("1. Ensure Ollama is running on the host machine: ollama serve")
            print("2. Check if the container can access host.docker.internal:11434")
            print("3. Verify Docker network configuration allows host access")
            print(
                "4. Try running: curl http://host.docker.internal:11434/api/tags from the host"
            )
            return False


def main():
    """Main function to check Ollama status"""
    success = wait_for_ollama(max_retries=10, retry_delay=2)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
