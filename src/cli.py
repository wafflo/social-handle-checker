from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from colorama import init

from .display import (
    DisplayOptions,
    render_banner,
    render_info_block,
    render_legend,
    render_platform_catalog,
    render_summary,
    render_wordlists,
)
from .engine import normalize_usernames, run_checks
from .models import NetworkOptions
from .platforms import DEFAULT_PLATFORMS, PLATFORMS, build_runtime_platforms
from .wordlists import list_builtin_wordlists, load_builtin_wordlist, load_user_wordlist


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="socialcheck",
        description="Hybrid cross-platform social handle checker.",
    )
    parser.add_argument(
        "--platforms",
        default="all",
        help="Comma-separated platform keys, or 'all'.",
    )
    parser.add_argument(
        "--usernames-file",
        help="Path to a newline-delimited custom username list.",
    )
    parser.add_argument(
        "--wordlist",
        help="Built-in wordlist name. Use --list-wordlists to inspect options.",
    )
    parser.add_argument(
        "--username",
        action="append",
        default=[],
        help="Single username to add. May be used multiple times.",
    )
    parser.add_argument(
        "--list-platforms",
        action="store_true",
        help="Print supported platforms and exit.",
    )
    parser.add_argument(
        "--list-wordlists",
        action="store_true",
        help="Print built-in wordlists and exit.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to write result files into.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Maximum concurrent requests.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=12,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retry count for timeouts, 429s, and transient 5xx responses.",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=1.4,
        help="Base backoff in seconds for retries.",
    )
    parser.add_argument(
        "--retry-max-sleep",
        type=float,
        default=10.0,
        help="Maximum backoff sleep between retries.",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=0.15,
        help="Minimum randomized delay before each request.",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=0.65,
        help="Maximum randomized delay before each request.",
    )
    parser.add_argument(
        "--proxy",
        action="append",
        default=[],
        help="Proxy URL. May be used multiple times. Example: http://user:pass@host:port",
    )
    parser.add_argument(
        "--proxy-file",
        help="Path to a file containing one proxy URL per line.",
    )
    parser.add_argument(
        "--proxy-mode",
        choices=("off", "single", "rotate", "random"),
        default="off",
        help="How proxies should be used when supplied.",
    )
    parser.add_argument(
        "--no-rotate-on-retry",
        action="store_true",
        help="Keep the same proxy on retry instead of switching when proxy rotation is enabled.",
    )
    parser.add_argument(
        "--user-agent",
        help="Override the default User-Agent string.",
    )
    parser.add_argument(
        "--random-user-agent",
        action="store_true",
        help="Rotate through a small built-in User-Agent pool.",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Extra request header in 'Name: Value' format. May be used multiple times.",
    )
    parser.add_argument(
        "--no-follow-redirects",
        action="store_true",
        help="Disable redirect following for probe requests.",
    )
    parser.add_argument(
        "--override-url",
        action="append",
        default=[],
        help="Runtime URL override in 'platform=https://...' format.",
    )
    parser.add_argument(
        "--override-mode",
        action="append",
        default=[],
        help="Runtime mode override in 'platform=official|resolve|probe' format.",
    )
    parser.add_argument(
        "--override-confidence",
        action="append",
        default=[],
        help="Runtime confidence override in 'platform=high|medium|low' format.",
    )
    parser.add_argument(
        "--style",
        choices=("pretty", "stealth", "json"),
        default="pretty",
        help="Terminal output style.",
    )
    parser.add_argument(
        "--show-reasons",
        action="store_true",
        help="Show condensed reasoning beside each result.",
    )
    parser.add_argument(
        "--show-urls",
        action="store_true",
        help="Show the resolved URL beside each result.",
    )
    parser.add_argument(
        "--legend",
        action="store_true",
        help="Show a legend for compact status codes.",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the header banner.",
    )
    return parser


def resolve_platforms(raw: str) -> list[str]:
    if raw.lower() == "all":
        return list(DEFAULT_PLATFORMS)
    items = [item.strip() for item in raw.split(",") if item.strip()]
    invalid = [item for item in items if item not in PLATFORMS]
    if invalid:
        raise SystemExit(f"Unknown platforms: {', '.join(invalid)}")
    return items


def gather_usernames(args: argparse.Namespace) -> list[str]:
    names: list[str] = []
    names.extend(args.username)

    if args.wordlist:
        names.extend(load_builtin_wordlist(args.wordlist))

    if args.usernames_file:
        names.extend(load_user_wordlist(args.usernames_file))

    names = normalize_usernames(names)
    if not names:
        raise SystemExit("No usernames supplied. Use --username, --wordlist, or --usernames-file.")
    return names


def parse_kv_overrides(items: list[str], *, allowed_values: set[str] | None = None) -> dict[str, str]:
    output: dict[str, str] = {}
    for raw in items:
        if "=" not in raw:
            raise SystemExit(f"Invalid override format: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key not in PLATFORMS:
            raise SystemExit(f"Unknown platform in override: {key}")
        if allowed_values and value not in allowed_values:
            raise SystemExit(f"Invalid override value for {key}: {value}")
        output[key] = value
    return output


def parse_headers(items: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw in items:
        if ":" not in raw:
            raise SystemExit(f"Invalid header format: {raw}")
        key, value = raw.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def load_proxy_file(path: str | None) -> list[str]:
    if not path:
        return []
    text = Path(path).read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def build_network_options(args: argparse.Namespace) -> NetworkOptions:
    proxies = tuple([*args.proxy, *load_proxy_file(args.proxy_file)])
    if proxies and args.proxy_mode == "off":
        args.proxy_mode = "single"
    return NetworkOptions(
        concurrency=max(1, args.concurrency),
        timeout_seconds=max(1, args.timeout),
        retries=max(0, args.retries),
        retry_backoff=max(0.0, args.retry_backoff),
        retry_max_sleep=max(0.0, args.retry_max_sleep),
        min_delay=max(0.0, args.min_delay),
        max_delay=max(0.0, args.max_delay),
        proxy=proxies[0] if proxies else None,
        proxies=proxies,
        proxy_mode=args.proxy_mode,
        rotate_on_retry=not args.no_rotate_on_retry,
        user_agent=args.user_agent,
        random_user_agent=args.random_user_agent,
        extra_headers=parse_headers(args.header),
        follow_redirects=not args.no_follow_redirects,
    )


def main() -> None:
    init(autoreset=True)
    parser = build_parser()
    args = parser.parse_args()

    override_urls = parse_kv_overrides(args.override_url)
    override_modes = parse_kv_overrides(args.override_mode, allowed_values={"official", "resolve", "probe"})
    override_conf = parse_kv_overrides(args.override_confidence, allowed_values={"high", "medium", "low"})
    runtime_platforms = build_runtime_platforms(
        override_urls=override_urls,
        override_modes=override_modes,
        override_confidence=override_conf,
    )

    if args.list_platforms:
        print(render_platform_catalog(runtime_platforms))
        return

    if args.list_wordlists:
        print(render_wordlists(list_builtin_wordlists()))
        return

    usernames = gather_usernames(args)
    platforms = resolve_platforms(args.platforms)
    display = DisplayOptions(
        style=args.style,
        show_reasons=args.show_reasons,
        show_urls=args.show_urls,
        show_banner=not args.no_banner,
        show_legend=args.legend,
    )
    network = build_network_options(args)

    if args.style != "json" and display.show_banner:
        print(render_banner(len(platforms), len(usernames), network))
        print(render_info_block())

    results = asyncio.run(
        run_checks(
            usernames=usernames,
            platforms=platforms,
            output_dir=Path(args.output_dir),
            runtime_platforms=runtime_platforms,
            network=network,
            display=display,
        )
    )

    if args.style == "json":
        print(json.dumps([item.to_dict() for item in results], indent=2, ensure_ascii=False))
        return

    print(render_summary(results, display))
    if display.show_legend:
        print(render_legend(display.style))


if __name__ == "__main__":
    main()
