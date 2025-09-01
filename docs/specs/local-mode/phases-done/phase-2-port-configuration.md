# Phase 2: Port Configuration Fix

## Objective
Replace hardcoded Weaviate ports (8080, 50051) with dynamic configuration values from frontend_config to support custom port configurations.

## Problem Summary
UserManager hardcodes Weaviate ports in 5 locations, preventing users from connecting to Weaviate instances running on non-default ports.

## Implementation Details

### File: `/opt/elysia/elysia/api/services/user.py`

### Required Changes (5 locations)

#### Change 1: `add_user_local()` - First occurrence
**Location:** Lines 337-345
**Current Pattern:**
```python
save_location_client_manager = ClientManager(
    logger=logger,
    wcd_url=wcd_url,
    wcd_api_key=wcd_api_key,
    weaviate_is_local=is_local,
    local_weaviate_port=8080,  # Hardcoded
    local_weaviate_grpc_port=50051,  # Hardcoded
)
```

**New Pattern:**
```python
save_location_client_manager = ClientManager(
    logger=logger,
    wcd_url=wcd_url,
    wcd_api_key=wcd_api_key,
    weaviate_is_local=is_local,
    local_weaviate_port=frontend_config.local_weaviate_port,
    local_weaviate_grpc_port=frontend_config.local_weaviate_grpc_port,
)
```

#### Change 2: `add_user_local()` - Second occurrence
**Location:** Lines 382-389
**Apply:** Same pattern as Change 1

#### Change 3: `get_user_local()` - First occurrence
**Location:** Lines 429-436
**Apply:** Same pattern as Change 1

#### Change 4: `get_user_local()` - Second occurrence
**Location:** Lines 473-480
**Apply:** Same pattern as Change 1

#### Change 5: `update_config()`
**Location:** Lines 524-530
**Apply:** Same pattern as Change 1

## Agent Workflow

### Step 1: Analysis Agent
1. Examine frontend_config structure:
   ```bash
   grep -n "class FrontendConfig" elysia/api/api_types.py
   grep -n "local_weaviate_port\|local_weaviate_grpc_port" elysia/api/api_types.py
   ```
2. Verify frontend_config is available in all 5 contexts
3. Check default values if ports are not set

### Step 2: Implementation Agent
1. Open `/opt/elysia/elysia/api/services/user.py`
2. For each of the 5 locations:
   - Find the ClientManager instantiation
   - Replace `local_weaviate_port=8080` with `local_weaviate_port=frontend_config.local_weaviate_port`
   - Replace `local_weaviate_grpc_port=50051` with `local_weaviate_grpc_port=frontend_config.local_weaviate_grpc_port`
3. Verify all 5 changes are made
4. Save the file

### Step 3: Validation Agent
1. Run unit tests:
   ```bash
   pytest tests/no_reqs/test_user.py -v  # if exists
   pytest --ignore=tests/requires_env
   ```

2. Test with custom ports:
   ```python
   # Start Weaviate on custom ports (9090, 50052)
   # Then test:
   from elysia.api.services.user import UserManager
   from elysia.api.api_types import FrontendConfig
   
   config = FrontendConfig(
       local_weaviate_port=9090,
       local_weaviate_grpc_port=50052,
       # ... other required fields
   )
   # Verify connection works with custom ports
   ```

### Step 4: Integration Test Agent
1. Configure Weaviate to run on custom ports (e.g., 9090, 50052)
2. Start Elysia: `elysia start`
3. Configure in UI with custom port URL: `http://localhost:9090`
4. Save configuration
5. Verify connection works
6. Test operations (list collections, query, etc.)

## Success Criteria
- [ ] All 5 hardcoded port instances replaced
- [ ] Connection works with default ports (8080, 50051)
- [ ] Connection works with custom ports (e.g., 9090, 50052)
- [ ] Frontend config properly passes port values
- [ ] No regression in existing functionality
- [ ] Tests pass: `pytest --ignore=tests/requires_env`

## Edge Cases to Test
1. **Missing port configuration:** Ensure reasonable defaults are used
2. **Invalid port numbers:** Should fail gracefully with clear error
3. **Port conflicts:** When specified port is already in use
4. **Mixed configuration:** Cloud URL with local ports specified

## Rollback Plan
If issues occur:
1. Revert all 5 changes in user.py
2. Return to hardcoded values temporarily
3. Document specific failure for debugging

## Dependencies
- Requires Phase 1 to be completed first (ClientManager fix)
- Frontend must properly set port values in frontend_config
- May need to verify frontend_config persistence

## Notes
- More complex than Phase 1 due to multiple locations
- Requires understanding of frontend_config flow
- Test thoroughly with various port configurations
- Consider adding validation for port ranges (1-65535)