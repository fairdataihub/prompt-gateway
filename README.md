# prompt-gateway

## Getting started

### Prerequisites/Dependencies

You will need the following installed on your system:

- Python 3.8+
- [Pip](https://pip.pypa.io/en/stable/)
- [Docker](https://www.docker.com/)
- [Ollama](https://ollama.ai/) - Required for local LLM inference

### Ollama Setup

This application is designed to run in a Docker container while Ollama runs on the host machine. The application will automatically retry connecting to Ollama up to 10 times during startup.

1. **Install Ollama** on the host machine (if not already installed):

   - Download from [https://ollama.ai/download](https://ollama.ai/download)
   - Follow the installation instructions for your platform

2. **Start Ollama** on the host machine:

   ```bash
   ollama serve
   ```

3. **Verify Ollama is accessible** (optional but recommended):

   ```bash
   python startup_check.py
   ```

   This script will check if Ollama is accessible from within a container context.

4. **Pull required models** (if needed):

   ```bash
   ollama pull llama3:8b
   ```

### API Key Authentication

This application uses token-based authentication to secure access to the LLM endpoints. API tokens are stored as environment variables in JSON format and must be included in request headers using the standard Bearer token format.

#### Setting Up API Tokens

1. **Generate API tokens** using the provided utility:

   ```bash
   python generate_api_key.py
   ```

   This will generate secure API tokens and provide setup instructions.

2. **Configure API tokens** using one of these methods:

   **Option A: Using a .env file**

   ```bash
   # Create a .env file in the project root
   echo 'API_KEYS=[{"appname":"APP1","key":"your-token-here"},{"appname":"WEBAPP","key":"another-token-here"}]' > .env
   ```

   **Option B: Using system environment variables**

   ```bash
   export API_KEYS='[{"appname":"APP1","key":"your-token-here"},{"appname":"WEBAPP","key":"another-token-here"}]'
   ```

   The JSON format is designed to work with external environment variable management tools. Each object in the array contains an `appname` and `key` property.

3. **Using API tokens in requests**:

   Include the token in the `Authorization` header using Bearer format:

   ```bash
   curl -X POST "http://host.docker.internal:5000/query" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-token-here" \
     -d '{"query": "Hello, how are you?"}'
   ```

#### Security Notes

- Keep your API tokens secure and don't share them
- Use different tokens for different applications
- Rotate tokens periodically for better security
- Never commit API tokens to version control
- The health check endpoints (`/echo`, `/up`, `/health/ollama`) do not require authentication

### Setup

If you would like to update the api, please follow the instructions below.

1. Create a local virtual environment and activate it:

   ```bash
   python -m venv .venv
   source .venv/bin/activate # on Windows use .venv\Scripts\activate
   ```

   If you are using Anaconda, you can create a virtual environment with:

   ```bash
   conda create -n prompt-gateway-dev-env python=3.13
   conda activate prompt-gateway-dev-env
   ```

2. Install the dependencies for this package.

   ```bash
   pip install -r requirements.txt
   ```

## Running

**Important**: Ensure Ollama is running on the host machine before starting the application. The app will automatically retry connecting to Ollama up to 10 times during startup.

For developer mode:

```bash
python app.py --host $HOST --port $PORT
```

or

```bash
flask run --debug
```

For production mode:

```bash
python3 app.py --host $HOST --port $PORT
```

## Docker Deployment

When running in a Docker container, ensure that:

1. **Ollama is running on the host machine** (not in the container)
2. **The container can access host.docker.internal:11434** (Ollama's default port)
3. **Docker network configuration allows host access**
4. **API tokens are properly configured** as environment variables

Example Docker run command:

```bash
docker run -p 5000:5000 \
  -e API_KEY_APP1=your-token-here \
  -e API_KEY_WEBAPP=another-token-here \
  --network host your-app-image
```

## Health Checks

The application provides several health check endpoints:

- `/up` - Basic application health check
- `/health/ollama` - Check if Ollama is running and accessible
- `/query` - Test the LLM functionality (requires Ollama to be running and API token authentication)

## Troubleshooting

If you encounter issues with Ollama connectivity:

1. **Check if Ollama is running on the host**:

   ```bash
   curl http://host.docker.internal:11434/api/tags
   ```

2. **Verify container can access host**:

   ```bash
   python startup_check.py
   ```

3. **Check application logs** for detailed error messages about Ollama connectivity issues.

4. **Ensure the required model is available**:

   ```bash
   ollama list
   ```

5. **Docker network issues**: If the container cannot access host.docker.internal:11434, try:
   - Using `--network host` flag
   - Or mapping the port: `-p 11434:11434`

If you encounter authentication issues:

1. **Verify API tokens are configured**:

   ```bash
   python -c "from config import get_api_keys; print(get_api_keys())"
   ```

2. **Check that the Authorization header is included** in your requests

3. **Ensure the token matches** one of the configured environment variables
