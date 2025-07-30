"""
Markdown Formatter for Chat Messages

Converts markdown text from LLMs (OpenAI, Gemini, Anthropic) to HTML for display
in QTextEdit with proper styling that matches the current theme.

Following PROJECT_RULES.md:
- ≤ 150 LOC with ≤ 2 public symbols per component
- Theme-aware formatting
- Performance optimized for streaming
"""

import markdown
from PySide6.QtCore import QObject, Signal

from ..themes import ThemeMode, get_theme_manager


class MarkdownFormatter(QObject):
    """
    Markdown to HTML formatter with theme-aware styling.

    Converts markdown from LLM responses to themed HTML for QTextEdit display.
    Supports all common markdown features used by OpenAI, Gemini, and Anthropic.
    """

    # Signal emitted when formatting completes
    formatted = Signal(str)  # HTML content

    def __init__(self) -> None:
        super().__init__()
        self.theme_manager = get_theme_manager()

        # Initialize markdown processor with common extensions
        self.md = markdown.Markdown(
            extensions=[
                "fenced_code",
                "codehilite",
                "tables",
                "nl2br",  # Convert newlines to <br>
                "toc",  # Table of contents for headers
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "use_pygments": False,  # Use custom CSS instead
                }
            },
        )

    def format_message(self, markdown_text: str) -> str:
        """
        Convert markdown text to themed HTML.

        Args:
            markdown_text: Raw markdown content from LLM

        Returns:
            HTML string with theme-appropriate styling
        """
        if not markdown_text.strip():
            return ""

        # Fix list indentation: normalize to 4 spaces for proper nesting
        import re
        processed_text = re.sub(r'^(\s{1,3})([-*+]\s+)', r'    \2', markdown_text, flags=re.MULTILINE)

        # Convert markdown to HTML
        html_content = self.md.convert(processed_text)

        # Reset markdown processor for next use
        self.md.reset()

        # Apply theme-aware styling
        styled_html = self._apply_theme_styles(html_content)

        return styled_html

    def _apply_theme_styles(self, html_content: str) -> str:
        """Apply theme-appropriate CSS styles to HTML content."""
        current_theme = self.theme_manager.current_mode

        # Get theme colors
        if current_theme == ThemeMode.DARK:
            colors = self._get_dark_theme_colors()
        else:
            colors = self._get_light_theme_colors()

        # Create styled HTML with embedded CSS
        style_block = f"""
        <style>
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {colors["header"]};
            margin-top: 1.2em;
            margin-bottom: 0.6em;
            font-weight: bold;
        }}
        h1 {{ font-size: 1.4em; }}
        h2 {{ font-size: 1.3em; }}
        h3 {{ font-size: 1.2em; }}
        h4, h5, h6 {{ font-size: 1.1em; }}

        /* Code blocks */
        pre {{
            background-color: {colors["code_bg"]};
            color: {colors["code_text"]};
            border: 1px solid {colors["border"]};
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
            overflow-x: auto;
        }}

        /* Inline code */
        code {{
            background-color: {colors["inline_code_bg"]};
            color: {colors["inline_code_text"]};
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}

        /* Strong/Bold text */
        strong, b {{
            color: {colors["bold"]};
            font-weight: bold;
        }}

        /* Emphasis/Italic text */
        em, i {{
            color: {colors["italic"]};
            font-style: italic;
        }}

        /* Tables */
        table {{
            border-collapse: collapse;
            margin: 8px 0;
            width: 100%;
        }}
        th, td {{
            border: 1px solid {colors["border"]};
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: {colors["table_header_bg"]};
            color: {colors["table_header_text"]};
            font-weight: bold;
        }}

        /* Lists */
        ul, ol {{
            margin: 8px 0;
            padding-left: 24px;
        }}
        li {{
            margin: 4px 0;
        }}

        /* Nested lists */
        li > ul, li > ol {{
            margin: 4px 0;
            padding-left: 20px;
        }}

        /* List items containing nested lists */
        li > p:last-child {{
            margin-bottom: 4px;
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 4px solid {colors["quote_border"]};
            background-color: {colors["quote_bg"]};
            margin: 8px 0;
            padding: 8px 16px;
            font-style: italic;
        }}

        /* Links */
        a {{
            color: {colors["link"]};
            text-decoration: underline;
        }}
        a:hover {{
            color: {colors["link_hover"]};
        }}

        /* Horizontal rules */
        hr {{
            border: none;
            border-top: 1px solid {colors["border"]};
            margin: 16px 0;
        }}
        </style>
        """

        return f"{style_block}<div>{html_content}</div>"

    def _get_dark_theme_colors(self) -> dict[str, str]:
        """Get color scheme for dark theme."""
        return {
            "header": "#90CAF9",
            "code_bg": "#1E1E1E",
            "code_text": "#E6E1E5",
            "border": "#49454F",
            "inline_code_bg": "#2E2E2E",
            "inline_code_text": "#90CAF9",
            "bold": "#FFFFFF",
            "italic": "#CAC4D0",
            "table_header_bg": "#49454F",
            "table_header_text": "#E6E1E5",
            "quote_border": "#90CAF9",
            "quote_bg": "#1E1E1E",
            "link": "#90CAF9",
            "link_hover": "#BBDEFB",
        }

    def _get_light_theme_colors(self) -> dict[str, str]:
        """Get color scheme for light theme."""
        return {
            "header": "#1976D2",
            "code_bg": "#F5F5F5",
            "code_text": "#1C1B1F",
            "border": "#CAC4D0",
            "inline_code_bg": "#F0F0F0",
            "inline_code_text": "#1976D2",
            "bold": "#000000",
            "italic": "#5F5F5F",
            "table_header_bg": "#E3F2FD",
            "table_header_text": "#1C1B1F",
            "quote_border": "#1976D2",
            "quote_bg": "#F9F9F9",
            "link": "#1976D2",
            "link_hover": "#1565C0",
        }


# Global formatter instance
_formatter_instance: MarkdownFormatter | None = None


def get_markdown_formatter() -> MarkdownFormatter:
    """Get the global markdown formatter instance."""
    global _formatter_instance
    if _formatter_instance is None:
        _formatter_instance = MarkdownFormatter()
    return _formatter_instance


# Export public symbols per PROJECT_RULES.md
__all__ = ["MarkdownFormatter", "get_markdown_formatter"]
