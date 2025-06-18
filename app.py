"""Entry point for the application.

This module serves as the main entry point for the Flask application.
It handles application initialization, configuration, and server startup.
"""

import logging

# Flask imports for web framework functionality
from flask import Flask
from flask_cors import CORS  # For handling Cross-Origin Resource Sharing
from waitress import serve  # Production WSGI server

# Import the API blueprint from the apis module
from apis import api
from utils import ensure_ollama_available, ensure_models_available


def create_app(config_module=None, log_level="INFO"):
    """Initialize the core application.

    This function creates and configures a Flask application with all necessary
    middleware, extensions, and settings.

    Args:
        config_module: Optional configuration module to use (defaults to "config")
        log_level: Logging level for the application (defaults to "INFO")

    Returns:
        Flask: Configured Flask application instance
    """
    # Create and configure the Flask app
    app = Flask(__name__)

    # Configure Swagger UI settings for API documentation
    # "none" means no endpoints are expanded by default
    app.config["SWAGGER_UI_DOC_EXPANSION"] = "none"
    # Disable masking of Swagger documentation
    app.config["RESTX_MASK_SWAGGER"] = False

    # Set up logging configuration
    # This configures the root logger with the specified log level
    logging.basicConfig(level=getattr(logging, log_level))

    # Load application configuration from the specified module
    # If no module is specified, defaults to "config"
    app.config.from_object(config_module or "config")

    # Ensure Ollama is running and accessible before starting the app
    try:
        logging.info("Checking Ollama availability (will retry up to 10 times)...")
        ensure_ollama_available(max_retries=10, retry_delay=2)
        logging.info("✅ Ollama health check passed - service is ready")

        # Ensure all required models are available
        logging.info("Ensuring all required models are available...")
        ensure_models_available()
        logging.info("✅ All required models are ready")
    except RuntimeError as e:
        logging.error("❌ Ollama health check failed after all retries: %s", e)
        logging.error(
            "Please ensure Ollama is running and accessible on localhost:11434"
        )
        raise

    # Initialize the API blueprint with the Flask app
    # This registers all API routes and endpoints
    api.init_app(app)

    # Configure CORS (Cross-Origin Resource Sharing)
    # This allows the API to be accessed from different domains/origins
    CORS(
        app,
        resources={
            "/*": {  # Apply CORS to all routes
                "origins": "*",  # Allow all origins (for development - restrict in production)
            }
        },
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Credentials",
        ],
        supports_credentials=True,  # Allow cookies and authentication headers
    )

    return app


if __name__ == "__main__":
    # Command-line argument parsing for server configuration
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Start the Flask application server")
    parser.add_argument(
        "-P", "--port", default=5000, type=int, help="Port to listen on"
    )
    parser.add_argument(
        "-H", "--host", default="0.0.0.0", type=str, help="Host to bind to"
    )
    parser.add_argument(
        "-L",
        "--loglevel",
        default="INFO",
        type=str,
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Parse command line arguments
    args = parser.parse_args()
    port = args.port
    host = args.host
    loglevel = args.loglevel

    # Create the Flask application with specified logging level
    flask_app = create_app(log_level=loglevel)

    # Start the production server using Waitress
    # Waitress is a production-quality WSGI server for Python
    print(f"Starting server on {host}:{port} with log level: {loglevel}")
    serve(flask_app, port=port, host=host)
