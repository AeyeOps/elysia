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
                # Filter out internal ELYSIA_ collection names
                if name and name.startswith("ELYSIA_"):
                    name = ""
                raise HTTPException(404, f"Collection {name} not found" if name else "Collection not found")
            
            raise HTTPException(400, str(e))
            
        except KeyError as e:
            logger.exception(f"KeyError in {func.__name__}: {e}")
            raise HTTPException(422, f"Missing required field: {str(e).strip('\"\'')}")
            
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