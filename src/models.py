from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import Mode, Status


@dataclass(slots=True)
class PlatformConfig:
    key: str
    label: str
    mode: Mode
    confidence: str
    url_template: str | None = None
    docs_url: str | None = None
    notes: str | None = None
    ok_statuses: set[int] = field(default_factory=lambda: {200})
    not_found_statuses: set[int] = field(default_factory=lambda: {404})
    blocked_statuses: set[int] = field(default_factory=lambda: {401, 403})
    rate_limit_statuses: set[int] = field(default_factory=lambda: {429})
    exists_markers: tuple[str, ...] = ()
    missing_markers: tuple[str, ...] = ()
    username_transform: str | None = None


@dataclass(slots=True)
class CheckResult:
    platform: str
    username: str
    checked_value: str
    mode: str
    status: Status
    confidence: str
    url: str | None = None
    http_status: int | None = None
    reason: str | None = None
    notes: str | None = None
    attempts: int = 1
    proxy: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "username": self.username,
            "checked_value": self.checked_value,
            "mode": self.mode,
            "status": self.status.value,
            "confidence": self.confidence,
            "url": self.url,
            "http_status": self.http_status,
            "reason": self.reason,
            "notes": self.notes,
            "attempts": self.attempts,
            "proxy": self.proxy,
        }


@dataclass(slots=True)
class NetworkOptions:
    concurrency: int = 8
    timeout_seconds: int = 12
    retries: int = 2
    retry_backoff: float = 1.4
    retry_max_sleep: float = 10.0
    min_delay: float = 0.0
    max_delay: float = 0.0
    proxy: str | None = None
    proxies: tuple[str, ...] = ()
    proxy_mode: str = "off"
    rotate_on_retry: bool = True
    user_agent: str | None = None
    random_user_agent: bool = False
    extra_headers: dict[str, str] = field(default_factory=dict)
    follow_redirects: bool = True
