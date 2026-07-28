"""
Sprint 2 IAM Test Configuration
==================================
Local conftest for Sprint 2 tests that operates without requiring
full application startup (no FastAPI app, no bcrypt, no DB connection).
All external dependencies are mocked at the service layer.
"""
import os
import sys

# Ensure src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

# Stub out heavy modules before they're imported
import unittest.mock as mock

# Prevent bcrypt from being imported
sys.modules.setdefault("bcrypt", mock.MagicMock())
sys.modules.setdefault("passlib", mock.MagicMock())
sys.modules.setdefault("passlib.context", mock.MagicMock())
sys.modules.setdefault("passlib.hash", mock.MagicMock())
sys.modules.setdefault("jose", mock.MagicMock())
sys.modules.setdefault("jose.jwt", mock.MagicMock())
sys.modules.setdefault("aioredis", mock.MagicMock())
sys.modules.setdefault("redis", mock.MagicMock())
sys.modules.setdefault("celery", mock.MagicMock())
sys.modules.setdefault("stripe", mock.MagicMock())
sys.modules.setdefault("sendgrid", mock.MagicMock())
sys.modules.setdefault("anthropic", mock.MagicMock())
sys.modules.setdefault("openai", mock.MagicMock())
sys.modules.setdefault("google.generativeai", mock.MagicMock())
sys.modules.setdefault("groq", mock.MagicMock())
