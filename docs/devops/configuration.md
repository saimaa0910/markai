# Configuration & Environment Variable Reference

## Overview

Configuration settings in **MarkAI** are managed using **Pydantic BaseSettings** ([config.py](file:///d:/markai/apps/api/src/api/core/config.py)). Environment variables are populated from system environment variables or loaded automatically from the root `.env` file.

---

## Environment Variable Reference Table

| Variable Name | Default Value | Description | Required in Prod |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | `"Enterprise AI Marketing Operating System (EAIMOS)"` | System application title | No |
| `API_V1_STR` | `"/api/v1"` | Versioned API route prefix | No |
| `ENVIRONMENT` | `"development"` | Execution environment (`development`, `production`, `testing`) | Yes |
| `CORS_ORIGINS` | `"http://localhost:3000,http://localhost:3001"` | Comma-separated list of allowed CORS origins | Yes |
| `DATABASE_URL` | `"postgresql://postgres:postgres@localhost:5432/eaimos"` | PostgreSQL database connection string | Yes |
| `REDIS_URL` | `"redis://localhost:6379/0"` | Redis cache & Celery broker connection string | Yes |
| `SECRET_KEY` | `"SUPER_SECRET_JWT_KEY_MIN_32_CHARS..."` | JWT signing & Fernet encryption key | **CRITICAL** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | JWT access token lifetime | No |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `43200` (30 days) | JWT refresh token lifetime | No |
| `MINIO_ENDPOINT` | `"localhost:9000"` | S3 / MinIO object storage endpoint | Yes |
| `MINIO_ACCESS_KEY` | `"minioadmin"` | MinIO root access key | Yes |
| `MINIO_SECRET_KEY` | `"minioadmin"` | MinIO root secret key | Yes |
| `MINIO_BUCKET_NAME` | `"eaimos-storage"` | Bucket name for knowledge document storage | No |
| `SMTP_HOST` | `"smtp.sendgrid.net"` | SMTP server hostname for email delivery | Optional |
| `SMTP_PORT` | `587` | SMTP server port | Optional |
| `SMTP_USER` | `"apikey"` | SMTP authentication username | Optional |
| `SMTP_PASSWORD` | `""` | SMTP authentication password | Optional |
| `EMAIL_FROM` | `"noreply@viptant.ai"` | Default sender email address | No |
| `OPENAI_API_KEY` | `""` | Provider key for OpenAI models (`gpt-4o`) | Optional |
| `ANTHROPIC_API_KEY` | `""` | Provider key for Anthropic Claude models | Optional |
| `GEMINI_API_KEY` | `""` | Provider key for Google Gemini models | Optional |
| `GROQ_API_KEY` | `""` | Provider key for Groq Llama-3 acceleration | Optional |
| `OPENROUTER_API_KEY` | `""` | Provider key for OpenRouter proxy models | Optional |
