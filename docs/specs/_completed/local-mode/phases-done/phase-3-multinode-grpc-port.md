# Phase 3: Multi-Node Local Cluster gRPC Port Detection

## Objective
Enable proper gRPC port detection for multi-node local Weaviate clusters by implementing intelligent port offset calculation.

## Problem Summary
When connecting to non-primary nodes in a local cluster (e.g., `http://localhost:8081`), the system doesn't know the corresponding gRPC port (50052). This breaks connections to nodes 2 and 3 in multi-node setups.

## Current Behavior vs Required Behavior

### Current (Broken)
- User enters: `http://localhost:8081`
- System uses: HTTP port 8081, gRPC port 50051 (wrong!)
- Result: Connection fails due to gRPC port mismatch

### Required
- User enters: `http://localhost:8081`
- System detects: HTTP port 8081, calculates gRPC port 50052
- Result: Connection succeeds to node 2

## Implementation Strategy

### Option Selected: Smart Port Offset Detection
Calculate gRPC port based on HTTP port offset from default (8080):
- HTTP 8080 → gRPC 50051 (default)
- HTTP 8081 → gRPC 50052 (offset +1)
- HTTP 8082 → gRPC 50053 (offset +2)

### File: `/opt/elysia/elysia/util/client.py`

### Change: Enhance `_get_local_host_and_port()` method

**Location:** After line 208 (when port is extracted from URL)
**Add Logic:**
```python
def _get_local_host_and_port(self) -> tuple[str, int]:
    """
    Derive host and port for local connections from wcd_url and configured ports.
    Accepts full URLs like "http://localhost:8080" and extracts hostname/port.
    """
    host = self.wcd_url if self.wcd_url is not None else "localhost"
    port = self.local_weaviate_port
    grpc_port = self.local_weaviate_grpc_port  # Track gRPC port
    
    try:
        parsed = urlparse(host)
        if parsed.scheme in ("http", "https"):
            if parsed.hostname:
                host = parsed.hostname
            if parsed.port:
                port = parsed.port
                # Calculate gRPC port offset based on HTTP port
                if self.local_weaviate_port and self.local_weaviate_grpc_port:
                    # Calculate offset from default HTTP port
                    http_offset = port - self.local_weaviate_port
                    # Apply same offset to gRPC port
                    grpc_port = self.local_weaviate_grpc_port + http_offset
                    if self.logger:
                        self.logger.debug(
                            f"Calculated gRPC port {grpc_port} from HTTP port {port} "
                            f"(offset: {http_offset})"
                        )
        # ... rest of existing code
    except Exception:
        # ... existing fallback
        
    # Store calculated gRPC port for use in get_client/get_async_client
    self._calculated_grpc_port = grpc_port
    return host, port
```

### Change: Update `get_client()` and `get_async_client()` methods

**Use calculated gRPC port:**
```python
# In get_client() around line 314
grpc_port=getattr(self, '_calculated_grpc_port', self.local_weaviate_grpc_port),

# In get_async_client() around line 349
grpc_port=getattr(self, '_calculated_grpc_port', self.local_weaviate_grpc_port),
```

## Agent Workflow

### Step 1: Analysis Agent
1. Review current port extraction logic
2. Identify where gRPC port is used (lines 314, 349)
3. Determine best place to calculate offset

### Step 2: Implementation Agent
1. Modify `_get_local_host_and_port()` to calculate gRPC offset
2. Store calculated gRPC port as instance variable
3. Update `get_client()` to use calculated port
4. Update `get_async_client()` to use calculated port
5. Add debug logging for troubleshooting

### Step 3: Test Agent
1. Test with default ports (8080/50051)
2. Test with node 2 (8081/50052)
3. Test with node 3 (8082/50053)
4. Test with custom base ports (e.g., 9090/60051)
5. Test error cases (invalid ports, port out of range)

## Success Criteria
- [ ] Node 1 connection works (http://localhost:8080)
- [ ] Node 2 connection works (http://localhost:8081)
- [ ] Node 3 connection works (http://localhost:8082)
- [ ] Custom port bases work (e.g., 9090 base)
- [ ] Fallback to defaults when offset can't be calculated
- [ ] Debug logging shows correct port calculations

## Edge Cases
1. **Non-sequential ports:** User has HTTP 8080 but gRPC on 60000
   - Solution: Falls back to configured gRPC port
2. **Negative offsets:** User enters http://localhost:8079
   - Solution: Still calculate offset correctly
3. **Port overflow:** Offset causes gRPC port > 65535
   - Solution: Log warning, use default

## Testing Scenarios

### Scenario 1: Three-node cluster (your current setup)
```bash
# Start Weaviate nodes on 8080/50051, 8081/50052, 8082/50053

# Test each node
for port in 8080 8081 8082; do
    echo "Testing node on port $port"
    python -c "
from elysia.util.client import ClientManager
cm = ClientManager(
    wcd_url='http://localhost:$port',
    weaviate_is_local=True,
    local_weaviate_port=8080,
    local_weaviate_grpc_port=50051
)
client = cm.get_client()
print(f'Connected to port $port successfully!')
"
done
```

### Scenario 2: Custom port base
```python
# If Weaviate runs on 9090/60051, 9091/60052, etc.
cm = ClientManager(
    wcd_url='http://localhost:9091',  # Should detect gRPC 60052
    weaviate_is_local=True,
    local_weaviate_port=9090,  # Base HTTP
    local_weaviate_grpc_port=60051  # Base gRPC
)
```

## Rollback Plan
If issues occur:
1. Remove offset calculation logic
2. Revert to using configured gRPC port only
3. Document that multi-node requires load balancer

## Alternative Approaches (Not Selected)
1. **Load Balancer:** Require users to set up HAProxy/nginx
   - Pros: Standard solution
   - Cons: Extra complexity for local development

2. **Comma-separated URLs:** Support multiple URLs
   - Pros: Explicit configuration
   - Cons: Complex implementation, UI changes needed

3. **Configuration mapping:** Add HTTP→gRPC port mapping in config
   - Pros: Flexible
   - Cons: Requires UI changes, more complex configuration

## Notes
- This maintains backward compatibility
- Single-node setups work unchanged
- Multi-node setups "just work" with consistent port offsets
- Follows "fail fast" principle - clear errors if ports don't match