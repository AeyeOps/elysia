# Weaviate Python SDK - Complete Configuration Guide

## Overview
Comprehensive guide to using the Weaviate Python client correctly, based on troubleshooting and documentation analysis.

## Correct Imports

### Core Classes
```python
from weaviate.classes.config import (
    Property,           # For defining collection properties
    DataType,           # For property data types
    ReplicationConfig,  # For replication configuration (if available)
    Configure           # For vectorizers and other configurations
)
```

### Context Manager Usage
```python
# RECOMMENDED: Use context manager
with ClientManager().connect_to_client() as client:
    # Your operations here
    pass
```

### Manual Client Management (Alternative)
```python
import weaviate

# For local Weaviate
with weaviate.connect_to_local() as client:
    # operations

# For cloud Weaviate  
with weaviate.connect_to_weaviate_cloud(
    url="https://your-cluster.weaviate.network",
    auth_credentials=weaviate.Auth.api_key("your-api-key")
) as client:
    # operations
```

## Property Definition Patterns

### Basic Property Creation
```python
from weaviate.classes.config import Property, DataType

properties = [
    Property(name="user_id", data_type=DataType.TEXT),
    Property(name="config_data", data_type=DataType.TEXT),
    Property(name="timestamp", data_type=DataType.DATE),
    Property(name="score", data_type=DataType.NUMBER),
    Property(name="is_active", data_type=DataType.BOOL),
]
```

### Collection Creation with Properties
```python
collection = client.collections.create(
    name="ELYSIACTL_CONFIG",
    properties=properties,
    # replication_config=ReplicationConfig(factor=3)  # If available
)
```

## Replication Configuration

### Method 1: Using Configure (Recommended)
```python
from weaviate.classes.config import Configure

collection = client.collections.create(
    name="MyCollection",
    properties=properties,
    vectorizer_config=Configure.Vectorizer.text2vec_openai(
        model="text-embedding-ada-002",
        properties=["content"]
    ),
    # replication_config may be handled differently
)
```

### Method 2: Dictionary-based Configuration
```python
collection_config = {
    "name": "MyCollection",
    "properties": [
        {
            "name": "content",
            "dataType": ["text"]
        }
    ],
    "replicationConfig": {
        "factor": 3
    }
}

client.collections.create(collection_config)
```

## ClientManager Configuration

### Environment-based Configuration
```python
from dotenv import load_dotenv
import os

# Load environment
load_dotenv(dotenv_path='.env', override=True)

# Get values from environment
wcd_url = os.environ.get("WCD_URL", "")
wcd_api_key = os.environ.get("WCD_API_KEY", "")
weaviate_is_local = os.environ.get("WEAVIATE_IS_LOCAL", "False").lower() == "true"

# Create client with explicit configuration
with ClientManager(
    wcd_url=wcd_url,
    wcd_api_key=wcd_api_key,
    weaviate_is_local=weaviate_is_local
).connect_to_client() as client:
    # operations
```

### Dynamic Node Switching
```python
def verify_data_on_node(port, collection_name, test_id):
    """Verify data on specific node"""
    # Temporarily override URL
    original_url = os.environ.get("WCD_URL")
    os.environ["WCD_URL"] = f"http://localhost:{port}"
    
    try:
        with ClientManager().connect_to_client() as client:
            # verification logic
            pass
    finally:
        # Restore original URL
        if original_url:
            os.environ["WCD_URL"] = original_url
```

## Data Operations

### Insert Data
```python
from weaviate.classes.data import DataObject

# Method 1: Using DataObject
data_object = DataObject(
    properties={
        "user_id": "test_user",
        "config_data": "test_data",
        "timestamp": "2024-01-01T00:00:00Z"
    }
)

client.collections.data.insert("ELYSIACTL_CONFIG", data_object)

# Method 2: Using dictionary
client.collections.data.insert("ELYSIACTL_CONFIG", {
    "user_id": "test_user",
    "config_data": "test_data",
    "timestamp": "2024-01-01T00:00:00Z"
})
```

### Query Data
```python
from weaviate.classes.query import Filter

# Get all objects
response = client.collections.get("ELYSIACTL_CONFIG").get()

# Filter by property
response = client.collections.get("ELYSIACTL_CONFIG") \
    .with_where(Filter.by_property("user_id").equal("test_user")) \
    .do()

# Get by ID
response = client.collections.get("ELYSIACTL_CONFIG").get_by_id("object-uuid")
```

## Collection Management

### Check if Collection Exists
```python
if client.collections.exists("MyCollection"):
    print("Collection exists")
```

### Delete Collection
```python
if client.collections.exists("MyCollection"):
    client.collections.delete("MyCollection")
```

### List All Collections
```python
collections = client.collections.list_all()
for name in collections:
    print(f"Collection: {name}")
```

## Error Handling

### Common Exceptions
```python
try:
    with ClientManager().connect_to_client() as client:
        # operations
except weaviate.exceptions.UnexpectedStatusCodeException as e:
    print(f"HTTP Error {e.status_code}: {e}")
except weaviate.exceptions.WeaviateConnectionError as e:
    print(f"Connection Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
```

## Environment Configuration (.env)

### Required Variables
```
# Weaviate Connection
WCD_URL=http://localhost:18080
WCD_API_KEY=local-mode
WEAVIATE_IS_LOCAL=True

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Cluster Configuration
WEAVIATE_CLUSTER_PORTS=18080,18081,18082
```

### Dynamic Port Parsing
```python
# Parse comma-separated ports
ports_str = os.environ.get("WEAVIATE_CLUSTER_PORTS", "18080,18081,18082")
nodes = [int(port.strip()) for port in ports_str.split(",")]
```

## Best Practices

### 1. Use Context Managers
Always use context managers for proper resource management:
```python
# ✅ Good
with ClientManager().connect_to_client() as client:
    # operations

# ❌ Avoid
client = ClientManager().connect_to_client()
# operations
client.close()
```

### 2. Environment-based Configuration
Don't hardcode configuration values:
```python
# ✅ Good
load_dotenv('.env', override=True)
wcd_url = os.environ.get("WCD_URL")

# ❌ Avoid
wcd_url = "http://localhost:18080"
```

### 3. Proper Error Handling
Always handle exceptions appropriately:
```python
# ✅ Good
try:
    # operations
except Exception as e:
    print(f"Error: {e}")
    return False

# ❌ Avoid
# operations without error handling
```

### 4. Resource Cleanup
Always clean up resources in finally blocks:
```python
# ✅ Good
try:
    # operations
finally:
    # cleanup
    pass

# ❌ Avoid
# operations without cleanup
```

## Troubleshooting

### Import Errors
- `Property` not found → Import from `weaviate.classes.config`
- `DataType` not found → Import from `weaviate.classes.config`
- `ReplicationConfig` not found → May not be available in current version

### Connection Issues
- Check `WCD_URL` and `WCD_API_KEY` in `.env`
- Verify `WEAVIATE_IS_LOCAL` setting
- Ensure Weaviate cluster is running

### Collection Creation Issues
- Check property definitions
- Verify vectorizer configuration
- Ensure collection doesn't already exist

## Version Compatibility

### Weaviate Python Client v4.x
- Uses new collections API
- Context manager is preferred
- Different import paths for classes
- Enhanced error handling

### Breaking Changes
- `weaviate.classes.Property` → `weaviate.classes.config.Property`
- `weaviate.classes.DataType` → `weaviate.classes.config.DataType`
- New replication configuration methods

## Related Files
- `/opt/elysia/tests/phase4/create_system_collections.py` - Collection creation example
- `/opt/elysia/tests/phase4/verify_replication.py` - Replication verification
- `/opt/elysia/tests/phase4/test_derived_collections.py` - Derived collection testing
- `/opt/elysia/tests/phase4/.env` - Environment configuration