# Phase 1: ClientManager Connection Fix

## Objective
Fix the critical "Invalid port: '8080:443'" error that blocks all local Weaviate connections by correcting the logic flow in ClientManager.

## Problem Summary
ClientManager's `get_client()` and `get_async_client()` methods check for API key even when using local Weaviate, causing the code to fall through to cloud connection logic which fails for local URLs.

## Implementation Details

### File: `/opt/elysia/elysia/util/client.py`

### Change 1: Fix `get_client()` method
**Location:** Line 321
**Current Code:**
```python
if self.wcd_url is None or self.wcd_api_key is None:
    raise ValueError("WCD_URL and WCD_API_KEY must be set")
```

**New Code:**
```python
if not self.weaviate_is_local and (self.wcd_url is None or self.wcd_api_key is None):
    raise ValueError("WCD_URL and WCD_API_KEY must be set")
```

### Change 2: Fix `get_async_client()` method
**Location:** Line 355
**Current Code:**
```python
if self.wcd_url is None or self.wcd_api_key is None:
    raise ValueError("WCD_URL and WCD_API_KEY must be set")
```

**New Code:**
```python
if not self.weaviate_is_local and (self.wcd_url is None or self.wcd_api_key is None):
    raise ValueError("WCD_URL and WCD_API_KEY must be set")
```

## Agent Workflow

### Step 1: Implementation Agent
1. Open `/opt/elysia/elysia/util/client.py`
2. Navigate to line 321
3. Add `not self.weaviate_is_local and` to the condition
4. Navigate to line 355
5. Add `not self.weaviate_is_local and` to the condition
6. Save the file

### Step 2: Validation Agent
1. Verify Weaviate is running: `curl http://localhost:8080/v1/schema`
2. Run basic tests: `pytest tests/no_reqs/test_client.py -v` (if exists)
3. Test the API connection:
   ```python
   from elysia.util.client import ClientManager
   cm = ClientManager(
       wcd_url="http://localhost:8080",
       weaviate_is_local=True,
       wcd_api_key=""  # Empty API key should work now
   )
   client = cm.get_client()
   print("Connection successful!")
   ```

### Step 3: Integration Test Agent
1. Start Elysia: `elysia start`
2. Navigate to settings in UI
3. Configure with:
   - URL: `http://localhost:8080`
   - Check "Local Mode"
   - Leave API Key empty
4. Save configuration
5. Verify no "Invalid port: '8080:443'" error
6. Verify collections list loads

## Success Criteria
- [ ] No "Invalid port: '8080:443'" error when saving local configuration
- [ ] Local Weaviate connection works without API key
- [ ] Existing cloud connections still work (regression test)
- [ ] Tests pass: `pytest --ignore=tests/requires_env`

## Rollback Plan
If issues occur, revert the two line changes:
1. Remove `not self.weaviate_is_local and` from line 321
2. Remove `not self.weaviate_is_local and` from line 355

## Notes
- This is a minimal, focused fix following CLAUDE.md guidelines
- The fix preserves all existing functionality for cloud connections
- No frontend changes required
- Changes are easily testable and reversible