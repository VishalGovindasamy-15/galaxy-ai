"""Keyboard controller — hotkey handler for interactive mode.

Manages keyboard shortcuts for the Galaxy terminal UI.
[Tab] — switch panels, [Space] — approve, [Q] — quit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Hotkey:
    """A registered hotkey binding."""
    key: str
    description: str
    callback: Callable[[], None] | None = None
    enabled: bool = True

    def trigger(self) -> None:
        if self.callback and self.enabled:
            self.callback()


class KeyboardController:
    """Manages keyboard shortcuts for Galaxy interactive mode.

    Usage:
        kb = KeyboardController()
        kb.register("tab", "Switch panel", callback=switch_fn)
        kb.register("space", "Approve action", callback=approve_fn)
        kb.register("q", "Quit", callback=quit_fn)

        # In event loop:
        kb.handle("tab")
    """

    def __init__(self) -> None:
        self._hotkeys: dict[str, Hotkey] = {}

    def register(
        self,
        key: str,
        description: str,
        callback: Callable[[], None] | None = None,
    ) -> None:
        """Register a hotkey binding."""
        self._hotkeys[key.lower()] = Hotkey(
            key=key.lower(),
            description=description,
            callback=callback,
        )

    def unregister(self, key: str) -> None:
        """Remove a hotkey binding."""
        self._hotkeys.pop(key.lower(), None)

    def handle(self, key: str) -> bool:
        """Handle a keypress.

        Args:
            key: The key that was pressed.

        Returns:
            True if the key was handled, False otherwise.
        """
        hotkey = self._hotkeys.get(key.lower())
        if hotkey and hotkey.enabled:
            hotkey.trigger()
            return True
        return False

    def enable(self, key: str) -> None:
        """Enable a hotkey."""
        hotkey = self._hotkeys.get(key.lower())
        if hotkey:
            hotkey.enabled = True

    def disable(self, key: str) -> None:
        """Disable a hotkey."""
        hotkey = self._hotkeys.get(key.lower())
        if hotkey:
            hotkey.enabled = False

    @property
    def bindings(self) -> list[Hotkey]:
        """Get all registered hotkeys."""
        return list(self._hotkeys.values())

    def get_help_text(self) -> str:
        """Get formatted help text for all hotkeys."""
        lines = []
        for hotkey in self._hotkeys.values():
            status = "" if hotkey.enabled else " (disabled)"
            lines.append(f"  [{hotkey.key.upper()}] {hotkey.description}{status}")
        return "\n".join(lines) if lines else "  No hotkeys registered"

    def setup_defaults(
        self,
        on_switch: Callable[[], None] | None = None,
        on_approve: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ) -> None:
        """Register default Galaxy hotkeys."""
        self.register("tab", "Switch panel", callback=on_switch)
        self.register("space", "Approve/Continue", callback=on_approve)
        self.register("q", "Quit", callback=on_quit)
        self.register("h", "Show help", callback=None)
        self.register("d", "Toggle dashboard", callback=None)
