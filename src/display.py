from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from textwrap import shorten

from colorama import Fore, Style

from .enums import Mode, Status
from .models import CheckResult, NetworkOptions, PlatformConfig


STATUS_COLORS: dict[Status, str] = {
    Status.AVAILABLE: Fore.GREEN,
    Status.TAKEN: Fore.LIGHTBLACK_EX,
    Status.EXISTS: Fore.CYAN,
    Status.NOT_FOUND: Fore.YELLOW,
    Status.UNRESOLVED: Fore.YELLOW,
    Status.UNKNOWN: Fore.MAGENTA,
    Status.BLOCKED: Fore.RED,
    Status.RATE_LIMITED: Fore.LIGHTRED_EX,
    Status.ERROR: Fore.RED,
}

STATUS_SHORT: dict[Status, str] = {
    Status.AVAILABLE: "AVL",
    Status.TAKEN: "TKN",
    Status.EXISTS: "EXS",
    Status.NOT_FOUND: "NFD",
    Status.UNRESOLVED: "UNR",
    Status.UNKNOWN: "UNK",
    Status.BLOCKED: "BLK",
    Status.RATE_LIMITED: "429",
    Status.ERROR: "ERR",
}

CONFIDENCE_SHORT = {"high": "H", "medium": "M", "low": "L"}
CONFIDENCE_COLORS = {"high": Fore.GREEN, "medium": Fore.YELLOW, "low": Fore.LIGHTBLACK_EX}
MODE_COLORS = {Mode.OFFICIAL.value: Fore.GREEN, Mode.RESOLVE.value: Fore.CYAN, Mode.PROBE.value: Fore.YELLOW}

PLATFORM_SHORT = {
    "reddit": "RDT",
    "bluesky": "BSK",
    "tiktok": "TTK",
    "instagram": "IG",
    "threads": "THR",
    "x": "X",
    "github": "GH",
    "youtube": "YT",
    "twitch": "TW",
    "pinterest": "PIN",
    "tumblr": "TMB",
    "snapchat": "SNP",
    "facebook": "FB",
    "linkedin": "LI",
    "discord_invite": "DGG",
    "reddit_profile": "RPF",
}

MODE_EXPLAIN = {
    Mode.OFFICIAL.value: "Best signal. Platform exposes a true availability-style surface.",
    Mode.RESOLVE.value: "Middle signal. Name resolves or it does not, but claimability is not guaranteed.",
    Mode.PROBE.value: "Inference signal. Public profile route is checked, not the internal signup flow.",
}

STATUS_EXPLAIN = {
    Status.AVAILABLE: "Official source said the name is open.",
    Status.TAKEN: "Official source or resolver said the name is already in use.",
    Status.EXISTS: "Public route looked live.",
    Status.NOT_FOUND: "Public route looked missing.",
    Status.UNRESOLVED: "Resolver could not find the handle.",
    Status.UNKNOWN: "Response was ambiguous.",
    Status.BLOCKED: "Platform blocked the request or asked for auth/challenge.",
    Status.RATE_LIMITED: "Platform slowed or limited the request.",
    Status.ERROR: "Transport or parsing failure.",
}


@dataclass(slots=True)
class DisplayOptions:
    style: str = "pretty"
    show_reasons: bool = False
    show_urls: bool = False
    show_banner: bool = True
    show_legend: bool = False


def _truncate(value: str, limit: int) -> str:
    return shorten(value, width=limit, placeholder="…") if value else value


def render_banner(platform_count: int, username_count: int, network: NetworkOptions | None = None) -> str:
    pacing = "default pacing"
    if network:
        pacing = (
            f"concurrency={network.concurrency} retries={network.retries} "
            f"delay={network.min_delay:.1f}-{network.max_delay:.1f}s"
        )
    return (
        f"\n{Fore.CYAN}╭─ social-handle-checker{Style.RESET_ALL}\n"
        f"{Fore.CYAN}│{Style.RESET_ALL} scan   : {username_count} name(s) × {platform_count} platform(s)\n"
        f"{Fore.CYAN}│{Style.RESET_ALL} output : hybrid handle intelligence\n"
        f"{Fore.CYAN}│{Style.RESET_ALL} net    : {pacing}\n"
        f"{Fore.CYAN}╰────────────────────────────────────────{Style.RESET_ALL}"
    )


def render_info_block() -> str:
    return (
        f"{Fore.CYAN}info{Style.RESET_ALL}  "
        "This tool mixes official checks, handle resolvers, and public-page probes. "
        "Read the mode and confidence columns before treating a result as claimable."
    )


def render_wordlists(wordlists: list[str]) -> str:
    lines = [render_info_block(), "", f"{Fore.CYAN}built-in wordlists{Style.RESET_ALL}"]
    for item in wordlists:
        lines.append(f"  {Fore.LIGHTBLACK_EX}•{Style.RESET_ALL} {item}")
    return "\n".join(lines)


def render_platform_catalog(platforms: dict[str, PlatformConfig]) -> str:
    lines = [
        render_info_block(),
        "",
        f"{Fore.CYAN}legend{Style.RESET_ALL}  "
        f"{Fore.GREEN}official{Style.RESET_ALL}=highest signal  "
        f"{Fore.CYAN}resolve{Style.RESET_ALL}=middle signal  "
        f"{Fore.YELLOW}probe{Style.RESET_ALL}=public-route inference",
        "",
        f"{Fore.CYAN}{'key':16} {'mode':10} {'confidence':12} {'what you are looking at'}{Style.RESET_ALL}",
    ]

    for key, config in platforms.items():
        mode_color = MODE_COLORS.get(config.mode.value, Fore.WHITE)
        conf_color = CONFIDENCE_COLORS.get(config.confidence, Fore.WHITE)
        lines.append(
            f"{Fore.LIGHTBLACK_EX}◈{Style.RESET_ALL} "
            f"{key:16} "
            f"{mode_color}{config.mode.value:10}{Style.RESET_ALL} "
            f"{conf_color}{config.confidence:12}{Style.RESET_ALL} "
            f"{config.notes or ''}"
        )

    lines.extend(
        [
            "",
            f"{Fore.CYAN}mode guide{Style.RESET_ALL}",
            f"  {Fore.GREEN}official{Style.RESET_ALL} {MODE_EXPLAIN[Mode.OFFICIAL.value]}",
            f"  {Fore.CYAN}resolve{Style.RESET_ALL}  {MODE_EXPLAIN[Mode.RESOLVE.value]}",
            f"  {Fore.YELLOW}probe{Style.RESET_ALL}    {MODE_EXPLAIN[Mode.PROBE.value]}",
        ]
    )
    return "\n".join(lines)


def render_legend(style: str) -> str:
    if style == "stealth":
        return (
            f"\n{Fore.CYAN}legend{Style.RESET_ALL} "
            "AVL=available TKN=taken EXS=exists NFD=not-found UNR=unresolved "
            "UNK=unknown BLK=blocked 429=rate-limited ERR=error | H/M/L=confidence"
        )
    return (
        f"\n{Fore.CYAN}legend{Style.RESET_ALL} "
        "AVAILABLE/TAKEN = stronger signals. EXISTS/NOT_FOUND = public-route inference. "
        "UNKNOWN/BLOCKED/429 = treat cautiously."
    )


def render_result(result: CheckResult, options: DisplayOptions) -> str:
    color = STATUS_COLORS.get(result.status, Fore.WHITE)

    if options.style == "stealth":
        platform = PLATFORM_SHORT.get(result.platform, result.platform[:3].upper())
        short_status = STATUS_SHORT.get(result.status, result.status.value[:3])
        conf = CONFIDENCE_SHORT.get(result.confidence, result.confidence[:1].upper())
        line = f"{platform}::{short_status}::{conf}::{result.username}"
        extras: list[str] = []
        if options.show_reasons and result.reason:
            extras.append(_truncate(result.reason, 72))
        if options.show_urls and result.url:
            extras.append(_truncate(result.url, 72))
        if extras:
            line += " // " + " | ".join(extras)
        return color + line + Style.RESET_ALL

    mode_color = MODE_COLORS.get(result.mode, Fore.WHITE)
    conf_color = CONFIDENCE_COLORS.get(result.confidence, Fore.WHITE)
    line = (
        f"{Fore.LIGHTBLACK_EX}◈{Style.RESET_ALL} "
        f"{Fore.WHITE}{result.platform:<15}{Style.RESET_ALL} "
        f"{color}{result.status.value:<12}{Style.RESET_ALL} "
        f"{result.username:<18} "
        f"{mode_color}{result.mode:<8}{Style.RESET_ALL} "
        f"{conf_color}{result.confidence:<6}{Style.RESET_ALL}"
    )

    meta_bits: list[str] = []
    if result.attempts > 1:
        meta_bits.append(f"tries={result.attempts}")
    if result.http_status:
        meta_bits.append(f"http={result.http_status}")
    if result.proxy:
        meta_bits.append("proxy=on")
    if meta_bits:
        line += f" {Fore.LIGHTBLACK_EX}[{' '.join(meta_bits)}]{Style.RESET_ALL}"

    extras = []
    if options.show_reasons and result.reason:
        extras.append(_truncate(result.reason, 96))
    if options.show_urls and result.url:
        extras.append(_truncate(result.url, 96))
    if extras:
        line += f"\n  {Fore.LIGHTBLACK_EX}└─{Style.RESET_ALL} " + " | ".join(extras)
    return line


STATUS_ORDER = [
    Status.AVAILABLE,
    Status.TAKEN,
    Status.EXISTS,
    Status.NOT_FOUND,
    Status.UNRESOLVED,
    Status.UNKNOWN,
    Status.BLOCKED,
    Status.RATE_LIMITED,
    Status.ERROR,
]


def render_summary(results: list[CheckResult], options: DisplayOptions) -> str:
    by_platform: dict[str, Counter[Status]] = defaultdict(Counter)
    total_counter: Counter[Status] = Counter()

    for result in results:
        by_platform[result.platform][result.status] += 1
        total_counter[result.status] += 1

    if options.style == "stealth":
        header = f"\n{Fore.CYAN}:: matrix ::{Style.RESET_ALL}"
        lines = [header]
        totals = " ".join(
            f"{STATUS_SHORT[s]}={total_counter[s]}" for s in STATUS_ORDER if total_counter[s]
        )
        if totals:
            lines.append(totals)
        for platform in sorted(by_platform):
            label = PLATFORM_SHORT.get(platform, platform[:3].upper())
            counts = " ".join(
                f"{STATUS_SHORT[s]}={by_platform[platform][s]}" for s in STATUS_ORDER if by_platform[platform][s]
            )
            lines.append(f"{label}: {counts}")
        return "\n".join(lines)

    lines = [
        f"\n{Fore.CYAN}╭─ summary{Style.RESET_ALL}",
        f"{Fore.CYAN}│{Style.RESET_ALL} totals  "
        + ", ".join(f"{status.value}={total_counter[status]}" for status in STATUS_ORDER if total_counter[status]),
    ]

    for platform in sorted(by_platform):
        counts = ", ".join(
            f"{status.value}={by_platform[platform][status]}"
            for status in STATUS_ORDER
            if by_platform[platform][status]
        )
        lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} {platform:<15} {counts}")

    lines.extend(
        [
            f"{Fore.CYAN}╰────────────────────────────────────────{Style.RESET_ALL}",
            f"{Fore.CYAN}info{Style.RESET_ALL}  "
            f"{Fore.GREEN}stronger{Style.RESET_ALL}=AVAILABLE/TAKEN, "
            f"{Fore.YELLOW}inference{Style.RESET_ALL}=EXISTS/NOT_FOUND, "
            f"{Fore.MAGENTA}uncertain{Style.RESET_ALL}=UNKNOWN/BLK/429/ERR",
        ]
    )
    return "\n".join(lines)
