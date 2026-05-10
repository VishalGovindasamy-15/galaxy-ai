"""Boot view — ASCII logo and boot sequence display."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from galaxy.cli.colors import GALAXY_CYAN, GALAXY_PURPLE, GALAXY_DIM
from galaxy.core.version import __version__

GALAXY_LOGO = r"""
   ██████╗  █████╗ ██╗      █████╗ ██╗  ██╗██╗   ██╗
  ██╔════╝ ██╔══██╗██║     ██╔══██╗╚██╗██╔╝╚██╗ ██╔╝
  ██║  ███╗███████║██║     ███████║ ╚███╔╝  ╚████╔╝
  ██║   ██║██╔══██║██║     ██╔══██║ ██╔██╗   ╚██╔╝
  ╚██████╔╝██║  ██║███████╗██║  ██║██╔╝ ██╗   ██║
   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
"""


def render_boot(console: Console, steps: list[str] | None = None) -> None:
    """Render the boot sequence with ASCII logo.

    Args:
        console: Rich console to render to.
        steps: Optional list of boot step messages.
    """
    logo_text = Text(GALAXY_LOGO, style=f"bold {GALAXY_CYAN}")
    subtitle = Text(
        f"  Autonomous Software Engineering OS  v{__version__}",
        style=f"{GALAXY_DIM}",
    )

    console.print(Panel(
        logo_text + Text("\n") + subtitle,
        border_style=GALAXY_PURPLE,
        padding=(0, 2),
    ))

    if steps:
        for step in steps:
            console.print(f"  [{GALAXY_CYAN}]▸[/] {step}")
        console.print()
