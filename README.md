# CRM Data Quality & Enrichment Platform

A production-quality Django REST API for CRM data management, validation, enrichment, and quality scoring. Built as a comprehensive learning project covering enterprise backend engineering patterns.

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 5.x + Django REST Framework |
| Database | PostgreSQL 16+ (local) |
| Auth | JWT (djangorestframework-simplejwt) |
| Background Jobs | Celery + Redis (Phase 8+) |
| Testing | pytest + pytest-django |
| Docs | OpenAPI 3 / Swagger (drf-spectacular) |
| Containerization | Docker (Phase 12+) |
| CI/CD | GitHub Actions (Phase 13+) |
| Cloud | AWS (Phase 14+) |

---

## Local Windows Setup (Phase 1)

### Prerequisites

1. **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
2. **PostgreSQL 16+** — [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
3. **Git** — already initialized in this repo

Verify installations:
```powershell
python --version       # Should be 3.12+
psql --version         # Should be 16+
git --version
```

---

### Python Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Command Prompt)
.venv\Scripts\activate.bat

# Verify activation (you should see (.venv) in prompt)
python --version
pip --version
```

---

### Install Dependencies

```powershell
# Install all development dependencies
pip install -r requirements/development.txt

# Verify
pip list
```

---

### Environment Variables

```powershell
# Copy the template
copy .env.example .env

# Edit .env with your PostgreSQL credentials
# (Use Notepad, VS Code, or any text editor)
notepad .env
```

---

### PostgreSQL Setup

Connect to PostgreSQL as the admin user:
```powershell
psql -U postgres
```

Run these SQL commands:
```sql
-- Create the application database
CREATE DATABASE crm_platform;

-- Create a dedicated application user (never use postgres superuser)
CREATE USER crm_user WITH PASSWORD 'your_secure_password';

-- Grant the user access to the database
GRANT ALL PRIVILEGES ON DATABASE crm_platform TO crm_user;

-- Grant schema permissions (PostgreSQL 15+ requires this)
\c crm_platform
GRANT ALL ON SCHEMA public TO crm_user;

-- Verify
\l    -- List databases
\du   -- List users
\q    -- Quit
```

Update your `.env`:
```
DATABASE_NAME=crm_platform
DATABASE_USER=crm_user
DATABASE_PASSWORD=your_secure_password
```

---

### Running Django

```powershell
# Run database migrations (Phase 2+ adds models)
python manage.py migrate

# Start development server
python manage.py runserver

# Server starts at: http://127.0.0.1:8000
```

---

### Verify Health Endpoints

```powershell
# Liveness check
curl http://localhost:8000/health/
# Expected: {"status": "ok", "service": "crm-data-quality-platform"}

# Readiness check (verifies PostgreSQL)
curl http://localhost:8000/ready/
# Expected: {"status": "ready", "checks": {"database": "ok"}}
```

---

### Running Tests

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_health.py -v

# Run only tests that don't require DB (fast)
pytest -m "not django_db"
```

---

## Project Structure

```
crm-data-quality-platform/
├── config/                  # Project settings & URL configuration
│   ├── settings/
│   │   ├── base.py          # Shared settings (all environments)
│   │   ├── development.py   # Local development overrides
│   │   └── test.py          # Test-specific settings
│   ├── urls.py              # Root URL routing
│   ├── wsgi.py              # Production WSGI entry point
│   └── asgi.py              # ASGI entry point (async)
│
├── common/                  # Shared views, utilities, base classes
│   ├── views.py             # /health/ and /ready/ endpoints
│   └── urls.py
│
├── requirements/            # Split requirements by environment
│   ├── base.txt             # Core dependencies
│   ├── development.txt      # Dev tools (pytest, ipython)
│   └── test.txt             # CI/CD test dependencies
│
├── tests/                   # All tests
│   └── test_health.py       # Phase 1 health endpoint tests
│
├── docs/                    # Documentation
│   ├── architecture.md
│   └── interview-notes.md
│
├── manage.py                # Django management CLI
├── requirements.txt         # Convenience (points to development.txt)
├── pytest.ini               # Pytest configuration
├── .env.example             # Environment variable template
├── .env                     # Local secrets (NOT committed)
└── .gitignore
```

---

## Implementation Phases

| Phase | Status | Description |
|---|---|---|
| 1 — Local Foundation | ✅ Complete | Django + DRF + PostgreSQL + health endpoints |
| 2 — Database Foundation | 🔜 Next | Models, migrations, constraints, psql/pgAdmin |
| 3 — Security Foundation | ⏳ | JWT, RBAC, multi-tenancy |
| 4 — Core Domain | ⏳ | Companies + Contacts CRUD |
| 5 — PostgreSQL + ORM | ⏳ | Indexes, EXPLAIN ANALYZE, N+1 |
| 6 — Data Quality | ⏳ | Normalization, validation, scoring |
| 7 — Large Data | ⏳ | CSV import, streaming, bulk ops |
| 8 — Background Processing | ⏳ | Celery + Redis |
| 9 — Enterprise Features | ⏳ | Audit, caching, rate limiting |
| 10 — Testing + Performance | ⏳ | 1M row benchmarks |
| 11 — Optional AI | ⏳ | AI provider abstraction |
| 12 — Docker | ⏳ | Containerization |
| 13 — CI/CD | ⏳ | GitHub Actions |
| 14 — AWS | ⏳ | Production architecture |

---

## Security Architecture

- JWT authentication (access + refresh tokens)
- Role-based access control: ADMIN / MANAGER / ANALYST
- Multi-tenancy: row-level isolation, server-enforced
- Input validation via DRF serializers
- Rate limiting on sensitive endpoints
- No hardcoded credentials (all via environment variables)
- Structured error responses (no stack traces exposed)

See [docs/architecture.md](docs/architecture.md) for full details.
