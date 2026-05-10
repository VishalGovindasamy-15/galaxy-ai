"""Galaxy color constants and design tokens.

Centralized color palette for the entire CLI.
"""

from __future__ import annotations

# ─── Core Brand Colors ──────────────────────────────────────────────────────

GALAXY_CYAN = "#00d4ff"
GALAXY_PURPLE = "#a855f7"
GALAXY_GREEN = "#22c55e"
GALAXY_YELLOW = "#eab308"
GALAXY_RED = "#ef4444"
GALAXY_ORANGE = "#f97316"
GALAXY_DIM = "#6b7280"
GALAXY_WHITE = "#f9fafb"

# ─── Agent Tier Colors ──────────────────────────────────────────────────────

MASTER_COLOR = GALAXY_PURPLE
DOMAIN_COLOR = GALAXY_CYAN
WORKER_COLOR = GALAXY_GREEN

# ─── Status Colors ──────────────────────────────────────────────────────────

STATUS_IDLE = GALAXY_DIM
STATUS_WORKING = GALAXY_CYAN
STATUS_SUCCESS = GALAXY_GREEN
STATUS_FAILED = GALAXY_RED
STATUS_WARNING = GALAXY_YELLOW

# ─── Rich Markup Shortcuts ──────────────────────────────────────────────────

def cyan(text: str) -> str:
    return f"[{GALAXY_CYAN}]{text}[/]"

def green(text: str) -> str:
    return f"[{GALAXY_GREEN}]{text}[/]"

def red(text: str) -> str:
    return f"[{GALAXY_RED}]{text}[/]"

def yellow(text: str) -> str:
    return f"[{GALAXY_YELLOW}]{text}[/]"

def dim(text: str) -> str:
    return f"[{GALAXY_DIM}]{text}[/]"

def purple(text: str) -> str:
    return f"[{GALAXY_PURPLE}]{text}[/]"
