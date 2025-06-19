"""Initialize the api system for the backend"""

import re
from functools import wraps
import requests
import ollama
from flask import request
from flask_restx import Api, Resource
from utils import ALLOWED_MODELS, check_ollama_health
from config import validate_api_key

api = Api(
    title="CWL Validator API",
    description="The backend api system for the CWL Validator",
    doc="/docs",
)


def require_api_key(f):
    """Decorator to require API key authentication.

    This decorator checks for an 'Authorization' header with Bearer token
    and validates it against the configured API keys.

    Args:
        f: The function to decorate

    Returns:
        The decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return {
                "message": "Authentication Error",
                "error": "Authorization header is required. Please provide 'Authorization: Bearer <token>'.",
            }, 401

        # Check if it's a Bearer token
        if not auth_header.startswith("Bearer "):
            return {
                "message": "Authentication Error",
                "error": "Invalid authorization format. Use 'Bearer <token>'.",
            }, 401

        # Extract the token
        token = auth_header[7:]  # Remove 'Bearer ' prefix

        if not validate_api_key(token):
            return {"message": "Authentication Error", "error": "Invalid token."}, 401

        return f(*args, **kwargs)

    return decorated_function


@api.route("/echo", endpoint="echo")
class HelloEveryNyan(Resource):
    """Test if the server is active"""

    @api.response(200, "Success")
    @api.response(400, "Validation Error")
    def get(self):
        """Returns a simple 'Server Active' message"""

        return "Server active!"


@api.route("/up", endpoint="up")
class Up(Resource):
    """Health check for kamal"""

    @api.response(200, "Success")
    def get(self):
        """Returns a simple message"""

        return ":)"


@api.route("/health/ollama", endpoint="ollama_health")
class OllamaHealth(Resource):
    """Health check for Ollama service"""

    @api.response(200, "Ollama is healthy")
    @api.response(503, "Ollama is not available")
    def get(self):
        """Check if Ollama is running and accessible"""
        is_healthy, message = check_ollama_health()
        if is_healthy:
            return {"status": "healthy", "message": message}, 200
        else:
            return {"status": "unhealthy", "message": message}, 503


@api.route("/query", endpoint="query")
class Query(Resource):
    """Query the model"""

    @api.response(200, "Success")
    @api.response(400, "Validation Error")
    @api.response(401, "Authentication Error")
    @api.expect(
        api.parser().add_argument(
            "query",
            type=str,
            help="The query to the model",
            required=True,
        ),
        api.parser().add_argument(
            "model",
            type=str,
            help="The model to use",
            required=False,
            default="llama3:8b",
        ),
        api.parser().add_argument(
            "context",
            type=str,
            help="The context to use",
            required=False,
            default="",
        ),
        api.parser().add_argument(
            "temperature",
            type=float,
            help="Controls randomness (0.0-2.0). Lower values are more deterministic",
            required=False,
            default=0.7,
        ),
        api.parser().add_argument(
            "top_p",
            type=float,
            help="Nucleus sampling parameter (0.0-1.0)",
            required=False,
            default=0.9,
        ),
        api.parser().add_argument(
            "top_k",
            type=int,
            help="Top-k sampling parameter",
            required=False,
            default=40,
        ),
        api.parser().add_argument(
            "num_predict",
            type=int,
            help="Maximum number of tokens to generate",
            required=False,
            default=2048,
        ),
        api.parser().add_argument(
            "stop",
            type=str,
            help="Comma-separated stop sequences",
            required=False,
            default="",
        ),
        api.parser().add_argument(
            "stream",
            type=bool,
            help="Whether to stream the response",
            required=False,
            default=False,
        ),
        api.parser().add_argument(
            "format",
            type=str,
            help="Response format (json, etc.)",
            required=False,
            default="",
        ),
        api.parser().add_argument(
            "num_ctx",
            type=int,
            help="Context window size",
            required=False,
            default=4096,
        ),
        api.parser().add_argument(
            "num_gpu",
            type=int,
            help="Number of GPU layers to use",
            required=False,
            default=1,
        ),
        api.parser().add_argument(
            "num_thread",
            type=int,
            help="Number of CPU threads to use",
            required=False,
            default=4,
        ),
    )
    @require_api_key
    def post(self):
        """Query the model"""

        def clean_output(output):
            # Remove ANSI escape codes
            ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
            cleaned_output = ansi_escape.sub("", output).strip()
            # Remove INFO messages and unnecessary whitespace, and replace newlines with spaces
            cleaned_lines = []
            for line in cleaned_output.splitlines():
                if not line.startswith("INFO"):
                    cleaned_lines.append(line.strip())
            return " ".join(cleaned_lines)

        # Extract all parameters
        query = api.payload.get("query")
        model = api.payload.get("model", "llama3:8b")
        context = api.payload.get("context", "")
        temperature = api.payload.get("temperature", 0.7)
        top_p = api.payload.get("top_p", 0.9)
        top_k = api.payload.get("top_k", 40)
        num_predict = api.payload.get("num_predict", 2048)
        stop = api.payload.get("stop", "")
        stream = api.payload.get("stream", False)
        format_param = api.payload.get("format", "")
        num_ctx = api.payload.get("num_ctx", 4096)
        num_gpu = api.payload.get("num_gpu", 1)
        num_thread = api.payload.get("num_thread", 4)

        # Validate and sanitize the query input
        if not query:
            return {
                "message": "Validation Error",
                "error": "query is required",
            }, 400

        # Validate model
        if not model or model.strip() == "":
            model = "llama3:8b"  # Use default if empty

        if model not in ALLOWED_MODELS:
            return {
                "message": "Validation Error",
                "error": f"Invalid model. Allowed models: {', '.join(ALLOWED_MODELS)}",
            }, 400

        # Prevent path traversal attacks
        if ".." in query or query.startswith("/"):
            return {"message": "Validation Error", "error": "Invalid query"}, 400

        # Prevent command injection
        if re.search(r"[;&|]", query):
            return {
                "message": "Validation Error",
                "error": "Invalid characters in query",
            }, 400

        # Validate parameter ranges
        if not 0.0 <= temperature <= 2.0:
            return {
                "message": "Validation Error",
                "error": "temperature must be between 0.0 and 2.0",
            }, 400

        if not 0.0 <= top_p <= 1.0:
            return {
                "message": "Validation Error",
                "error": "top_p must be between 0.0 and 1.0",
            }, 400

        if top_k < 0:
            return {
                "message": "Validation Error",
                "error": "top_k must be non-negative",
            }, 400

        if num_predict < 0:
            return {
                "message": "Validation Error",
                "error": "num_predict must be non-negative",
            }, 400

        query = clean_output(query)  # Remove ANSI escape codes

        # Process stop sequences
        stop_sequences = []
        if stop:
            stop_sequences = [s.strip() for s in stop.split(",") if s.strip()]

        # Build options dictionary
        options = {
            "num_ctx": num_ctx,
            "num_gpu": num_gpu,
            "num_thread": num_thread,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "num_predict": num_predict,
        }

        # Add stop sequences to options if provided
        if stop_sequences:
            options["stop"] = stop_sequences

        # Process the query
        try:
            # Build the chat parameters
            chat_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": context},
                    {"role": "user", "content": query},
                ],
                "options": options,
                "stream": stream,
            }

            # Add optional parameters if they differ from defaults
            if format_param:
                chat_params["format"] = format_param

            response_from_model = ollama.chat(**chat_params)

            # Handle both streaming and non-streaming responses
            if stream:
                # For streaming, collect all messages
                messages = []
                for chunk in response_from_model:
                    if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                        messages.append(chunk.message.content)
                response_data = {
                    "message": "".join(messages),
                    "model": model,
                    "created_at": None,
                    "done": True,
                }
            else:
                # For non-streaming, extract from single response
                try:
                    # Convert to string first to avoid generator issues
                    response_str = str(response_from_model)
                    if hasattr(response_from_model, "message"):
                        message_obj = getattr(response_from_model, "message", None)
                        if message_obj and hasattr(message_obj, "content"):
                            content = getattr(message_obj, "content", response_str)
                        else:
                            content = response_str
                    else:
                        content = response_str

                    response_data = {
                        "message": content,
                        "model": getattr(response_from_model, "model", model),
                        "created_at": getattr(response_from_model, "created_at", None),
                        "done": getattr(response_from_model, "done", True),
                    }
                except (AttributeError, TypeError, ValueError) as e:
                    response_data = {
                        "message": f"Response received but could not parse: {str(response_from_model)}",
                        "model": model,
                        "created_at": None,
                        "done": True,
                        "parse_error": str(e),
                    }

            result = {
                "message": "Success",
                "response": response_data,
                "parameters": {
                    "model": model,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "num_predict": num_predict,
                    "stream": stream,
                    "context_length": num_ctx,
                },
            }
            status_code = 200
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
        ) as e:
            result = {
                "message": "Ollama service is not available",
                "error": "Cannot connect to Ollama. Please ensure it is running on host.docker.internal:11434",
                "details": str(e),
            }
            status_code = 503
        except (ValueError, TypeError) as e:
            result = {"message": "Invalid request parameters", "error": str(e)}
            status_code = 400
        except RuntimeError as e:
            result = {"message": "Ollama runtime error", "error": str(e)}
            status_code = 500

        return result, status_code
