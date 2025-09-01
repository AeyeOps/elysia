# UV Package Manager Guide for Elysia

Elysia has been retrofitted with [UV](https://github.com/astral-sh/uv), a blazingly fast Python package manager written in Rust. UV provides 10-100x faster dependency resolution and installation while maintaining full compatibility with existing pip workflows.

## Quick Start

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup Elysia with UV
git clone https://github.com/AeyeOps/elysia.git
cd elysia
uv sync --extra dev  # Installs everything in seconds!
uv run elysia start  # Run the application
```

## Command Reference Table

| UV Command (New Way) | Pip Command (Old Way) | Description |
|---------------------|----------------------|-------------|
| `uv sync` | `pip install -e .` | Install package in development mode |
| `uv sync --extra dev` | `pip install -e ".[dev]"` | Install with dev dependencies |
| `uv sync --no-dev` | `pip install .` | Install without dev dependencies |
| `uv add <package>` | Edit pyproject.toml + `pip install -e .` | Add and install a new dependency |
| `uv add --dev <package>` | Edit pyproject.toml + `pip install -e ".[dev]"` | Add and install a dev dependency |
| `uv remove <package>` | Edit pyproject.toml + `pip install -e .` | Remove a dependency |
| `uv lock` | N/A (pip has no lockfile) | Create/update lockfile for reproducible builds |
| `uv lock --upgrade` | `pip install --upgrade -e .` | Update all dependencies to latest versions |
| `uv run <command>` | `python -m <module>` or `<command>` | Run command in project environment |
| `uv run pytest` | `pytest` | Run tests in project environment |
| `uv run elysia start` | `elysia start` | Start the FastAPI application |
| `uv pip list` | `pip list` | List installed packages |
| `uv pip freeze` | `pip freeze` | Show installed packages with versions |
| `uv python install 3.11` | `pyenv install 3.11` or manual install | Install a specific Python version |
| `uv python list` | `pyenv versions` or `ls /usr/bin/python*` | List available Python versions |
| `uv venv` | `python -m venv .venv` | Create a virtual environment |
| `rm -rf .venv && uv sync` | `pip uninstall -y elysia-ai && rm -rf build/ dist/ *.egg-info && pip install -e .` | Clean rebuild from scratch |
| `uv sync --reinstall` | `pip install --force-reinstall -e .` | Force reinstall all packages |
| `uv tree` | `pipdeptree` | Show dependency tree |

## Performance Comparison

| Operation | UV Time | Pip Time | Speedup |
|-----------|---------|----------|---------|
| Resolve 223 packages | 92ms | ~15s | **163x faster** |
| Install 136 packages | 473ms | ~45s | **95x faster** |
| Add single package | <1s | 5-10s | **5-10x faster** |
| Clean rebuild | 2-3s | 30-60s | **10-20x faster** |

## Common Workflows

### Development Setup
```bash
# UV (new way) - Single command, ~3 seconds
uv sync --extra dev

# Pip (old way) - Multiple steps, ~1 minute
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -e ".[dev]"
```

### Running Tests
```bash
# UV (new way) - Ensures correct environment
uv run pytest --ignore=tests/requires_env --tb=short -v
uv run pytest --cov=elysia --ignore=tests/requires_env

# Pip (old way) - Depends on activated environment
pytest --ignore=tests/requires_env --tb=short -v
pytest --cov=elysia --ignore=tests/requires_env
```

### Adding Dependencies
```bash
# UV (new way) - Updates pyproject.toml automatically
uv add requests
uv add --dev pytest-mock

# Pip (old way) - Manual process
# 1. Edit pyproject.toml manually
# 2. Run: pip install -e ".[dev]"
```

### Starting the Application
```bash
# UV (new way) - Always uses project environment
uv run elysia start
uv run elysia start --port 8080 --reload

# Pip (old way) - Requires activated venv
elysia start
elysia start --port 8080 --reload
```

### Updating Dependencies
```bash
# UV (new way) - Controlled updates with lockfile
uv lock --upgrade           # Update lockfile
uv sync                     # Apply updates

# Pip (old way) - Less controlled
pip install --upgrade -e ".[dev]"
pip list --outdated         # Check what's outdated
```

### Clean Rebuild
```bash
# UV (new way) - Fast and clean
rm -rf .venv
uv sync --extra dev         # ~3 seconds

# Pip (old way) - Slower and more complex
pip uninstall -y elysia-ai
rm -rf build/ dist/ *.egg-info .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"     # ~1 minute
```

## Key Advantages of UV

1. **Speed**: 10-100x faster dependency resolution and installation
2. **Lockfile**: `uv.lock` ensures everyone gets the same dependencies
3. **Python Management**: Built-in Python version management
4. **Parallel Operations**: Downloads 8 packages and installs 4 simultaneously
5. **Better Dependency Resolution**: More intelligent conflict resolution
6. **Single Tool**: Replaces pip, pip-tools, pipenv, poetry, pyenv, virtualenv
7. **Cross-platform**: Works identically on Linux, macOS, and Windows
8. **Backward Compatible**: All pip commands still work if needed

## Configuration

UV configuration is stored in `pyproject.toml`:

```toml
[tool.uv]
package = true                    # Build and install as a package
python-downloads = "automatic"    # Auto-manage Python versions
resolution = "highest"            # Use latest compatible versions
index-strategy = "first-index"    # PyPI as primary source
concurrent-downloads = 8          # Parallel downloads
concurrent-installs = 4           # Parallel installs
```

## FAQ

### Q: Do I need to activate a virtual environment with UV?
No! UV automatically manages environments. Just use `uv run` to execute commands.

### Q: Can I still use pip if needed?
Yes, UV is fully compatible with pip. You can use both tools interchangeably.

### Q: What about the MANIFEST.in file?
UV fully respects MANIFEST.in. All distribution files are included as before.

### Q: How do I switch Python versions?
```bash
uv python install 3.12
uv sync --python 3.12
```

### Q: Where does UV store the virtual environment?
By default in `.venv` in your project directory, just like standard Python venvs.

### Q: Can I use UV in CI/CD pipelines?
Yes! UV is designed for CI/CD with reproducible builds via `uv.lock`.

## Migration Tips

1. **Start Fresh**: Remove existing `.venv` and let UV create a new one
2. **Commit the Lockfile**: Always commit `uv.lock` for reproducible builds
3. **Use `uv run`**: Prefix commands with `uv run` to ensure correct environment
4. **Check UV Version**: Run `uv --version` to ensure you have the latest

## Troubleshooting

If you encounter issues:

1. **Clear the cache**: `uv cache clean`
2. **Force reinstall**: `uv sync --reinstall`
3. **Check Python version**: `uv python list`
4. **Verbose output**: Add `-v` or `-vv` for debugging

## Learn More

- [UV Documentation](https://github.com/astral-sh/uv)
- [UV Performance Benchmarks](https://astral.sh/blog/uv)
- [Migration Guide](https://docs.astral.sh/uv/guides/migration/)