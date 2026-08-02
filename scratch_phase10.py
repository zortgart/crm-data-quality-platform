phase10_arch = """
## PHASE 10 — Notification System

### Key Concepts

#### 1. Django Signals
- **Implementation:** `post_save` signal connected to `ImportJob`.
- **Purpose:** Decouples the core business logic (importing CSVs) from side-effects (notifying the user). 
- **Action:** Automatically creates a `Notification` object when an `ImportJob` reaches a terminal status (`COMPLETED` or `FAILED`).

#### 2. REST Endpoints
- **Implementation:** `NotificationViewSet` with custom `@action` decorators for `read` and `read_all`.
- **Purpose:** Allows frontend applications to query unread notifications, mark them as read, or mark all as read.

### Test Count After Phase 10
Total tests: **68** (Added 4 integration tests for the notification signals and API endpoints).

---
"""

with open("docs/architecture.md", "a", encoding="utf-8") as f:
    f.write(phase10_arch)

phase10_notes = """
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
"""

with open("docs/interview-notes.md", "a", encoding="utf-8") as f:
    f.write(phase10_notes)

print("Updated docs.")
