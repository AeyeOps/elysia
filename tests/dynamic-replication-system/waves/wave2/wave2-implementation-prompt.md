# Implementation Prompt for Wave 2: Resilience Testing

## System Context
You are implementing resilience validation for Elysia's dynamic replication system. Build on Wave 1 foundation to test system behavior during node failures and recovery.

## Task Overview
Test how the 3-node Weaviate cluster handles node failures, ensuring data remains accessible and replication continues functioning under degraded conditions.

## Specific Requirements
1. **Node Failure Simulation**: Create scripts to safely stop/start individual nodes using Docker
2. **Data Accessibility**: Verify collections remain readable during single node failures
3. **Collection Creation**: Test creating new collections when cluster is degraded
4. **Rapid Cycling**: Implement automated node stop/start sequences to test stability
5. **Recovery Validation**: Confirm nodes resync data upon rejoining

## Key Scripts Needed
- `node_failure_test.py`: Stop node, verify data access, restart node
- `degraded_collection_creation.py`: Create collections during single-node-down scenarios
- `rapid_cycling_test.py`: Automated node cycling with data validation
- `recovery_verification.py`: Check data sync after node restart

## Success Criteria
- [ ] System functional with 1 node down (2/3 operational)
- [ ] Data accessible during failures
- [ ] Collections created successfully in degraded state
- [ ] No data loss during rapid cycling
- [ ] Nodes resync correctly upon rejoining

## Execution Notes
Human will handle Docker stop/start commands. Focus on programmatic verification of data consistency. Log all operations for debugging. Estimated time: 2-3 hours.</content>
<parameter name="file_path">testing/phase4/wave2-implementation-prompt.md