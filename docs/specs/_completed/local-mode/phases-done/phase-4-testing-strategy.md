# Phase 4 Dynamic Replication - Testing Strategy

## Executive Summary
A pragmatic, phased approach to validate dynamic replication using the existing 3-node cluster. Focuses on end-to-end testing through human-agent collaboration rather than complex automated component tests.

## Testing Philosophy
- **End-to-end over unit tests** - Test actual behavior in real environments
- **Human-agent collaboration** - Leverage both human observation and agent execution
- **Incremental confidence** - Start simple, build complexity gradually
- **Fail fast** - Find critical issues early before investing in complex scenarios
- **Observable validation** - Use clear, visual confirmations where possible

## Prerequisites

Before executing the testing waves, ensure the following are in place:

1. **3-node local Weaviate cluster**: Docker containers running on ports 8080/8081/8082 (via docker-compose.test.yml)
2. **Main spec fixes implemented**: ClientManager API key validation logic, hardcoded ports in user.py
3. **Elysia local configuration**: .env with WEAVIATE_IS_LOCAL=true, WCD_URL=http://localhost:8080
4. **Functional Elysia API**: /init, /collections endpoints working for collection and data generation
5. **Test scripts prepared**: Python ClientManager scripts for cluster detection and operations
6. **Docker environment**: Commands for container management (stop/start/logs/stats)
7. **API testing tools**: curl and jq installed for verification commands

*Note: Setting up missing prerequisites may take 2-4 hours*

---

## Current Environment

---

## WAVE 1: Positive Path Validation (Current 3-Node Cluster)
**Goal**: Prove the happy path works correctly with existing setup
**Duration**: 1-2 hours
**Complexity**: Low

### Test 1.1: Verify Cluster Detection
**Human-Agent Collaborative Test**
```bash
# Human: Ensure 3-node cluster is running
docker ps | grep weaviate  # Should show 3 containers

# Agent: Run verification script
python -c "
from elysia.util.client import ClientManager
import asyncio

async def check_cluster():
    cm = ClientManager(
        wcd_url='http://localhost:8080',
        weaviate_is_local=True
    )
    async with cm.connect_to_async_client() as client:
        nodes = await client.cluster.nodes()
        print(f'Cluster nodes detected: {len(nodes)}')
        for node in nodes:
            print(f'  - {node.name}: {node.status}')

asyncio.run(check_cluster())
"

# Expected: Should show 3 nodes, all healthy
```

### Test 1.2: Create System Collections and Verify Replication
**Agent Executes, Human Verifies**
```python
# Agent: Create each system collection
async def create_and_verify():
    # 1. Create CONFIG collection (via API endpoint)
    # 2. Create FEEDBACK via feedback creation
    # 3. Trigger METADATA creation via preprocessing
    
    # Then verify each has replication_factor=3

# Human: Check via Weaviate API
curl http://localhost:8080/v1/schema | jq '.classes[] | 
  select(.class | startswith("ELYSIACTL_")) | 
  {class: .class, replication: .replicationConfig}'

# Expected: All show "factor": 3
```

### Test 1.3: Data Availability Across Nodes
**Human-Agent Collaborative**
```python
# Agent: Write data to node 1
# Connect to localhost:8080 and insert test config

# Human: Verify data readable from all nodes
curl http://localhost:8080/v1/objects?class=ELYSIACTL_CONFIG__  # Should work
curl http://localhost:8081/v1/objects?class=ELYSIACTL_CONFIG__  # Should work
curl http://localhost:8082/v1/objects?class=ELYSIACTL_CONFIG__  # Should work
```

### Test 1.4: Derived Collection Inheritance
**Agent Creates, Human Verifies**
```python
# Agent: 
# 1. Create parent collection with specific replication (e.g., factor=2)
# 2. Trigger chunking to create CHUNKED collection
# 3. Report both configs

# Human: Verify chunked inherits parent's factor=2
curl http://localhost:8080/v1/schema | jq '.classes[] | 
  select(.class | contains("CHUNKED")) | 
  .replicationConfig'
```

### Wave 1 Success Criteria
- [ ] Cluster shows 3 healthy nodes
- [ ] System collections created with factor=3
- [ ] Data written to node 1 readable from nodes 2 & 3
- [ ] Derived collections inherit parent replication
- [ ] No errors in Elysia logs

---

## WAVE 2: Resilience Testing (Still 3-Node)
**Goal**: Verify system handles node failures gracefully
**Duration**: 2-3 hours
**Complexity**: Medium

### Test 2.1: Single Node Failure
**Human Actions, Agent Verification**
```bash
# Human: Stop node 1
docker stop weaviate-node-1

# Agent: Verify system collections still accessible
# - Try to read from CONFIG via node 2 (8081)
# - Try to write to FEEDBACK via node 3 (8082)

# Human: Verify in logs
# Check that operations succeed without errors

# Human: Restart node 1
docker start weaviate-node-1

# Agent: Verify node rejoins and data syncs
```

### Test 2.2: Collection Creation During Degraded State
**Human Degrades, Agent Tests**
```bash
# Human: Stop one node
# Agent: Try to create new system collection
# Expected: Should still create with factor=3 (even if only 2 are up)
# Human: Restart node and verify it gets the collection
```

### Test 2.3: Rapid Node Cycling
**Human-Agent Tag Team**
```bash
# Human: Stop node 1
# Agent: Write data
# Human: Start node 1, stop node 2
# Agent: Read/write data
# Human: Start node 2, stop node 3
# Agent: Verify all data still accessible
```

### Wave 2 Success Criteria
- [ ] System remains functional with 1 node down
- [ ] Data remains accessible during failures
- [ ] Nodes resync when rejoining
- [ ] No data loss during cycling

---

## WAVE 3: Edge Cases & Error Handling
**Goal**: Verify fail-fast behavior and error messages
**Duration**: 1-2 hours
**Complexity**: Medium

### Test 3.1: Misconfiguration Detection
**Agent Tests, Human Reviews Errors**
```python
# Agent: Try various misconfigurations
# - Create derived collection with non-existent parent
# - Access cluster info with network issues simulated

# Human: Review error messages
# - Are they clear and actionable?
# - Do they identify the problem?
```

### Test 3.2: Single-Node Behavior
**Human Reconfigures, Agent Tests**
```bash
# Human: Reconfigure to single-node cluster
# - Stop nodes 2 and 3
# - Update config to point to single node

# Agent: Create system collections
# Expected: Should work with no replication (factor=None)

# Human: Verify no replication config in schema
```

### Test 3.3: Concurrent Operations
**Agent Stress Test**
```python
# Agent: Simultaneously from different connections:
# - Create CONFIG from connection 1
# - Create FEEDBACK from connection 2  
# - Create METADATA from connection 3

# Human: Monitor for race conditions or conflicts
```

### Wave 3 Success Criteria
- [ ] Clear error messages for misconfigurations
- [ ] Single-node mode works without replication
- [ ] No race conditions in concurrent creation
- [ ] Fail-fast behavior observed

---

## WAVE 4: Performance Validation
**Goal**: Ensure replication doesn't degrade performance unacceptably
**Duration**: 2-3 hours
**Complexity**: Medium-High

### Test 4.1: Baseline Performance
**Agent Measures, Human Analyzes**
```python
# Agent: Measure operations on single-node (baseline)
# - Time to create collection
# - Time to insert 1000 records
# - Time to query 1000 times

# Then repeat with 3-node cluster
# Human: Compare results - acceptable overhead?
```

### Test 4.2: Replication Lag
**Agent Writes, Human Observes**
```python
# Agent: Rapid writes to node 1
# Human: Query other nodes and observe lag
# - How quickly does data appear on nodes 2 & 3?
# - Is there eventual consistency?
```

### Test 4.3: Resource Usage
**Human Monitors, Agent Loads**
```bash
# Human: Monitor resource usage
docker stats

# Agent: Create collections and load data
# Human: Observe CPU/memory impact of replication
```

### Wave 4 Success Criteria
- [ ] Performance overhead < 20% for writes
- [ ] Read performance improved or neutral
- [ ] Replication lag < 1 second
- [ ] Resource usage reasonable

---

## WAVE 5: Scale Testing (Future - Optional)
**Goal**: Validate with different cluster sizes
**Duration**: 3-4 hours
**Complexity**: High
**Prerequisite**: Additional cluster configurations

### Test 5.1: Five-Node Cluster
```bash
# Human: Set up 5-node cluster
# Agent: Verify factor=5 for system collections
# Human: Test failover with 2 nodes down
```

### Test 5.2: Scale Down Testing
```bash
# Human: Start with 5 nodes, create collections
# Human: Scale down to 3 nodes
# Agent: Verify collections still accessible
# Note: Replication factor remains at 5 (doesn't auto-adjust down)
```

### Test 5.3: Large Cluster (7+ nodes)
```bash
# Verify algorithm works with larger clusters
# Test performance impact of high replication factor
```

---

## Test Execution Plan

### Phase 1: Core Validation (Day 1)
- **Wave 1** - Positive path with 3-node cluster
- **Decision Point**: If failures, stop and fix before proceeding

### Phase 2: Robustness (Day 2)
- **Wave 2** - Resilience testing
- **Wave 3** - Edge cases
- **Decision Point**: Assess if ready for production

### Phase 3: Performance (Day 3)
- **Wave 4** - Performance validation
- **Decision Point**: Performance acceptable?

### Phase 4: Future Growth (As Needed)
- **Wave 5** - Scale testing when cluster sizes change

---

## Human-Agent Collaboration Protocol

### Human Responsibilities
1. **Environment Setup** - Ensure cluster is in correct state
2. **Physical Actions** - Start/stop containers, network changes
3. **Observation** - Monitor logs, resource usage, visual verification
4. **Decision Making** - Interpret results, decide on next steps

### Agent Responsibilities
1. **Test Execution** - Run test scripts and operations
2. **Data Generation** - Create test data and collections
3. **Verification** - Check programmatic conditions
4. **Reporting** - Summarize results and errors

### Communication Format
```
Human: "3-node cluster is running, ready for Test 1.1"
Agent: [Executes test, reports results]
Human: "Confirmed 3 nodes visible. Proceeding to Test 1.2"
Agent: [Creates collections, shows verification commands]
Human: "Running curl command... all show factor=3. Test passed."
```

---

## Success Metrics

### Minimum Viable Validation (After Wave 1)
- System collections replicate correctly in 3-node cluster
- Basic operations work on all nodes
- No critical errors

### Production Ready (After Wave 3)
- All positive paths validated
- Error handling confirmed
- Single-node fallback works
- Clear failure messages

### Performance Validated (After Wave 4)
- Acceptable performance overhead
- No resource exhaustion
- Reasonable replication lag

---

## Risk Mitigation

### Critical Risks
1. **Data Loss** - Test in non-production first
2. **Performance Degradation** - Have rollback plan
3. **Cluster Instability** - Test gradually, one collection type at a time

### Rollback Plan
If critical issues found:
1. Revert code changes
2. Recreate collections without replication
3. Document specific failure for debugging

---

## Appendix: Quick Test Commands

### Check Cluster Status
```bash
curl http://localhost:8080/v1/nodes | jq '.'
```

### View Collection Replication
```bash
curl http://localhost:8080/v1/schema | jq '.classes[] | 
  select(.class | startswith("ELYSIACTL_")) | 
  {class: .class, factor: .replicationConfig.factor}'
```

### Test Data Availability
```bash
for port in 8080 8081 8082; do
  echo "Node $port:"
  curl -s http://localhost:$port/v1/objects?class=ELYSIACTL_CONFIG__ | jq '.objects | length'
done
```

### Monitor Logs
```bash
docker logs weaviate-node-1 --tail 100 -f
```