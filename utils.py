"""Utility functions for the prompt gateway application.

This module contains utility functions for Ollama management, health checks,
and model management.
"""

import time
import requests
import ollama


# Constant list of allowed models
ALLOWED_MODELS = ["deepseek-r1:8b", "llama3:8b"]


def check_ollama_health():
    """Check if Ollama is running and accessible"""
    try:
        # Try to connect to Ollama's default endpoint
        response = requests.get("http://localhost:11434/api/tags", timeout=5)

        if response.status_code == 200:
            return True, "Ollama is running and accessible"
        else:
            return False, f"Ollama responded with status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama. Is it running on localhost:11434?"
    except requests.exceptions.Timeout:
        return False, "Connection to Ollama timed out"
    except requests.exceptions.RequestException as e:
        return False, f"Request error checking Ollama health: {str(e)}"


def ensure_ollama_available(max_retries=10, retry_delay=2):
    """Ensure Ollama is available with retry logic for Docker container startup"""
    for attempt in range(max_retries):
        is_healthy, message = check_ollama_health()
        if is_healthy:
            return True

        if attempt < max_retries - 1:  # Don't sleep on the last attempt
            print(
                f"Ollama not available (attempt {attempt + 1}/{max_retries}): {message}"
            )
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    raise RuntimeError(
        f"Ollama health check failed after {max_retries} attempts: {message}"
    )


def pull_model_if_not_exists(model_name):
    """Pull a model into Ollama if it doesn't already exist"""
    try:
        # Check if model exists by trying to list it
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            existing_models = response.json().get("models", [])
            model_exists = any(
                model.get("name") == model_name for model in existing_models
            )

            if not model_exists:
                print(f"Pulling model {model_name}...")
                ollama.pull(model_name)
                print(f"✅ Successfully pulled model {model_name}")
            else:
                print(f"✅ Model {model_name} already exists")
        else:
            print(f"Warning: Could not check existing models for {model_name}")
    except Exception as e:
        print(f"Warning: Could not pull model {model_name}: {str(e)}")


def ensure_models_available():
    """Ensure all allowed models are available in Ollama"""
    print("Ensuring all required models are available...")
    for model in ALLOWED_MODELS:
        pull_model_if_not_exists(model)
    print("✅ All required models check complete")
