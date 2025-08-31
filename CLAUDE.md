# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Behavioral Guidelines

When working in this codebase:
- **Be concise and direct** - Minimize explanations unless specifically requested
- **Prefer editing over creating** - Always modify existing files rather than creating new ones when possible
- **Follow existing patterns** - Study neighboring code and maintain consistency with established conventions
- **Test after changes** - Always run `pytest --ignore=tests/requires_env` after making code changes
- **Check for existing dependencies** - Never assume a library is available; verify in pyproject.toml first
- **Maintain code style** - Follow the existing code formatting and naming conventions
- **No unsolicited documentation** - Don't create README or documentation files unless explicitly requested
- **Security first** - Never expose or log sensitive information like API keys or tokens

## Development Commands

### Running the Application
```bash
# Start the FastAPI app (default: localhost:8000)
elysia start

# With custom options
elysia start --port 8080 --host 0.0.0.0 --reload
```

### Testing
```bash
# Run tests excluding integration tests that require environment setup
pytest --ignore=tests/requires_env --tb=short -v

# Run all tests (requires proper .env configuration)
pytest -v

# Run specific test file
pytest tests/no_reqs/test_file.py -v

# Run with coverage
pytest --cov=elysia --ignore=tests/requires_env
```

### Installation & Dependencies
```bash
# Install package in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Build documentation
mkdocs serve  # Local preview at http://127.0.0.1:8000
mkdocs build  # Build static site
```

## Architecture Overview

Elysia is an agentic framework that uses decision trees to orchestrate tool usage for data retrieval and processing, particularly with Weaviate vector databases.

### Core Components

**Tree System (`elysia/tree/`)**
- `Tree` class: Main entry point for decision tree execution
- Manages tool registration, execution flow, and conversation state
- Uses DSPy for LLM interactions with configurable base/complex models

**Tool Framework (`elysia/tools/`)**
- Built-in tools for Weaviate operations: `Query`, `Aggregate`, `Visualise`, `SummariseItems`
- Custom tools can be registered via `@tool` decorator
- Tools communicate through standardized objects (`Return`, `Update`, `Warning`, `Error`)

**API Layer (`elysia/api/`)**
- FastAPI application serving the web interface
- WebSocket support for real-time streaming responses
- User session management with per-user configurations
- Routes: `/chat`, `/collections`, `/settings`, `/auth`

**Configuration System (`elysia/config.py`)**
- Global settings and per-user configuration support
- Model providers: OpenAI, Anthropic, OpenRouter, Gemini, local models via Ollama
- Environment variable loading from `.env` file
- Weaviate connection management with auth support

**Preprocessing (`elysia/preprocessing/`)**
- Collection analysis and metadata extraction for Weaviate data
- Creates `ELYSIA_` prefixed collections for storing preprocessing results
- Required before collections can be queried through the tree

### Key Design Patterns

1. **Async-First**: Core operations use async/await for scalability
2. **Streaming Responses**: Tools yield updates progressively via generators
3. **Multi-Model Support**: Separate base/complex models for different task complexities
4. **User Isolation**: Each user has isolated settings and Weaviate connections

### Weaviate Integration

The system expects Weaviate clusters to be configured with:
- Authentication (API key or local anonymous access)
- Collections must be preprocessed via `preprocess()` before use
- Supports both cloud and local Weaviate instances (local requires `weaviate_is_local=True`)

### Environment Configuration

Required environment variables:
```
# Weaviate connection
WCD_URL=<weaviate-cluster-url>
WCD_API_KEY=<weaviate-api-key>

# Model providers (at least one required)
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
OPENROUTER_API_KEY=...
GEMINI_API_KEY=...

# Model selection (optional, defaults to smart_setup)
BASE_MODEL=<model-name>
BASE_PROVIDER=<provider>
COMPLEX_MODEL=<model-name>
COMPLEX_PROVIDER=<provider>
```

For local Weaviate without authentication:
```
WCD_URL=http://localhost:8080
WEAVIATE_IS_LOCAL=true
```