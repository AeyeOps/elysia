# Phase 5: Missing User Recovery Bug Fix

## Objective
Fix the critical "user not found" bug where raw ValueError exceptions leak to clients instead of returning proper HTTP 401 responses with the "Session not initialized" message, as defined in ADR-001.

## Problem Summary
The Elysia API endpoints currently throw raw ValueError exceptions when users are not found, exposing internal implementation details to clients. According to ADR-001, these should be mapped to HTTP 401 responses with the standardized message "Session not initialized". The @recoverable_endpoint decorator pattern needs to be implemented and applied to user-related endpoints.

## Implementation Details

### File: `/opt/elysia/elysia/api/middleware/recovery.py`

### Change 1: Create the @recoverable_endpoint decorator
**Location:** New file
**Current Code:**
```python
# File does not exist
```

**New Code:**
```python
import logging
import re
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def recoverable_endpoint(func):
    """
    Decorator that transforms exceptions into proper HTTP responses.
    
    This decorator should be applied to all API endpoints to ensure
    consistent error handling and client-friendly error messages.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            error_str = str(e).lower()
            if "not found" in error_str:
                if "user" in error_str:
                    logger.exception(f"User session error in {func.__name__}")
                    raise HTTPException(401, "Session not initialized")
                elif "collection" in error_str:
                    logger.exception(f"Collection error in {func.__name__}")
                    # Extract collection name if possible
                    name = extract_resource_name(str(e))
                    raise HTTPException(404, f"Collection {name} not found" if name else "Collection not found")
            logger.exception(f"Validation error in {func.__name__}")
            raise HTTPException(400, str(e))
        except KeyError as e:
            logger.exception(f"Missing field in {func.__name__}")
            raise HTTPException(422, f"Missing required field: {e}")
        except ConnectionError as e:
            if "weaviate" in str(e).lower():
                logger.exception(f"Weaviate connection error in {func.__name__}")
                raise HTTPException(503, "Database temporarily unavailable")
            logger.exception(f"Connection error in {func.__name__}")
            raise HTTPException(503, "Service temporarily unavailable")
        except Exception as e:
            logger.exception(f"Unhandled error in {func.__name__}")
            raise HTTPException(500, "Internal server error")
    
    return wrapper

def extract_resource_name(error_message: str) -> str | None:
    """Extract resource name from error message if possible."""
    # Implementation would parse common error patterns
    # Example: "Collection 'MY_COLLECTION' not found" -> "MY_COLLECTION"
    match = re.search(r"['\"]([^'\"]+)['\"]", error_message)
    return match.group(1) if match else None
```

### File: `/opt/elysia/elysia/api/routes/init.py`

### Change 2: Apply @recoverable_endpoint to initialise_user
**Location:** Line 51
**Current Code:**
```python
@router.post("/user/{user_id}")
async def initialise_user(
    user_id: str, user_manager: UserManager = Depends(get_user_manager)
):
```

**New Code:**
```python
@router.post("/user/{user_id}")
@recoverable_endpoint
async def initialise_user(
    user_id: str, user_manager: UserManager = Depends(get_user_manager)
):
```

### Change 3: Apply @recoverable_endpoint to initialise_tree
**Location:** Line 139
**Current Code:**
```python
@router.post("/tree/{user_id}/{conversation_id}")
async def initialise_tree(
    user_id: str,
    conversation_id: str,
    data: InitialiseTreeData,
    user_manager: UserManager = Depends(get_user_manager),
):
```

**New Code:**
```python
@router.post("/tree/{user_id}/{conversation_id}")
@recoverable_endpoint
async def initialise_tree(
    user_id: str,
    conversation_id: str,
    data: InitialiseTreeData,
    user_manager: UserManager = Depends(get_user_manager),
):
```

### Change 4: Add import statement
**Location:** Line 1
**Current Code:**
```python
from fastapi import APIRouter, Depends
```

**New Code:**
```python
from fastapi import APIRouter, Depends
from elysia.api.middleware.recovery import recoverable_endpoint
```

### File: `/opt/elysia/elysia/api/routes/user_config.py`

### Change 5: Apply @recoverable_endpoint to get_current_user_config
**Location:** Line 95
**Current Code:**
```python
@router.get("/{user_id}")
async def get_current_user_config(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
```

**New Code:**
```python
@router.get("/{user_id}")
@recoverable_endpoint
async def get_current_user_config(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
```

### Change 6: Apply @recoverable_endpoint to save_config_user
**Location:** Line 314
**Current Code:**
```python
@router.post("/{user_id}/{config_id}")
async def save_config_user(
    user_id: str,
    config_id: str,
    data: SaveConfigUserData,
    user_manager: UserManager = Depends(get_user_manager),
):
```

**New Code:**
```python
@router.post("/{user_id}/{config_id}")
@recoverable_endpoint
async def save_config_user(
    user_id: str,
    config_id: str,
    data: SaveConfigUserData,
    user_manager: UserManager = Depends(get_user_manager),
):
```

### Change 7: Apply @recoverable_endpoint to list_configs
**Location:** Line 761
**Current Code:**
```python
@router.get("/{user_id}/list")
async def list_configs(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
```

**New Code:**
```python
@router.get("/{user_id}/list")
@recoverable_endpoint
async def list_configs(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager),
):
```

### Change 8: Add import statement to user_config.py
**Location:** Line 6
**Current Code:**
```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
```

**New Code:**
```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from elysia.api.middleware.recovery import recoverable_endpoint
```

### File: `/opt/elysia/elysia/api/routes/collections.py`

### Change 9: Apply @recoverable_endpoint to collections_list
**Location:** Line 66
**Current Code:**
```python
@router.get("/{user_id}/list")
async def collections_list(
    user_id: str, user_manager: UserManager = Depends(get_user_manager)
):
```

**New Code:**
```python
@router.get("/{user_id}/list")
@recoverable_endpoint
async def collections_list(
    user_id: str, user_manager: UserManager = Depends(get_user_manager)
):
```

### Change 10: Add import statement to collections.py
**Location:** Line 1
**Current Code:**
```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
```

**New Code:**
```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from elysia.api.middleware.recovery import recoverable_endpoint
```

## Agent Workflow

### Step 1: Implementation Agent
1. Create `/opt/elysia/elysia/api/middleware/recovery.py` with the @recoverable_endpoint decorator
2. Open `/opt/elysia/elysia/api/routes/init.py`
3. Add import: `from elysia.api.middleware.recovery import recoverable_endpoint`
4. Apply `@recoverable_endpoint` decorator to `initialise_user` at line 51
5. Apply `@recoverable_endpoint` decorator to `initialise_tree` at line 139
6. Open `/opt/elysia/elysia/api/routes/user_config.py`
7. Add import: `from elysia.api.middleware.recovery import recoverable_endpoint`
8. Apply `@recoverable_endpoint` decorator to `get_current_user_config` at line 95
9. Apply `@recoverable_endpoint` decorator to `save_config_user` at line 314
10. Apply `@recoverable_endpoint` decorator to `list_configs` at line 761
11. Open `/opt/elysia/elysia/api/routes/collections.py`
12. Add import: `from elysia.api.middleware.recovery import recoverable_endpoint`
13. Apply `@recoverable_endpoint` decorator to `collections_list` at line 66

### Step 2: Validation Agent
1. Run tests to ensure no regressions: `pytest --ignore=tests/requires_env --tb=short -v`
2. Test user not found scenario:
   ```python
   import requests
   # Try to access config for non-existent user
   response = requests.get("http://localhost:8000/api/user_config/nonexistent_user")
   assert response.status_code == 401
   assert response.json()["detail"] == "Session not initialized"
   ```
3. Test existing functionality still works with valid users
4. Verify exception logging occurs in server logs

### Step 3: Integration Test Agent
1. Start Elysia: `elysia start`
2. Test missing user scenarios:
   - Try to access `/api/user_config/fake_user` - should return 401 with "Session not initialized"
   - Try to access `/api/collections/fake_user/list` - should return 401 with "Session not initialized"
   - Try to post to `/api/init/user/fake_user` then access user config - should work normally
3. Verify proper error responses in browser developer tools
4. Check server logs contain full exception details for debugging

## Testing

Create test cases that verify:
1. **User Not Found**: Endpoints return 401 with "Session not initialized" message
2. **Collection Not Found**: Related endpoints return 404 with collection-specific messages
3. **Exception Logging**: Full exception details are logged server-side with function context
4. **Existing Functionality**: Valid user operations work as expected
5. **Error Message Security**: No internal paths or implementation details leak to clients

## Success Criteria
- [ ] @recoverable_endpoint decorator created and functional
- [ ] All user-related endpoints return proper 401 responses for missing users
- [ ] No raw ValueError exceptions exposed to clients
- [ ] Exception details logged server-side for debugging
- [ ] Client receives actionable "Session not initialized" message
- [ ] Tests pass: `pytest --ignore=tests/requires_env`
- [ ] No regression in existing user flows

## Rollback Plan
If issues occur, remove the following:
1. Delete `/opt/elysia/elysia/api/middleware/recovery.py`
2. Remove `@recoverable_endpoint` decorators from all modified endpoints
3. Remove import statements for `recoverable_endpoint`
4. Endpoints will revert to previous exception handling behavior

## Notes
- This implements the architectural pattern defined in ADR-001
- Only applies to Phase 1 critical endpoints as specified in the ADR migration plan
- Maintains backward compatibility with existing error handling middleware
- Follows CLAUDE.md principle of preferring editing over creating new files where possible
- Error responses follow FastAPI/OpenAPI standard format