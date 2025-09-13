# Phase 4: Dynamic Replication Testing

This directory contains the implementation for Phase 4 Dynamic Replication testing, which validates Elysia's dynamic replication system in a 3-node local Weaviate cluster.

## Wave 1: Positive Path Validation ✅

Wave 1 validates that dynamic replication works correctly under normal conditions.

### Prerequisites

1. **Docker and Docker Compose** installed
2. **Python 3.8+** with required dependencies
3. **API Keys** configured in `.env` file

### Environment Setup

1. **Start the 3-node Weaviate cluster:**
   ```bash
   cd /opt/elysia/tests/phase4
   docker-compose up -d
   ```

2. **Wait for cluster initialization** (may take 2-3 minutes)

3. **Verify cluster is ready:**
   ```bash
   python simple_check.py    # Quick port check
   python cluster_check.py   # Detailed health check
   ```

### Wave 1 Test Scripts

| Script | Purpose | Success Criteria |
|--------|---------|------------------|
| `cluster_check.py` | Verify 3 healthy Weaviate nodes | All nodes respond to `/v1/meta` |
| `create_system_collections.py` | Create ELYSIACTL_* collections with replication_factor=3 | Collections created successfully |
| `verify_replication.py` | Test data sync across nodes | Data written to node 1 readable from all nodes |
| `test_derived_collections.py` | Validate replication inheritance | Derived collections inherit parent's replication settings |

### Running Wave 1 Tests

```bash
# Run all Wave 1 tests
python wave1_runner.py

# Or run individually
python cluster_check.py
python create_system_collections.py
python verify_replication.py
python test_derived_collections.py
```

---

## Wave 2: Resilience Testing 🧪

Wave 2 tests how the 3-node Weaviate cluster handles node failures and recovery, ensuring data remains accessible and replication continues functioning under degraded conditions.

### Wave 2 Test Scripts

| Script | Purpose | Duration | Success Criteria |
|--------|---------|----------|------------------|
| `node_failure_test.py` | Stop node, verify data access, restart node | 5-10 min | Data accessible from remaining nodes, node recovers |
| `degraded_collection_creation.py` | Create collections during single-node-down scenarios | 8-15 min | Collections created successfully in degraded state |
| `rapid_cycling_test.py` | Automated node stop/start sequences with data validation | 15-25 min | No data loss during rapid cycling |
| `recovery_verification.py` | Check data sync after node restart | 20-30 min | Nodes resync correctly upon rejoining |

### Running Wave 2 Tests

```bash
# Run all Wave 2 tests
python wave2_runner.py

# Or run individually
python node_failure_test.py
python degraded_collection_creation.py
python rapid_cycling_test.py
python recovery_verification.py
```

### Wave 2 Success Criteria

- [ ] System functional with 1 node down (2/3 operational)
- [ ] Data accessible during failures
- [ ] Collections created successfully in degraded state
- [ ] No data loss during rapid cycling
- [ ] Nodes resync correctly upon rejoining

### Wave 2 Test Scenarios

1. **Single Node Failure**: Test with one node down (2/3 operational)
2. **Dual Node Failure**: Test with two nodes down (1/3 operational)
3. **Rapid Cycling**: Automated node stop/start sequences
4. **Recovery Validation**: Comprehensive recovery verification

---

## Configuration

All test scripts automatically load the local `.env` file which contains:
- `WCD_URL=http://localhost:18080` - Primary node URL
- `WEAVIATE_IS_LOCAL=True` - Local cluster mode
- `WEAVIATE_CLUSTER_PORTS=18080,18081,18082` - All cluster node ports
- API keys for various providers

## Expected Output

### Successful Wave 1 Completion
```
🎉 WAVE 1 COMPLETE: All positive path validation tests passed!
✅ Cluster shows 3 healthy nodes
✅ System collections created with factor=3
✅ Data written to node 1 readable from nodes 2 & 3
✅ Derived collections inherit parent replication
```

### Successful Wave 2 Completion
```
🎉 ALL TESTS PASSED - System demonstrates excellent resilience!
✅ System functional with 1 node down
✅ Data accessible during failures
✅ Collections created successfully in degraded state
✅ No data loss during rapid cycling
✅ Nodes resync correctly upon rejoining
```

## Troubleshooting

### Cluster Issues
- **Not starting**: Check Docker resources, verify ports 18080-18082 available
- **Connection refused**: Wait longer for initialization (2-3 minutes)
- **Replication not working**: Check Weaviate version compatibility

### Test Failures
- **Node not recovering**: Check Docker logs, increase timeout values
- **Data not replicating**: Verify collection creation succeeded first
- **Permission errors**: Check API keys in `.env` file

## Cleanup

```bash
# Stop containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v
```