# Sprint 4: AI Content Generator & Prompt Engineering Workspace - Implementation Plan

This plan details the implementation of the AI Content Generator module. It will allow users to generate professional marketing copies, social media posts, and email campaigns using specific prompt constraints (tone, audience, keywords). It also integrates A/B variant generation (generating multiple creative variations) and variant scoring.

## User Review Required

> [!IMPORTANT]
> **Integration with LLM Gateway:**
> - Generates multiple creative variations (e.g., Variant A, Variant B) in parallel or sequential calls to the `LLMGateway` based on selected style settings.
> - Multi-tenant isolation is maintained: Generated copies and their associated variants are strictly partitioned by `organization_id`.

## Proposed Changes

### 1. Database Schema

We will define two new tables:

#### [NEW] [apps/api/src/api/models/content_generator.py](file:///d:/markai/apps/api/src/api/models/content_generator.py)
Represents a generation request.
- `title`: String (255) - e.g. "Google Ads Campaign Q3"
- `prompt_used`: Text
- `organization_id`: ForeignKey to organizations

#### [NEW] [apps/api/src/api/models/content_variant.py](file:///d:/markai/apps/api/src/api/models/content_variant.py)
A/B creative variants generated for a request.
- `generated_content_id`: ForeignKey to generated_contents
- `variant_label`: String (10) - e.g. "Variant A", "Variant B"
- `content`: Text
- `model_used`: String (100)
- `rating`: Integer, optional (user rating from 1 to 5)

---

### 2. API Endpoints

We will create CRUD routers under `/api/v1/generator/`:
- **Content Generation:** `/api/v1/generator/` (`GET`, `POST` - runs the multi-variant generator, `DELETE`)
- **Variant Actions:** `/api/v1/generator/variants/{id}/rate` (`POST` - rates a variant)

---

### 3. Frontend Dashboard Panel

We will implement a content generation dashboard in Next.js:
- **`apps/web/src/app/dashboard/generator/page.tsx`**: Form inputs for topic description, copywriting type (email, social post, ad copy), tone selection (professional, creative, witty, formal), audience, and keywords. Renders side-by-side card layouts for Variant A and Variant B with copy buttons and rating stars.

---

## Verification Plan

### Automated Tests
- Write test file `apps/api/tests/test_generator.py` to assert variant generation, database links, and rating updates.
- Run: `poetry run pytest tests/test_generator.py`
