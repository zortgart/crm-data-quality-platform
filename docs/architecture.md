# Architecture — CRM Data Quality & Enrichment Platform

## System Architecture

```
Client (HTTP)
     │
     ▼
Django REST Framework
     │
     ├── JWT Middleware (Phase 3)
     ├── Tenant Resolution Middleware (Phase 3)
     ├── Rate Limiting Middleware (Phase 9)
     ├── Request ID Middleware (Phase 9)
     │
     ▼
Business Logic
     │
     ├── Data Quality Pipeline (Phase 6)
     │     ├── Normalization
     │     ├── Validation
     │     ├── Duplicate Detection
     │     └── Enrichment
     │
     ▼
Django ORM
     │
     ▼
PostgreSQL (local → RDS in Phase 14)

Phase 8+:
Django ──► Redis ──► Celery Workers ──► PostgreSQL
```

## Multi-Tenancy Strategy

- Shared schema, row-level isolation
- Every table has `organization_id` FK
- Every queryset filters by `request.user.organization_id`
- Client-supplied `organization_id` is NEVER trusted

## Security Layers

1. JWT token verification
2. RBAC permission classes
3. Object-level tenant checks
4. Input sanitization via serializers
5. Rate limiting
6. File upload validation

## Database Design

See Phase 2 for detailed entity design and migration strategy.
