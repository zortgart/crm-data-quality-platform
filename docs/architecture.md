# Architecture — CRM Data Quality & Enrichment Platform

> **Living document** — updated after every phase completion.
> Last updated: Phase 6 — Data Quality

---

## Phase Completion Status

| Phase | Status | Summary |
|---|---|---|
| 1 — Local Foundation | ✅ Complete | Django + DRF + PostgreSQL + health endpoints |
| 2 — Database Foundation | ✅ Complete | Organization, CustomUser, UUID PKs, migrations |
| 3 — Security Foundation | ✅ Complete | JWT auth, RBAC roles, logout blacklist, tenant isolation |
| 4 — Core Domain | ✅ Complete | Companies, Contacts CRUD |
| 5 — PostgreSQL + ORM | ✅ Complete | Indexes, EXPLAIN, N+1 |
| 6 — Data Quality | ✅ Complete | Normalize, validate, deduplicate, score |
| 7 — Large Data | 🔜 Next | CSV import, streaming |
| 8 — Background Processing | ⏳ | Celery + Redis |
| 9 — Enterprise Features | ⏳ | Audit, caching, observability |
| 10 — Testing + Performance | ⏳ | 1M row benchmarks |
| 11 — Optional AI | ⏳ | AI provider abstraction |
| 12 — Docker | ⏳ | Containerization |
| 13 — CI/CD | ⏳ | GitHub Actions |
| 14 — AWS | ⏳ | Production architecture |

---

## System Architecture (Current — Phase 3)

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

---

## PHASE 3 — Security Foundation (Added)

### New Files Added

```
accounts/
├── serializers.py     ← CustomTokenObtainPairSerializer, UserProfileSerializer
├── views.py           ← LoginView, logout_view, RefreshView, me_view
├── urls.py            ← auth URL patterns
└── permissions.py     ← IsAdminRole, IsManagerOrAbove, IsAnalystOrAbove, IsSameOrganization

config/
└── api_urls.py        ← /api/v1/ central API router

tests/
└── test_auth.py       ← 19 tests (login, logout, RBAC, tenant isolation)
```

### API Endpoints (Phase 3)

| Method | URL | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/auth/login/` | ❌ Public | Email + password → access + refresh tokens |
| `POST` | `/api/v1/auth/logout/` | ✅ Bearer | Blacklist refresh token |
| `POST` | `/api/v1/auth/refresh/` | ❌ Public | Swap refresh → new access token |
| `GET` | `/api/v1/auth/me/` | ✅ Bearer | Current user profile |

### JWT Flow (Implemented)

```
Client                          Server
──────────────────────────────────────────────────────
POST /auth/login/          →    Validate email + password
{ email, password }             CustomTokenObtainPairSerializer
                           ←    { access (60min), refresh (7days), user{} }

GET /auth/me/              →    JWTAuthentication reads Bearer token
Authorization: Bearer ...       Validates signature + expiry
                           ←    { id, email, role, org_id, full_name }

POST /auth/refresh/        →    Validate refresh token
{ refresh }                     Old token blacklisted (ROTATE=True)
                           ←    { access (new), refresh (new) }

POST /auth/logout/         →    RefreshToken.blacklist()
{ refresh }                     Token stored in token_blacklist_blacklistedtoken
                           ←    { message: "Successfully logged out." }
```

### Custom JWT Payload Claims

```json
{
  "token_type": "access",
  "exp": 1234567890,
  "user_id": "b33dea29-9c71-4cd9-...",
  "email": "alice@acme.com",
  "role": "ADMIN",
  "first_name": "Alice",
  "last_name": "Admin",
  "organization_id": "uuid-of-acme-org"
}
```
Client decodes this (Base64) to know role + org without extra API call.
The signature (HMAC-SHA256) prevents tampering.

### RBAC Permission Classes (Implemented)

| Class | Allowed Roles | Use On |
|---|---|---|
| `IsAdminRole` | ADMIN only | User mgmt, org settings, audit logs |
| `IsManagerOrAbove` | ADMIN + MANAGER | Company/Contact CRUD, imports |
| `IsAnalystOrAbove` | All authenticated | Read-only lists, dashboard |
| `IsSameOrganization` | Object-level check | Any per-object endpoint (IDOR prevention) |

**Usage pattern (Phase 4+):**
```python
@api_view(["GET"])
@permission_classes([IsManagerOrAbove])
def create_contact(request):
    ...
```

**Java equivalent:**
```java
@PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
public ResponseEntity<ContactDTO> createContact(...) { ... }
```

### New Database Tables (Phase 3 — JWT Blacklist)

```
token_blacklist_outstandingtoken   ← every issued refresh token recorded
token_blacklist_blacklistedtoken   ← blacklisted (logged-out) tokens
```

### DRF Global Defaults Set (Phase 3)

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["JSONRenderer"],
}
```
Every endpoint is now authenticated by default. Public endpoints opt out with `permission_classes=[AllowAny]`.

### Test Count After Phase 3

| File | Tests | Covers |
|---|---|---|
| `test_health.py` | 8 | Health + readiness endpoints |
| `test_models.py` | 14 | Organization + User models |
| `test_auth.py` | 19 | Login, logout, refresh, /me/, RBAC, tenant |
| **Total** | **41** | |

---

## PHASE 4 — Core Domain (Added)

### New Files Added

```
companies/
├── models.py          ← Company model
├── serializers.py     ← CompanyListSerializer, CompanyDetailSerializer
├── views.py           ← CompanyViewSet
├── urls.py            ← Company routes
└── admin.py           ← Company admin

contacts/
├── models.py          ← Contact model
├── serializers.py     ← ContactListSerializer, ContactDetailSerializer
├── views.py           ← ContactViewSet
├── urls.py            ← Contact routes
└── admin.py           ← Contact admin

tests/
├── test_companies.py  ← 5 tests (CRUD, RBAC, tenant isolation)
└── test_contacts.py   ← 3 tests (CRUD, cross-tenant validation)
```

### API Endpoints (Phase 4)

| Method | URL | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/companies/` | ✅ ANALYST | List companies (tenant scoped) |
| `POST` | `/api/v1/companies/` | ✅ MANAGER | Create company |
| `GET` | `/api/v1/companies/{id}/` | ✅ ANALYST | Retrieve company |
| `PUT/PATCH` | `/api/v1/companies/{id}/` | ✅ MANAGER | Update company |
| `DELETE` | `/api/v1/companies/{id}/` | ✅ MANAGER | Delete company |
| `GET` | `/api/v1/contacts/` | ✅ ANALYST | List contacts (tenant scoped) |
| `POST` | `/api/v1/contacts/` | ✅ MANAGER | Create contact |
| `GET` | `/api/v1/contacts/{id}/` | ✅ ANALYST | Retrieve contact |
| `PUT/PATCH` | `/api/v1/contacts/{id}/` | ✅ MANAGER | Update contact |
| `DELETE` | `/api/v1/contacts/{id}/` | ✅ MANAGER | Delete contact |

### Security & Multi-Tenancy Enforcement

- **Organization ID injected server-side**: When creating a Company or Contact, the client CANNOT specify the organization. It's injected automatically via `perform_create(self, serializer)` using `request.user.organization`.
- **Tenant-scoped queries**: `get_queryset()` in ViewSets ALWAYS filters by the user's organization. Cross-tenant access is impossible.
- **Cross-tenant references prevented**: `ContactDetailSerializer.validate_company()` ensures you can't assign a Contact to a Company belonging to a different organization.

### Performance Optimization

- Used `select_related("organization")` (and `"company"`) in ViewSets to perform SQL JOINs, avoiding N+1 query problems when serializers access related fields.

### Test Count After Phase 4

| File | Tests | Covers |
|---|---|---|
| `test_health.py` | 8 | Health + readiness endpoints |
| `test_models.py` | 14 | Organization + User models |
| `test_auth.py` | 19 | Login, logout, refresh, /me/, RBAC, tenant |
| `test_companies.py` | 5 | Companies CRUD, RBAC, isolation |
| `test_contacts.py` | 3 | Contacts CRUD, cross-tenant validation |
| `test_performance.py` | 1 | N+1 query prevention (select_related) |
| `test_validation.py` | 10 | Normalizers, Quality Score, Duplicate Detector, Integration |
| **Total** | **60** | |

---

## PHASE 6 — Data Quality (Added)

### Pipeline Architecture

When a `Contact` is created or updated via the API, `ContactViewSet` triggers a 3-step synchronous pipeline before returning the response:

1. **Normalization:**
   - **Email:** Lowercased, stripped.
   - **Phone:** Parsed to E.164 standard using Google's `phonenumbers` library.
   - **Company Name:** Stripped of common legal suffixes (e.g. "Inc.", "Corp.") and lowercased.
   - **Job Title:** Common abbreviations expanded ("Sr. Eng." → "Senior Engineer").
2. **Quality Scoring:**
   - A `quality_score` (0-100) is dynamically computed based on data completeness (Valid Email: +30, Valid Phone: +20, Has Company: +20, First/Last Name: +20, Job Title: +10).
3. **Duplicate Detection:**
   - Evaluates the new/updated contact against all other contacts in the same organization.
   - Creates `DuplicatePair` records using `bulk_create(ignore_conflicts=True)` with different confidence tiers:
     - **L1 (100%):** Exact normalized email match.
     - **L2 (80%):** Exact normalized phone match.
     - **L3 (60%):** Exact normalized name + company match.

### New Models
- `DuplicatePair`: Tracks flagged duplicates. Uses `unique_together` for `(contact_a, contact_b)`.

### Test Count After Phase 6
Total tests: **60** (Added `test_validation.py` with 10 unit and integration tests)

---

## PHASE 5 — PostgreSQL + ORM (Added)

### Database Optimizations

**N+1 Query Prevention:**
Verified that fetching a list of Contacts does not generate a separate query for each contact's Company or Organization. Achieved using Django's `select_related()` and validated via `CaptureQueriesContext` in `tests/test_performance.py`.

**PostgreSQL Indexes Added:**
1. `idx_contacts_org_name`: Composite index `(organization_id, last_name, first_name)` for fast sorting of a tenant's contact list.
2. `idx_contacts_quality`: Single index on `(quality_score)` for dashboard aggregations.
3. `idx_contacts_org_created`: Composite index on `(organization_id, created_at)` for time-series lookups.
Note: Django automatically creates an index for any `ForeignKey` (e.g., `organization_id`), so base tenant isolation queries are already indexed.

### Performance Testing Utilities
- `common/management/commands/generate_mock_data.py`: CLI tool to generate 10,000+ synthetic contacts and 50+ companies in seconds using `bulk_create`.
- `common/management/commands/explain_queries.py`: CLI tool to run and print PostgreSQL's `EXPLAIN ANALYZE` for typical ORM queries.

### Test Count After Phase 5
Total tests: **50** (Added `test_performance.py`)
