# Python dotenv Configuration Pattern for Testing

## Overview
Proper handling of environment variables in test scripts using python-dotenv.

## Issue Encountered
Settings attribute errors when trying to access `settings.WCD_URL` in test scripts.

## Root Cause
Test scripts were trying to access global settings object before environment variables were loaded.

## Solution Pattern

### 1. Load Environment First
```python
from dotenv import load_dotenv
import os

# Load .env file with override
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)
```

### 2. Use Environment Variables Directly
Instead of accessing `settings.WCD_URL`, use `os.environ`:
```python
# ❌ Don't do this
original_url = settings.WCD_URL

# ✅ Do this instead
original_url = os.environ.get("WCD_URL")
```

### 3. Temporary Environment Modification
For testing different configurations:
```python
original_url = os.environ.get("WCD_URL")

try:
    # Temporarily change environment
    os.environ["WCD_URL"] = "http://localhost:18081"

    # Use ClientManager (it will pick up the new environment)
    with ClientManager().connect_to_client() as client:
        # code using client

finally:
    # Always restore original environment
    if original_url:
        os.environ["WCD_URL"] = original_url
```

### 4. Environment Restoration
Always restore the original environment state:
```python
finally:
    # Method 1: Selective restoration
    if original_url:
        os.environ["WCD_URL"] = original_url

    # Method 2: Complete restoration (preferred for complex changes)
    os.environ.clear()
    os.environ.update(original_env)
    load_dotenv(override=True)
```

## Complete Example
```python
import os
from dotenv import load_dotenv
from elysia.util.client import ClientManager

def test_different_nodes():
    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Save original state
    original_env = os.environ.copy()

    nodes = [18080, 18081, 18082]

    try:
        for port in nodes:
            # Temporarily change URL
            os.environ["WCD_URL"] = f"http://localhost:{port}"

            # ClientManager automatically uses new environment
            with ClientManager().connect_to_client() as client:
                # Test operations on this node
                pass

    finally:
        # Restore complete environment
        os.environ.clear()
        os.environ.update(original_env)
        load_dotenv(override=True)
```

## Benefits

1. **Isolation**: Each test can have its own environment
2. **Consistency**: Environment matches .env file
3. **Safety**: Automatic cleanup prevents environment pollution
4. **Flexibility**: Easy to test different configurations
5. **Debugging**: Clear separation of configuration concerns

## Common Mistakes

1. **Loading dotenv without override**: `load_dotenv()` instead of `load_dotenv(override=True)`
2. **Not saving original state**: Forgetting to backup `os.environ.copy()`
3. **Partial restoration**: Only restoring some variables
4. **Loading dotenv multiple times**: Can cause unexpected overrides

## File Structure
```
tests/phase4/
├── .env                    # Test configuration
├── test_script.py         # Test script that loads .env
└── wave1_runner.py        # Orchestrates all tests
```

## Environment Variables Used
```
WCD_URL=http://localhost:18080    # Weaviate cluster URL
WEAVIATE_IS_LOCAL=True            # Local mode flag
WCD_API_KEY=local-mode           # API key (local mode)
WEAVIATE_CLUSTER_PORTS=18080,18081,18082  # Dynamic cluster ports
```

## Dynamic Configuration Parsing

Parse comma-separated values from environment:
```python
# Get cluster ports from environment variable
ports_str = os.environ.get("WEAVIATE_CLUSTER_PORTS", "18080,18081,18082")
nodes = [int(port.strip()) for port in ports_str.split(",")]

print(f"Testing {len(nodes)} cluster nodes: {nodes}")
# Output: Testing 3 cluster nodes: [18080, 18081, 18082]
```

## Testing
```bash
# Verify environment loading
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env', override=True); print(os.environ.get('WCD_URL'))"

# Run tests
python wave1_runner.py
```