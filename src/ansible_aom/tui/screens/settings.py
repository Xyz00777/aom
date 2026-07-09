from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from ansible_aom.core.config_layer import AomSettings, load_config_with_layers


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
        config: AomSettings = load_config_with_layers()
        lines = self._build_display_lines(config)
        yield Static("\n".join(lines), id="settings-content")

    def _build_display_lines(self, config: AomSettings) -> list[str]:
        lines = []
        lines.append("AOM - Settings")
        lines.append("=" * 40)
        lines.append("")
        lines.append("Capture:")
        lines.append(f"  Verbose: {config.capture.verbose}")
        lines.append(f"  Include setup: {config.capture.include_setup}")
        excluded = ", ".join(config.capture.exclude_modules) or "(none)"
        lines.append(f"  Exclude modules: {excluded}")
        lines.append("")
        lines.append("Redaction:")
        lines.append(f"  Enabled: {config.redaction.enabled}")
        whitelist = ", ".join(config.redaction.whitelist) or "(none)"
        lines.append(f"  Whitelist: {whitelist}")
        custom_fields = ", ".join(config.redaction.custom_fields) or "(none)"
        lines.append(f"  Custom fields: {custom_fields}")
        patterns = ", ".join(str(p) for p in config.redaction.custom_patterns) or "(none)"
        lines.append(f"  Custom key patterns: {patterns}")
        lines.append("")
        lines.append("Live:")
        lines.append(f"  Show failed hint: {config.live.show_failed_hint}")
        lines.append(f"  Show warnings: {config.live.show_warnings}")
        lines.append(f"  Show deprecations: {config.live.show_deprecations}")
        lines.append("")
        lines.append("Log:")
        lines.append(f"  Max lines: {config.log.max_lines}")
        lines.append("")
        lines.append("Session:")
        lines.append(f"  Keep count: {config.session.keep_sessions}")
        lines.append(f"  Keep days: {config.session.keep_days}")
        lines.append("")
        lines.append("Press Escape or S to close")
        return lines

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
