# Interview Notes — CRM Data Quality & Enrichment Platform

> **Living document** — a new section is added after every phase.
> Use this to prepare for backend engineering interviews.
> Last updated: Phase 2 — Database Foundation

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
