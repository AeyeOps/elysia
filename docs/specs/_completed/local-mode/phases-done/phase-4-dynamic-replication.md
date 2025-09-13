# Phase 4: Dynamic Replication Configuration

## Objective
Replace hardcoded and missing replication configurations in system collections with dynamic cluster-aware settings.

## Collection Types

### System Collections (MUST replicate to all nodes)
Essential for system consistency and high availability:
1. **ELYSIACTL_CONFIG__** - User configurations (hardcoded factor=3)
2. **ELYSIACTL_FEEDBACK__** - System feedback (missing replication)
3. **ELYSIACTL_METADATA__** - Collection metadata (missing replication)

### Derived Collections (inherit from parent)
4. **ELYSIACTL_CHUNKED_<collection>__** - Chunked documents (missing replication, should inherit)

### User Collections (DO NOT TOUCH)
User-controlled collections should remain user-controlled.

## Current Problems

### 1. Hardcoded System Collection
**File:** `/opt/elysia/elysia/api/routes/user_config.py`  
**Lines:** 491-493
```python
replication_config=wc.Configure.replication(factor=3)
```
Problem: Assumes 3-node cluster, breaks for other cluster sizes.

### 2. Missing System Collection Configs
**ELYSIACTL_FEEDBACK__** - `/opt/elysia/elysia/api/utils/feedback.py:18-179`
**ELYSIACTL_METADATA__** - `/opt/elysia/elysia/preprocessing/collection.py:640-644`

### 3. Missing Derived Collection Config
**ELYSIACTL_CHUNKED_** - `/opt/elysia/elysia/tools/retrieval/chunk.py:268-279`

## Solution Design

### Utility Functions
**Location:** Add to existing `/opt/elysia/elysia/util/client.py`

```python
import weaviate.classes.config as wc

async def get_system_replication_config(client):
    """
    Get replication config for system collections (CONFIG, FEEDBACK, METADATA).
    System collections MUST replicate to all nodes for consistency.
    
    Args:
        client: WeaviateAsyncClient instance from client_manager.connect_to_async_client()
        
    Returns:
        wc.Configure.replication(factor=node_count) or None if single node or error
        
    Raises:
        ValueError: If cluster information cannot be retrieved (fail-fast approach)
    """
    try:
        nodes = await client.cluster.nodes()
        node_count = len(nodes)
        if node_count <= 1:
            return None  # Single node clusters don't need replication
        return wc.Configure.replication(factor=node_count)
    except Exception as e:
        # Fail fast - if we can't determine cluster size, raise error
        raise ValueError(f"Cannot determine cluster size for replication config: {e}")

async def get_derived_replication_config(parent_collection_name, client):
    """
    Get replication config for derived collections (CHUNKED).
    Should inherit from parent collection's replication settings.
    
    Args:
        parent_collection_name: Name of the parent collection to inherit from
        client: WeaviateAsyncClient instance from client_manager.connect_to_async_client()
        
    Returns:
        Replication config matching parent or None if parent has no replication
        
    Raises:
        ValueError: If parent collection doesn't exist or config unavailable (fail-fast approach)
    """
    try:
        if not await client.collections.exists(parent_collection_name):
            raise ValueError(f"Parent collection '{parent_collection_name}' does not exist")
            
        collection = client.collections.get(parent_collection_name)
        collection_config = await collection.config.get()
        
        if hasattr(collection_config, 'replication_config') and collection_config.replication_config:
            return collection_config.replication_config
        return None  # Parent has no replication config
    except Exception as e:
        # Fail fast - if we can't get parent config, raise error
        raise ValueError(f"Cannot retrieve replication config from parent collection '{parent_collection_name}': {e}")
```

### Implementation Changes

#### 1. Fix ELYSIACTL_CONFIG__ Collection 
**File:** `/opt/elysia/elysia/api/routes/user_config.py`  

**Add import at top of file:**
```python
from elysia.util.client import get_system_replication_config
```

**Replace line 491-493:**
```python
# Current:
replication_config=wc.Configure.replication(factor=3)

# New:
replication_config=await get_system_replication_config(client)
```

#### 2. Fix ELYSIACTL_FEEDBACK__ Collection
**File:** `/opt/elysia/elysia/api/utils/feedback.py`  

**Add import at top of file:**
```python
from elysia.util.client import get_system_replication_config
```

**Add to collection creation (around lines 50-70):**
```python
replication_config=await get_system_replication_config(client)
```

#### 3. Fix ELYSIACTL_METADATA__ Collection
**File:** `/opt/elysia/elysia/preprocessing/collection.py`  

**Add import at top of file:**
```python
from elysia.util.client import get_system_replication_config
```

**Replace collection creation at line 640-642:**
```python
# Current:
metadata_collection = await client.collections.create(
    f"ELYSIACTL_METADATA__",
    vectorizer_config=Configure.Vectorizer.none(),

# New:
metadata_collection = await client.collections.create(
    f"ELYSIACTL_METADATA__",
    vectorizer_config=Configure.Vectorizer.none(),
    replication_config=await get_system_replication_config(client),
```

#### 4. Fix ELYSIACTL_CHUNKED_* Collections
**File:** `/opt/elysia/elysia/tools/retrieval/chunk.py`  

**Add import at top of file:**
```python
from elysia.util.client import get_derived_replication_config
```

**Replace collection creation at lines 268-282:**
```python
# Current:
return await client.collections.create(
    self.get_chunked_collection_name(),
    properties=[
        Property(name=content_field, data_type=DataType.TEXT),
        Property(
            name="chunk_spans",
            data_type=DataType.INT_ARRAY,
        ),
    ],
    references=[
        ReferenceProperty(
            name="fullDocument", target_collection=self.collection_name
        )
    ],
    vector_config=await self.get_vectoriser(content_field, client),
)

# New:
return await client.collections.create(
    self.get_chunked_collection_name(),
    properties=[
        Property(name=content_field, data_type=DataType.TEXT),
        Property(
            name="chunk_spans",
            data_type=DataType.INT_ARRAY,
        ),
    ],
    references=[
        ReferenceProperty(
            name="fullDocument", target_collection=self.collection_name
        )
    ],
    vector_config=await self.get_vectoriser(content_field, client),
    replication_config=await get_derived_replication_config(self.collection_name, client),
)
```

## Architectural Principles

### System vs User Collections
- **System collections** (CONFIG, FEEDBACK, METADATA): MUST replicate to all nodes for consistency
- **Derived collections** (CHUNKED): Inherit from parent collection's replication settings
- **User collections**: Remain user-controlled (DO NOT MODIFY)

### Fail-Fast Approach
- Functions raise `ValueError` if cluster/collection information cannot be retrieved
- No silent fallbacks or compensation for misconfigurations
- Clear error messages for debugging and troubleshooting
- Let the calling code handle errors appropriately (collection creation will fail with clear error)

### Single Responsibility
- `get_system_replication_config()`: System collections only
- `get_derived_replication_config()`: Derived collections only
- No generic "one size fits all" function

### Async/Sync Compatibility
- **Both functions are async**: They use `WeaviateAsyncClient` from `client_manager.connect_to_async_client()` context
- **Consistent with codebase**: All collection creation in the target files uses async clients
- **Client parameter**: Both functions receive the `client` parameter directly (not client_manager)
- **Import placement**: All imports must be at the top of files, never conditional or in try/catch blocks

## Testing Strategy

### Success Cases
1. **Single-node cluster**: `get_system_replication_config()` returns `None` (no replication needed)
2. **Multi-node cluster (e.g., 3 nodes)**: System collections get `factor=3`
3. **Derived collections**: Match parent collection replication exactly
4. **Parent with no replication**: `get_derived_replication_config()` returns `None`

### Fail-Fast Cases (should raise ValueError)
1. **Cluster unreachable**: Clear error about cluster connectivity
2. **Parent collection missing**: Clear error about missing parent collection
3. **Weaviate authentication failure**: Clear error about authentication
4. **Permission denied**: Clear error about insufficient permissions

### Integration Tests
- Verify collection creation succeeds with valid replication config
- Verify collection creation fails gracefully with clear errors when config functions raise exceptions