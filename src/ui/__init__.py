"""
UI Components Package

Contains UI dialogs and components for the chat frontend.
Following PROJECT_RULES.md:
- ≤ 150 LOC with ≤ 2 public symbols per UI controller
- Keep UI thread under 10ms per frame
"""

from .backend_settings_widget import BackendSettingsWidget
from .markdown_formatter import MarkdownFormatter, get_markdown_formatter
from .settings_dialog import SettingsDialog
from .ui_settings_widget import UISettingsWidget

__all__ = [
    "BackendSettingsWidget",
    "MarkdownFormatter",
    "SettingsDialog",
    "UISettingsWidget",
    "get_markdown_formatter",
]
