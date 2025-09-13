# Phase 6: System Namespace Protection Implementation

## Objective
Implement validation to prevent users from creating collections with the reserved `ELYSIACTL_` prefix, as defined in ADR-002.

## Problem Summary
Users can currently create collections starting with `ELYSIACTL_`, which could interfere with system collections, create security vulnerabilities, and cause confusion about collection ownership. ADR-002 establishes this as a reserved namespace that must be protected.

## Implementation Details

### File: `/opt/elysia/elysia/api/utils/validation.py` (NEW)

Create a validation utility module:

```python
"""Validation utilities for API operations."""
from typing import List
from fastapi import HTTPException

# Reserved prefixes that users cannot use for collection names
RESERVED_PREFIXES: List[str] = ["ELYSIACTL_", "SYSTEM_"]

def validate_collection_name(name: str) -> None:
    """
    Validate that a collection name doesn't use reserved namespaces.
    
    Args:
        name: The proposed collection name
        
    Raises:
        HTTPException: If the name uses a reserved prefix
    """
    if not name:
        raise HTTPException(400, "Collection name cannot be empty")
    
    name_upper = name.upper()
    
    for prefix in RESERVED_PREFIXES:
        if name_upper.startswith(prefix.upper()):
            raise HTTPException(
                400,
                f"Collection names starting with '{prefix}' are reserved for system use. "
                "Please choose a different name for your collection."
            )
    
    # Additional validation could go here (e.g., length, special characters)
    if len(name) > 100:
        raise HTTPException(400, "Collection name must be 100 characters or less")
```

### File: `/opt/elysia/elysia/preprocessing/collection.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.utils.validation import validate_collection_name
```

**Change 2: Add validation to preprocess_async**
**Location:** Line 367 (at the start of the function)
**Current Code:**
```python
async def preprocess_async(
    collection_name: str,
```

**After Current Code, Add:**
```python
    # Validate collection name doesn't use reserved namespace
    try:
        validate_collection_name(collection_name)
    except HTTPException as e:
        raise ValueError(e.detail)
```

**Change 3: Add validation to preprocess (sync version)**
**Location:** Line ~800 (find the sync preprocess function)
**Add the same validation at the start of the function**

### File: `/opt/elysia/elysia/api/routes/init.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.utils.validation import validate_collection_name
```

**Change 2: If there's a collection initialization endpoint**
**Note:** Add validation before any collection creation
```python
# In any endpoint that accepts collection names
validate_collection_name(collection_name)
```

### File: `/opt/elysia/elysia/tools/retrieval/chunk.py`

**Change 1: Add import**
**Location:** Line 1 (with other imports)
```python
from elysia.api.utils.validation import validate_collection_name
```

**Change 2: Add validation before creating chunked collection**
**Location:** Line 268 (before client.collections.create)
**Before:**
```python
return await client.collections.create(
```

**Add Before:**
```python
# Note: ELYSIACTL_CHUNKED_ collections are system collections, so skip validation
# validate_collection_name would reject these
# This is intentional - only system code can create ELYSIACTL_ collections
```

### System Collection Creation Points (NO CHANGES NEEDED)

These locations create system collections and should NOT have validation:
- `/opt/elysia/elysia/api/routes/user_config.py:490` - Creates ELYSIACTL_CONFIG
- `/opt/elysia/elysia/api/utils/feedback.py:19` - Creates ELYSIACTL_FEEDBACK
- `/opt/elysia/elysia/tree/tree.py:1995` - Creates system collections
- `/opt/elysia/elysia/preprocessing/collection.py:640` - Creates ELYSIACTL_METADATA

## Agent Workflow

### Step 1: Implementation Agent
1. Create the new file `/opt/elysia/elysia/api/utils/validation.py`
2. Copy the validation utility code
3. Save the file

### Step 2: Integration Agent
1. Open `/opt/elysia/elysia/preprocessing/collection.py`
   - Add the import statement
   - Add validation to `preprocess_async` function (after line 367)
   - Find and add validation to `preprocess` sync function
   - Save the file

2. Check for user-facing collection creation endpoints
   - Search for endpoints that accept collection names from users
   - Add validation before processing

### Step 3: Testing Agent
1. Create test file: `/opt/elysia/tests/api/utils/test_validation.py`
2. Test validation logic:
   - Test rejection of ELYSIACTL_ prefix (case-insensitive)
   - Test rejection of SYSTEM_ prefix
   - Test acceptance of valid names
   - Test friendly error messages

## Testing

### Unit Test Coverage
Create `/opt/elysia/tests/api/utils/test_validation.py`:

```python
import pytest
from fastapi import HTTPException
from elysia.api.utils.validation import validate_collection_name

def test_validate_collection_name_rejects_elysia_prefix():
    """Test that ELYSIACTL_ prefix is rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_collection_name("ELYSIACTL_test")
    assert exc.value.status_code == 400
    assert "reserved for system use" in exc.value.detail

def test_validate_collection_name_case_insensitive():
    """Test that validation is case-insensitive."""
    test_cases = ["elysia_test", "Elysia_Test", "ELYSIACTL_TEST", "ElYsIa_test"]
    for name in test_cases:
        with pytest.raises(HTTPException) as exc:
            validate_collection_name(name)
        assert exc.value.status_code == 400

def test_validate_collection_name_rejects_system_prefix():
    """Test that SYSTEM_ prefix is rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_collection_name("SYSTEM_test")
    assert exc.value.status_code == 400
    assert "reserved for system use" in exc.value.detail

def test_validate_collection_name_accepts_valid_names():
    """Test that valid names are accepted."""
    valid_names = [
        "MyCollection",
        "user_data",
        "PRODUCTS",
        "elysia",  # Just "elysia" without underscore is OK
        "my_elysia_collection",  # ELYSIA in middle is OK
        "collection_ELYSIA"  # ELYSIA at end is OK
    ]
    for name in valid_names:
        validate_collection_name(name)  # Should not raise

def test_validate_collection_name_empty():
    """Test that empty names are rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_collection_name("")
    assert exc.value.status_code == 400
    assert "cannot be empty" in exc.value.detail

def test_validate_collection_name_too_long():
    """Test that overly long names are rejected."""
    long_name = "a" * 101
    with pytest.raises(HTTPException) as exc:
        validate_collection_name(long_name)
    assert exc.value.status_code == 400
    assert "100 characters or less" in exc.value.detail
```

### Manual Testing Checklist
- [ ] Try to preprocess a collection named "ELYSIACTL_test"
- [ ] Verify error message is user-friendly
- [ ] Try variations: "elysia_test", "Elysia_test"
- [ ] Verify system can still create ELYSIACTL_ collections
- [ ] Test that "MyElysia" and "elysia" work fine
- [ ] Check API returns 400 with clear message

### Integration Test
```python
@pytest.mark.asyncio
async def test_preprocess_rejects_reserved_namespace():
    """Test that preprocessing rejects ELYSIACTL_ collections."""
    from elysia.preprocessing.collection import preprocess_async
    
    with pytest.raises(ValueError) as exc:
        await preprocess_async(
            collection_name="ELYSIACTL_user_collection",
            client_manager=mock_client_manager
        )
    
    assert "reserved for system use" in str(exc.value)
```

## Success Criteria
- [ ] Validation utility created with namespace checking
- [ ] Preprocessing functions validate collection names
- [ ] User-facing endpoints validate collection names
- [ ] Case-insensitive validation works correctly
- [ ] System can still create ELYSIACTL_ collections
- [ ] Clear, friendly error messages for users
- [ ] All tests pass
- [ ] No regressions in existing functionality

## Error Messages

### User Attempts to Create Reserved Collection
**Request:** `preprocess("ELYSIACTL_MyData")`
**Response:** 
```
400 Bad Request
{
    "detail": "Collection names starting with 'ELYSIACTL_' are reserved for system use. Please choose a different name for your collection."
}
```

### Case Variations Also Blocked
**Request:** `preprocess("elysia_data")` or `preprocess("Elysia_Data")`
**Response:** Same 400 error with friendly message

## Implementation Notes

1. **Case-Insensitive Matching**: Always convert to uppercase for comparison
2. **System Bypass**: System code that creates ELYSIACTL_ collections should NOT call validation
3. **Future Prefixes**: RESERVED_PREFIXES list allows easy addition of new reserved namespaces
4. **Friendly Messages**: Always explain WHY the name is rejected and suggest action
5. **Backward Compatibility**: Existing ELYSIACTL_ system collections continue to work

## Phase Completion
This phase establishes namespace protection as defined in ADR-002, preventing user-system collection conflicts while maintaining clear, helpful error messages for users who accidentally use reserved prefixes.