"""
EAIMOS Observability Constants
===============================
Constants for Sprint 11 Observability, Telemetry & Incident Monitoring Services.
"""

from typing import Set

SUPPORTED_LOG_LEVELS: Set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
SUPPORTED_ALERT_SEVERITIES: Set[str] = {"WARNING", "CRITICAL", "OFFLINE"}
SUPPORTED_ALERT_CHANNELS: Set[str] = {"SLACK", "EMAIL", "WEBHOOK", "CONSOLE"}
