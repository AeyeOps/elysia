# CRUSH.md

This file provides guidance for AI agents working in this repository.

## Development Commands

### Installation
```bash
uv sync --extra dev
```

### Testing
```bash
# Run all tests (excluding env-required)
pytest --ignore=tests/requires_env --tb=short -v

# Run single test
pytest tests/no_reqs/api/test_config_nr.py -v

# Run with coverage
pytest --cov=elysia --ignore=tests/requires_env
```

### Running the App
```bash
elysia start --reload
```

### Building
```bash
uv build
```

### Documentation
```bash
mkdocs serve  # Local preview at http://127.0.0.1:8000
```

## Code Style Guidelines

- **Imports**: Group into standard library, third-party, local; no conditional imports.
- **Formatting**: Follow PEP 8; use type hints for all signatures and complex variables.
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes.
- **Async**: Prefer `async/await` for I/O operations.
- **Error Handling**: Fail fast; catch specific exceptions, use custom exceptions where appropriate.
- **Dependencies**: Check `pyproject.toml` before adding new ones.
- **Security**: Never expose or log sensitive data like API keys.
- **Patterns**: Follow existing async-first patterns; streaming responses via generators.

## Behavioral Guidelines

- Be concise and direct - Minimize explanations unless specifically requested
- Prefer editing over creating - Always modify existing files when possible
- Follow existing patterns - Study neighboring code and maintain consistency
- Test after changes - Always run `pytest --ignore=tests/requires_env` after code changes
- No unsolicited documentation - Don't create README files unless explicitly requested
- Security first - Never expose or log sensitive information like API keys or tokens
- File Reading: For large files, read portions first (e.g., beginning, middle, end) rather than the whole file to avoid exceeding context window limits</content>
<parameter name="file_path">CRUSH.md