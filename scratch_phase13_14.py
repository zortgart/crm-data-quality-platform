phase13_14_arch = """
## PHASE 13 — CI/CD Pipeline (Theoretical)

### Key Concepts
A standard CI/CD pipeline (e.g., using GitHub Actions) for this project would include:
1. **Continuous Integration (CI):**
   - Linting (flake8, black)
   - Running the test suite (`pytest`) with PostgreSQL and Redis services spun up via Docker.
   - Code coverage reporting.
2. **Continuous Deployment (CD):**
   - Triggered on push to `main`.
   - Builds the Docker image.
   - Pushes the image to a container registry (e.g., AWS ECR).
   - Triggers deployment on the target environment (e.g., ECS or EKS).

---

## PHASE 14 — AWS Production Architecture (Theoretical)

### Key Concepts
To deploy this CRM Data Quality Platform to AWS for high availability and scale, the architecture would map as follows:
- **Application Servers:** AWS ECS (Fargate) or EKS running the Django web containers and Celery worker containers.
- **Database:** Amazon RDS for PostgreSQL (Multi-AZ for failover, with read replicas for heavy analytical queries).
- **Caching & Message Broker:** Amazon ElastiCache for Redis (handles Celery queues, rate limiting, and DRF caching).
- **Storage:** Amazon S3 (for handling large CSV uploads and static/media files) integrated with Django via `django-storages`.
- **Load Balancing:** AWS Application Load Balancer (ALB) to route traffic and terminate SSL/TLS.
- **Security:** AWS Secrets Manager for injecting `DJANGO_SECRET_KEY`, `DATABASE_URL`, etc. at runtime. Private subnets for the database and cache.

---
"""

with open("docs/architecture.md", "a", encoding="utf-8") as f:
    f.write(phase13_14_arch)

phase13_14_notes = """
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
"""

with open("docs/interview-notes.md", "a", encoding="utf-8") as f:
    f.write(phase13_14_notes)

print("Updated docs for Phase 13 and 14.")
