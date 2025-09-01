# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.dev2] - 2025-09-01

### Added
- Auto-initialization for missing users to prevent session errors
- Automatic user creation when session not found (e.g., after server restart)
- Optional `auto_create` parameter in `get_user_local()` for backward compatibility

## [0.2.dev1] - 2025-09-01

### Added

#### Infrastructure and Configuration
- Local Weaviate support without requiring API keys for anonymous access
- Multi-node cluster detection and configuration
- Dynamic replication factor based on cluster size
- gRPC port detection for local multi-node clusters
- Environment variable support for `WEAVIATE_IS_LOCAL` flag
- Frontend configuration management for local Weaviate settings
- Configurable local Weaviate ports (HTTP and gRPC)

#### Error Handling Architecture
- Implemented recoverable endpoint decorator pattern (ADR-001)
- Added middleware layer at `/opt/elysia/elysia/api/middleware/recovery.py`
- Standardized error responses across 8 critical API endpoints
- Comprehensive error transformation with appropriate HTTP status codes
- Server-side exception logging while maintaining clean client responses

#### Documentation
- Architecture Decision Record (ADR-001) for recoverable endpoint error handling
- Architecture Decision Record (ADR-002) for system collection namespace convention
- Frontend error handling guide for API integration
- Phase-based implementation specifications (Phases 1-6)
- Specification development guidance (CLAUDE.md)
- Enhanced local Weaviate setup instructions

#### Testing
- Comprehensive test suite for local Weaviate connectivity
- Recovery middleware unit tests
- Client manager tests for local and cloud configurations
- Integration tests for multi-node cluster scenarios

### Changed

#### API Improvements
- ClientManager now supports both local and cloud Weaviate instances seamlessly
- User configuration endpoints prevent overriding frontend storage settings
- Collection creation respects cluster size for replication factor
- Port configuration now uses frontend_config values instead of hardcoded ports

#### Error Response Standardization
- User not found: HTTP 401 "Session not initialized"
- Collection not found: HTTP 404 with collection name
- Missing fields: HTTP 422 with field identification
- Service unavailable: HTTP 503 with appropriate messaging
- Internal errors: HTTP 500 with generic message

### Fixed

#### Connection Issues
- Fixed "Invalid port: '8080:443'" error for local Weaviate connections
- Resolved API key validation bypass for local instances
- Corrected port extraction logic in ClientManager
- Fixed authentication flow for anonymous local access

#### Configuration Issues
- Replaced hardcoded Weaviate ports throughout codebase
- Fixed replication factor for ELYSIA_CONFIG collections in multi-node setups
- Resolved frontend configuration override issues

### Security

- Internal collection names (ELYSIA_*) are filtered from client error messages
- Full exception details logged server-side while exposing only safe messages to clients
- Established reserved namespace convention for system collections
- Prevented leakage of implementation details through error responses

## Files Modified

- **Core System**: 38 files changed, 3032 insertions(+), 33 deletions(-)
- **API Routes**: 4 route files updated with error handling decorators
- **Configuration**: Enhanced support for local and cloud deployments
- **Documentation**: Added 6 phase specifications and 2 ADRs
- **Testing**: Added comprehensive test coverage for local configurations

## Migration Notes

No breaking changes. The error handling improvements are backward compatible. Existing deployments will continue to function with enhanced error responses and security.

## Contributors

Implementation completed through collaborative agent-based development with specialized teams for backend, frontend, QA, and testing.