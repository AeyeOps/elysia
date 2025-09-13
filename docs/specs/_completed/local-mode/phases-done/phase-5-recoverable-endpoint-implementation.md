# Phase 5: Recoverable Endpoint Error Handling Implementation

## Objective
Implement the @recoverable_endpoint decorator pattern from ADR-001 to properly handle missing user errors, preventing raw exceptions from leaking to clients and providing appropriate HTTP responses.

## Problem Summary
When a user is not found in the system, API endpoints throw raw ValueError exceptions with internal details like "User with ID 'abc123' not found in collection 'ELYSIACTL_CONFIG_1169a452fe5da387b9c7ce2e6dc4cf8b'". These should return HTTP 401 with "Session not initialized" per ADR-001.

## Implementation Details

### File: `/opt/elysia/elysia/api/middleware/recovery.py` (NEW)

Create the recovery middleware with the @recoverable_endpoint decorator:

```python
import logging
import re
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def recoverable_endpoint(func):
    """
    Decorator that transforms exceptions into proper HTTP responses.
    
    Usage:
        @router.post("/endpoint")
        @recoverable_endpoint
        async def endpoint(...):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            error_str = str(e).lower()
            logger.exception(f"ValueError in {func.__name__}: {e}")
            
            if "not found" in error_str and "user" in error_str:
                raise HTTPException(401, "Session not initialized")
            elif "not found" in error_str and "collection" in error_str:
                name = extract_resource_name(str(e))
                raise HTTPException(404, f"Collection {name} not found" if name else "Collection not found")
            
            raise HTTPException(400, str(e))
            
        except KeyError as e:
            logger.exception(f"KeyError in {func.__name__}: {e}")
            raise HTTPException(422, f"Missing required field: {str(e).strip('\"')}")
            
        except ConnectionError as e:
            logger.exception(f"ConnectionError in {func.__name__}: {e}")
            if "weaviate" in str(e).lower():
                raise HTTPException(503, "Database temporarily unavailable")
            raise HTTPException(503, "Service temporarily unavailable")
            
        except Exception as e:
            logger.exception(f"Unhandled error in {func.__name__}: {e}")
            raise HTTPException(500, "Internal server error")
    
    return wrapper

def extract_resource_name(error_message: str) -> str:
    """Extract resource name from error message."""
    match = re.search(r"['\"]([^'\"]+)['\"]", error_message)
    return match.group(1) if match else ""
```

### File: `/opt/elysia/elysia/api/routes/init.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.middleware.recovery import recoverable_endpoint
```

**Change 2: Apply decorator to initialise_user**
**Location:** Line 51
**Current Code:**
```python
@router.post("/user/{user_id}")
async def initialise_user(
```

**New Code:**
```python
@router.post("/user/{user_id}")
@recoverable_endpoint
async def initialise_user(
```

### File: `/opt/elysia/elysia/api/routes/user_config.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.middleware.recovery import recoverable_endpoint
```

**Change 2: Apply decorator to get_current_user_config**
**Location:** Line 95
**Current Code:**
```python
@router.get("/{user_id}")
async def get_current_user_config(
```

**New Code:**
```python
@router.get("/{user_id}")
@recoverable_endpoint
async def get_current_user_config(
```

**Change 3: Apply decorator to new_user_config**
**Location:** Line 223
**Current Code:**
```python
@router.post("/{user_id}/new")
async def new_user_config(
```

**New Code:**
```python
@router.post("/{user_id}/new")
@recoverable_endpoint
async def new_user_config(
```

**Change 4: Apply decorator to save_config_user**
**Location:** Line 314
**Current Code:**
```python
@router.post("/{user_id}/{config_id}")
async def save_config_user(
```

**New Code:**
```python
@router.post("/{user_id}/{config_id}")
@recoverable_endpoint
async def save_config_user(
```

**Change 5: Apply decorator to delete_config**
**Location:** Line 731
**Current Code:**
```python
@router.delete("/{user_id}/{config_id}")
async def delete_config(
```

**New Code:**
```python
@router.delete("/{user_id}/{config_id}")
@recoverable_endpoint
async def delete_config(
```

**Change 6: Apply decorator to list_configs**
**Location:** Line 761
**Current Code:**
```python
@router.get("/{user_id}/list")
async def list_configs(
```

**New Code:**
```python
@router.get("/{user_id}/list")
@recoverable_endpoint
async def list_configs(
```

### File: `/opt/elysia/elysia/api/routes/collections.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.middleware.recovery import recoverable_endpoint
```

**Change 2: Apply decorator to collections_list**
**Location:** Line 66
**Current Code:**
```python
@router.get("/{user_id}/list")
async def collections_list(
```

**New Code:**
```python
@router.get("/{user_id}/list")
@recoverable_endpoint
async def collections_list(
```

### File: `/opt/elysia/elysia/api/routes/db.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.middleware.recovery import recoverable_endpoint
```

**Change 2: Apply decorator to get_saved_trees**
**Location:** Line 13
**Current Code:**
```python
@router.get("/{user_id}/saved_trees")
async def get_saved_trees(
```

**New Code:**
```python
@router.get("/{user_id}/saved_trees")
@recoverable_endpoint
async def get_saved_trees(
```

## Agent Workflow

### Step 1: Implementation Agent
1. Create the new directory `/opt/elysia/elysia/api/middleware/` if it doesn't exist
2. Create the file `/opt/elysia/elysia/api/middleware/recovery.py`
3. Copy the complete decorator implementation code
4. Save the file

### Step 2: Route Updates Agent
1. Open `/opt/elysia/elysia/api/routes/init.py`
   - Add the import statement
   - Add `@recoverable_endpoint` decorator at line 51
   - Save the file

2. Open `/opt/elysia/elysia/api/routes/user_config.py`
   - Add the import statement
   - Add `@recoverable_endpoint` decorator at lines 95, 223, 314, 731, and 761
   - Save the file

3. Open `/opt/elysia/elysia/api/routes/collections.py`
   - Add the import statement
   - Add `@recoverable_endpoint` decorator at line 66
   - Save the file

4. Open `/opt/elysia/elysia/api/routes/db.py`
   - Add the import statement
   - Add `@recoverable_endpoint` decorator at line 13
   - Save the file

### Step 3: Testing Agent
1. Create test directory: `mkdir -p /opt/elysia/tests/api/middleware/`
2. Create test file: `/opt/elysia/tests/api/middleware/test_recovery.py`
3. Run unit tests: `pytest tests/api/middleware/test_recovery.py -v`
4. Test missing user scenario manually:
   ```bash
   # Start the API server
   elysia start
   
   # Test missing user returns 401
   curl -X GET http://localhost:8000/api/user/config/nonexistent_user
   # Expected: {"detail": "Session not initialized"} with status 401
   
   # Verify no internal paths in response
   curl -X POST http://localhost:8000/api/init/user/fake_user
   # Should NOT contain "ELYSIACTL_CONFIG" or collection IDs
   ```

## Testing

### Unit Test Coverage
Create `/opt/elysia/tests/api/middleware/test_recovery.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from elysia.api.middleware.recovery import recoverable_endpoint, extract_resource_name

@pytest.mark.asyncio
async def test_recoverable_endpoint_user_not_found():
    """Test that user not found returns 401."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("User 'abc123' not found in collection ELYSIACTL_CONFIG_xyz")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session not initialized"

@pytest.mark.asyncio
async def test_recoverable_endpoint_collection_not_found():
    """Test that collection not found returns 404."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("Collection 'MyCollection' not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 404
    assert "MyCollection" in exc_info.value.detail

@pytest.mark.asyncio
async def test_recoverable_endpoint_key_error():
    """Test that KeyError returns 422."""
    @recoverable_endpoint
    async def test_func():
        d = {}
        return d["missing_key"]
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 422
    assert "Missing required field" in exc_info.value.detail

@pytest.mark.asyncio
async def test_recoverable_endpoint_connection_error():
    """Test that ConnectionError returns 503."""
    @recoverable_endpoint
    async def test_func():
        raise ConnectionError("Cannot connect to Weaviate")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Database temporarily unavailable"

@pytest.mark.asyncio
async def test_recoverable_endpoint_generic_error():
    """Test that generic exceptions return 500."""
    @recoverable_endpoint
    async def test_func():
        raise RuntimeError("Something went wrong")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Internal server error"

@pytest.mark.asyncio
async def test_recoverable_endpoint_logs_exception():
    """Test that exceptions are logged."""
    with patch('elysia.api.middleware.recovery.logger') as mock_logger:
        @recoverable_endpoint
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(HTTPException):
            await test_func()
        
        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args[0][0]
        assert "ValueError" in call_args
        assert "test_func" in call_args

def test_extract_resource_name():
    """Test resource name extraction."""
    assert extract_resource_name("Collection 'TestCollection' not found") == "TestCollection"
    assert extract_resource_name('User "user123" not found') == "user123"
    assert extract_resource_name("No quotes here") == ""
```

### Manual Testing Checklist
- [ ] Start API server: `elysia start`
- [ ] Test each endpoint with missing user
- [ ] Verify 401 status and clean message
- [ ] Check server logs contain full exception with collection names
- [ ] Confirm no collection IDs or internal paths in client responses
- [ ] Test with valid users to ensure normal operation unaffected
- [ ] Run existing test suite: `pytest --ignore=tests/requires_env`

## Success Criteria
- [ ] Recovery middleware file created with decorator implementation
- [ ] All 8 identified endpoints have @recoverable_endpoint decorator
- [ ] Missing user errors return HTTP 401 with "Session not initialized"
- [ ] Missing collection errors return HTTP 404 with collection name
- [ ] KeyError returns HTTP 422 with field name
- [ ] ConnectionError returns HTTP 503 with appropriate message
- [ ] No internal collection names (ELYSIACTL_CONFIG_xxx) leak to clients
- [ ] Full exception details logged server-side for debugging
- [ ] All existing tests pass
- [ ] New recovery tests pass
- [ ] Manual testing confirms expected behavior

## Endpoints Covered

| Route | Function | File:Line | Error Mapping |
|-------|----------|-----------|---------------|
| POST /api/init/user/{user_id} | initialise_user | init.py:51 | User not found → 401 |
| GET /api/user/config/{user_id} | get_current_user_config | user_config.py:95 | User not found → 401 |
| POST /api/user/config/{user_id}/new | new_user_config | user_config.py:223 | User not found → 401 |
| POST /api/user/config/{user_id}/{config_id} | save_config_user | user_config.py:314 | User not found → 401 |
| DELETE /api/user/config/{user_id}/{config_id} | delete_config | user_config.py:731 | User/Config not found → 401/404 |
| GET /api/user/config/{user_id}/list | list_configs | user_config.py:761 | User not found → 401 |
| GET /api/collections/{user_id}/list | collections_list | collections.py:66 | User not found → 401 |
| GET /api/db/{user_id}/saved_trees | get_saved_trees | db.py:13 | User not found → 401 |

## Phase Completion
This phase implements ADR-001 for critical user-related endpoints, establishing the pattern for gradual migration of remaining endpoints in future phases. The decorator provides a clean separation between internal errors and client-facing messages while preserving full debugging information server-side.