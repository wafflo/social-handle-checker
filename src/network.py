from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Mapping

import aiohttp

from .models import NetworkOptions


UA_POOL: tuple[str, ...] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "social-handle-checker/0.3 (+https://github.com/)",
)


@dataclass(slots=True)
class ManagedResponse:
    status: int | None
    url: str
    text: str
    headers: Mapping[str, str]
    error: str | None = None
    attempts: int = 1
    proxy: str | None = None


class ProxyPool:
    def __init__(self, options: NetworkOptions) -> None:
        items = [p.strip() for p in (*options.proxies, options.proxy or "") if p and p.strip()]
        self._proxies = tuple(dict.fromkeys(items))
        self._index = 0
        self._mode = options.proxy_mode
        self._rotate_on_retry = options.rotate_on_retry

    def pick(self, attempt: int) -> str | None:
        if not self._proxies or self._mode == "off":
            return None
        if self._mode == "single":
            return self._proxies[0]
        if self._mode == "random":
            return random.choice(self._proxies)
        if self._mode == "rotate":
            if attempt == 0 or self._rotate_on_retry:
                proxy = self._proxies[self._index % len(self._proxies)]
                self._index += 1
                return proxy
            return self._proxies[(self._index - 1) % len(self._proxies)]
        return self._proxies[0]

    @property
    def count(self) -> int:
        return len(self._proxies)


class PlatformCooldowns:
    def __init__(self) -> None:
        self._until: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def wait(self, platform: str) -> None:
        while True:
            async with self._lock:
                until = self._until.get(platform, 0.0)
            remaining = until - time.monotonic()
            if remaining <= 0:
                return
            await asyncio.sleep(min(remaining, 0.5))

    async def push(self, platform: str, delay_seconds: float) -> None:
        async with self._lock:
            now = time.monotonic()
            current = self._until.get(platform, now)
            self._until[platform] = max(current, now + max(0.0, delay_seconds))


class RequestManager:
    def __init__(self, session: aiohttp.ClientSession, options: NetworkOptions) -> None:
        self.session = session
        self.options = options
        self.proxy_pool = ProxyPool(options)
        self.cooldowns = PlatformCooldowns()

    def _build_headers(self, custom: Mapping[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        ua = self.options.user_agent
        if self.options.random_user_agent or not ua:
            ua = random.choice(UA_POOL)
        headers["User-Agent"] = ua
        headers.update(self.options.extra_headers)
        if custom:
            headers.update(custom)
        return headers

    def _backoff(self, attempt: int) -> float:
        if attempt <= 0:
            return 0.0
        sleep = self.options.retry_backoff * (2 ** (attempt - 1))
        return min(sleep, self.options.retry_max_sleep)

    def _pre_delay(self) -> float:
        low = min(self.options.min_delay, self.options.max_delay)
        high = max(self.options.min_delay, self.options.max_delay)
        if high <= 0:
            return 0.0
        return random.uniform(low, high)

    def _retry_after_seconds(self, headers: Mapping[str, str]) -> float | None:
        raw = headers.get("Retry-After")
        if not raw:
            return None
        try:
            return max(0.0, float(raw))
        except ValueError:
            try:
                dt = parsedate_to_datetime(raw)
                return max(0.0, dt.timestamp() - time.time())
            except Exception:
                return None

    async def get(
        self,
        *,
        platform: str,
        url: str,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        allow_redirects: bool | None = None,
    ) -> ManagedResponse:
        attempt_limit = max(0, self.options.retries)
        last_error: str | None = None
        last_response: ManagedResponse | None = None

        for attempt in range(attempt_limit + 1):
            await self.cooldowns.wait(platform)

            pre_delay = self._pre_delay()
            if pre_delay > 0:
                await asyncio.sleep(pre_delay)

            proxy = self.proxy_pool.pick(attempt)
            merged_headers = self._build_headers(headers)

            try:
                async with self.session.get(
                    url,
                    params=params,
                    headers=merged_headers,
                    allow_redirects=self.options.follow_redirects if allow_redirects is None else allow_redirects,
                    proxy=proxy,
                ) as resp:
                    text = await resp.text(errors="ignore")
                    managed = ManagedResponse(
                        status=resp.status,
                        url=str(resp.url),
                        text=text,
                        headers=dict(resp.headers),
                        attempts=attempt + 1,
                        proxy=proxy,
                    )
                    last_response = managed

                    if resp.status == 429 and attempt < attempt_limit:
                        retry_after = self._retry_after_seconds(resp.headers)
                        delay = retry_after if retry_after is not None else self._backoff(attempt + 1)
                        await self.cooldowns.push(platform, delay)
                        await asyncio.sleep(delay)
                        continue

                    if 500 <= resp.status < 600 and attempt < attempt_limit:
                        delay = self._backoff(attempt + 1)
                        await asyncio.sleep(delay)
                        continue

                    return managed
            except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
                last_error = str(exc)
                if attempt < attempt_limit:
                    await asyncio.sleep(self._backoff(attempt + 1))
                    continue
                return ManagedResponse(
                    status=None,
                    url=url,
                    text="",
                    headers={},
                    error=last_error,
                    attempts=attempt + 1,
                    proxy=proxy,
                )

        if last_response is not None:
            return last_response
        return ManagedResponse(status=None, url=url, text="", headers={}, error=last_error or "request failed")
