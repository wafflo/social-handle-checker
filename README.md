<div align="center">

<img src="./assets/banner-main.png" alt="Social Handle Checker Banner" width="100%" />

# Social Handle Checker

### Cross-platform username checker for OSINT, brand research, handle hunting, and multi-platform username discovery

<p>
  <a href="https://dragic.site">
    <img src="https://img.shields.io/badge/Website-dragic.site-8b5cf6?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Website" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Interface-CLI-111827?style=for-the-badge" alt="CLI" />
  <img src="https://img.shields.io/badge/License-MIT-16a34a?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/Focus-OSINT%20%7C%20Username%20Checking-e11d48?style=for-the-badge" alt="OSINT Username Checking" />
</p>

**Social Handle Checker** is a hybrid cross-platform username checker built for **OSINT**, **username sellers**, **brand research**, **handle hunting**, and **fast multi-platform username discovery**.

It combines **official availability checks**, **resolver-based logic**, and **public profile probes** to help identify whether a username **exists**, **resolves**, **appears open**, or **needs manual review** across major platforms.

<p>
  <a href="https://dragic.site"><strong>Visit dragic.site</strong></a>
</p>

</div>

---

## Preview

<div align="center">
  <img src="./assets/pfpppp.png" alt="Dragic Round PFP" width="170" />
  <img src="./assets/asdasda.png" alt="Dragic Square Graphic" width="170" />
  <img src="./assets/pfp.png" alt="Dragic Alt PFP" width="170" />
</div>

---

## What this does

Social Handle Checker helps you check whether a username:

- **Exists**
- **Resolves**
- **Appears open**
- **Needs manual review**
- **Returns blocked, rate-limited, or uncertain signals**

Instead of pretending every platform gives a perfect answer, this tool separates checks by **mode** and **confidence** so you can tell what is authoritative and what is inference.

---

## Why this is different

Most username checkers are one of these:

- weak one-site scripts
- fake “all-platform” tools with misleading results
- messy OSINT tools with poor output and no real usability

**Social Handle Checker** uses a hybrid model:

- **Official** → strongest signal
- **Resolve** → useful signal, not always claimability
- **Probe** → public-route inference only

That makes it practical for:

- username sellers
- handle hunters
- brand research
- OSINT workflows
- fast cross-platform discovery

---

## Supported logic

### Official checks
Platforms where the checker uses a stronger or documented signal where possible.

- Reddit

### Resolver checks
Platforms where handle resolution exists, even if it is not a guaranteed registration check.

- Bluesky

### Public profile probes
Platforms checked through public profile routes and route behavior.

- TikTok
- Instagram
- Threads
- X
- GitHub
- YouTube
- Twitch
- Pinterest
- Tumblr
- Snapchat
- Facebook
- LinkedIn
- Reddit profiles
- Discord vanity invites

---

## Result states

| Status | Meaning |
|---|---|
| `AVAILABLE` | Official check says the username is available |
| `TAKEN` | Official check says the username is unavailable |
| `EXISTS` | Public route appears to resolve to a live profile |
| `NOT_FOUND` | Public route does not appear to resolve |
| `UNRESOLVED` | Resolver could not resolve the handle |
| `UNKNOWN` | Signal was inconclusive |
| `BLOCKED` | Request was blocked or challenged |
| `RATE_LIMITED` | Platform rate limited the request |
| `ERROR` | Request failed or could not be parsed |

---

## Features

- Cross-platform handle scanning
- Official / resolver / probe hybrid logic
- Built-in wordlists
- Custom wordlist support
- Pretty CLI output
- Compact stealth output
- Retry and pacing controls
- Proxy support
- Runtime overrides
- Confidence-aware results
- Bulk username scanning
- Cleaner output for both casual users and power users

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/social-handle-checker.git
cd social-handle-checker
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -e .
```

---

## Quick start

### Check one username
```bash
socialcheck --username dragic --platforms all --style pretty
```

### Check with reasons
```bash
socialcheck --username dragic --platforms all --style pretty --show-reasons
```

### Use a built-in wordlist
```bash
socialcheck --wordlist gamer --platforms reddit,bluesky,tiktok,instagram,github
```

### Use your own usernames file
```bash
socialcheck --usernames-file usernames.txt --platforms all
```

### List supported platforms
```bash
socialcheck --list-platforms
```

---

## Built-in wordlists

The project includes pre-made lists for fast testing:

- `common`
- `gamer`
- `brandable`

You can also supply your own list:

```bash
socialcheck --usernames-file usernames.txt --platforms all
```

---

## Advanced usage

### Retry and pacing
```bash
socialcheck --usernames-file usernames.txt --platforms all --retries 3 --min-delay 0.4 --max-delay 1.2
```

### Proxy support
```bash
socialcheck --usernames-file usernames.txt --platforms all --proxy-file proxies.txt --proxy-mode rotate
```

### Override behavior
```bash
socialcheck --username dragic --platforms github --override-confidence github=high
```

### Stealth output
```bash
socialcheck --wordlist brandable --platforms all --style stealth --legend
```

---

## Accuracy model

This project does **not** pretend that every missing page means a username is claimable.

That is the difference between a useful tool and a misleading one.

- **Official checks** are treated as the strongest signal
- **Resolvers** are useful, but not always equivalent to signup availability
- **Public probes** are route-based inference, not guarantees

**Confidence matters.**  
**Uncertainty is labeled instead of hidden.**

---

## Use cases

### For OSINT
- cross-platform handle discovery
- profile presence checks
- handle resolution
- basic attribution support
- fast username correlation workflows

### For username sellers / handle hunters
- scan bulk lists quickly
- spot obvious claims
- find unresolved or absent handles
- compare names across many platforms from one CLI
- reduce manual tab-hopping

### For brand research
- check name presence across platforms
- find obvious conflicts
- audit handle consistency
- spot missing name coverage

---

## Gallery

<div align="center">
  <img src="./assets/dragic_upscaled.png" alt="Dragic Banner Alt" width="100%" />
  <br /><br />
  <img src="./assets/pfpppp.png" alt="Round PFP" width="150" />
  <img src="./assets/asdasda.png" alt="Square Graphic" width="150" />
  <img src="./assets/pfp.png" alt="Alt PFP" width="150" />
</div>

---

## Website

If you want project updates, branding, or anything else tied to the Dragic side:

<div align="center">

## **[dragic.site](https://dragic.site)**

</div>

---

## Repo structure

```text
social-handle-checker/
├── assets/
│   ├── 7a713a51-2d6b-4849-a575-13dae0ba857f.png
│   ├── asdasda.png
│   ├── banner-main.png
│   ├── dragic_upscaled.png
│   ├── pfp.png
│   └── pfpppp.png
├── src/
│   └── social_handle_checker/
├── README.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

---

## Image setup

This README expects these image files to sit inside the **assets** folder:

- `assets/7a713a51-2d6b-4849-a575-13dae0ba857f.png`
- `assets/asdasda.png`
- `assets/banner-main.png`
- `assets/dragic_upscaled.png`
- `assets/pfp.png`
- `assets/pfpppp.png`

If any image does not load on GitHub, make sure the filename matches **exactly**, including capitalization.

---

## Roadmap

- More platform adapters
- Better HTML signal parsing
- Better export options
- More resolver support
- Better classification logic
- Better batch scanning workflows
- Cleaner screenshots and CLI examples

---

## License

MIT License.

---

## Author

<div align="center">

### dragic / wafflo

**Website:** [dragic.site](https://dragic.site)

<img src="./assets/asdasda.png" alt="Dragic Avatar" width="140" />

</div>
