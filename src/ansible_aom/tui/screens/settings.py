from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from ansible_aom.core.config import AppConfig, load_config


class SettingsScreen(Screen):
    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    SettingsScreen > Static {
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="dismiss", description="Close settings"),
        Binding(key="S", action="dismiss", description="Close settings"),
    ]

    def compose(self) -> ComposeResult:
        config: AppConfig = load_config()
        lines = self._build_display_lines(config)
        yield Static("\n".join(lines), id="settings-content")

    def _build_display_lines(self, config: AppConfig) -> list[str]:
        lines = []
        lines.append("AOM - Settings")
        lines.append("=" * 40)
        lines.append("")
        lines.append("Status Bar:")
        elements = config.status_bar.elements
        elements_str = ", ".join(elements) if elements else "(none)"
        lines.append(f"  Elements: {elements_str}")
        lines.append("")
        lines.append("Redaction:")
        whitelist = config.redaction.whitelist
        whitelist_str = ", ".join(whitelist) if whitelist else "(none)"
        lines.append(f"  Whitelist: {whitelist_str}")
        custom_fields = config.redaction.custom_fields
        fields_str = ", ".join(custom_fields) if custom_fields else "(none)"
        lines.append(f"  Custom fields: {fields_str}")
        patterns = config.redaction.custom_patterns
        patterns_str = ", ".join(str(p) for p in patterns) if patterns else "(none)"
        lines.append(f"  Custom patterns: {patterns_str}")
        lines.append("")
        lines.append("Warnings:")
        lines.append(f"  Show warnings: {config.warnings.show_warnings}")
        lines.append(f"  Show deprecations: {config.warnings.show_deprecations}")
        lines.append("")
        lines.append("Log:")
        lines.append(f"  Max lines: {config.log_max_lines}")
        lines.append("")
        lines.append("Session:")
        lines.append(f"  Keep count: {config.session_keep_count}")
        lines.append(f"  Keep days: {config.session_keep_days}")
        lines.append("")
        lines.append("Press Escape or S to close")
        return lines

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
