# Weaviate Local Mode Specification

## Summary
This document identifies areas in the Elysia codebase that need updates for proper local Weaviate support. The goal is to ensure consistent handling of local vs cloud Weaviate instances throughout the application.

## Status Legend
- ✅ **IMPLEMENTED** - Already correctly handles local mode
- ❌ **NEEDS FIX** - Requires modification
- ⚠️ **NEEDS REVIEW** - May need adjustment based on use case

## Identified Issues

### 1. ClientManager Class - Logic Flow Issue
**File:** `/opt/elysia/elysia/util/client.py`
**Status:** ❌ NEEDS FIX
**Issue:** After setting up local connection, code falls through to API key validation causing "Invalid port: '8080:443'" error

**Problem in `get_client()` method:**
- Line 321: Checks `if self.wcd_url is None or self.wcd_api_key is None:` even for local connections
- This causes local connections without API key to either error or attempt cloud connection
- **Fix:** Change to `if not self.weaviate_is_local and (self.wcd_url is None or self.wcd_api_key is None):`

**Problem in `get_async_client()` method:**
- Line 355: Same issue - validates API key even for local connections
- **Fix:** Apply same conditional check as above

### 2. Hardcoded Ports in UserManager
**File:** `/opt/elysia/elysia/api/services/user.py`
**Status:** ❌ NEEDS FIX
**Issue:** Multiple instances of hardcoded ports (8080, 50051) instead of using frontend_config values

**Occurrences:**
- Lines 337-345: `add_user_local()` - hardcoded ports in ClientManager creation
- Lines 382-389: `add_user_local()` - duplicate hardcoded ports
- Lines 429-436: `get_user_local()` - hardcoded ports
- Lines 473-480: `get_user_local()` - duplicate hardcoded ports
- Lines 524-530: `update_config()` - hardcoded ports

**Required Fix:** Use `frontend_config.local_weaviate_port` and `frontend_config.local_weaviate_grpc_port`

### 3. Collection Creation with Replication
**File:** `/opt/elysia/elysia/preprocessing/collection.py`
**Status:** ✅ IMPLEMENTED
**Details:** Line 73 correctly sets replication_factor=1 for single-node detection

### 4. Environment Configuration
**File:** `/opt/elysia/.env`
**Status:** ✅ IMPLEMENTED
**Details:** Added local Weaviate settings:
```
WCD_URL=http://localhost:8080
WEAVIATE_IS_LOCAL=true
```

### 5. API Routes
**File:** `/opt/elysia/elysia/api/routes/init.py`
**Status:** ✅ IMPLEMENTED
**Details:** Uses ClientManager properly, no hardcoded assumptions

### 6. Feedback Collection Creation
**File:** `/opt/elysia/elysia/api/utils/feedback.py`
**Status:** ⚠️ NEEDS REVIEW
**Details:** Line 179 creates collection without replication config
- May need dynamic replication_factor based on cluster size
- Currently relies on Weaviate defaults

## Implementation Priority

### Critical (Connection Blocking)
1. Fix ClientManager logic flow in `client.py` lines 321 and 355 - causes "Invalid port: '8080:443'" error

### High Priority (Breaking Issues)
2. Fix hardcoded ports in `user.py` - prevents proper local connection with custom ports

### Low Priority (Enhancements)
3. Review feedback collection replication settings

## Next Steps
1. Fix ClientManager API key validation logic for local connections
2. Replace hardcoded ports with config values in `user.py`
3. Test with various local Weaviate configurations
4. Validate multi-node local cluster scenarios

## Error Symptoms
- **"Invalid port: '8080:443'"** - Occurs when ClientManager falls through to cloud connection for local URLs
- **Connection failures with custom ports** - Occurs when hardcoded ports don't match actual Weaviate configuration

## Notes
- Keep changes minimal and focused (per CLAUDE.md guidelines)
- Test after each change with `pytest --ignore=tests/requires_env`
- Prefer configuration over hardcoding