# IRIS API Integration System

A production-ready, SOC2/HIPAA-compliant backend system for IRIS API integration with comprehensive audit logging, data retention management, and healthcare record processing.

## 🚀 Production Status: READY

This system is now **production-ready** with:
- ✅ Complete database migrations
- ✅ Comprehensive security implementation  
- ✅ All API endpoints functional
- ✅ SOC2-compliant audit logging
- ✅ Healthcare PHI/PII encryption
- ✅ Production deployment scripts
- ✅ Docker containerization

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Python 3.11+ (for development)

### Development Setup (5 minutes)

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd 2_scraper
cp .env.example .env  # Already configured for development
```

2. **Start with Docker (Recommended):**
```bash
# Start all services (app, database, redis, workers)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

3. **Run database migrations:**
```bash
# Migrations are auto-applied on startup, or run manually:
docker-compose exec app python -m alembic upgrade head
```

4. **Access the application:**
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (development only)

### Production Deployment

1. **Configure production environment:**
```bash
cp .env.production.template .env.production
# Edit .env.production with your production values
```

2. **Deploy with automated script:**
```bash
./deploy.sh deploy
```

3. **Verify deployment:**
```bash
./deploy.sh health
```

### Manual Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start database and Redis
docker-compose up -d db redis

# Run migrations
python -m alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start background workers (separate terminals)
celery -A app.core.tasks worker --loglevel=info
celery -A app.core.tasks beat --loglevel=info
```

## Architecture

**Modular Monolith with Event-Driven Patterns**

- **Core API Gateway**: FastAPI with JWT authentication and RBAC
- **IRIS Integration Module**: Secure external API communication with circuit breakers
- **Audit Logger Module**: SOC2-compliant immutable logging with integrity chains
- **Purge Scheduler Module**: Intelligent data retention and legal hold management
- **Healthcare Records Module**: FHIR-compliant PHI/PII processing with encryption
- **Event Bus**: Advanced async communication with at-least-once delivery

## Project Structure

```
app/
├── core/                    # Core system components
│   ├── config.py           # Configuration management
│   ├── database.py         # Basic database models
│   ├── database_advanced.py # Production-ready models
│   ├── security.py         # Authentication & encryption
│   ├── event_bus.py        # Event-driven communication
│   └── tasks.py            # Background task management
├── modules/                 # Business logic modules
│   ├── auth/               # Authentication module
│   ├── iris_api/           # IRIS API integration
│   ├── audit_logger/       # SOC2 audit logging
│   └── purge_scheduler/    # Data retention management
├── utils/                  # Utility functions
├── tests/                  # Test suite
└── main.py                 # Application entry point
```

## Features

### Security & Compliance
- ✅ JWT-based authentication with role-based access control
- ✅ AES-256 encryption for sensitive data
- ✅ SOC2-compliant audit logging with blockchain-style integrity
- ✅ Rate limiting and request validation
- ✅ Secure credential management

### IRIS API Integration
- ✅ OAuth2/HMAC authentication support
- ✅ Circuit breaker pattern for resilience
- ✅ Request/response encryption
- ✅ Comprehensive error handling and retry logic
- ✅ Health monitoring and alerting

## 📡 API Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /register` - User registration with RBAC
- `POST /login` - JWT authentication with MFA support
- `GET /me` - Current user profile
- `PUT /me` - Update user profile
- `GET /users` - List users (admin only)
- `POST /forgot-password` - Password reset workflow
- `POST /logout` - Token invalidation

### IRIS API Integration (`/api/v1/iris/`)
- `GET /health` - IRIS endpoint health checks
- `GET /health/summary` - System health overview
- `POST /endpoints` - Create API endpoint configuration
- `POST /endpoints/{id}/credentials` - Add encrypted credentials
- `POST /sync` - Synchronize patient data from IRIS
- `GET /sync/status/{id}` - Check sync operation status
- `GET /status` - Legacy IRIS status endpoint

### Audit Logging (`/api/v1/audit/`)
- `GET /health` - Audit service health
- `GET /stats` - Audit logging statistics
- `POST /logs/query` - Advanced audit log queries
- `GET /logs` - Basic audit log retrieval
- `POST /reports/compliance` - Generate SOC2 compliance reports
- `GET /reports/types` - Available report types
- `POST /integrity/verify` - Verify audit log integrity
- `GET /siem/configs` - SIEM export configurations
- `POST /siem/export/{config}` - Export logs to SIEM
- `POST /replay/events` - Event replay for investigation

### Data Retention (`/api/v1/purge/`)
- `GET /health` - Purge scheduler health
- `GET /policies` - Data retention policies
- `GET /status` - Purge scheduler status

### Healthcare Records (`/api/v1/healthcare/`)
- `GET /health` - Healthcare service health
- `POST /documents` - Create clinical documents
- `GET /documents` - List clinical documents with PHI protection
- `GET /documents/{id}` - Get specific document
- `POST /consents` - Create patient consent records
- `GET /consents` - List patient consents
- `POST /fhir/validate` - Validate FHIR resources
- `POST /anonymize` - Anonymize PHI data for research
- `GET /audit/phi-access` - PHI access audit logs
- `GET /compliance/summary` - Healthcare compliance status

### System (`/`)
- `GET /` - API information
- `GET /health` - Overall system health
- `GET /docs` - OpenAPI documentation (dev only)

### Data Management
- ✅ Intelligent purge scheduling with override conditions
- ✅ Configurable retention policies
- ✅ Soft-delete with recovery windows
- ✅ Emergency purge suspension mechanisms
- ✅ Cascade deletion logic

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Setup with Docker

1. **Clone and navigate to project**
   ```bash
   cd /path/to/project
   ```

2. **Copy environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database**
   ```bash
   # Start PostgreSQL and Redis
   # Run database migrations
   alembic upgrade head
   ```

3. **Start application**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Start background workers**
   ```bash
   # In separate terminals
   celery -A app.core.tasks worker --loglevel=info
   celery -A app.core.tasks beat --loglevel=info
   ```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info

### IRIS API
- `GET /api/v1/iris/status` - Check IRIS integration status
- `POST /api/v1/iris/sync` - Trigger data synchronization

### Audit Logging
- `GET /api/v1/audit/logs` - Retrieve audit logs (admin)
- `GET /api/v1/audit/stats` - Get audit statistics

### Purge Management
- `GET /api/v1/purge/policies` - List retention policies
- `GET /api/v1/purge/status` - Get purge scheduler status

## Development

### Testing
```bash
pytest app/tests/
```

### Code Quality
```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
ruff app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Security Considerations

- All sensitive data is encrypted at rest and in transit
- Audit logs are immutable with cryptographic integrity verification
- Role-based access control with temporal validity
- Rate limiting and request validation
- Secure credential storage with automatic rotation

## Compliance

This system is designed to meet:
- **SOC2 Type II** requirements for audit logging
- **HIPAA** requirements for healthcare data protection
- **GDPR** requirements for data retention and deletion

## Monitoring

Key metrics monitored:
- API response times and error rates
- Database connection pool status
- Queue lengths and processing times
- Security events and access patterns
- Data retention and purge operations

## Production Deployment

For production deployment:
1. Use environment-specific configuration
2. Enable SSL/TLS certificates
3. Configure proper database backups
4. Set up monitoring and alerting
5. Implement log aggregation
6. Configure auto-scaling policies

## License

[Your License Here]