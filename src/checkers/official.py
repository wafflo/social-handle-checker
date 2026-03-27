from __future__ import annotations

import json

from ..enums import Status
from ..models import CheckResult, PlatformConfig
from ..network import RequestManager


async def check_reddit(manager: RequestManager, username: str, config: PlatformConfig) -> CheckResult:
    url = "https://www.reddit.com/api/username_available"
    response = await manager.get(platform=config.key, url=url, params={"user": username})

    if response.error:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=username,
            mode=config.mode.value,
            status=Status.ERROR,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason=f"Network error: {response.error}",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    if response.status in config.rate_limit_statuses:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=username,
            mode=config.mode.value,
            status=Status.RATE_LIMITED,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason="Rate limited by Reddit official endpoint.",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    if response.status in config.blocked_statuses:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=username,
            mode=config.mode.value,
            status=Status.BLOCKED,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason=f"Official endpoint blocked with HTTP {response.status}.",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    if response.status == 404:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=username,
            mode=config.mode.value,
            status=Status.UNKNOWN,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason="Official endpoint returned a site-level 404 page.",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    if response.status is None or response.status >= 400:
        excerpt = response.text.strip().replace("\n", " ")[:120]
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=username,
            mode=config.mode.value,
            status=Status.ERROR,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason=f"Unexpected HTTP {response.status}: {excerpt}",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    content_type = response.headers.get("Content-Type", "").lower()
    parsed: object
    if "json" in content_type:
        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = response.text.strip().lower()
    else:
        lowered = response.text.strip().lower()
        if lowered == "true":
            parsed = True
        elif lowered == "false":
            parsed = False
        else:
            parsed = lowered

    if parsed is True:
        status = Status.AVAILABLE
        reason = "Official Reddit endpoint reported available."
    elif parsed is False:
        status = Status.TAKEN
        reason = "Official Reddit endpoint reported taken."
    else:
        status = Status.UNKNOWN
        reason = f"Unexpected Reddit payload: {repr(parsed)[:120]}"

    return CheckResult(
        platform=config.key,
        username=username,
        checked_value=username,
        mode=config.mode.value,
        status=status,
        confidence=config.confidence,
        url=response.url,
        http_status=response.status,
        reason=reason,
        notes=config.notes,
        attempts=response.attempts,
        proxy=response.proxy,
    )
