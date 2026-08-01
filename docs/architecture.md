# Architecture — CRM Data Quality & Enrichment Platform

> **Living document** — updated after every phase completion.
> Last updated: Phase 2 — Database Foundation

---

## Phase Completion Status

| Phase | Status | Summary |
|---|---|---|
| 1 — Local Foundation | ✅ Complete | Django + DRF + PostgreSQL + health endpoints |
| 2 — Database Foundation | ✅ Complete | Organization, CustomUser, UUID PKs, migrations |
| 3 — Security Foundation | 🔜 Next | JWT, RBAC, multi-tenancy enforcement |
| 4 — Core Domain | ⏳ | Companies, Contacts CRUD |
| 5 — PostgreSQL + ORM | ⏳ | Indexes, EXPLAIN, N+1 |
| 6 — Data Quality | ⏳ | Normalize, validate, deduplicate, score |
| 7 — Large Data | ⏳ | CSV import, streaming |
| 8 — Background Processing | ⏳ | Celery + Redis |
| 9 — Enterprise Features | ⏳ | Audit, caching, observability |
| 10 — Testing + Performance | ⏳ | 1M row benchmarks |
| 11 — Optional AI | ⏳ | AI provider abstraction |
| 12 — Docker | ⏳ | Containerization |
| 13 — CI/CD | ⏳ | GitHub Actions |
| 14 — AWS | ⏳ | Production architecture |

---

## System Architecture (Current — Phase 2)

```
Client (HTTP)
     │
     ▼
Django REST Framework (API Layer)
     │
     ├── [Phase 3] JWT Authentication Middleware
     ├── [Phase 3] Tenant Resolution Middleware
     ├── [Phase 9] Rate Limiting Middleware
     ├── [Phase 9] Request ID / Correlation ID Middleware
     │
     ▼
Views (Function-Based → Class-Based ViewSets in Phase 4)
     │
     ▼
Business Logic / Services
     │
     ├── [Phase 6] Data Quality Pipeline
     │     ├── Normalization (email, phone, job-title, company)
     │     ├── Validation
     │     ├── Duplicate Detection (L1/L2/L3)
     │     └── Enrichment (provider abstraction)
     │
     ▼
Django ORM
     │
     ▼
PostgreSQL 18 (local Windows)
     → Phase 14: AWS RDS PostgreSQL
```

**Phase 8+ (Background Processing):**
```
Django ──► Local Redis ──► Celery Workers ──► PostgreSQL
```

---

## Project Structure (Current)

```
crm-data-quality-platform/
├── config/                      # Django project config
│   ├── settings/
│   │   ├── base.py              # Shared settings (all envs)
│   │   ├── development.py       # Local dev overrides
│   │   └── test.py              # Test-specific settings
│   ├── urls.py                  # Root URL routing
│   ├── wsgi.py                  # Production WSGI entry
│   └── asgi.py                  # ASGI entry (async)
│
├── common/                      # Shared utilities
│   ├── models.py                # ✅ UUIDModel, TimeStampedModel (abstract)
│   ├── views.py                 # ✅ /health/ and /ready/ endpoints
│   └── urls.py                  # ✅ Health URL routing
│
├── organizations/               # ✅ Phase 2: Tenant root
│   ├── models.py                # Organization model
│   ├── admin.py
│   └── migrations/0001_initial.py
│
├── accounts/                    # ✅ Phase 2: Auth + Users
│   ├── models.py                # CustomUser, UserRole, UserManager
│   ├── admin.py
│   └── migrations/0001_initial.py
│
├── [Phase 3] companies/         # Company management
├── [Phase 3] contacts/          # Contact management
├── [Phase 6] validation/        # Data quality pipeline
├── [Phase 6] enrichment/        # Enrichment providers
├── [Phase 7] imports/           # CSV bulk imports
├── [Phase 9] audit/             # Audit logging
│
├── tests/
│   ├── test_health.py           # ✅ 8 tests (Phase 1)
│   └── test_models.py           # ✅ 14 tests (Phase 2)
│
├── docs/
│   ├── architecture.md          # This file
│   └── interview-notes.md       # Interview Q&A per phase
│
├── manage.py
├── requirements/
│   ├── base.txt                 # Django, DRF, psycopg, decouple
│   ├── development.txt          # + pytest, django-extensions, ipython
│   └── test.txt                 # + pytest only
├── pytest.ini
├── .env.example
└── .gitignore
```

---

## Database Architecture (Phase 2)

### Current Tables in PostgreSQL

```
organizations                      accounts_user
─────────────────────────────      ──────────────────────────────────────
id          UUID  PK               id              UUID  PK
name        VARCHAR(255) NOT NULL  email           VARCHAR(254) UNIQUE
slug        VARCHAR(100) UNIQUE    password        VARCHAR(128) [hashed]
is_active   BOOLEAN DEFAULT TRUE   first_name      VARCHAR(100)
created_at  TIMESTAMPTZ            last_name       VARCHAR(100)
updated_at  TIMESTAMPTZ            role            VARCHAR(20) [choices]
                                   organization_id UUID  FK → organizations
                                   is_active       BOOLEAN
                                   is_staff        BOOLEAN
                                   is_superuser    BOOLEAN
                                   last_login      TIMESTAMPTZ
                                   created_at      TIMESTAMPTZ
                                   updated_at      TIMESTAMPTZ
```

### Entity Relationships (Current)

```
Organization (1) ──────────── (N) User
```

### Planned Relationships (Phase 3-7)

```
Organization (1) ──── (N) User
Organization (1) ──── (N) Company
Organization (1) ──── (N) Contact
Organization (1) ──── (N) ImportJob
Company      (1) ──── (N) Contact
Contact      (N) ──── (N) Contact    [via DuplicatePair]
ImportJob    (1) ──── (N) ImportRow
User         (1) ──── (N) AuditLog
```

### Key Constraints (Phase 2)

| Table | Constraint | Type | Purpose |
|---|---|---|---|
| `organizations` | `slug` | UNIQUE | URL-safe tenant identifier must be unique |
| `accounts_user` | `email` | UNIQUE | Login identifier must be unique |
| `accounts_user` | `organization_id` | FK | Enforces referential integrity |
| Both | `id` | UUID PK | Non-guessable IDs, no IDOR via sequential IDs |

### Planned Indexes (Phase 5)

```sql
-- Every tenant-scoped query filters by organization_id
CREATE INDEX idx_contacts_org      ON contacts(organization_id);
CREATE INDEX idx_companies_org     ON companies(organization_id);
CREATE INDEX idx_import_jobs_org   ON import_jobs(organization_id);

-- Dashboard aggregation
CREATE INDEX idx_contacts_quality  ON contacts(quality_score);

-- Duplicate detection
CREATE INDEX idx_contacts_email_norm ON contacts(normalized_email);

-- Import job polling
CREATE INDEX idx_import_jobs_status ON import_jobs(status, created_at);
```

---

## Multi-Tenancy Architecture

**Strategy:** Shared schema, row-level tenant isolation

```python
# Every model will have:
organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

# Every ViewSet will override get_queryset():
def get_queryset(self):
    return super().get_queryset().filter(
        organization=self.request.user.organization
    )
```

**Rules (never break these):**
- ✅ Organization resolved from authenticated JWT token
- ✅ QuerySet always filtered by `organization_id`
- ❌ NEVER trust `organization_id` from request body
- ❌ NEVER expose data across organization boundaries
- ✅ Test tenant isolation explicitly (IDOR/BOLA tests in Phase 3)

---

## Security Architecture

### Authentication (Phase 3)
```
POST /api/v1/auth/login/
     │
     ▼
Validate email + password
     │
     ▼
djangorestframework-simplejwt
     ├── Access Token  (short-lived: 60 min)
     └── Refresh Token (long-lived: 7 days, rotated on use)

Client: Authorization: Bearer <access_token>
```

### RBAC — Role-Based Access Control

| Role | Access |
|---|---|
| `ADMIN` | Full: CRUD + user management + audit logs + imports |
| `MANAGER` | Companies + Contacts CRUD + imports + enrichment |
| `ANALYST` | Read-only: contacts/companies/imports + dashboard |

**Implementation:**
```python
class UserRole(models.TextChoices):
    ADMIN   = "ADMIN",   "Admin"
    MANAGER = "MANAGER", "Manager"
    ANALYST = "ANALYST", "Analyst"

# Default: ANALYST (principle of least privilege)
role = models.CharField(default=UserRole.ANALYST)
```

### Security Layers (Progressive)

| Phase | Layer | Implementation |
|---|---|---|
| 1 | Health endpoints | `AllowAny` — intentionally public |
| 3 | JWT Auth | `djangorestframework-simplejwt` |
| 3 | RBAC | Custom DRF permission classes |
| 3 | Tenant isolation | ORM queryset filtering |
| 9 | Rate limiting | `django-ratelimit` |
| 9 | File upload | MIME type + size validation |
| All | Secrets | `python-decouple` — never hardcoded |
| All | SQL | ORM parameterized queries — no concatenation |

---

## Data Quality Pipeline (Phase 6)

```
Contact Input
     │
     ▼  1. Normalization
     │     Email → lowercase, strip, punycode
     │     Phone → E.164 (phonenumbers library)
     │     Company → strip suffixes (Corp., LLC, Inc.)
     │     Job Title → Sr.→Senior, Eng.→Engineer
     │
     ▼  2. Validation
     │     Email format, phone validity, required fields
     │
     ▼  3. Duplicate Detection
     │     L1: normalized_email match    → HIGH confidence
     │     L2: phone match               → MEDIUM confidence
     │     L3: name + company match      → LOW confidence
     │     Optional: fuzzy (rapidfuzz)
     │
     ▼  4. Enrichment
     │     EnrichmentProvider (ABC)
     │     MockCompanyProvider (dev)
     │     MockContactProvider (dev)
     │
     ▼  5. Quality Scoring (100 points)
          Valid email:           +25
          Valid phone:           +20
          Verified company:      +20
          Normalized job title:  +15
          Employment verified:   +20
```

---

## Large Data Strategy (Phase 7)

| Concern | Approach |
|---|---|
| CSV upload | Stream — never load entirely into memory |
| Processing | Chunks of 500–1000 rows |
| DB writes | `bulk_create()` / `bulk_update()` with `batch_size` |
| Memory | Generators and iterators throughout |
| Transactions | Each chunk in its own `transaction.atomic()` |
| Errors | Row errors logged to `ImportRow`, don't abort whole import |
| Progress | `ImportJob.processed` counter updated per chunk |

**Target:** 1M+ contacts without OOM or timeouts.

---

## Environment Configuration

| Variable | Purpose | Phase |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django signing key | 1 |
| `DJANGO_SETTINGS_MODULE` | Which settings file to use | 1 |
| `DEBUG` | Debug mode (never True in prod) | 1 |
| `DATABASE_*` | PostgreSQL connection | 1 |
| `REDIS_URL` | Redis broker URL | 8 |
| `CELERY_BROKER_URL` | Celery message broker | 8 |
| `OPENAI_API_KEY` | Optional AI (Phase 11) | 11 |
| `AWS_*` | Cloud deployment | 14 |
