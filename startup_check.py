#!/usr/bin/env python3
"""
Startup check script for Ollama availability in Docker container scenarios.
This script checks if Ollama is accessible from within a container.
"""

import sys
import time
import logging
import requests

# Configure basic logging for the script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


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
    logging.info("🔍 Checking Ollama availability for Docker container...")
    logging.info(
        "Note: Ollama should be running outside the container on the host machine"
    )

    for attempt in range(max_retries):
        is_healthy, message = check_ollama_health()
        if is_healthy:
            logging.info("✅ %s", message)
            logging.info("🚀 Ollama is ready! The application can now start.")
            return True

        if attempt < max_retries - 1:  # Don't sleep on the last attempt
            logging.warning(
                "❌ Ollama not available (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                message,
            )
            logging.info("⏳ Retrying in %d seconds...", retry_delay)
            time.sleep(retry_delay)
        else:
            logging.error(
                "❌ Ollama health check failed after %d attempts: %s",
                max_retries,
                message,
            )
            logging.info("\nTroubleshooting tips:")
            logging.info(
                "1. Ensure Ollama is running on the host machine: ollama serve"
            )
            logging.info(
                "2. Check if the container can access host.docker.internal:11434"
            )
            logging.info("3. Verify Docker network configuration allows host access")
            logging.info(
                "4. Try running: curl http://host.docker.internal:11434/api/tags from the host"
            )
            return False


def main():
    """Main function to check Ollama status"""
    success = wait_for_ollama(max_retries=10, retry_delay=2)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
