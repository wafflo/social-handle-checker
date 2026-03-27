from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    OFFICIAL = "official"
    RESOLVE = "resolve"
    PROBE = "probe"


class Status(str, Enum):
    AVAILABLE = "AVAILABLE"
    TAKEN = "TAKEN"
    EXISTS = "EXISTS"
    NOT_FOUND = "NOT_FOUND"
    UNRESOLVED = "UNRESOLVED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    RATE_LIMITED = "RATE_LIMITED"
    ERROR = "ERROR"
