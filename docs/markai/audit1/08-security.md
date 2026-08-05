# Enterprise Source Code Audit - Security Audit

## Security Audit Summary

| Finding | Severity | Evidence | Files |
| :--- | :--- | :--- | :--- |
| **Hardcoded Secret Key** | 🔴 Critical | The default `SECRET_KEY` is hardcoded as `"SUPER_SECRET_JWT_KEY_MIN_32_CHARS_LONG_PLEASE_REPLACE_IN_PRODUCTION"`. If not overridden in `.env`, it will be used in production. | [config.py](file:///d:/markai/apps/api/src/api/core/config.py#L61-L64) |
| **Hardcoded API Keys in env** | 🟡 Medium | Default credentials like `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` are hardcoded as `"minioadmin"`. | [config.py](file:///d:/markai/apps/api/src/api/core/config.py#L68-L72) |
| **SQL Injection Risks** | ✓ Secure | Database operations use SQLAlchemy ORM or compiled query statements. No raw string concatenations detected. | [repositories/](file:///d:/markai/apps/api/src/api/repositories) |
| **Prompt Injection Protection** | ✓ Secure | The input scanner `AISecurityPipeline` checks user inputs against standard jailbreak keywords. Triggering 2+ keywords blocks the request. | [pipeline.py](file:///d:/markai/apps/api/src/api/ai/security/pipeline.py#L38-L50) |
| **Credentials Leaks Protection** | ✓ Secure | Regex scanner in `AISecurityPipeline` blocks inputs containing raw unencrypted provider keys (OpenAI, Groq, Gemini) or database URLs. | [pipeline.py](file:///d:/markai/apps/api/src/api/ai/security/pipeline.py#L27-L36) |
| **MFA & Account Lockout** | ✓ Secure | Enforces TOTP MFA and account lockout after 5 failed login attempts to prevent brute-force attacks. | [auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L405-L470) |
| **Encryption of Custom Keys** | ✓ Secure | Custom provider API keys are encrypted using AES-256 before storage and decrypted dynamically on routing. | [encryption.py](file:///d:/markai/apps/api/src/api/core/encryption.py) |
| **CORS Validation** | ✓ Secure | Restricts CORS origins using `settings.cors_origins_list` with Pydantic alias checks. | [config.py](file:///d:/markai/apps/api/src/api/core/config.py#L40-L48) |

------------------------------------------------------------

## Detailed Findings

### 1. Hardcoded JWT Secret Key
In [core/config.py](file:///d:/markai/apps/api/src/api/core/config.py#L61-L64), `SECRET_KEY` has a default value:
```python
SECRET_KEY: str = Field(
    default="SUPER_SECRET_JWT_KEY_MIN_32_CHARS_LONG_PLEASE_REPLACE_IN_PRODUCTION",
    validation_alias="SECRET_KEY",
)
```
If the environment variable `SECRET_KEY` is not explicitly set in the production environment, the platform will use this weak default key, allowing attackers to sign arbitrary JWTs.
> [!CAUTION]
> Ensure that `SECRET_KEY` has no default value or throws a configuration error if it is not set in production.

### 2. Prompt Injection and Jailbreak Rules Heuristics
The platform implements an AI Security Pipeline in [ai/security/pipeline.py](file:///d:/markai/apps/api/src/api/ai/security/pipeline.py).
The validation rules check user inputs for specific patterns:
- Checks against a list of common jailbreak keywords (e.g. `ignore previous instructions`, `system override`, `dan mode`, etc.).
- Scans for PII leakage using regexes for `email`, `phone`, `ssn`, `credit_card`, `passport`, `ip_address`, and masks/redacts the values according to policy rules.
- Blocks request processing if credentials leak patterns (e.g. `sk-[a-zA-Z0-9]{48}`) match the prompt.

This provides solid protection against prompt injection and data leaks.
