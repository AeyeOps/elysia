# Implementation Prompt for Wave 3: Edge Cases & Error Handling

## System Context
You are testing edge cases and error handling in Elysia's replication system. Focus on fail-fast behavior, clear error messages, and graceful degradation.

## Task Overview
Validate system responses to misconfigurations, boundary conditions, and concurrent operations to ensure robust error handling and user-friendly failures.

## Specific Requirements
1. **Misconfiguration Detection**: Test invalid replication factors, missing parents, network issues
2. **Single-Node Behavior**: Verify system works with replication_factor=None
3. **Error Message Quality**: Ensure clear, actionable error messages for failures
4. **Concurrent Operations**: Test simultaneous collection creation from multiple connections
5. **Boundary Testing**: Validate behavior with edge cases (empty data, large datasets)

## Key Scripts Needed
- `misconfiguration_tests.py`: Test various invalid configurations and error responses
- `single_node_validation.py`: Verify single-node mode without replication
- `concurrent_operations.py`: Simulate multiple simultaneous collection operations
- `error_message_audit.py`: Collect and analyze error messages for clarity

## Success Criteria
- [ ] Clear, actionable error messages for misconfigurations
- [ ] Single-node mode works without replication settings
- [ ] No race conditions in concurrent creation
- [ ] Fail-fast behavior with invalid inputs
- [ ] Graceful handling of network interruptions

## Execution Notes
Document all error scenarios encountered. Focus on user experience - errors should guide users to solutions. Coordinate with human for manual error induction. Estimated time: 1-2 hours.</content>
<parameter name="file_path">testing/phase4/wave3-implementation-prompt.md