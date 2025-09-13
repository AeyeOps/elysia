# ADR-001: Recoverable Endpoint Error Handling

## Status
**PROPOSED** - 2025-09-01

## Context

### Current State
- API endpoints throw raw exceptions to clients
- Stack traces and internal paths leak in error messages
- No consistent error format across endpoints
- Debugging information lost when exceptions are caught
- Frontend cannot reliably parse error responses

### Problem Statement
```python
# Current problematic pattern
@router.post("/endpoint")
async def endpoint(data: dict):
    user = get_user(data["user_id"])  # Throws ValueError with internal details
    # Client receives: "User with ID 'abc123' not found in collection 'ELYSIACTL_CONFIG_1169a452fe5da387b9c7ce2e6dc4cf8b'"
```

### Requirements
1. Hide implementation details from clients
2. Provide actionable error messages
3. Use standard HTTP status codes
4. Preserve debugging information server-side
5. Enable gradual migration

## Decision

### Architecture Pattern: @recoverable_endpoint Decorator

```python
from elysia.api.middleware.recovery import recoverable_endpoint
from fastapi import APIRouter

router = APIRouter()

@router.post("/your_endpoint")
@recoverable_endpoint
async def your_endpoint_function(...):
    # Endpoint logic
    pass
```

### Exception Mapping Rules

```python
EXCEPTION_MAPPINGS = {
    "ValueError": [
        {"pattern": r"user.*not found", "status": 401, "message": "Session not initialized"},
        {"pattern": r"collection.*not found", "status": 404, "message": "Collection {name} not found"},
        {"pattern": r".*", "status": 400, "message": "{original}"}
    ],
    "KeyError": [
        {"pattern": r".*", "status": 422, "message": "Missing required field: {key}"}
    ],
    "ConnectionError": [
        {"pattern": r"weaviate", "status": 503, "message": "Database temporarily unavailable"},
        {"pattern": r".*", "status": 503, "message": "Service temporarily unavailable"}
    ],
    "Exception": [
        {"pattern": r".*", "status": 500, "message": "Internal server error"}
    ]
}
```

### Response Format

```json
// Standard error response (400, 401, 403, 404, 500, 503)
{
    "detail": "Human-readable error message"
}

// Validation error response (422)
{
    "detail": [
        {
            "loc": ["body", "field_name"],
            "msg": "Error message",
            "type": "error_type"
        }
    ]
}
```

## Implementation

### Core Decorator Code

```python
# elysia/api/middleware/recovery.py
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
            
            if "not found" in error_str:
                if "user" in error_str:
                    raise HTTPException(401, "Session not initialized")
                elif "collection" in error_str:
                    name = extract_resource_name(str(e))
                    raise HTTPException(404, f"Collection {name} not found" if name else "Collection not found")
            
            raise HTTPException(400, str(e))
            
        except KeyError as e:
            logger.exception(f"KeyError in {func.__name__}: {e}")
            raise HTTPException(422, f"Missing required field: {e}")
            
        except ConnectionError as e:
            logger.exception(f"ConnectionError in {func.__name__}: {e}")
            if "weaviate" in str(e).lower():
                raise HTTPException(503, "Database temporarily unavailable")
            raise HTTPException(503, "Service temporarily unavailable")
            
        except Exception as e:
            logger.exception(f"Unhandled error in {func.__name__}: {e}")
            raise HTTPException(500, "Internal server error")
    
    return wrapper

def extract_resource_name(error_message: str) -> str | None:
    """Extract resource name from error message."""
    match = re.search(r"['\"]([^'\"]+)['\"]", error_message)
    return match.group(1) if match else None
```

### Usage Example

```python
# Before: Raw exceptions leak to client
@router.post("/init/user/{user_id}")
async def init_user(user_id: str):
    user = await get_user(user_id)  # ValueError: User 'abc123' not found
    return {"status": "initialized"}

# After: Clean error responses
@router.post("/init/user/{user_id}")
@recoverable_endpoint
async def init_user(user_id: str):
    user = await get_user(user_id)  # Client receives: {"detail": "Session not initialized"}
    return {"status": "initialized"}
```

## Migration Plan

### Phase 1: Critical User Endpoints
```python
# Priority endpoints to migrate first
PHASE_1_ENDPOINTS = [
    "/init/user/{user_id}",
    "/user/config/{user_id}/save", 
    "/collections/{user_id}/list"
]
```

### Phase 2: Data Manipulation Endpoints
```python
PHASE_2_ENDPOINTS = [
    "/process_collection",
    "/query",
    "/feedback"
]
```

### Phase 3: Remaining Endpoints
```python
# All other endpoints
```

## Testing Requirements

### Unit Test Template
```python
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_recoverable_endpoint_user_not_found():
    """Test that user not found returns 401."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("User 'abc123' not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session not initialized"

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
```

## Consequences

### Positive
- **Security**: No internal details leak to clients
- **Consistency**: All errors follow same format
- **Debuggability**: Full errors logged server-side
- **User Experience**: Clear, actionable error messages
- **Gradual Adoption**: Can be applied incrementally
- **FastAPI Compliance**: Uses standard HTTPException

### Negative
- **Decorator Overhead**: Small performance cost per request
- **Pattern Learning**: Developers must remember to apply decorator
- **Error Pattern Maintenance**: Mapping rules need updates as new patterns emerge

### Neutral
- **Existing Code**: No changes required to existing error-free code
- **Frontend Changes**: Frontend already expects this format

## Alternatives Considered

### 1. Global Exception Handler
```python
@app.exception_handler(Exception)
async def global_handler(request, exc):
    # Handle all exceptions globally
```
**Rejected**: Less granular control, harder to test

### 2. Try-Catch in Each Endpoint
```python
@router.post("/endpoint")
async def endpoint():
    try:
        # logic
    except Exception as e:
        # handle
```
**Rejected**: Repetitive code, inconsistent implementation

### 3. Middleware Approach
```python
@app.middleware("http")
async def error_middleware(request, call_next):
    # Wrap all requests
```
**Rejected**: Too broad, affects non-API routes

## References

- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [OpenAPI Error Response Specification](https://spec.openapis.org/oas/v3.1.0#responses-object)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Review Checklist

- [ ] Decorator applied to endpoint
- [ ] Exceptions logged with context
- [ ] Client messages are actionable
- [ ] HTTP status codes are appropriate
- [ ] Tests cover error scenarios
- [ ] No sensitive data in responses