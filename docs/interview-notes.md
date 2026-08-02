# Interview Notes — CRM Data Quality & Enrichment Platform

> **Living document** — a new section is added after every phase.
> Use this to prepare for backend engineering interviews.
> Last updated: Phase 8 — Background Processing

---

## PHASE 1 — Local Foundation

### Key Concepts

#### 1. Python Virtual Environments
**What:** Isolated Python environment — packages installed here don't affect the global Python or other projects.
**Why:** Projects have conflicting dependency versions. Isolation solves this.
**How:** `python -m venv .venv` → `.venv\Scripts\Activate.ps1`
**Java equivalent:** Maven/Gradle per-project dependency isolation. But venv is an explicit folder you activate.

**Interview Q:** *"How do you manage Python dependency isolation?"*
**Answer:** Virtual environments (`venv`). Production: pin exact versions in `requirements.txt`. In teams, use `pip-tools` or `poetry` for deterministic builds.

---

#### 2. Django Settings Split (base / development / test)
**What:** Settings split by environment so dev config never leaks to production.
**Why:** `DEBUG=True` in production exposes stack traces — a serious security vulnerability.
**How:** `DJANGO_SETTINGS_MODULE=config.settings.development` in `.env`
**Java equivalent:** Spring Profiles — `application-dev.yml`, `@Profile("dev")`

**Interview Q:** *"How do you manage multiple environments in Django?"*
**Answer:** Split settings files. Secrets via environment variables — never hardcoded. `python-decouple` reads `.env` file with type casting.

---

#### 3. Environment Variables & Secrets Management
**What:** Never hardcode secrets. Read from environment at runtime.
**Why:** Hardcoded secrets in Git history can never be fully removed — a permanent security exposure.
**How:** `.env` file (gitignored) + `python-decouple`. `.env.example` committed (template, no real values).
**Java equivalent:** Spring's `@Value("${property}")`, `application.properties`, externalized config.

**Rule:** `.env` → gitignored. `.env.example` → committed.

**Interview Q:** *"How do you prevent secrets from being committed to Git?"*
**Answer:** `.gitignore`, environment variables, `.env.example` template, secret scanning in CI (Phase 13).

---

#### 4. Liveness vs Readiness Health Checks
**What:**
- **Liveness** (`/health/`): "Is the process running?" — no dependency checks, always fast
- **Readiness** (`/ready/`): "Can the app serve traffic?" — checks DB, Redis, etc.

**Why separate?** A process can be alive but not ready (DB is down). Don't restart it — remove from load balancer.
**Java equivalent:** Spring Boot Actuator `/actuator/health/liveness` and `/actuator/health/readiness`. Kubernetes uses these as probes.

**Interview Q:** *"What's the difference between liveness and readiness probes?"*
**Answer:** Liveness = process health → restart if fails. Readiness = dependency health → remove from load balancer, don't restart.

---

#### 5. WSGI vs ASGI
- **WSGI:** Synchronous. Traditional Django. Used by gunicorn, uWSGI.
- **ASGI:** Async. Supports WebSockets. Used by uvicorn, Daphne. Django 5.x supports async views.
- **Java equivalent:** WSGI ≈ Servlet/Tomcat. ASGI ≈ Reactive WebFlux/Netty.

---

#### 6. `manage.py` — Django CLI
**What:** Single entry point for all developer tasks.
**Commands:** `runserver`, `migrate`, `makemigrations`, `shell`, `createsuperuser`, `check`
**Java equivalent:** Maven goals (`mvn spring-boot:run`) or Gradle tasks.

---

#### 7. `urls.py` vs `views.py`
- **`urls.py`** = Routing table. Maps URL patterns to view functions. Like `@RequestMapping` in Spring.
- **`views.py`** = Business logic handler. Receives request, does work, returns response. Like `@RestController` in Spring.

**Flow:** Request → `urls.py` matches pattern → calls `views.py` function → returns JSON response.

---

### Phase 1 Interview Questions (10)

1. What is a Python virtual environment and why is it needed?
2. How does Django's settings module system work? How do you handle multiple environments?
3. What's the difference between liveness and readiness health checks?
4. Why should `.env` files never be committed to Git?
5. What is WSGI? What is ASGI? When would you use each?
6. How does `python-decouple` work? What does it read first — `.env` file or actual environment variables?
7. Why do we set `USE_TZ=True` in Django settings?
8. What does `DEFAULT_AUTO_FIELD` control in Django?
9. What's the purpose of `requirements/base.txt` vs `requirements/development.txt`?
10. Why is `DEBUG=True` a security vulnerability in production?

---

---

## PHASE 2 — Database Foundation

### Key Concepts

#### 1. Abstract Base Models (`abstract = True`)
**What:** A model with `abstract = True` never creates its own DB table. It exists only to be inherited.
**Why:** DRY — define `id`, `created_at`, `updated_at` once; inherit everywhere.
**How:**
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True  # ← no table created for this

class Organization(UUIDModel, TimeStampedModel):
    pass  # ← gets id, created_at, updated_at automatically
```
**Java equivalent:** `@MappedSuperclass` — a JPA base class that is never an `@Entity` itself.

**Interview Q:** *"What is `@MappedSuperclass` equivalent in Django?"*
**Answer:** A model with `abstract = True` in its `Meta` class. No table is created; fields are inherited by child models.

---

#### 2. Custom User Model (`AUTH_USER_MODEL`)
**What:** Replaces Django's built-in `auth.User` with our own model.
**Why:** Built-in User uses `username` as login field. We want `email`. We also need `role` and `organization`.
**Critical rule:** Must be set BEFORE the first migration. This is a one-way door — changing it later requires manual schema surgery.
**Java equivalent:** Implementing Spring Security's `UserDetails` interface on your `@Entity User` class.

```python
# config/settings/base.py
AUTH_USER_MODEL = "accounts.User"  # set before ANY migrations
```

**Interview Q:** *"Why must you set AUTH_USER_MODEL before the first migration?"*
**Answer:** Django bakes FK references to the user model into every migration file. If you change it after, all those references point to the wrong table. You'd have to manually rewrite migrations, move data, and fix FK constraints.

---

#### 3. `AbstractBaseUser` vs `AbstractUser`
| | `AbstractUser` | `AbstractBaseUser` |
|---|---|---|
| Keeps `username` field | ✅ Yes | ❌ No |
| Keeps built-in fields | ✅ Yes | ❌ Only `password` + `last_login` |
| Control over fields | Limited | Full control |
| We use | ❌ | ✅ (we want email login, no username) |

**Interview Q:** *"When would you use AbstractBaseUser over AbstractUser?"*
**Answer:** When you need full control — especially to change the login field from username to email, or remove fields Django's AbstractUser includes by default.

---

#### 4. UUID Primary Keys
**What:** UUID (128-bit) instead of auto-increment integer as primary key.
**Why:**
- ✅ IDs are not guessable — prevents IDOR (Insecure Direct Object Reference) attacks
- ✅ Can be generated before DB insert — useful for distributed systems
- ✅ Globally unique across all tables
- ❌ Slightly larger (16 bytes vs 4/8 bytes)
- ❌ Non-sequential — slightly slower B-tree index inserts

```python
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
```

**Java equivalent:**
```java
@Id @GeneratedValue(generator = "UUID")
@GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
private UUID id;
```

**Interview Q:** *"Why use UUID over auto-increment integer PKs?"*
**Answer:** Security (not guessable = no IDOR), distributed uniqueness (no coordination needed), works across multiple databases. Trade-off: slightly larger storage and potentially slower index performance.

---

#### 5. Django ORM — Model to Table Mapping
**What:** Each Django model class maps to one PostgreSQL table. Fields map to columns.
**Java equivalent:** JPA `@Entity` class → Hibernate creates/manages the table.

```python
# Python model           →    PostgreSQL table
class Organization:           organizations
    id = UUIDField()     →    id UUID PRIMARY KEY
    name = CharField()   →    name VARCHAR(255) NOT NULL
    slug = SlugField(    →    slug VARCHAR(100) UNIQUE
          unique=True)
```

Django's migration system generates the exact SQL — you can inspect it:
```powershell
python manage.py sqlmigrate organizations 0001
```

---

#### 6. Django Migrations — The Two-Step Process
**Step 1: `makemigrations`** — Reads your models and GENERATES a migration file (Python code describing the change).
**Step 2: `migrate`** — Reads migration files and RUNS the SQL against PostgreSQL.

```
models.py          0001_initial.py           PostgreSQL
(you write)   →   (auto-generated)   →      (tables created)
              makemigrations             migrate
```

Migration files are committed to Git — your whole team sees exactly what changed in the DB and when.

**Java equivalent:** Flyway or Liquibase migration files. Unlike Hibernate `ddl-auto=update`, Django migrations are explicit and version-controlled.

**Interview Q:** *"How does Django's migration system work?"*
**Answer:** Two commands: `makemigrations` reads models and generates Python migration files. `migrate` reads those files and executes the SQL. Files are committed to Git — like Flyway scripts.

---

#### 7. ForeignKey — Referential Integrity
```python
organization = models.ForeignKey(
    "organizations.Organization",
    on_delete=models.CASCADE,  # delete user if org deleted
    related_name="users",      # org.users.all() reverse lookup
)
```

`on_delete` options:
| Option | Behaviour |
|---|---|
| `CASCADE` | Delete child records when parent is deleted |
| `PROTECT` | Block parent deletion if children exist |
| `SET_NULL` | Set FK to NULL when parent deleted |
| `SET_DEFAULT` | Set FK to default when parent deleted |

**Java equivalent:** `@ManyToOne` with `CascadeType` and `@OneToMany(mappedBy=...)`

---

#### 8. RBAC Roles as TextChoices
```python
class UserRole(models.TextChoices):
    ADMIN   = "ADMIN",   "Admin"
    MANAGER = "MANAGER", "Manager"
    ANALYST = "ANALYST", "Analyst"
```
- Stored as string in DB: `"ADMIN"`, `"MANAGER"`, `"ANALYST"`
- Access in code: `UserRole.ADMIN`, `UserRole.ANALYST`
- Default: `ANALYST` — Principle of Least Privilege

**Java equivalent:** `@Enumerated(EnumType.STRING)` on an `enum UserRole { ADMIN, MANAGER, ANALYST }`

**Interview Q:** *"What is the Principle of Least Privilege?"*
**Answer:** Users are given the minimum access needed to do their job. In our system, new users default to ANALYST (read-only). Elevated access must be explicitly granted.

---

#### 9. Password Hashing
**Never store plain text passwords.**
```python
user.set_password("PlainText123")  # hashes using PBKDF2+SHA256+salt
user.check_password("PlainText123")  # returns True
user.check_password("Wrong")         # returns False
user.password  # → "pbkdf2_sha256$720000$salt$hash" — never the plain text
```
**Java equivalent:** `BCryptPasswordEncoder.encode()` / `.matches()`

**Interview Q:** *"How does Django store passwords?"*
**Answer:** PBKDF2 + SHA256 with a random salt. Format: `algorithm$iterations$salt$hash`. Never plain text. `set_password()` hashes; `check_password()` verifies by hashing the input and comparing.

---

#### 10. Django Admin
**What:** Auto-generated web UI for browsing/managing database data during development.
**Access:** http://localhost:8000/admin/ (requires superuser)
**Create superuser:** `python manage.py createsuperuser`
**Java equivalent:** Spring Boot Admin or a custom admin panel — but Django's is FREE and auto-generated.

---

### Phase 2 Interview Questions (10)

1. What is `AUTH_USER_MODEL` and why must it be set before the first migration?
2. What is the difference between `AbstractUser` and `AbstractBaseUser`?
3. What is `@MappedSuperclass` equivalent in Django?
4. Why use UUID primary keys? What are the trade-offs vs auto-increment?
5. How does Django's migration system work? How is it different from Hibernate `ddl-auto=update`?
6. What does `on_delete=CASCADE` do on a ForeignKey? Name two other options.
7. What is `related_name` on a ForeignKey and how do you use it?
8. How does Django store passwords? What algorithm does it use?
9. What is the Principle of Least Privilege? How is it applied in our User model?
10. What is `auto_now_add` vs `auto_now`? When would you use each?

---

---

## PHASE 3 — Security Foundation

### Key Concepts

#### 1. JWT — JSON Web Token
**What:** A compact, signed token used to prove identity. Three parts: `header.payload.signature`
**Why:** Stateless — the server doesn't store sessions. The token itself carries all the info needed (user_id, role, expiry). Scales horizontally with no shared state.
**How:**
```
Header:    { "alg": "HS256", "typ": "JWT" }  → Base64 encoded
Payload:   { "user_id": "uuid", "role": "ADMIN", "exp": 1234 }  → Base64 encoded
Signature: HMAC_SHA256(header + "." + payload, SECRET_KEY)
```
Client sends: `Authorization: Bearer <token>` on every request.

**Java equivalent:** `jjwt` library / Spring Security OAuth2 JWT support

**Interview Q:** *"Can you decode a JWT? Is it encrypted?"*
**Answer:** Yes, anyone can decode a JWT — it's Base64, not encrypted. But they CANNOT forge one without the SECRET_KEY because the signature would fail verification. Never put sensitive data (passwords, SSNs) in a JWT payload.

---

#### 2. Access Token vs Refresh Token
**What:**
- **Access Token:** Short-lived (60 min). Sent with every API request. If stolen, expires soon.
- **Refresh Token:** Long-lived (7 days). Only sent to `/auth/refresh/`. Used to get a new access token.

**Why two tokens?**
- If access token was long-lived (7 days) and stolen → attacker has 7 days of access.
- Short access token + long refresh token gives balance: convenience for users, security for ops.

**Java equivalent:** Same pattern in Spring Security OAuth2 — `access_token` + `refresh_token`

**Interview Q:** *"Why not just use one long-lived JWT?"*
**Answer:** A stolen long-lived JWT is a 7-day breach. Short access tokens (60 min) limit the damage window. The refresh token has a smaller attack surface — it's only ever sent to one endpoint.

---

#### 3. Token Blacklist (Logout)
**What:** On logout, the refresh token is recorded in `token_blacklist_blacklistedtoken` table. Any future `/refresh/` attempt with it fails.
**Why:** JWTs are stateless — you can't "delete" a token. Blacklisting is the only way to explicitly invalidate one.
**Limitation:** The access token STILL works until it expires (60 min). This is a known JWT trade-off. Mitigation: keep access token lifetime short.

**Tables created:**
```
token_blacklist_outstandingtoken  ← every issued refresh token
token_blacklist_blacklistedtoken  ← tokens that have been blacklisted
```

**Java equivalent:** A `revoked_tokens` table checked on every token validation.

**Interview Q:** *"How do you implement logout with JWT?"*
**Answer:** Blacklist the refresh token in the database. The access token remains valid until expiry — this is a known limitation. For stricter security, use very short access token lifetimes (5-15 min) or maintain a token version counter on the user record.

---

#### 4. RBAC — Role-Based Access Control
**What:** Users are assigned roles (ADMIN, MANAGER, ANALYST). Endpoints check the role before allowing access.
**Why:** Finer control than just "authenticated vs not". A data entry ANALYST shouldn't delete an organization.

**Our permission class hierarchy:**
```
AllowAny           → public (login, health checks)
IsAnalystOrAbove   → all logged-in users (read-only endpoints)
IsManagerOrAbove   → ADMIN + MANAGER (write endpoints)
IsAdminRole        → ADMIN only (user mgmt, system config)
IsSameOrganization → per-object tenant check (IDOR prevention)
```

**Java equivalent:**
```java
@PreAuthorize("hasRole('ADMIN')")              → IsAdminRole
@PreAuthorize("hasAnyRole('ADMIN','MANAGER')") → IsManagerOrAbove
@PreAuthorize("isAuthenticated()")             → IsAnalystOrAbove
```

**Interview Q:** *"How does DRF permission system work?"*
**Answer:** Two methods: `has_permission(request, view)` = view-level check (runs for all requests). `has_object_permission(request, view, obj)` = object-level check (runs only when a specific object is fetched). Both must return True for access.

---

#### 5. IDOR — Insecure Direct Object Reference
**What:** An attacker guesses/enumerates another user's resource ID and accesses it.
**Example:**
```
ACME user calls: GET /api/v1/contacts/some-uuid/
That UUID belongs to GLOBEX → should return 403, not the contact!
```
**Fix:** `IsSameOrganization` permission class checks `obj.organization_id == request.user.organization_id`
**Why UUID helps:** UUID IDs are not guessable (unlike integer 1, 2, 3...). But UUID alone is not enough — you must also check ownership.

**Java equivalent:** `@PostAuthorize("returnObject.organizationId == principal.organizationId")`

**Interview Q:** *"What is IDOR and how do you prevent it?"*
**Answer:** IDOR = accessing another user's data via a guessable/known ID. Prevention: 1) Use UUID (not sequential int) PKs, 2) Always check object ownership in permission layer, 3) Scope all querysets to the authenticated user's organization.

---

#### 6. DRF Serializers — Two Roles
**What:** Serializers handle both directions:
- **Incoming (Deserialization):** Validate + parse request body → Python object
- **Outgoing (Serialization):** Python object → JSON response

```python
# Incoming: like @RequestBody + @Valid in Spring
serializer = LoginSerializer(data=request.data)
serializer.is_valid(raise_exception=True)  # validates, raises 400 if invalid

# Outgoing: like Jackson ObjectMapper / DTO
serializer = UserProfileSerializer(request.user)
return Response(serializer.data)  # returns JSON
```

**Java equivalent:**
- Deserialization: `@RequestBody UserDTO dto` + `@Valid` + Bean Validation
- Serialization: Jackson `ObjectMapper` / `@JsonProperty` / record DTO

**Interview Q:** *"What is the difference between a Serializer and a ModelSerializer in DRF?"*
**Answer:** `Serializer` = fully manual, you define every field. `ModelSerializer` = auto-generates fields from a Django model (like Lombok + JPA entity). `ModelSerializer` is 80% of real-world usage. Use plain `Serializer` for non-model data (login requests, analytics responses).

---

#### 7. Custom Token Claims
**What:** We add extra data to the JWT payload beyond the default `user_id` and `exp`.
**Why:** The client (React app, mobile) can read the role and org_id from the token without making a separate API call.
```python
token["role"] = user.role              # "ADMIN", "MANAGER", "ANALYST"
token["organization_id"] = str(user.organization_id)
token["email"] = user.email
```
**Security note:** Claims are readable (Base64) but not modifiable (signature-protected).

**Interview Q:** *"What custom claims did you add to the JWT and why?"*
**Answer:** `role`, `organization_id`, `email`, `first_name`. This avoids the client needing to call `/auth/me/` immediately after login — it already knows who the user is and what they can do from the token itself.

---

#### 8. Token Rotation
**What:** `ROTATE_REFRESH_TOKENS=True` → every `/auth/refresh/` call issues a NEW refresh token and blacklists the old one.
**Why:** If a refresh token is stolen, the attacker can only use it once. The moment the legitimate user refreshes, the attacker's copy is blacklisted.
**Java equivalent:** Refresh token rotation is a standard OAuth2 security recommendation.

**Interview Q:** *"What is refresh token rotation and why is it important?"*
**Answer:** Issuing a new refresh token on every use and blacklisting the old one. If a token is stolen and used, the server detects two concurrent refresh attempts — one will fail. It also limits the window of any single token's usefulness.

---

#### 9. Default Authentication in DRF
**What:** Setting `DEFAULT_AUTHENTICATION_CLASSES` and `DEFAULT_PERMISSION_CLASSES` means EVERY view is automatically protected unless it explicitly opts out.
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["IsAuthenticated"],
}
```
**Why:** Secure by default — you can't accidentally leave an endpoint public. You must consciously add `permission_classes=[AllowAny]` to make something public.

**Java equivalent:** Spring Security's `.anyRequest().authenticated()` as the catch-all rule at the bottom of the security filter chain.

**Interview Q:** *"How do you secure an endpoint by default in DRF?"*
**Answer:** Set `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` in `REST_FRAMEWORK` settings. Then only endpoints that explicitly set `permission_classes = [AllowAny]` are public. This is "secure by default" — any new endpoint you add is automatically protected.

---

#### 10. DRF APIClient in Tests
**What:** `APIClient` is DRF's test HTTP client. It makes real HTTP requests through the Django test runner without a real server.
**How:**
```python
client = APIClient()
# Simulate JWT auth — no need for a real token in tests
client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
response = client.get("/api/v1/auth/me/")
```
**Java equivalent:** `MockMvc` in Spring Boot tests / `TestRestTemplate`

**Interview Q:** *"How do you test authenticated DRF endpoints?"*
**Answer:** Use `APIClient` from DRF's test package. Call `api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")` to attach a real JWT to all subsequent requests. Or use `api_client.force_authenticate(user=user)` to skip token generation entirely in unit tests.

---

### Phase 3 Interview Questions (10)

1. What is a JWT? What are its three parts? Is the payload encrypted?
2. What is the difference between an access token and a refresh token? Why do we have both?
3. How do you implement logout with JWT? What is the limitation?
4. What is RBAC? How are the permission classes structured in our platform?
5. What is IDOR? How do you prevent it with UUIDs and object-level permissions?
6. What is the difference between `has_permission` and `has_object_permission` in DRF?
7. What is `DEFAULT_PERMISSION_CLASSES` and why is "secure by default" important?
8. What is refresh token rotation? Why is it a security best practice?
9. What custom claims did we add to the JWT payload? Why?
10. What is the Java equivalent of DRF's `APIClient` in tests?

---

---

## PHASE 4 — Core Domain

### Key Concepts

#### 1. REST ViewSets (ModelViewSet)
**What:** DRF's `ModelViewSet` automatically provides full CRUD endpoints (`list`, `create`, `retrieve`, `update`, `partial_update`, `destroy`) mapped to a database model.
**Why:** Removes boilerplate. You don't need to write separate views for GET, POST, PUT, DELETE.
**How:** You define a class inheriting from `ModelViewSet`, point it to a queryset and a serializer class, and register it with a `DefaultRouter`.
**Java equivalent:** `@RestController` combined with Spring Data REST, which auto-generates CRUD endpoints for repositories.

**Interview Q:** *"How do you quickly create a full CRUD API in Django?"*
**Answer:** Use DRF's `ModelViewSet` and register it with a `DefaultRouter`. It automatically provides all 6 standard REST operations out of the box, which you can customize by overriding methods like `get_queryset()` or `perform_create()`.

---

#### 2. N+1 Query Problem & `select_related()`
**What:** N+1 is a performance issue where fetching a list of N items causes 1 query for the list, plus N additional queries to fetch a related foreign key (like accessing `contact.company.name` in a loop).
**Why:** It drastically slows down list views.
**How:** Use `select_related("foreign_key_field")` in your queryset. This tells Django to perform a SQL `JOIN` and fetch the related object in the same query.
**Java equivalent:** `@EntityGraph` or `JOIN FETCH` in JPQL.

**Interview Q:** *"What is the N+1 query problem and how do you solve it in Django?"*
**Answer:** N+1 happens when accessing a related object (like a foreign key) inside a loop, causing a new query for each item. In Django, we solve it using `select_related()` for foreign keys (does a SQL JOIN) or `prefetch_related()` for many-to-many/reverse relations (does one extra query using an IN clause).

---

#### 3. Tenant Data Isolation (Server-Side Injection)
**What:** In a multi-tenant SaaS, you must guarantee users can't create or read data belonging to another tenant.
**Why:** Trusting the client to send `{"organization_id": "123"}` is a critical security flaw.
**How:**
1.  **Read:** Override `get_queryset()` to `return Company.objects.filter(organization=self.request.user.organization)`.
2.  **Write:** Override `perform_create(self, serializer)` to inject it: `serializer.save(organization=self.request.user.organization)`.
**Java equivalent:** Using an interceptor, AOP, or base repository method `findAllByOrganizationId()` where `organizationId` is always pulled from the `SecurityContext`.

**Interview Q:** *"How do you ensure a user cannot create records for a different tenant in a SaaS application?"*
**Answer:** Never accept the tenant ID (organization ID) from the request payload. Always inject it server-side in the backend logic, pulling it from the authenticated user's context (e.g., overriding `perform_create()` in DRF to use `request.user.organization`).

---

#### 4. Multiple Serializers per ViewSet
**What:** Using different serializers for different actions within the same ViewSet (e.g., `ContactListSerializer` vs `ContactDetailSerializer`).
**Why:** Performance and payload size. A list view of 100 contacts doesn't need all 20 fields. A detail view for 1 contact needs everything.
**How:** Override `get_serializer_class()` in the ViewSet and return a different class based on `self.action` (e.g., if `self.action == 'list'`).
**Java equivalent:** Using different Jackson `@JsonView` profiles or returning different DTOs (e.g., `ContactSummaryDTO` vs `ContactDetailDTO`).

**Interview Q:** *"How do you return a smaller payload for list views compared to detail views in DRF?"*
**Answer:** Override the `get_serializer_class()` method in the ViewSet. Return a lightweight serializer if `self.action == 'list'`, and a full serializer otherwise.

---

#### 5. Cross-Tenant ForeignKey Validation
**What:** Ensuring that when creating a Contact linked to a Company, the provided Company actually belongs to the user's organization.
**Why:** A user could pass a valid `company_id` that belongs to a different tenant, effectively linking their contact to someone else's company.
**How:** Implement a `validate_company(self, company)` method on the serializer that checks if `company.organization == request.user.organization`.
**Java equivalent:** Validating the association in the service layer before saving: `if (!company.getOrganizationId().equals(currentUser.getOrganizationId())) throw new AccessDeniedException();`

**Interview Q:** *"If a user submits a valid foreign key ID in a payload, is it safe to just save it?"*
**Answer:** No. In a multi-tenant system, you must validate that the referenced foreign key record actually belongs to the current user's tenant before saving. Otherwise, you risk exposing or corrupting data across tenant boundaries.

### Phase 4 Interview Questions (5)

1. What is a `ModelViewSet` in Django REST Framework and what methods does it provide?
2. What is the N+1 query problem, and how do you solve it for foreign keys in Django?
3. How do you ensure tenant data isolation when reading and writing data in DRF ViewSets?
5. Why is cross-tenant foreign key validation necessary, and where do you implement it in DRF?

---

---

## PHASE 5 — PostgreSQL + ORM

### Key Concepts

#### 1. EXPLAIN ANALYZE
**What:** A PostgreSQL command that executes a query and returns the actual execution plan (cost, time, index usage).
**Why:** To diagnose slow queries and verify that your indexes are actually being used by the database optimizer.
**How:** In Django, you can call `.explain(analyze=True)` on a queryset.
**Java equivalent:** Prefixing a JPQL or native query with `EXPLAIN ANALYZE` in pgAdmin, or using a tool like `hypersistence-optimizer`.

**Interview Q:** *"How do you verify if a database index is being used by your Django query?"*
**Answer:** I generate the queryset and call `.explain(analyze=True)` on it. This tells PostgreSQL to execute the query and return the execution plan, showing whether it performed a 'Seq Scan' (full table scan) or an 'Index Scan' / 'Bitmap Index Scan'.

---

#### 2. Sequential Scan vs. Index Scan
**What:** 
- **Sequential Scan (Seq Scan):** The database reads the entire table from top to bottom.
- **Index Scan:** The database traverses a B-Tree index to quickly find the exact row pointers.
**Why:** Sequential scans are bad for large tables (O(N)), but sometimes chosen by PostgreSQL for very small tables or queries that return a large percentage of the table.

**Interview Q:** *"I added an index to a column, but EXPLAIN ANALYZE shows a Sequential Scan. Why?"*
**Answer:** The PostgreSQL query planner might decide a sequential scan is faster if the table is very small, or if your query condition (e.g., `score >= 0`) returns a large percentage of the rows in the table. In those cases, reading sequential disk blocks is cheaper than traversing the index and doing random I/O.

---

#### 3. Composite Indexes
**What:** An index created on multiple columns (e.g., `organization_id` + `last_name`).
**Why:** To optimize queries that filter by one column and sort/filter by another.
**How:** `models.Index(fields=["organization", "last_name"])` in Django's `Meta` class.
**Java equivalent:** `@Table(indexes = { @Index(name = "idx", columnList = "organization_id, last_name") })` in JPA/Hibernate.

**Interview Q:** *"If you have a multi-tenant app where you frequently list users by tenant, ordered by last name, what index would you create?"*
**Answer:** I would create a composite index on `(tenant_id, last_name)`. A single-column index on `tenant_id` would still require an in-memory sort for the last name. The composite index allows the database to instantly retrieve the records already sorted.

---

#### 4. Bulk Create (`bulk_create`)
**What:** An ORM method to insert multiple objects into the database in a single SQL query.
**Why:** Calling `.save()` in a loop of 10,000 items creates 10,000 separate `INSERT` statements, which is extremely slow due to network/transaction overhead.
**How:** Instantiate model objects in memory, append to a list, and call `Model.objects.bulk_create(list_of_objects, batch_size=5000)`.
**Java equivalent:** Hibernate JDBC batching (`spring.jpa.properties.hibernate.jdbc.batch_size=500`) + calling `saveAll()`.

**Interview Q:** *"How do you insert 10,000 rows into a database using an ORM efficiently?"*
**Answer:** You should never call `.save()` in a loop. You instantiate the objects in memory and use `bulk_create` (or `saveAll` in Java) with a `batch_size` to chunk the inserts. This reduces 10,000 SQL queries down to a small handful of large `INSERT` statements.

### Phase 5 Interview Questions (4)

1. How do you find out if a query is slow in PostgreSQL?
2. What is the difference between an Index Scan and a Sequential Scan?
3. When should you use a composite index instead of multiple single-column indexes?
4. How do you efficiently load thousands of records into the database?

---

---

## PHASE 6 — Data Quality

### Key Concepts

#### 1. Data Normalization
**What:** The process of cleaning and standardizing data formats before it is saved (e.g., lowercasing emails, expanding "Sr." to "Senior").
**Why:** It is required for accurate duplicate detection and searching. You cannot reliably find duplicates if one record has "john@acme.com" and the other has "John@Acme.com ".
**How:** We intercept the saving process in `perform_create` and `perform_update` inside DRF ViewSets, passing fields through normalizer functions before calling `save()`.
**Java equivalent:** Pre-persist hooks (`@PrePersist`) in JPA, or custom Jackson deserializers, or cleaning data inside the Service layer before calling `repository.save()`.

**Interview Q:** *"How do you handle dirty data like inconsistent casing in emails?"*
**Answer:** I build normalizers that run right before the data is saved to the database. For emails, I strip whitespace and lowercase them. I save both the original email (for display) and a `normalized_email` field specifically used for duplicate detection and fast lookups.

#### 2. E.164 Phone Format
**What:** The international standard for phone numbers (e.g., `+14155552671`), ensuring global uniqueness.
**Why:** Phone numbers come in hundreds of different formats. Normalizing to E.164 allows for exact duplicate detection.
**How:** Using Google's `phonenumbers` library (`pip install phonenumbers`), we parse the string and reformat it to `PhoneNumberFormat.E164`.

**Interview Q:** *"How would you detect if two differently formatted phone numbers are the same?"*
**Answer:** I would never try to write my own regex for that. I would use the standard Google `phonenumbers` library to parse both inputs and format them both into the E.164 standard. If the resulting E.164 strings match, they are the same phone number.

#### 3. Duplicate Detection Tiers (L1/L2/L3)
**What:** Finding duplicates using different fallback strategies with varying levels of confidence.
**Why:** Not all duplicates are obvious exact matches.
**How:** 
- L1 (100%): Exact match on normalized email.
- L2 (80%): Exact match on normalized phone.
- L3 (60%): Exact match on normalized First Name + Last Name + Company ID.
**Java equivalent:** Using a rules engine or cascading repository queries in a domain service.

**Interview Q:** *"How do you identify duplicate user records in a database?"*
**Answer:** I implement a tiered approach. First, I look for a high-confidence match like an exact normalized email match. If that fails, I drop to a medium-confidence match, like a normalized phone number. Finally, I use a lower-confidence heuristic, like matching the exact first name, last name, and company.

#### 4. Upserting / Ignoring Conflicts (`ignore_conflicts=True`)
**What:** Inserting records into a database while gracefully ignoring records that violate a unique constraint.
**Why:** When detecting duplicates, we might find a duplicate pair `(Contact A, Contact B)` that we already flagged previously. We don't want the database to throw an `IntegrityError`.
**How:** We use Django's `bulk_create(objects, ignore_conflicts=True)`.
**Java equivalent:** `INSERT ON CONFLICT DO NOTHING` native queries, or handling `DataIntegrityViolationException`.

**Interview Q:** *"If you try to insert 100 records and 1 of them violates a unique constraint, the whole transaction fails. How do you bypass this?"*
**Answer:** In Django, I use `bulk_create` with the `ignore_conflicts=True` flag. This translates to an `INSERT ... ON CONFLICT DO NOTHING` statement in PostgreSQL, allowing the 99 valid records to be inserted while silently skipping the 1 duplicate.

### Phase 6 Interview Questions (4)

1. Why is data normalization important before doing deduplication?
2. What is the E.164 format and why is it used?
3. How do you design a system to catch duplicates when data might be missing (e.g., no email)?
4. How do you insert multiple records and ignore ones that violate unique constraints?

---

---

## PHASE 7 — Large Data (Imports)

### Key Concepts

#### 1. Preventing Out-Of-Memory (OOM) Errors
**What:** The practice of processing data sequentially rather than loading it all into memory at once.
**Why:** If a user uploads a 500MB CSV file with 2 million rows, calling `file.read()` or `list(csv.reader)` will load the entire dataset into RAM. If multiple users do this simultaneously, the server will crash due to Out-Of-Memory (OOM) errors.
**How:** We use a text stream (`io.StringIO`) and iterate over it line-by-line using a generator (`for row in csv.DictReader(stream):`). 
**Java equivalent:** Java `BufferedReader.readLine()` or Spring Batch `FlatFileItemReader`, which streams lines from disk.

**Interview Q:** *"How would you handle a user uploading a 2-million row CSV file without crashing the server?"*
**Answer:** I would never load the entire file into memory. I would stream the file from disk (or network/S3) using a generator. I would read it line-by-line, process it in chunks (e.g., 500 rows at a time), and use batch inserts (`bulk_create` / JDBC batching) to write to the database. Once a chunk is written, those rows are garbage collected.

#### 2. Transaction Chunking
**What:** Breaking a massive database insert into smaller, atomic batches.
**Why:** Trying to insert 1,000,000 rows in a single database transaction locks tables for too long, uses excessive database memory, and risks rolling back all 1,000,000 rows if row 999,999 fails.
**How:** We group rows into arrays of ~500. We wrap the `bulk_create` for each chunk in its own `with transaction.atomic():` block.
**Java equivalent:** `@Transactional` on a chunk processing method in Spring Batch, or manual `TransactionTemplate` boundaries.

**Interview Q:** *"If you are inserting 1 million rows, should you use one large database transaction or a transaction for every row?"*
**Answer:** Neither. One transaction is too large and risks locking/rollback issues. A transaction per row is way too slow due to network and disk I/O overhead. The best approach is "chunking" — inserting batches of 500 to 1000 rows in a single transaction.

#### 3. Graceful Error Handling (Partial Success)
**What:** Allowing an import job to succeed for valid rows even if some rows contain errors.
**Why:** If 1 row in a 10,000 row CSV has a bad email, failing the entire file is terrible UX. 
**How:** We validate each row individually using our Serializer. Valid rows go into a `valid_contacts` array; invalid rows go into an `error_rows` array. We write both to the database, tracking the specific errors in an `ImportRow` table so the user can download an error report later.

**Interview Q:** *"A user uploads a CSV, but 5 rows have invalid data. How do you handle this?"*
**Answer:** I validate rows individually in memory. I insert the valid rows in bulk, and I log the failed rows (with their specific validation errors) to a separate 'ImportRow' error table. The import job finishes successfully, and the user can pull a report of just the 5 rows that failed to fix and re-upload.

### Phase 7 Interview Questions (3)

1. How do you prevent a Python/Java application from running out of memory when parsing a huge file?
2. What is "chunking" in the context of database transactions?
3. How do you design an import system that doesn't completely fail when encountering a single bad row of data?

---

---

## PHASE 8 — Background Processing (Celery)

### Key Concepts

#### 1. The Broker / Worker Pattern
**What:** Decoupling a long-running task from the main HTTP request thread. The web server sends a message to a "Broker" (Redis/RabbitMQ), and a separate "Worker" (Celery process) picks it up and runs it.
**Why:** HTTP requests are meant to be fast (completed in < 500ms). If an HTTP request takes 5 minutes to parse a CSV, the user's browser will time out, the load balancer will drop the connection, and server threads will be exhausted.
**How:** We integrated Celery and Redis. The DRF ViewSet saves the file to disk and calls `task.delay()`. The API immediately returns `201 Created` with a `status="PENDING"`. The frontend can then poll the API to update a progress bar.
**Java equivalent:** Spring `@Async` (simple threads), or a JMS queue (ActiveMQ / RabbitMQ) with a `@JmsListener` worker.

**Interview Q:** *"A user clicks 'Generate 100-page PDF report' and the API takes 2 minutes to respond, causing timeouts. How do you fix this?"*
**Answer:** I would implement the Broker/Worker pattern using Celery and Redis (or RabbitMQ). The API should immediately return a `202 Accepted` or `201 Created` with a `job_id`. The actual PDF generation happens asynchronously in a background Celery worker. The frontend can then poll a `/status/{job_id}` endpoint or receive a WebSocket notification when the PDF is ready.

#### 2. Eager Testing Mode
**What:** Running background tasks synchronously during unit tests.
**Why:** Unit testing asynchronous message queues is difficult and flaky. You don't want to require Redis to be running in your CI/CD pipeline just to run basic unit tests.
**How:** Setting `CELERY_TASK_ALWAYS_EAGER = True` in Django settings forces `.delay()` to execute immediately in the same thread.
**Java equivalent:** Using `SyncTaskExecutor` instead of `ThreadPoolTaskExecutor` in Spring test configurations.

**Interview Q:** *"If you move your logic into an asynchronous queue, how do you unit test it without making your test suite slow and flaky?"*
**Answer:** In development/testing, message queues usually have an 'eager' or 'synchronous' mode. In Django with Celery, I set `CELERY_TASK_ALWAYS_EAGER = True` in my test settings. This causes `.delay()` calls to execute synchronously in the same thread, allowing me to write standard, deterministic assertions without needing a running Redis instance or `time.sleep()`.

### Phase 8 Interview Questions (2)

1. Explain the Broker / Worker pattern and why it's necessary for web applications.
2. How do you handle unit testing for code that runs asynchronously in a background worker?

---

---

## PHASE 9 — Enterprise Features (Audit, Cache, Observability)

### Key Concepts

#### 1. Tenant-Safe Caching
**What:** Using caching (Redis/LocMem) to store frequently accessed but rarely changed data (like a list of companies) to save database queries.
**Why:** Improves API response times and reduces DB load.
**The Multi-Tenant Danger:** If you use `@cache_page` on `/api/v1/companies/` blindly, User A's response is cached. User B visits the same URL and gets User A's companies — a massive data leak.
**How:** We combine `@cache_page(60 * 5)` with `@vary_on_headers("Authorization")`. This ensures the cache key is unique *per user token*, safely isolating the cache per tenant.
**Java equivalent:** `@Cacheable` with a SpEL expression incorporating the principal/tenant ID (e.g., `@Cacheable(value = "companies", key = "#principal.organizationId")`).

**Interview Q:** *"How do you safely cache an API response in a multi-tenant application?"*
**Answer:** You must never cache globally by URL alone. The cache key must include the tenant identifier. In Django REST Framework, I use `@vary_on_headers("Authorization")` alongside the cache decorator so that every user gets their own isolated cached response.

#### 2. Audit Logging
**What:** Tracking every CUD (Create, Update, Delete) operation in the system.
**Why:** Enterprise compliance (SOC2, HIPAA) requires knowing *who* changed *what* and *when*.
**How:** A custom `AuditLogMiddleware` intercepts `POST`, `PUT`, `PATCH`, and `DELETE` requests. It extracts the user, organization, path, IP, and raw payload, and saves an `AuditLog` record asynchronously.
**Java equivalent:** Hibernate Envers for entity-level auditing, or a Spring `HandlerInterceptor` for API-level auditing.

**Interview Q:** *"How would you implement an audit trail to satisfy compliance requirements?"*
**Answer:** I would implement a middleware (or database triggers) that intercepts all state-altering requests (POST/PUT/DELETE). It logs the authenticated user, the timestamp, the IP address, the endpoint, and the payload/changes to a secure, append-only AuditLog table.

#### 3. Observability & Correlation IDs
**What:** Assigning a unique UUID (Correlation ID or `X-Request-ID`) to every single incoming HTTP request.
**Why:** In modern/microservice architectures, a single request might generate 50 log lines across different modules. Without a correlation ID, it is impossible to group those logs together when debugging a failure.
**How:** A `RequestIDMiddleware` generates a UUID and stores it in thread-local storage (`threading.local`). A custom Python `logging.Filter` injects this ID into every log formatter.
**Java equivalent:** MDC (Mapped Diagnostic Context) in SLF4J/Logback, combined with a generic Servlet Filter.

**Interview Q:** *"If an API request fails in production and generates 20 different log statements, how do you group them together to understand what happened?"*
**Answer:** I use Correlation IDs. A middleware generates a unique UUID at the start of the request and stores it in thread-local storage (or MDC in Java). A custom logging filter injects this ID into every log line. In our log aggregator (like Datadog or Splunk), I can simply search for that UUID and see the exact chronological trace of that specific request.

### Phase 9 Interview Questions (3)

1. What is the danger of caching API responses in a multi-tenant SaaS, and how do you prevent it?
2. What are the key pieces of information you must capture in an enterprise audit log?
3. What is a Correlation ID (or Request ID) and why is it critical for observability?

---

## PHASE 10 — Notification System

### Key Concepts

#### 1. Event-Driven Architecture (Django Signals)
**What:** A way to allow decoupled applications get notified when actions occur elsewhere in the framework (Publish/Subscribe pattern).
**Why:** If you hardcode notification logic into the CSV import process, your import logic becomes tightly coupled with the notification logic. Signals allow the `notifications` app to "listen" for `ImportJob` updates without the `imports` app needing to know about it.
**How:** We use `@receiver(post_save, sender=ImportJob)`. When an import finishes, it fires an event. The receiver catches it and creates a Notification.
**Java equivalent:** Spring Application Events (`ApplicationEventPublisher.publishEvent()`, `@EventListener`).

**Interview Q:** *"How do you decouple side-effects (like sending an email or notification) from core business logic?"*
**Answer:** I use an event-driven approach. In Django, this means using Signals. Instead of hardcoding the notification inside the `process_csv` function, the function simply saves the state of the job. A signal receiver listens for that `post_save` event and handles creating the notification. This keeps the core domain clean and adheres to the Single Responsibility Principle.

#### 2. Custom API Actions
**What:** Adding non-CRUD behavior to a REST ViewSet.
**Why:** Sometimes you need an endpoint that performs a specific action rather than just updating an entire object, like "Marking a notification as read."
**How:** Using DRF's `@action(detail=True, methods=['post'])` to expose `/api/v1/notifications/{id}/read/`.
**Java equivalent:** Adding a specific POST mapping `@PostMapping("/{id}/read")` in a Spring REST Controller.

**Interview Q:** *"How do you model an action like 'mark as read' in a RESTful API?"*
**Answer:** While REST is generally resource-oriented, pure state updates can sometimes be clunky if the client has to send the full JSON object just to flip a boolean. A common and accepted pattern is to expose a sub-resource or an action endpoint, like `POST /api/v1/notifications/{id}/read/`, which updates the internal state securely.

### Phase 10 Interview Questions (2)

1. What is the Observer pattern (Publish/Subscribe), and how do Django Signals implement it?
2. What are the pros and cons of using Signals vs placing the logic directly in the Model's `.save()` method? (Pro: decoupled. Con: can be hard to trace/debug if abused).

---

## PHASE 11 — Optional AI / Advanced Data

### Key Concepts

#### 1. The Strategy Pattern for AI Providers
**What:** A design pattern that defines a family of algorithms (e.g. AI models), encapsulates each one, and makes them interchangeable.
**Why:** You don't want your Views tightly coupled to the `openai` python package. If tomorrow you switch to Google Gemini or Anthropic Claude, or if you need to run offline tests, you don't want to rewrite your API logic.
**How:** We created `BaseEnrichmentProvider` (an Abstract Base Class) and concrete classes `OpenAIEnrichmentProvider` and `MockEnrichmentProvider`. A factory function `get_enrichment_provider()` decides which one to use at runtime.
**Java equivalent:** Interface `EnrichmentProvider` with implementations `@Service class OpenAiProvider implements EnrichmentProvider`. Spring uses `@Qualifier` or `@ConditionalOnProperty` to inject the right bean.

**Interview Q:** *"How would you integrate a 3rd-party API like OpenAI into your application without tightly coupling your business logic to it?"*
**Answer:** I use the Strategy Pattern (or Adapter Pattern). I define an interface (e.g., `EnrichmentProvider`) that outlines the inputs and expected structured outputs. Then I build a concrete implementation for OpenAI. My views/services only interact with the interface. This makes unit testing trivial (via a MockProvider) and allows for future-proofing if we switch AI vendors.

### Phase 11 Interview Questions (1)

1. What is the Strategy Pattern and how did you use it in the data enrichment feature? (Answered above).

---

## PHASE 12 — Docker Containerization (Interview Notes)

### How to Dockerize a Django/Celery/Postgres Stack

**Interview Q:** *"How would you containerize this application for production?"*
**Answer:** I would use Docker and `docker-compose`. I'd write a multi-stage `Dockerfile` for the Django app to keep the image size small. Then, my `docker-compose.yml` would define four services:
1. **db**: Official `postgres:16` image with a mounted volume for data persistence.
2. **redis**: Official `redis:7-alpine` image.
3. **web**: The Django app built from the Dockerfile, exposed on port 8000, running via a WSGI server like `gunicorn`. It depends on `db` and `redis`.
4. **worker**: The same Django image, but the startup command is overridden to `celery -A config worker --loglevel=info`.

**Key Docker Best Practices to Mention in Interviews:**
- **Multi-stage builds:** Compile dependencies (like `psycopg2`) in a builder stage, and copy only the installed wheels/libs to the final slim image.
- **Run as non-root:** Create a dedicated user inside the Dockerfile (e.g., `django-user`) so the container doesn't run as root, mitigating security risks if the container is compromised.
- **Wait-for-it scripts:** The web container must wait for the database to be ready before running `python manage.py migrate`.
- **Environment variables:** Never hardcode secrets in the Dockerfile. Pass them at runtime via `.env` files or orchestration secrets (like AWS Secrets Manager).

---

## PHASE 13 — CI/CD Pipeline (Interview Notes)

### How to Build a CI/CD Pipeline for Django

**Interview Q:** *"How do you ensure code quality before it reaches production?"*
**Answer:** I implement a Continuous Integration (CI) pipeline using a tool like GitHub Actions or GitLab CI. Whenever a developer opens a Pull Request, the pipeline automatically:
1. Runs linters (`flake8`, `black`) to ensure style consistency.
2. Spins up ephemeral database and cache services (Postgres and Redis).
3. Executes the full `pytest` suite.
4. Fails the PR if any tests fail or if test coverage drops below a certain threshold.

**Interview Q:** *"How do you deploy this application?"*
**Answer:** Through Continuous Deployment (CD). Once code is merged to `main`, the pipeline builds a new Docker image, tags it with the Git commit hash, pushes it to an Elastic Container Registry (ECR), and then updates the ECS/EKS service to seamlessly roll out the new containers with zero downtime.

---

## PHASE 14 — AWS Production Architecture (Interview Notes)

### Architecting for Scale and Reliability

**Interview Q:** *"If we need to handle 10,000 requests per minute and large CSV uploads, how would you architect this on AWS?"*
**Answer:** 
1. **Compute:** I'd run the Django API and Celery workers on ECS Fargate for serverless, autoscaling compute.
2. **Database:** I'd use Amazon RDS for PostgreSQL with Multi-AZ enabled for high availability. 
3. **Broker/Cache:** Amazon ElastiCache (Redis) would handle the Celery task queue and API caching.
4. **Storage:** I would never store CSVs on the local disk in production; I'd use Amazon S3 via `django-storages`. The Django API would generate a pre-signed S3 URL for the client to upload the file directly to S3, and then trigger a Celery task to stream and process it from there.
5. **Security:** The Database and Redis would be in private subnets, completely inaccessible from the public internet. The Django app would receive traffic only through an Application Load Balancer (ALB) sitting in public subnets.
