"""Telemetry primitives for analytics and error monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EventLogger:
    """Collects structured analytics events for feature usage."""

    events: List[Dict[str, object]] = field(default_factory=list)

    def capture(self, name: str, properties: Dict[str, object]) -> None:
        payload = {"event": name, **properties}
        self.events.append(payload)


@dataclass
class ErrorMonitor:
    """Captures errors that would normally be sent to a monitoring service."""

    errors: List[Dict[str, object]] = field(default_factory=list)

    def capture_error(self, name: str, context: Dict[str, object]) -> None:
        payload = {"error": name, **context}
        self.errors.append(payload)
