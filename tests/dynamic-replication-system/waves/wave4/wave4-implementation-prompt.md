# Implementation Prompt for Wave 4: Performance Validation

## System Context
You are conducting performance validation for Elysia's replication system. Measure overhead, latency, and resource usage to ensure replication doesn't degrade system performance unacceptably.

## Task Overview
Establish performance baselines and measure replication impact on write/read operations, resource consumption, and data consistency timing.

## Specific Requirements
1. **Baseline Measurement**: Test single-node performance for comparison
2. **Replication Overhead**: Measure performance delta with 3-node cluster
3. **Replication Lag**: Time data appearance across nodes after writes
4. **Resource Monitoring**: Track CPU/memory usage during operations
5. **Scalability Testing**: Validate performance with increasing data volumes

## Key Scripts Needed
- `performance_baseline.py`: Measure operations on single-node setup
- `replication_overhead_test.py`: Compare single vs multi-node performance
- `replication_lag_measurement.py`: Time data sync across nodes
- `resource_monitoring.py`: Track system resources during tests
- `scalability_test.py`: Test with growing datasets

## Success Criteria
- [ ] Performance overhead < 20% for writes
- [ ] Read performance improved or neutral
- [ ] Replication lag < 1 second
- [ ] Resource usage within acceptable limits
- [ ] No performance degradation with data growth

## Execution Notes
Use Docker stats and system monitoring tools. Run multiple iterations for statistical significance. Document performance metrics for future comparisons. Estimated time: 2-3 hours.</content>
<parameter name="file_path">testing/phase4/wave4-implementation-prompt.md