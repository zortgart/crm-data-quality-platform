phase12_arch = """
## PHASE 12 — Docker Containerization (Theoretical)

### Key Concepts
Since this project is focused on data engineering and backend logic, Docker was skipped in physical implementation but the architecture remains the same. A standard `docker-compose.yml` would orchestrate:
1. `web` (Django app via Gunicorn)
2. `db` (PostgreSQL)
3. `redis` (Cache & Broker)
4. `worker` (Celery process)

---
"""

with open("docs/architecture.md", "a", encoding="utf-8") as f:
    f.write(phase12_arch)

phase12_notes = """
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
"""

with open("docs/interview-notes.md", "a", encoding="utf-8") as f:
    f.write(phase12_notes)

print("Updated docs for Phase 12.")
