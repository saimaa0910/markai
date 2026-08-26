# EAIMOS AI GATEWAY — PROVIDER & ADAPTER AUDIT

This document provides a comprehensive audit of all 16 AI Provider Adapters integrated into the EAIMOS AI Gateway.

---

## 1. Provider Adapter Architecture Overview

EAIMOS currently contains two distinct provider base interfaces:
1. **`BaseLLMProvider` (`apps/api/src/api/ai/providers/base.py`)**:
   - Async & Sync methods: `achat`, `chat`, `astream`, `stream`, `embeddings`, `vision`, `json_output`, `check_connectivity`.
   - Uses `httpx.AsyncClient` and `httpx.Client`.
   - Instantiated directly by `AIGateway`.
2. **`BaseProvider` (`apps/api/src/api/ai/providers/base_provider.py`)**:
   - Synchronous methods: `generate`, `edit`, `variation`, `health`, `capabilities`.
   - Uses `requests.post` and `requests.get`.
   - Registered in `ProviderRegistry` and routed via `ImageProviderRouter`.

---

## 2. Detailed Audit Per Provider

### 1. Groq (`apps/api/src/api/ai/providers/groq.py`)
- **Base Class**: `BaseLLMProvider`
- **Default Models**: `openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, `llama3-70b-8192`, `llama3-8b-8192`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (Low latency OpenAI-compatible endpoint)
  - Streaming: `✅ COMPLETE` (SSE parser with chunk yielding)
  - JSON Output: `✅ COMPLETE` (`response_format={"type": "json_object"}`)
  - Vision: `❌ MISSING` (Raises `NotImplementedError`)
  - Embeddings: `🔴 BROKEN` (Hits `https://api.groq.com/openai/v1/embeddings` with `text-embedding-3-small`, but Groq does not natively serve this endpoint)
- **Status**: `⚠️ PARTIAL`

### 2. OpenAI (`apps/api/src/api/ai/providers/openai.py` & `openai_images.py`)
- **Base Class**: `BaseLLMProvider` (Text) & `BaseProvider` (Images)
- **Default Models**: `gpt-4o`, `gpt-4o-mini`, `text-embedding-3-small`, `dall-e-3`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE`
  - Streaming: `✅ COMPLETE`
  - JSON Output: `✅ COMPLETE` (Structured Outputs & JSON Mode)
  - Vision: `✅ COMPLETE` (Base64 and URL image payload parsing)
  - Embeddings: `✅ COMPLETE` (Returns 1536 float vectors from `text-embedding-3-small`)
  - Image Generation: `✅ COMPLETE` (`dall-e-3` b64 decode)
- **Status**: `✅ COMPLETE`

### 3. Anthropic Claude (`apps/api/src/api/ai/providers/claude.py`)
- **Base Class**: `BaseLLMProvider`
- **Default Models**: `claude-3-5-sonnet-20240620`, `claude-3-haiku-20240307`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (`/v1/messages` endpoint with `anthropic-version: 2023-06-01`)
  - Streaming: `✅ COMPLETE` (Parses `content_block_delta` SSE stream)
  - Vision: `✅ COMPLETE` (Formats image media types to Anthropic blocks)
  - JSON Output: `✅ COMPLETE` (System prompt JSON schema instructions)
  - Embeddings: `❌ MISSING` (Anthropic API does not offer embeddings; raises `NotImplementedError`)
- **Status**: `⚠️ PARTIAL`

### 4. Google Gemini (`apps/api/src/api/ai/providers/gemini.py` & `google_imagen.py`)
- **Base Class**: `BaseLLMProvider` (Text) & `BaseProvider` (Imagen)
- **Default Models**: `gemini-1.5-flash`, `gemini-1.5-pro`, `imagen-3.0-generate-002`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (`generateContent` endpoint)
  - Streaming: `✅ COMPLETE` (`streamGenerateContent?alt=sse`)
  - Vision: `✅ COMPLETE` (`inlineData` payload mapping)
  - JSON Output: `✅ COMPLETE` (`response_mime_type: "application/json"`)
  - Embeddings: `❌ MISSING` (Raises `NotImplementedError`)
  - Image Generation: `✅ COMPLETE` (Imagen 3 base64 generation)
- **Status**: `⚠️ PARTIAL`

### 5. DeepSeek (`apps/api/src/api/ai/providers/deepseek.py`)
- **Base Class**: `BaseLLMProvider`
- **Default Models**: `deepseek-chat`, `deepseek-reasoner`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (`https://api.deepseek.com/chat/completions`)
  - Streaming: `✅ COMPLETE` (OpenAI-compatible stream)
  - JSON Output: `✅ COMPLETE` (JSON mode supported)
  - Vision: `❌ MISSING` (Raises `NotImplementedError`)
  - Embeddings: `❌ MISSING` (Raises `NotImplementedError`)
- **Status**: `⚠️ PARTIAL`

### 6. Mistral AI (`apps/api/src/api/ai/providers/mistral.py`)
- **Base Class**: `BaseLLMProvider`
- **Default Models**: `mistral-large-latest`, `mistral-small-latest`, `open-mixtral-8x22b`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (`https://api.mistral.ai/v1/chat/completions`)
  - Streaming: `✅ COMPLETE`
  - Embeddings: `✅ COMPLETE` (`mistral-embed` endpoint)
  - Vision: `❌ MISSING` (Raises `NotImplementedError`)
- **Status**: `⚠️ PARTIAL`

### 7. Ollama (`apps/api/src/api/ai/providers/ollama.py`)
- **Base Class**: `BaseLLMProvider`
- **Default Models**: `llama3.1`, `mistral`, `nomic-embed-text`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (Localhost `http://localhost:11434/api/chat`)
  - Streaming: `✅ COMPLETE` (NDJSON stream parsing)
  - Embeddings: `✅ COMPLETE` (`/api/embeddings`)
  - Vision: `❌ MISSING` (Raises `NotImplementedError`)
- **Status**: `⚠️ PARTIAL`

### 8. OpenRouter (`apps/api/src/api/ai/providers/openrouter.py`)
- **Base Class**: `BaseLLMProvider`
- **Default Models**: `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`, `google/gemini-flash-1.5`
- **Capabilities**:
  - Chat Completion: `✅ COMPLETE` (`https://openrouter.ai/api/v1/chat/completions`)
  - Streaming: `✅ COMPLETE`
  - Vision: `✅ COMPLETE` (Pass-through payload)
  - JSON Output: `✅ COMPLETE`
- **Status**: `✅ COMPLETE`

### 9. Cloudflare Workers AI (`apps/api/src/api/ai/providers/cloudflare.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `@cf/stabilityai/stable-diffusion-xl-base-1.0`
- **Capabilities**:
  - Generation: `✅ COMPLETE` (Direct binary image response)
  - Synchronous I/O: `⚠️ PARTIAL` (Uses blocking `requests.post`)
- **Status**: `⚠️ PARTIAL`

### 10. Pollinations AI (`apps/api/src/api/ai/providers/pollinations.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `flux`, `turbo`
- **Capabilities**:
  - Generation: `✅ COMPLETE` (Keyless free image URL endpoint)
  - Synchronous I/O: `⚠️ PARTIAL` (Uses blocking `requests.get`)
- **Status**: `⚠️ PARTIAL`

### 11. Replicate (`apps/api/src/api/ai/providers/replicate.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `stability-ai/sdxl`
- **Capabilities**:
  - Generation: `⚠️ PARTIAL` (Polls prediction URL with `time.sleep(2)` blocking the worker loop)
  - Inpainting / Edit: `🟡 STATIC/HARDCODED` (Prepends `"Edit: "` to prompt without running true inpainting pipeline)
- **Status**: `⚠️ PARTIAL`

### 12. Together AI (`apps/api/src/api/ai/providers/together.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `black-forest-labs/FLUX.1-schnell`
- **Capabilities**:
  - Generation: `✅ COMPLETE` (Base64 JSON decoding)
  - Synchronous I/O: `⚠️ PARTIAL` (Blocking `requests.post`)
- **Status**: `⚠️ PARTIAL`

### 13. Fal AI (`apps/api/src/api/ai/providers/fal.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `fal-ai/flux/schnell`
- **Capabilities**:
  - Generation: `✅ COMPLETE` (Queue/Sync API download)
  - Synchronous I/O: `⚠️ PARTIAL` (Blocking `requests.post`)
- **Status**: `⚠️ PARTIAL`

### 14. Stability AI (`apps/api/src/api/ai/providers/stability.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `stable-diffusion-v1-6`, `stable-diffusion-xl-1024-v1-0`
- **Capabilities**:
  - Generation: `✅ COMPLETE` (Multipart image generation)
  - Inpainting / Edit: `✅ COMPLETE` (Multipart mask uploads)
  - Synchronous I/O: `⚠️ PARTIAL` (Blocking `requests.post`)
- **Status**: `⚠️ PARTIAL`

### 15. Ideogram (`apps/api/src/api/ai/providers/ideogram.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `V_2`
- **Capabilities**:
  - Generation: `✅ COMPLETE` (Aspect ratio mapping & image URL retrieval)
  - Synchronous I/O: `⚠️ PARTIAL` (Blocking `requests.post`)
- **Status**: `⚠️ PARTIAL`

### 16. Black Forest Labs (`apps/api/src/api/ai/providers/blackforestlabs.py`)
- **Base Class**: `BaseProvider`
- **Default Models**: `flux.1-schnell`, `flux.1-dev`
- **Capabilities**:
  - Generation: `⚠️ PARTIAL` (Polls task status endpoint with `time.sleep(1.5)` blocking loop)
  - Synchronous I/O: `⚠️ PARTIAL`
- **Status**: `⚠️ PARTIAL`

---

## 3. Provider Summary Table

| Provider | Type | Chat | Stream | Vision | Embed | Image Gen | I/O Model | Audit Verdict |
|---|---|---|---|---|---|---|---|---|
| **OpenAI** | LLM + Media | ✅ | ✅ | ✅ | ✅ | ✅ | Async / Sync | `✅ COMPLETE` |
| **OpenRouter** | LLM Gateway | ✅ | ✅ | ✅ | ❌ | ❌ | Async `httpx` | `✅ COMPLETE` |
| **Groq** | Low-Latency LLM | ✅ | ✅ | ❌ | 🔴 | ❌ | Async `httpx` | `⚠️ PARTIAL` |
| **Claude** | LLM | ✅ | ✅ | ✅ | ❌ | ❌ | Async `httpx` | `⚠️ PARTIAL` |
| **Gemini** | Multimodal LLM | ✅ | ✅ | ✅ | ❌ | ✅ | Async / Sync | `⚠️ PARTIAL` |
| **DeepSeek** | Reasoning LLM | ✅ | ✅ | ❌ | ❌ | ❌ | Async `httpx` | `⚠️ PARTIAL` |
| **Mistral** | LLM | ✅ | ✅ | ❌ | ✅ | ❌ | Async `httpx` | `⚠️ PARTIAL` |
| **Ollama** | Local LLM | ✅ | ✅ | ❌ | ✅ | ❌ | Async `httpx` | `⚠️ PARTIAL` |
| **Cloudflare** | Edge Media | ❌ | ❌ | ❌ | ❌ | ✅ | Sync `requests` | `⚠️ PARTIAL` |
| **Pollinations**| Free Media | ❌ | ❌ | ❌ | ❌ | ✅ | Sync `requests` | `⚠️ PARTIAL` |
| **Together** | Media / LLM | ❌ | ❌ | ❌ | ❌ | ✅ | Sync `requests` | `⚠️ PARTIAL` |
| **Fal AI** | Real-time Media | ❌ | ❌ | ❌ | ❌ | ✅ | Sync `requests` | `⚠️ PARTIAL` |
| **Stability** | Media / Inpaint | ❌ | ❌ | ❌ | ❌ | ✅ | Sync `requests` | `⚠️ PARTIAL` |
| **Ideogram** | Typography Media| ❌ | ❌ | ❌ | ❌ | ✅ | Sync `requests` | `⚠️ PARTIAL` |
| **Replicate** | Polled Media | ❌ | ❌ | ❌ | ❌ | ✅ | Polling / Sleep | `⚠️ PARTIAL` |
| **BFL Flux** | Polled Media | ❌ | ❌ | ❌ | ❌ | ✅ | Polling / Sleep | `⚠️ PARTIAL` |
