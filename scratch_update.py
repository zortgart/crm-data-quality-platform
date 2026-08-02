import re

with open('docs/architecture.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the table
content = content.replace('| 9 — Enterprise Features | 🔜 Next | Audit, caching, observability |', '| 9 — Enterprise Features | ✅ Complete | Audit, caching, observability |')
content = content.replace('| 10 — Testing + Performance | ⏳ |', '| 10 — Notification System | 🔜 Next |')

# Split into preamble and sections
# The sections start with "## PHASE 3" etc.
parts = re.split(r'\n---+\n\n## PHASE ', content)
preamble = parts[0]
sections_raw = parts[1:]

sections = []
for s in sections_raw:
    # get the phase number
    match = re.match(r'(\d+)', s)
    if match:
        phase_num = int(match.group(1))
        sections.append((phase_num, s))
    else:
        # Just append it as is with high number if something is weird
        sections.append((999, s))

# Sort sections
sections.sort(key=lambda x: x[0])

# Reconstruct
new_content = preamble + "\n\n---\n\n"
for _, s in sections:
    new_content += "## PHASE " + s + "\n---\n\n"

# Add Phase 9
phase_9_text = """## PHASE 9 — Enterprise Features

### Key Concepts

#### 1. Tenant-Safe Caching
- **Implementation:** DRF `@cache_page` combined with `@vary_on_headers('Authorization')`.
- **Purpose:** Prevents cross-tenant data leaks. Caching by URL alone in a multi-tenant application will serve User A's data to User B.
- **Backend:** Redis (LocMemCache in test mode).

#### 2. Audit Logging
- **Implementation:** Custom `AuditLogMiddleware` and `AuditLog` model.
- **Purpose:** Tracks every CUD (Create, Update, Delete) operation automatically without developer intervention.
- **Data Captured:** User, organization, path, method, IP address, and request payload.

#### 3. Observability
- **Implementation:** `RequestIDMiddleware` generates UUIDs for every request. `RequestIdFilter` injects this into Python's `logging` system.
- **Purpose:** Ensures every log line has a `[correlation_id]`. Critical for distributed tracing and debugging in enterprise systems.

#### 4. Rate Limiting
- **Implementation:** DRF `AnonRateThrottle` and `UserRateThrottle`.
- **Purpose:** Protects the API from brute force, scraping, and DoS attacks.

### Test Count After Phase 9
Total tests: **64** (Refactored some endpoints, fixed missing dependencies, forced caching overrides in test mode).

---
"""
new_content += phase_9_text

with open('docs/architecture.md', 'w', encoding='utf-8') as f:
    f.write(new_content.strip() + '\n')
print("Updated architecture.md")
