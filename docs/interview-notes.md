# Interview Notes — CRM Data Quality & Enrichment Platform

## Phase 1 — Local Foundation

### Key Concepts Learned

#### 1. Python Virtual Environments
**What:** Isolated Python environment — packages installed here don't affect the global Python installation.
**Why:** Projects have conflicting dependencies. Isolation solves this.
**How:** `python -m venv .venv` → `.venv\Scripts\activate`
**Java equivalent:** Maven/Gradle dependency management + classpath isolation. But venv is per-project, not per-module.

**Interview Q:** "How do you manage Python dependency isolation?"
**Answer:** Virtual environments (`venv` or `conda`). Production: pin exact versions in `requirements.txt`. In larger teams, use `pip-tools` or `poetry` for deterministic builds.

---

#### 2. Django Settings Split (base / development / test / production)
**What:** Split settings by environment to avoid environment-specific config leaking into production.
**Why:** `DEBUG=True` in production is a critical security vulnerability — exposes stack traces.
**How:** `DJANGO_SETTINGS_MODULE=config.settings.development`
**Java equivalent:** Spring Profiles (`@Profile("dev")`, `application-dev.yml`).

**Interview Q:** "How do you manage environment-specific configuration in Django?"
**Answer:** Settings split by environment. Secrets via environment variables (never hardcoded). `python-decouple` or `django-environ` for typed env var reading.

---

#### 3. Environment Variables and Secrets Management
**What:** Never hardcode secrets. Read from environment at runtime.
**Why:** Hardcoded secrets end up in Git history and can never be fully removed.
**How:** `python-decouple` reads `.env` file and environment variables with type casting.
**Rule:** `.env` goes in `.gitignore`. `.env.example` is committed (no real values).
**Java equivalent:** Spring's `@Value("${property}")`, `application.properties`, externalized config.

**Interview Q:** "How do you prevent secrets from being committed to Git?"
**Answer:** `.gitignore`, environment variables, `.env.example` template, secret scanning in CI.

---

#### 4. Liveness vs Readiness
**What:** Two distinct health check types.
**Liveness** (`/health/`): "Is the process running?" — no dependencies checked.
**Readiness** (`/ready/`): "Can the process serve traffic?" — checks DB, Redis, etc.
**Why separate?** A process can be alive but not ready (e.g., DB is down). Don't restart it — take it out of rotation.
**Java equivalent:** Spring Boot Actuator: `/actuator/health/liveness` and `/actuator/health/readiness`.
Kubernetes uses these as probes.

**Interview Q:** "What's the difference between liveness and readiness probes?"
**Answer:** Liveness = process health (restart if fails). Readiness = dependency health (remove from load balancer if fails, don't restart).

---

#### 5. WSGI vs ASGI
**WSGI:** Synchronous. Django's traditional interface. Used by gunicorn, uWSGI.
**ASGI:** Asynchronous. Supports async views, WebSockets. Used by uvicorn, Daphne.
**Django 5.x** supports async views natively.
**We use:** WSGI for Phase 1. May explore async in advanced phases.
**Java equivalent:** Servlet container (Tomcat) = WSGI. Reactive (WebFlux/Netty) = ASGI.

---

#### 6. DRF Renderers
**What:** Controls the output format of API responses.
**Development:** `BrowsableAPIRenderer` (HTML) + `JSONRenderer`
**Production:** `JSONRenderer` only (no HTML overhead, no info leakage)
**Why matters:** BrowsableAPIRenderer exposes your API structure to browsers — acceptable in dev, not in prod.

---

### Phase 1 Interview Questions

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
