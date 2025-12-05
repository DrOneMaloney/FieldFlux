"""Lightweight core application logic for FieldFlux."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .telemetry import ErrorMonitor, EventLogger


@dataclass
class User:
    """Represents a simple authenticated user."""

    username: str
    role: str  # admin, editor, viewer
    token: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class FieldRecord:
    """Represents an agronomic field."""

    id: str
    name: str
    crop: str
    owner: str
    attributes: Dict[str, str] = field(default_factory=dict)


class PermissionError(Exception):
    """Raised when a user does not have permission for an action."""


class FieldFluxApp:
    """In-memory application facade used by tests and scripts."""

    def __init__(
        self,
        *,
        logger: Optional[EventLogger] = None,
        error_monitor: Optional[ErrorMonitor] = None,
    ) -> None:
        self.db_url = os.getenv("DATABASE_URL")
        self.map_api_key = os.getenv("MAPS_API_KEY")
        self.analytics_key = os.getenv("ANALYTICS_WRITE_KEY")
        self.users: Dict[str, User] = {}
        self.fields: Dict[str, FieldRecord] = {}
        self.logger = logger or EventLogger()
        self.error_monitor = error_monitor or ErrorMonitor()

    def register_user(self, username: str, role: str) -> User:
        if role not in {"admin", "editor", "viewer"}:
            raise ValueError("Invalid role")
        user = User(username=username, role=role)
        self.users[username] = user
        self.logger.capture("user_registered", {"username": username, "role": role})
        return user

    def authenticate(self, username: str) -> User:
        if username not in self.users:
            self.error_monitor.capture_error("auth_failed", {"username": username})
            raise PermissionError("Unknown user")
        user = self.users[username]
        self.logger.capture("user_authenticated", {"username": username})
        return user

    def _require_permission(self, user: User, action: str) -> None:
        allowed: Dict[str, List[str]] = {
            "admin": ["create", "read", "update", "delete"],
            "editor": ["create", "read", "update"],
            "viewer": ["read"],
        }
        if action not in allowed.get(user.role, []):
            self.error_monitor.capture_error(
                "permission_denied", {"username": user.username, "action": action}
            )
            raise PermissionError(f"User {user.username} not allowed to {action}")

    def create_field(self, user: User, name: str, crop: str, **attributes: str) -> FieldRecord:
        self._require_permission(user, "create")
        field_id = uuid.uuid4().hex
        record = FieldRecord(
            id=field_id,
            name=name,
            crop=crop,
            owner=user.username,
            attributes=attributes,
        )
        self.fields[field_id] = record
        self.logger.capture("field_created", {"field_id": field_id, "owner": user.username})
        return record

    def update_field(self, user: User, field_id: str, **updates: str) -> FieldRecord:
        self._require_permission(user, "update")
        if field_id not in self.fields:
            self.error_monitor.capture_error("update_missing_field", {"field_id": field_id})
            raise KeyError("Field not found")
        record = self.fields[field_id]
        record.attributes.update(updates)
        if "name" in updates:
            record.name = updates["name"]
        if "crop" in updates:
            record.crop = updates["crop"]
        self.logger.capture(
            "field_updated",
            {"field_id": field_id, "user": user.username, "updates": sorted(updates)},
        )
        return record

    def delete_field(self, user: User, field_id: str) -> None:
        self._require_permission(user, "delete")
        if field_id not in self.fields:
            self.error_monitor.capture_error("delete_missing_field", {"field_id": field_id})
            raise KeyError("Field not found")
        del self.fields[field_id]
        self.logger.capture("field_deleted", {"field_id": field_id, "user": user.username})

    def get_field(self, user: User, field_id: str) -> FieldRecord:
        self._require_permission(user, "read")
        if field_id not in self.fields:
            self.error_monitor.capture_error("read_missing_field", {"field_id": field_id})
            raise KeyError("Field not found")
        self.logger.capture("field_viewed", {"field_id": field_id, "user": user.username})
        return self.fields[field_id]

    def list_fields(self, user: User) -> List[FieldRecord]:
        self._require_permission(user, "read")
        self.logger.capture("fields_listed", {"user": user.username, "count": len(self.fields)})
        return list(self.fields.values())

    def seed(self, fields: List[FieldRecord]) -> None:
        for record in fields:
            self.fields[record.id] = record
        self.logger.capture("seed_loaded", {"count": len(fields)})

    def healthcheck(self) -> Dict[str, Optional[str]]:
        return {
            "db_url_configured": bool(self.db_url),
            "map_api_key_configured": bool(self.map_api_key),
            "analytics_key_configured": bool(self.analytics_key),
        }
