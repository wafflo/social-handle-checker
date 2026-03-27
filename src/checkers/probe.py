from __future__ import annotations

from ..enums import Status
from ..models import CheckResult, PlatformConfig
from ..network import RequestManager


def transform_username(username: str, config: PlatformConfig) -> str:
    if config.username_transform == "bluesky_handle":
        return username if "." in username else f"{username}.bsky.social"
    return username


async def check_bluesky_resolve(
    manager: RequestManager,
    username: str,
    config: PlatformConfig,
) -> CheckResult:
    handle = transform_username(username, config)
    url = "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle"
    response = await manager.get(platform=config.key, url=url, params={"handle": handle})

    if response.error:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=handle,
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

    if response.status == 200:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=handle,
            mode=config.mode.value,
            status=Status.TAKEN,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason="Handle resolved successfully.",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    if response.status in {400, 404}:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=handle,
            mode=config.mode.value,
            status=Status.UNRESOLVED,
            confidence=config.confidence,
            url=response.url,
            http_status=response.status,
            reason="Handle did not resolve. This is not a guaranteed signup-availability signal.",
            notes=config.notes,
            attempts=response.attempts,
            proxy=response.proxy,
        )

    if response.status in config.rate_limit_statuses:
        status = Status.RATE_LIMITED
        reason = "Rate limited by Bluesky public API."
    elif response.status in config.blocked_statuses:
        status = Status.BLOCKED
        reason = f"Blocked with HTTP {response.status}."
    else:
        status = Status.UNKNOWN
        reason = f"Unexpected HTTP {response.status}: {response.text[:120]}"

    return CheckResult(
        platform=config.key,
        username=username,
        checked_value=handle,
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


async def check_public_probe(
    manager: RequestManager,
    username: str,
    config: PlatformConfig,
) -> CheckResult:
    checked_value = transform_username(username, config)
    if not config.url_template:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=checked_value,
            mode=config.mode.value,
            status=Status.ERROR,
            confidence=config.confidence,
            reason="Missing url_template in platform config.",
            notes=config.notes,
        )

    url = config.url_template.format(username=checked_value)
    response = await manager.get(platform=config.key, url=url)

    if response.error:
        return CheckResult(
            platform=config.key,
            username=username,
            checked_value=checked_value,
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

    body = response.text
    status = response.status or 0

    if status in config.rate_limit_statuses:
        result_status = Status.RATE_LIMITED
        reason = "Rate limited by remote service."
    elif status in config.blocked_statuses:
        result_status = Status.BLOCKED
        reason = "Request blocked or requires auth/challenge."
    elif status in config.not_found_statuses:
        result_status = Status.NOT_FOUND
        reason = "Public route returned a not-found style status."
    elif status in config.ok_statuses:
        lowered = body.lower()
        if config.missing_markers and any(marker.lower() in lowered for marker in config.missing_markers):
            result_status = Status.NOT_FOUND
            reason = "Public route body included a missing-profile marker."
        elif config.exists_markers and any(marker.lower() in lowered for marker in config.exists_markers):
            result_status = Status.EXISTS
            reason = "Public route body included an exists marker."
        else:
            result_status = Status.EXISTS
            reason = "Public route returned a likely profile page response."
    else:
        result_status = Status.UNKNOWN
        reason = f"Unexpected HTTP {status}."

    return CheckResult(
        platform=config.key,
        username=username,
        checked_value=checked_value,
        mode=config.mode.value,
        status=result_status,
        confidence=config.confidence,
        url=response.url,
        http_status=status,
        reason=reason,
        notes=config.notes,
        attempts=response.attempts,
        proxy=response.proxy,
    )
