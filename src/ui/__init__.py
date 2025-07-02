"""
UI Components Package

Contains UI dialogs and components for the chat frontend.
Following PROJECT_RULES.md:
- ≤ 150 LOC with ≤ 2 public symbols per UI controller
- Keep UI thread under 10ms per frame
"""

from .settings_dialog import SettingsDialog

__all__ = [
    "SettingsDialog",
]
