# ADR-002: System Collection Namespace Convention

## Status
**PROPOSED** - 2025-09-01

## Context

### Current State
The Elysia system creates and manages several internal collections in Weaviate:
- `ELYSIA_CONFIG_[hash]` - User configuration storage
- `ELYSIA_METADATA__` - Collection metadata for preprocessing
- `ELYSIA_FEEDBACK_[hash]` - User feedback storage
- `ELYSIA_CHUNKED_[collection]` - Preprocessed data chunks

These collections contain system-critical data and implementation details that should not be exposed to end users.

### Problem Statement
1. **Security Risk**: Internal collection names were leaking through error messages, exposing implementation details like "Collection 'ELYSIA_CONFIG_1169a452fe5da387b9c7ce2e6dc4cf8b' not found"
2. **Namespace Collision**: No mechanism prevents users from creating collections that start with `ELYSIA_`, which could:
   - Interfere with system operations
   - Create security vulnerabilities
   - Cause confusion about collection ownership
   - Break system assumptions about collection purposes
3. **Implicit Convention**: The `ELYSIA_` prefix convention exists but isn't formally documented or enforced

### Requirements
1. Establish a clear, documented convention for system collections
2. Prevent namespace collisions between user and system collections
3. Ensure internal collection names don't leak to clients
4. Provide clear feedback when users attempt to use reserved namespaces

## Decision

### 1. Reserved Namespace Convention
**All collections with names starting with `ELYSIA_` are reserved for system use.**

This establishes `ELYSIA_` as a protected namespace with special handling throughout the system:
- **Creation**: Only system components can create `ELYSIA_` prefixed collections
- **Visibility**: These collections are filtered from user-facing APIs and error messages
- **Access**: Direct manipulation by users is prohibited
- **Documentation**: The convention is explicitly documented and enforced

### 2. Error Message Filtering
The `@recoverable_endpoint` decorator (from ADR-001) specifically filters `ELYSIA_` prefixed collection names:

```python
if name and name.startswith("ELYSIA_"):
    raise HTTPException(404, "Collection not found")  # Generic message
else:
    raise HTTPException(404, f"Collection {name} not found")  # Include name
```

### 3. Collection Creation Validation
When users attempt to create collections through the API:

```python
def validate_collection_name(name: str) -> None:
    """Validate that collection name doesn't use reserved namespace."""
    if name.upper().startswith("ELYSIA_"):
        raise ValueError(
            "Collection names starting with 'ELYSIA_' are reserved for system use. "
            "Please choose a different name."
        )
```

### 4. System Collection Types

| Prefix Pattern | Purpose | Example |
|---------------|---------|---------|
| `ELYSIA_CONFIG_` | User configuration storage | `ELYSIA_CONFIG_1169a452` |
| `ELYSIA_METADATA_` | Collection metadata | `ELYSIA_METADATA__` |
| `ELYSIA_FEEDBACK_` | User feedback storage | `ELYSIA_FEEDBACK_abc123` |
| `ELYSIA_CHUNKED_` | Preprocessed data | `ELYSIA_CHUNKED_Products` |

## Consequences

### Positive
- **Security**: Internal implementation details are never exposed to clients
- **Clarity**: Clear separation between system and user collections
- **Maintainability**: System can safely assume `ELYSIA_` collections have specific schemas
- **Safety**: No risk of users accidentally breaking system collections
- **Future-proof**: New system collections can be added without collision risk

### Negative
- **Breaking Change**: If any users have existing collections starting with `ELYSIA_`, they'll need to rename them
- **Restriction**: Users lose the ability to use `ELYSIA` in their collection names
- **Enforcement Overhead**: Every collection creation point needs validation

### Neutral
- **Documentation**: Requires clear communication to users about reserved namespaces
- **Migration**: Existing systems may need updates to comply with validation

## Implementation Notes

### Phase 1: Documentation and Filtering (COMPLETED)
- ✅ Error messages filter `ELYSIA_` prefixed collections (Phase 5)
- ✅ ADR documents the convention

### Phase 2: Active Prevention (PROPOSED)
1. Add validation to collection creation endpoints
2. Update preprocessing to validate collection names
3. Add friendly error messages explaining the restriction
4. Consider case-insensitive matching (ELYSIA_, elysia_, Elysia_)

### Phase 3: Migration Support (FUTURE)
- Tool to detect existing user collections with `ELYSIA_` prefix
- Automated renaming assistance
- Backward compatibility layer if needed

## Alternatives Considered

### 1. Different Prefix
**Option**: Use `__SYSTEM_` or `_INTERNAL_` instead of `ELYSIA_`
**Rejected**: `ELYSIA_` is already established throughout the codebase

### 2. UUID-Only Approach
**Option**: Use only UUIDs for system collections (no prefix)
**Rejected**: Loses human readability and makes debugging harder

### 3. Separate Database/Schema
**Option**: Store system collections in a separate Weaviate instance or schema
**Rejected**: Adds complexity and deployment overhead

### 4. No Restriction
**Option**: Allow users to create `ELYSIA_` collections but document the convention
**Rejected**: Too risky for security and system integrity

## Related

- **ADR-001**: Establishes error handling that filters these collection names
- **Phase 5**: Implements the filtering in `@recoverable_endpoint` decorator
- **Frontend Guide**: Documents that internal names are not exposed

## Example Implementation

### Collection Creation Validation
```python
# elysia/api/routes/collections.py
from fastapi import HTTPException

RESERVED_PREFIXES = ["ELYSIA_", "SYSTEM_"]  # Future-proof for other prefixes

def validate_collection_name(name: str) -> None:
    """Ensure collection name doesn't use reserved namespaces."""
    name_upper = name.upper()
    
    for prefix in RESERVED_PREFIXES:
        if name_upper.startswith(prefix):
            raise HTTPException(
                400,
                f"Collection names starting with '{prefix}' are reserved for system use. "
                "Please choose a different name for your collection."
            )
```

### Preprocessing Validation
```python
# elysia/preprocessing/collection.py
async def preprocess(collection_name: str, ...) -> None:
    """Preprocess a collection for use with Elysia."""
    # Validate name before processing
    if collection_name.upper().startswith("ELYSIA_"):
        raise ValueError(
            f"Cannot preprocess '{collection_name}': "
            "Collections starting with 'ELYSIA_' are reserved for system use."
        )
    
    # Continue with preprocessing...
```

## Decision Outcome

The `ELYSIA_` namespace is formally reserved for system use. This convention:
1. **MUST** be enforced at collection creation points
2. **MUST** be filtered from client-facing error messages
3. **SHOULD** be clearly documented in API responses
4. **SHOULD** use case-insensitive matching for maximum safety

This decision prioritizes security and system integrity over user flexibility, which aligns with Elysia's goal of being a robust, production-ready system.