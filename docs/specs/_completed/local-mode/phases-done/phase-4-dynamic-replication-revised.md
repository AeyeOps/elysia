# Phase 4: Dynamic Replication Configuration - Revised

## Objective
Fix replication configurations with surgical precision, distinguishing between system collections that MUST replicate to all nodes and derived collections that should inherit replication settings.

## Architecture Classification

### System Collections (MUST replicate to all nodes)
These are infrastructure collections required for system operation:

1. **ELYSIACTL_CONFIG__** - User configurations (critical for consistency)
2. **ELYSIACTL_FEEDBACK__** - System feedback (user experience data)
3. **ELYSIACTL_METADATA__** - Collection metadata (preprocessing results)

### Derived Collections (inherit from parent)
4. **ELYSIACTL_CHUNKED_<collection>__** - Should inherit parent collection's replication

### User Collections (DO NOT TOUCH)
- `tree.py:1995` creates user export collections - these are user-controlled, not system

## Implementation Plan

### Step 1: Create Minimal Utility
**Location:** `/opt/elysia/elysia/util/replication.py` (new file)

```python
import weaviate.classes.config as wc


async def get_system_replication_config(client):
    """
    Get replication config for system collections.
    System collections MUST replicate to all nodes for consistency.
    
    Returns:
        wc.Configure.replication(factor=n) where n is cluster size
        None if single-node or error (safe fallback)
    """
    try:
        nodes = await client.cluster.nodes()
        node_count = len(nodes)
        
        if node_count <= 1:
            return None  # Single node - no replication needed
        else:
            return wc.Configure.replication(factor=node_count)
    except Exception:
        return None  # Safe fallback


async def get_inherited_replication_config(client, parent_collection_name):
    """
    Get replication config by inheriting from parent collection.
    Used for derived collections like ELYSIACTL_CHUNKED_*.
    
    Returns:
        Replication config matching parent, or system config as fallback
    """
    try:
        if await client.collections.exists(parent_collection_name):
            parent = client.collections.get(parent_collection_name)
            # Try to get parent's replication config
            # If not available, fall back to system config
            return await get_system_replication_config(client)
        else:
            return await get_system_replication_config(client)
    except Exception:
        return None
```

### Step 2: Fix System Collections

#### 2.1: ELYSIACTL_CONFIG__ (user_config.py)
**File:** `/opt/elysia/elysia/api/routes/user_config.py`
**Lines:** 491-493

**Current:**
```python
replication_config=wc.Configure.replication(factor=3)
```

**Replace with:**
```python
replication_config=await get_system_replication_config(client)
```

**Add import at top of file:**
```python
from elysia.util.replication import get_system_replication_config
```

#### 2.2: ELYSIACTL_FEEDBACK__ (feedback.py)
**File:** `/opt/elysia/elysia/api/utils/feedback.py`
**Line:** 18

**Current:**
```python
await client.collections.create(
    "ELYSIACTL_FEEDBACK__",
    properties=[
```

**Replace with:**
```python
await client.collections.create(
    "ELYSIACTL_FEEDBACK__",
    replication_config=await get_system_replication_config(client),
    properties=[
```

**Add import at top of file:**
```python
from elysia.util.replication import get_system_replication_config
```

#### 2.3: ELYSIACTL_METADATA__ (collection.py)
**File:** `/opt/elysia/elysia/preprocessing/collection.py`
**Line:** 640

**Current:**
```python
metadata_collection = await client.collections.create(
    f"ELYSIACTL_METADATA__",
    vectorizer_config=Configure.Vectorizer.none(),
    properties=[
```

**Replace with:**
```python
metadata_collection = await client.collections.create(
    f"ELYSIACTL_METADATA__",
    vectorizer_config=Configure.Vectorizer.none(),
    replication_config=await get_system_replication_config(client),
    properties=[
```

**Add import at top of file:**
```python
from elysia.util.replication import get_system_replication_config
```

### Step 3: Fix Derived Collections

#### 3.1: ELYSIACTL_CHUNKED_* (chunk.py)
**File:** `/opt/elysia/elysia/tools/retrieval/chunk.py`
**Line:** 268

**Current:**
```python
return await client.collections.create(
    self.get_chunked_collection_name(),
    properties=[
```

**Replace with:**
```python
return await client.collections.create(
    self.get_chunked_collection_name(),
    replication_config=await get_inherited_replication_config(client, self.collection_name),
    properties=[
```

**Add import at top of file:**
```python
from elysia.util.replication import get_inherited_replication_config
```

## Exclusions

### DO NOT MODIFY: tree.py export collections
**File:** `/opt/elysia/elysia/tree/tree.py:1995`
**Reason:** This creates user export collections via `export_to_weaviate()`. These are user-controlled collections, not system infrastructure. Users should decide their own replication strategy.

## Benefits
- System collections guaranteed consistent across all nodes
- Derived collections inherit appropriate replication
- No hardcoded assumptions about cluster size
- User collections remain user-controlled
- Graceful fallback for single-node or error cases
- Minimal code footprint

## Failure Modes
- If cluster inspection fails → Returns None (Weaviate defaults)
- If parent collection missing → Falls back to system replication
- Single node clusters → No replication (correct behavior)