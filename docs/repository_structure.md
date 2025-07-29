# Repository Structure Guide

This guide explains the EdgeOS API repository structure to help developers understand how to add new integrations and extend the system.

## Overview

EdgeOS is a FastAPI-based application with a modular architecture that follows Python best practices. The codebase is organized into clear, logical directories that separate concerns and make it easy to add new features and integrations.

## Root Directory Structure

```
citizen_portal_api/
├── app/                    # Main application code
├── docs/                   # Documentation files
├── scripts/                # Utility scripts and demo data
├── tests/                  # Test suites
├── docker-compose.yml      # Docker container orchestration
├── Dockerfile              # Docker image definition
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── README.md               # Project overview and setup
```

## Core Application (`app/`)

The main application code is organized into three primary directories:

### Core Components (`app/core/`)

Contains shared utilities and configuration used throughout the application:

- **`config.py`**: Environment variables, settings, and configuration management
- **`database.py`**: Database connection and session management
- **`models.py`**: Base database models and shared model utilities
- **`security.py`**: Authentication, authorization, and security utilities
- **`mail.py`**: Email service configuration and utilities
- **`simplefi.py`**: SimpleFi API integration utilities
- **`payments_utils.py`**: Payment processing utilities and helpers
- **`cache.py`**: Caching mechanisms and Redis integration
- **`locks.py`**: Distributed locking mechanisms for concurrent operations
- **`logger.py`**: Logging configuration and utilities
- **`utils.py`**: General utility functions
- **`exceptions/`**: Custom exception classes

### API Modules (`app/api/`)

Each domain has its own module following a consistent structure:

```
app/api/
├── base_crud.py           # Base CRUD operations for all modules
├── common/                # Shared API utilities
├── applications/          # Application management
├── attendees/             # Event attendee management
├── check_in/              # Check-in system
├── citizens/              # Citizen management
├── coupon_codes/          # Coupon/discount system
├── email_logs/            # Email tracking and logs
├── groups/                # Group management
├── organizations/         # Organization management
├── payments/              # Payment processing
├── popup_city/            # PopUp City management
├── products/              # Product catalog
├── access_tokens/         # API access token management
└── webhooks/              # Webhook handling
```

#### Standard API Module Structure

Each API module typically contains:

- **`models.py`**: SQLAlchemy database models
- **`schemas.py`**: Pydantic models for request/response validation
- **`routes.py`**: FastAPI route definitions and endpoints
- **`crud.py`**: Database operations (Create, Read, Update, Delete)
- **`dependencies.py`**: FastAPI dependencies (optional)

### Background Processes (`app/processes/`)

Contains automated background tasks and scheduled processes:

- **`auto_approval.py`**: Automated application approval logic
- **`send_reminder_emails.py`**: Reminder email scheduling
- **`send_scheduled_emails.py`**: General scheduled email processing

## Scripts (`scripts/`)

Utility scripts and demo data:

- **`populate_demo_data.py`**: Database population script
- **`popup_city.json`**: Demo PopUp City data
- **`email_templates.csv`**: Email template definitions
- **`citizen_applications.csv`**: Demo application data
- **`products.csv`**: Demo product catalog

## Testing (`tests/`)

Comprehensive test suite organized by module:

- **`conftest.py`**: Pytest configuration and fixtures
- **`test_*.py`**: Module-specific test files
- Tests follow the same structure as the API modules

## Adding New Integrations

### 1. Creating a New API Module

To add a new integration (e.g., `external_service`):

1. **Create the module directory**:
   ```
   mkdir app/api/external_service
   ```

2. **Follow the standard structure**:
   ```
   app/api/external_service/
   ├── __init__.py
   ├── models.py      # Database models
   ├── schemas.py     # Pydantic schemas
   ├── routes.py      # API endpoints
   └── crud.py        # Database operations
   ```

3. **Register the router in `main.py`**:
   ```python
   from app.api.external_service.routes import router as external_service_router
   
   app.include_router(
       external_service_router, 
       prefix='/external-service', 
       tags=['External Service']
   )
   ```

### 2. Database Integration

1. **Define models in `models.py`**:
   ```python
   from sqlalchemy import Column, Integer, String
   from app.core.database import Base
   
   class ExternalServiceRecord(Base):
       __tablename__ = "external_service_records"
       
       id = Column(Integer, primary_key=True)
       external_id = Column(String, unique=True)
       # ... other fields
   ```

2. **Create Pydantic schemas in `schemas.py`**:
   ```python
   from pydantic import BaseModel
   
   class ExternalServiceCreate(BaseModel):
       external_id: str
       # ... other fields
   
   class ExternalServiceResponse(BaseModel):
       id: int
       external_id: str
       # ... other fields
   ```

### 3. Configuration

Add configuration variables to `app/core/config.py`:

```python
class Settings:
    # ... existing settings
    EXTERNAL_SERVICE_API_KEY: str = os.getenv('EXTERNAL_SERVICE_API_KEY')
    EXTERNAL_SERVICE_URL: str = os.getenv('EXTERNAL_SERVICE_URL')
```

### 4. Background Processes

For background tasks, create files in `app/processes/`:

```python
# app/processes/external_service_sync.py
async def sync_external_service():
    # Synchronization logic
    pass
```

### 5. Testing

Create corresponding test files in `tests/`:

```python
# tests/test_external_service.py
def test_external_service_creation():
    # Test logic
    pass
```

## Key Patterns and Conventions

### 1. Database Patterns

- Use SQLAlchemy ORM for database models
- Follow the Base class pattern from `app.core.database`

### 2. API Patterns

- FastAPI routers for endpoint organization
- Pydantic schemas for request/response validation
- Dependency injection for authentication and database sessions
- Consistent error handling using custom exceptions

### 3. Configuration Management

- Environment variables for all configuration
- Type hints for all configuration variables
- Default values where appropriate
- Separation of test, development, and production settings

### 4. Error Handling

- Custom exception classes in `app/core/exceptions/`
- Consistent error response format
- Proper HTTP status codes

### 5. Security

- API key authentication for different modules
- Role-based access control where needed
- Input validation and sanitization

## Integration Points

### NocoDB Integration

- Webhook handlers in `app/api/webhooks/`
- Configuration in `app/core/config.py`
- Documentation in `docs/nocodb_webhooks.md`

### Email System

- Email utilities in `app/core/mail.py`
- Email processes in `app/processes/`
- Templates and scheduling system

### Payment Processing

- Payment utilities in `app/core/payments_utils.py`
- Payment API in `app/api/payments/`
- Integration with external payment providers

## Development Workflow

1. **Set up environment**: Use Docker Compose for local development
2. **Create feature branch**: Use descriptive branch names with `feature/*` format
3. **Implement changes**: Follow the established patterns
4. **Write tests**: Maintain test coverage
5. **Update documentation**: Keep docs current
6. **Code review**: Follow project standards

## Best Practices

- **Modularity**: Keep modules focused and loosely coupled
- **Documentation**: Document all public APIs and complex logic
- **Testing**: Write tests for all new functionality
- **Error Handling**: Provide meaningful error messages
- **Performance**: Consider caching and database optimization
- **Security**: Always validate input and implement proper authentication

This structure ensures maintainability, scalability, and ease of integration for new features and external services. 

---

**← [Back to Documentation Index](./index.md)**
