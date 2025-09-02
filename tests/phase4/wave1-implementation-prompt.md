# Implementation Prompt for Wave 1: Positive Path Validation

## System Context
You are an expert coding assistant implementing Phase 4 Dynamic Replication testing for Elysia's local Weaviate mode. Focus on end-to-end validation with human-agent collaboration.

## Task Overview
Implement Wave 1 tests to validate dynamic replication works correctly in a 3-node local Weaviate cluster. This is the foundational validation phase before proceeding to resilience testing.

## Specific Requirements
1. **Environment Setup**: Verify 3-node cluster (ports 8080,8081,8082) using docker-compose.test.yml
2. **Cluster Detection**: Create Python script using ClientManager to verify 3 healthy nodes
3. **Collection Creation**: Generate scripts to create system collections (CONFIG, FEEDBACK, METADATA) with replication_factor=3
4. **Data Verification**: Implement commands to check data availability across all nodes
5. **Derived Collections**: Test inheritance of replication settings from parent collections

## Key Scripts Needed
- `cluster_check.py`: Detect and report node status
- `create_system_collections.py`: Initialize ELYSIA_* collections with proper replication
- `verify_replication.py`: Confirm data sync across nodes
- `test_derived_collections.py`: Validate CHUNKED_* inheritance

## Success Criteria
- [ ] Cluster shows 3 healthy nodes
- [ ] System collections created with factor=3
- [ ] Data written to node 1 readable from nodes 2 & 3
- [ ] Derived collections inherit parent replication
- [ ] No errors in Elysia or Weaviate logs

## Execution Notes
Use the existing testing/phase4/ directory. Coordinate with human for Docker operations. Focus on clear, verifiable outputs for each test case.</content>
<parameter name="file_path">testing/phase4/wave1-implementation-prompt.md