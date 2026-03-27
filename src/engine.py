from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import aiofiles
import aiohttp

from .checkers.official import check_reddit
from .checkers.probe import check_bluesky_resolve, check_public_probe
from .display import DisplayOptions, render_result
from .enums import Mode, Status
from .models import CheckResult, NetworkOptions, PlatformConfig
from .network import RequestManager


class ResultWriter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def write(self, result: CheckResult) -> None:
        async with self._lock:
            status_name = result.status.value.lower()
            platform_file = self.output_dir / f"{result.platform}_{status_name}.txt"
            jsonl_file = self.output_dir / "results.jsonl"
            summary_file = self.output_dir / "summary.tsv"

            async with aiofiles.open(platform_file, "a", encoding="utf-8") as f:
                await f.write(result.checked_value + "\n")

            async with aiofiles.open(jsonl_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

            async with aiofiles.open(summary_file, "a", encoding="utf-8") as f:
                await f.write(
                    "\t".join(
                        [
                            result.platform,
                            result.username,
                            result.checked_value,
                            result.status.value,
                            result.confidence,
                            str(result.http_status or ""),
                            str(result.attempts),
                            result.proxy or "",
                            result.url or "",
                            result.reason or "",
                        ]
                    )
                    + "\n"
                )


def normalize_usernames(usernames: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for raw in usernames:
        item = raw.strip()
        if not item:
            continue
        if item.startswith("@"):
            item = item[1:]
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


async def dispatch_check(
    manager: RequestManager,
    username: str,
    config: PlatformConfig,
) -> CheckResult:
    if config.mode == Mode.OFFICIAL:
        if config.key == "reddit":
            return await check_reddit(manager, username, config)
    elif config.mode == Mode.RESOLVE:
        if config.key == "bluesky":
            return await check_bluesky_resolve(manager, username, config)
    elif config.mode == Mode.PROBE:
        return await check_public_probe(manager, username, config)

    return CheckResult(
        platform=config.key,
        username=username,
        checked_value=username,
        mode=config.mode.value,
        status=Status.ERROR,
        confidence=config.confidence,
        reason="No checker implemented for platform mode.",
        notes=config.notes,
    )


async def run_checks(
    usernames: list[str],
    platforms: list[str],
    output_dir: str | Path,
    runtime_platforms: dict[str, PlatformConfig],
    network: NetworkOptions,
    display: DisplayOptions | None = None,
) -> list[CheckResult]:
    writer = ResultWriter(output_dir)
    sem = asyncio.Semaphore(network.concurrency)
    results: list[CheckResult] = []

    timeout = aiohttp.ClientTimeout(total=network.timeout_seconds)
    connector = aiohttp.TCPConnector(limit_per_host=max(2, network.concurrency))
    display = display or DisplayOptions()

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        max_line_size=65536,
        max_field_size=65536,
    ) as session:
        manager = RequestManager(session, network)

        async def bound(username: str, platform_key: str) -> None:
            config = runtime_platforms[platform_key]
            async with sem:
                try:
                    result = await dispatch_check(manager, username, config)
                except Exception as exc:  # pragma: no cover - defensive branch
                    result = CheckResult(
                        platform=config.key,
                        username=username,
                        checked_value=username,
                        mode=config.mode.value,
                        status=Status.ERROR,
                        confidence=config.confidence,
                        reason=f"Unhandled error: {exc}",
                        notes=config.notes,
                    )

                results.append(result)
                await writer.write(result)
                print(render_result(result, display))

        await asyncio.gather(*(bound(username, platform) for username in usernames for platform in platforms))

    return results


def summarize_results(results: Iterable[CheckResult]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for item in results:
        grouped[item.platform][item.status.value] += 1
    return {platform: dict(counter) for platform, counter in grouped.items()}
