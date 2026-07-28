"""
Sprint 4 Test Configuration
=============================
Local test setup stubbing heavy dependencies.
"""
import os
import sys
import unittest.mock as mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

sys.modules.setdefault("bcrypt", mock.MagicMock())
sys.modules.setdefault("passlib", mock.MagicMock())
sys.modules.setdefault("passlib.context", mock.MagicMock())
sys.modules.setdefault("passlib.hash", mock.MagicMock())
sys.modules.setdefault("jose", mock.MagicMock())
sys.modules.setdefault("jose.jwt", mock.MagicMock())
