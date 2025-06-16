# Changelog

## [1.0.0] - 2025-06-16

### Added
- Migrated backend from Flask to FastAPI
- Added comprehensive API documentation with OpenAPI/Swagger
- Added Prometheus metrics endpoint at `/metrics`
- Added health check endpoint at `/api/v1/health`
- Added proper CORS configuration for frontend integration
- Added static file serving for frontend assets
- Added proper error handling with global exception handler
- Added startup and shutdown event handlers
- Added comprehensive logging with structured data
- Added Redis connection management with proper error handling
- Added database connection pooling and health checks
- Added model management with singleton pattern
- Added WiFi agent integration with anomaly detection
- Added resource monitoring capabilities
- Added status management with Redis persistence

### Changed
- Updated all API endpoints to use FastAPI routing
- Updated request/response models to use Pydantic
- Updated database queries to use SQLAlchemy async patterns
- Updated Redis operations to handle JSON serialization
- Updated Docker configuration to use port 5000
- Updated startup scripts to use uvicorn instead of Flask
- Updated requirements.txt with FastAPI dependencies
- Updated CORS configuration for development environment

### Fixed
- Fixed Redis connection issues with proper timeout configuration
- Fixed import errors by resolving circular dependencies
- Fixed async/await usage in all components
- Fixed JSON serialization for Redis storage
- Fixed database connection pooling configuration
- Fixed model manager singleton pattern implementation
- Fixed static file serving directory creation
- Fixed port conflicts in Docker Compose configuration
- Fixed frontend API integration with correct data structures
- Fixed logs endpoint to return real data from PostgreSQL
- Fixed dashboard endpoint to return expected data structure

### Removed
- Removed Flask-specific code and dependencies
- Removed old API routing structure
- Removed unused Flask blueprints and extensions
- Removed deprecated configuration files

### Technical Details
- Backend now runs on FastAPI with uvicorn ASGI server
- All endpoints follow RESTful conventions
- Proper async/await patterns throughout the codebase
- Comprehensive error handling and logging
- Redis used for caching and status management
- PostgreSQL used for persistent data storage
- Prometheus metrics for monitoring
- Docker containerization with proper networking
- Development environment with hot reload support 