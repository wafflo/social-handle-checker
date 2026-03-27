from __future__ import annotations

from dataclasses import replace

from .enums import Mode
from .models import PlatformConfig


PLATFORMS: dict[str, PlatformConfig] = {
    "reddit": PlatformConfig(
        key="reddit",
        label="Reddit",
        mode=Mode.OFFICIAL,
        confidence="high",
        docs_url="https://www.reddit.com/dev/api/oauth/",
        notes="Uses Reddit's documented username availability endpoint.",
    ),
    "bluesky": PlatformConfig(
        key="bluesky",
        label="Bluesky",
        mode=Mode.RESOLVE,
        confidence="medium",
        docs_url="https://docs.bsky.app/docs/api/com-atproto-identity-resolve-handle",
        notes="Unresolved handle is a useful signal, but not a guaranteed claimability check.",
        username_transform="bluesky_handle",
    ),
    "tiktok": PlatformConfig(
        key="tiktok",
        label="TikTok",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.tiktok.com/@{username}",
        docs_url="https://support.tiktok.com/en/getting-started/setting-up-your-profile/changing-your-username",
        notes="Public profile route probe only.",
        ok_statuses={200},
        not_found_statuses={404},
        blocked_statuses={401, 403},
        rate_limit_statuses={429},
    ),
    "instagram": PlatformConfig(
        key="instagram",
        label="Instagram",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.instagram.com/{username}/",
        docs_url="https://help.instagram.com/583107688369069",
        notes="Public profile route probe only.",
        blocked_statuses={401, 403, 999},
    ),
    "threads": PlatformConfig(
        key="threads",
        label="Threads",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.threads.net/@{username}",
        notes="Public profile route probe only.",
    ),
    "x": PlatformConfig(
        key="x",
        label="X",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://x.com/{username}",
        notes="Public profile route probe only.",
    ),
    "github": PlatformConfig(
        key="github",
        label="GitHub",
        mode=Mode.PROBE,
        confidence="medium",
        url_template="https://github.com/{username}",
        docs_url="https://docs.github.com/en/account-and-profile/concepts/username-changes",
        notes="404 on a user profile route is a useful signal, but still not a guaranteed registration check.",
    ),
    "youtube": PlatformConfig(
        key="youtube",
        label="YouTube",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.youtube.com/@{username}",
        notes="Public handle route probe only.",
    ),
    "twitch": PlatformConfig(
        key="twitch",
        label="Twitch",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.twitch.tv/{username}",
        docs_url="https://dev.twitch.tv/docs/api/reference#get-users",
        notes="Public profile route probe only; Twitch also has authenticated user lookup by login.",
    ),
    "pinterest": PlatformConfig(
        key="pinterest",
        label="Pinterest",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.pinterest.com/{username}/",
        notes="Public profile route probe only.",
    ),
    "tumblr": PlatformConfig(
        key="tumblr",
        label="Tumblr",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://{username}.tumblr.com/",
        notes="Public blog route probe only.",
    ),
    "snapchat": PlatformConfig(
        key="snapchat",
        label="Snapchat",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.snapchat.com/add/{username}",
        notes="Public add route probe only.",
    ),
    "facebook": PlatformConfig(
        key="facebook",
        label="Facebook",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.facebook.com/{username}",
        notes="Public page/profile route probe only.",
    ),
    "linkedin": PlatformConfig(
        key="linkedin",
        label="LinkedIn",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.linkedin.com/in/{username}",
        notes="Public profile route probe only.",
        blocked_statuses={401, 403, 999},
    ),
    "discord_invite": PlatformConfig(
        key="discord_invite",
        label="Discord Vanity Invite",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://discord.gg/{username}",
        docs_url="https://support.discord.com/hc/en-us/articles/115001542132-Custom-Invite-Link",
        notes="Checks vanity invite presence, not Discord user accounts.",
    ),
    "reddit_profile": PlatformConfig(
        key="reddit_profile",
        label="Reddit Profile Route",
        mode=Mode.PROBE,
        confidence="low",
        url_template="https://www.reddit.com/user/{username}/",
        notes="Public profile route probe only; less authoritative than Reddit's official availability endpoint.",
    ),
}

DEFAULT_PLATFORMS: tuple[str, ...] = tuple(PLATFORMS.keys())
OFFICIAL_FIRST: tuple[str, ...] = ("reddit", "bluesky")


def build_runtime_platforms(
    *,
    override_urls: dict[str, str] | None = None,
    override_modes: dict[str, str] | None = None,
    override_confidence: dict[str, str] | None = None,
) -> dict[str, PlatformConfig]:
    runtime: dict[str, PlatformConfig] = {key: replace(value) for key, value in PLATFORMS.items()}

    for key, new_url in (override_urls or {}).items():
        if key in runtime:
            runtime[key].url_template = new_url
            runtime[key].notes = (runtime[key].notes or "") + " Runtime URL override active."

    for key, new_mode in (override_modes or {}).items():
        if key in runtime:
            runtime[key].mode = Mode(new_mode)
            runtime[key].notes = (runtime[key].notes or "") + " Runtime mode override active."

    for key, new_conf in (override_confidence or {}).items():
        if key in runtime:
            runtime[key].confidence = new_conf
            runtime[key].notes = (runtime[key].notes or "") + " Runtime confidence override active."

    return runtime
