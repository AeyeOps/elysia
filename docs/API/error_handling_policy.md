# API Error Handling Policy

## Purpose
This document defines the standard error handling pattern for all Elysia API endpoints to ensure consistent, informative, and recoverable error responses.

## Architectural Pattern: Recoverable Endpoints

### Core Principle
Transform internal exceptions into proper HTTP responses with standardized error messages that:
1. Hide implementation details from clients
2. Provide actionable information
3. Use appropriate HTTP status codes
4. Log full details for debugging

### Implementation: The `@recoverable_endpoint` Decorator

All API endpoints should use the `@recoverable_endpoint` decorator to standardize error handling:

```python
from elysia.api.middleware.recovery import recoverable_endpoint
from fastapi import APIRouter

router = APIRouter()

@router.post("/your_endpoint")
@recoverable_endpoint
async def your_endpoint_function(...):
    # Your endpoint logic here
    pass
```

### Error Mapping Standards

The decorator maps exceptions to HTTP responses following these patterns:

| Exception Type | Condition | HTTP Status | Client Message |
|---------------|-----------|-------------|----------------|
| `ValueError` | "user.*not found" | 401 | "Session not initialized" |
| `ValueError` | "collection.*not found" | 404 | "Collection {name} not found" |
| `ValueError` | Other | 400 | Original message |
| `KeyError` | Any | 422 | "Missing required field: {key}" |
| `ConnectionError` | Weaviate-related | 503 | "Database temporarily unavailable" |
| `Exception` | Unknown | 500 | "Internal server error" |

### Logging Requirements

- All exceptions MUST be logged with `logger.exception()` before transformation
- Log entries should include the endpoint name and operation context
- Client messages should never contain stack traces or internal paths

### Response Format

All error responses follow the FastAPI/OpenAPI standard:

```json
{
    "detail": "Human-readable error message"
}
```

For validation errors (422):
```json
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

### Migration Strategy

1. **Phase 1**: Apply to critical endpoints that handle user sessions
   - `/init/user/{user_id}`
   - `/user/config/{user_id}/save`
   - `/collections/{user_id}/list`

2. **Phase 2**: Apply to data manipulation endpoints
   - `/process_collection`
   - `/query`
   - `/feedback`

3. **Phase 3**: Apply to all remaining endpoints

### Example Implementation

```python
# elysia/api/middleware/recovery.py
import logging
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
    import re
    match = re.search(r"['\"]([^'\"]+)['\"]", error_message)
    return match.group(1) if match else None
```

### Testing Requirements

Endpoints using `@recoverable_endpoint` should have tests that verify:
1. Correct status codes for different exception types
2. Client messages don't leak sensitive information
3. Logging captures full exception details
4. Recovery actions are suggested when appropriate

### Review Checklist

When reviewing code with this pattern:
- [ ] Decorator is applied to all new endpoints
- [ ] No raw exception messages leak to clients
- [ ] Appropriate HTTP status codes are used
- [ ] Logging includes context about the operation
- [ ] Client messages are actionable
- [ ] Tests cover error scenarios

## Benefits

1. **Consistency**: All errors follow the same format
2. **Security**: Internal details never leak to clients
3. **Debuggability**: Full errors are logged server-side
4. **User Experience**: Clear, actionable error messages
5. **Maintainability**: Centralized error handling logic
6. **Gradual Adoption**: Can be applied incrementally

## Future Enhancements

As patterns emerge, the decorator can be extended with:
- Rate limiting detection and 429 responses
- Retry-After headers for temporary failures
- Correlation IDs for tracking errors across services
- Metrics collection for error monitoring