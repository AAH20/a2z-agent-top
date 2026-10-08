"""
Hotkey Dispatcher and Keyboard Event Controller.
Handles single-key interactive commands for swarm navigation and execution interlocks.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Any


class HotkeyController:
    """
    Translates keyboard input characters into operational actions.
    Supports navigation, state toggling, views switching, and process termination.
    """

    def __init__(self):
        self._handlers: Dict[str, Callable[[], Any]] = {}

    def register(self, key: str, handler: Callable[[], Any]) -> None:
        """Register action callback for a key character."""
        self._handlers[key.lower()] = handler

    def handle_key(self, ch: int) -> bool:
        """
        Process raw key code from curses.
        Returns True if a handler was found and executed.
        """
        if ch == -1:
            return False

        char = chr(ch).lower() if 0 <= ch <= 255 else ""

        # Map special curses keycodes or characters
        if char in self._handlers:
            self._handlers[char]()
            return True

        # Special space bar representation
        if ch == 32 and " " in self._handlers:
            self._handlers[" "]()
            return True

        return False
