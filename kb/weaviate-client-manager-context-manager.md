# Weaviate Python Client - ClientManager Context Manager Usage

## Issue Summary
Wave 1 tests failed with: `'ClientManager' object does not support the context manager protocol`

## Root Cause
The test scripts were attempting to use `ClientManager()` directly as a context manager:
```python
# ❌ INCORRECT - ClientManager is not a context manager
with ClientManager() as client:
    # code
```

## Solution
Use the proper context manager method `connect_to_client()`:
```python
# ✅ CORRECT - Use the context manager method
with ClientManager().connect_to_client() as client:
    # code
```

## Alternative Patterns

### Pattern 1: Direct Connection (Recommended)
```python
import weaviate

# For local Weaviate
with weaviate.connect_to_local() as client:
    # code

# For cloud Weaviate
with weaviate.connect_to_weaviate_cloud(
    url="https://your-cluster.weaviate.network",
    auth_credentials=weaviate.Auth.api_key("your-api-key")
) as client:
    # code
```

### Pattern 2: Manual Connection Management
```python
import weaviate

# Manual connection (less preferred)
client = weaviate.connect_to_local()
try:
    # code
finally:
    client.close()
```

## ClientManager Methods

The `ClientManager` class provides these context manager methods:

- `connect_to_client()` - Synchronous client context manager
- `connect_to_async_client()` - Asynchronous client context manager

## Configuration via Environment

Test scripts should load configuration from `.env` files:
```python
from dotenv import load_dotenv
import os

# Load environment configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# ClientManager will automatically pick up environment variables
with ClientManager().connect_to_client() as client:
    # client is now configured from .env
```

## Required Environment Variables

For local Weaviate testing:
```
WCD_URL=http://localhost:18080
WEAVIATE_IS_LOCAL=True
WCD_API_KEY=local-mode
WEAVIATE_CLUSTER_PORTS=18080,18081,18082
```

## Dynamic Port Configuration

Instead of hardcoding ports, read from environment:
```python
# Load configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# Get cluster ports dynamically
ports_str = os.environ.get("WEAVIATE_CLUSTER_PORTS", "18080,18081,18082")
nodes = [int(port.strip()) for port in ports_str.split(",")]

# Use dynamic ports
for port in nodes:
    # Test each node
    pass
```

1. **Wrong context manager usage**: `with ClientManager() as client` ❌
2. **Missing dotenv loading**: Not calling `load_dotenv()` ✅
3. **Hardcoded configuration**: Avoid embedding URLs/API keys in code ✅
4. **Not restoring environment**: Use try/finally for environment cleanup ✅

## Verification

Test that the fix works:
```bash
cd /opt/elysia/tests/phase4
python -m py_compile *.py  # Should pass without errors
python wave1_runner.py     # Should run all tests successfully
```

## Related Files
- `/opt/elysia/elysia/util/client.py` - ClientManager implementation
- `/opt/elysia/tests/phase4/*.py` - Fixed test scripts
- `/opt/elysia/tests/phase4/.env` - Test configuration

## References
- Weaviate Python Client Documentation
- Context7 Library: `/weaviate/weaviate-python-client`
- ClientManager source code patterns