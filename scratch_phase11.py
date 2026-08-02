phase11_arch = """
## PHASE 11 — Optional AI / Advanced Data

### Key Concepts

#### 1. AI Provider Abstraction (Strategy Pattern)
- **Implementation:** `BaseEnrichmentProvider` abstract base class with `MockEnrichmentProvider` and `OpenAIEnrichmentProvider` implementations.
- **Purpose:** Allows easy swapping of AI backends without modifying core business logic.
- **Factory:** `get_enrichment_provider()` returns the correct provider based on `settings.ENRICHMENT_PROVIDER`.

#### 2. Model Enhancements
- Added `description` to `Company` model.
- Added `linkedin_url` to `Contact` model.
- Both fields are hydrated via AI data enrichment endpoints.

#### 3. Enrichment Endpoints
- `POST /api/v1/companies/{id}/enrich/`: Triggers AI to summarize industry, size, and description based on company name and domain.
- `POST /api/v1/contacts/{id}/enrich/`: Triggers AI to infer job title and linkedin url based on name and company context.

### Test Count After Phase 11
Total tests: **71** (Added 3 integration tests for the enrichment service and endpoints).

---
"""

with open("docs/architecture.md", "a", encoding="utf-8") as f:
    f.write(phase11_arch)

phase11_notes = """
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
"""

with open("docs/interview-notes.md", "a", encoding="utf-8") as f:
    f.write(phase11_notes)

print("Updated docs.")
