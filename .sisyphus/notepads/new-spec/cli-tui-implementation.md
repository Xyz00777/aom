# CLI/TUI Implementation Research - 2026-04-20

## Research Summary

This document captures research findings for implementing a CLI tool with both text-only and TUI modes.

---

## 1. Rich Console Output (Non-TUI Mode)

### Console Class Usage

**Evidence** ([Rich docs](https://rich.readthedocs.io/en/stable/reference/console.html)):

```python
from rich.console import Console

# Create console for output
console = Console()

# Print to stdout (detects TTY automatically)
console.print("[bold blue]Hello[/bold blue] World!")

# Force stdout (explicit)
console = Console(file=sys.stdout)

# Force terminal mode (bypass TTY detection)
console = Console(force_terminal=True)

# Non-interactive mode (for piping/CI)
console = Console(force_terminal=False, no_color=True)
```

### Key Rich Console Features:

1. **TTY Detection**: Rich auto-detects TTY with `sys.stdout.isatty()`
2. **force_terminal**: Set to `True` to force colors/styling (for CI with color support)
3. **no_color**: Set to `True` to disable all colors
4. **width/height**: Override terminal size detection

### Best Practice Pattern:

```python
import sys
from rich.console import Console

def get_console(force: bool = False) -> Console:
    """
    Create Console with environment-aware settings.
    
    - If stdout is a TTY: full colors/styling
    - If stdout is piped: no colors, plain text
    - If force=True: force colors even when piped
    """
    if not sys.stdout.isatty():
        # Piped mode - no colors
        return Console(force_terminal=False, no_color=True)
    
    if force:
        # Force colors (for CI systems that support colors)
        return Console(force_terminal=True)
    
    # Standard TTY mode
    return Console()
```

**Evidence** ([real-world example from ArchiveBox](https://github.com/ArchiveBox/ArchiveBox/blob/dev/archivebox/config/common.py#L30)):

```python
IS_TTY: bool = Field(default=sys.stdout.isatty())
USE_COLOR: bool = Field(default=sys.stdout.isatty())
SHOW_PROGRESS: bool = Field(default=sys.stdout.isatty())
```

### Rich Tables for Diff Display

**Evidence** ([Rich docs](https://rich.readthedocs.io/en/stable/tables.html)):

```python
from rich.console import Console
from rich.table import Table

def create_diff_table(run1_results: list, run2_results: list) -> Table:
    """Create a table showing task/host results comparison."""
    table = Table(title="Run Comparison", show_lines=True)
    
    # Columns
    table.add_column("Task/Host", style="cyan", no_wrap=True)
    table.add_column("Run 1", style="white")
    table.add_column("Run 2", style="white")
    table.add_column("Status", style="bold")
    
    # Rows with diff indicators
    for r1, r2 in zip(run1_results, run2_results):
        if r1.changed == r2.changed:
            status = "[dim]unchanged[/dim]"
            status_style = "dim"
        elif r2.changed > r1.changed:
            status = "[bold red]regressed[/bold red]"
            status_style = "red"
        else:
            status = "[bold green]improved[/bold green]"
            status_style = "green"
        
        table.add_row(
            r1.name,
            str(r1.changed),
            str(r2.changed),
            status
        )
    
    return table

# Usage
console = get_console()
table = create_diff_table(run1_results, run2_results)
console.print(table)
```

---

## 2. CLI Framework: Click vs Typer vs argparse

### Click (Recommended for Complex CLIs)

**Evidence** ([Click docs](https://click.palletsprojects.com/)):

```python
import click

@click.group()
@click.pass_context
def cli(ctx):
    """Ansible Output Monitor - TUI for ansible-playbook runs."""
    ctx.ensure_object(dict)

@cli.group()
def inspect():
    """Inspect command group."""
    pass

@inspect.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--tui', is_flag=True, help='Open interactive TUI')
@click.pass_context
def list(ctx, output_json, tui):
    """List all available sessions."""
    if tui:
        # Launch TUI mode
        from aom.inspect_tui import run_inspect_tui
        return run_inspect_tui()
    
    # Text mode
    sessions = get_sessions()
    
    if output_json:
        console.print_json(sessions)
    else:
        table = create_sessions_table(sessions)
        console.print(table)

@inspect.command()
@click.argument('session_id')
@click.option('--jsonl', is_flag=True, help='Output as JSONL stream')
@click.pass_context
def show(ctx, session_id, jsonl):
    """Show session details."""
    session = get_session(session_id)
    
    if jsonl:
        # Stream JSONL
        for event in session.events:
            console.print_json(event)
    else:
        # Rich table
        table = create_session_table(session)
        console.print(table)

@inspect.command()
@click.argument('session1')
@click.argument('session2')
@click.pass_context
def diff(ctx, session1, session2):
    """Compare two sessions."""
    run1 = get_session(session1)
    run2 = get_session(session2)
    table = create_diff_table(run1.results, run2.results)
    console.print(table)

if __name__ == '__main__':
    cli()
```

### Typer (Simpler, Type-Hint Based)

**Evidence** ([Typer docs](https://typer.tiangolo.com/)):

```python
import typer
from typing import Optional

app = typer.Typer(help="Ansible Output Monitor")
inspect_app = typer.Typer(help="Inspect sessions")

app.add_typer(inspect_app, name="inspect")

@inspect_app.command("list")
def inspect_list(
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
    tui: bool = typer.Option(False, "--tui", help="Open TUI")
):
    """List all sessions."""
    if tui:
        # Launch TUI
        run_inspect_tui()
        return
    
    sessions = get_sessions()
    if json:
        console.print_json(sessions)
    else:
        console.print(create_sessions_table(sessions))

@inspect_app.command("show")
def inspect_show(
    session_id: str = typer.Argument(..., help="Session ID"),
    jsonl: bool = typer.Option(False, "--jsonl", help="Stream as JSONL")
):
    """Show session details."""
    session = get_session(session_id)
    
    if jsonl:
        for event in session.events:
            console.print_json(event)
    else:
        console.print(create_session_table(session))

if __name__ == "__main__":
    app()
```

### Comparison: Click vs Typer

| Feature | Click | Typer |
|---------|-------|-------|
| Type hints | Manual | Automatic (uses type hints) |
| Complexity | Handles complex CLIs | Simpler API |
| Subcommands | `@group`, `@command` | `typer.Typer()`, `add_typer()` |
| Documentation | Mature, well-documented | Newer, simpler |
| Integration | Works with Rich | Works with Rich |

**Recommendation**: **Click** for complex CLI with multiple subcommands and options.

---

## 3. TUI vs CLI Detection

### TTY Detection

**Evidence** ([from ArchiveBox](https://github.com/ArchiveBox/ArchiveBox/blob/dev/archivebox/config/common.py#L30)):

```python
import sys

if sys.stdout.isatty():
    # Terminal mode - can use colors, interactive features
    USE_COLOR = True
    SHOW_PROGRESS = True
else:
    # Piped/redirected mode - plain text only
    USE_COLOR = False
    SHOW_PROGRESS = False
```

### Auto-TUI Detection Logic

**Pattern**:

```python
import sys

def should_show_tui() -> bool:
    """
    Determine if TUI mode should be used.
    
    Returns True if:
    - stdout is a TTY (not piped)
    - No --json flag
    - No --no-tui flag
    - Terminal supports colors (TERM not 'dumb')
    """
    if not sys.stdout.isatty():
        # Piped mode - can't show TUI
        return False
    
    if os.environ.get('TERM') == 'dumb':
        # Dumb terminal - can't show TUI
        return False
    
    # Check for force-text flags
    if '--json' in sys.argv or '--text' in sys.argv:
        return False
    
    return True
```

### Click Integration

```python
@click.command()
@click.option('--tui/--no-tui', default=None, help='Force TUI mode')
@click.option('--json', 'output_json', is_flag=True, help='JSON output')
@click.pass_context
def inspect(ctx, tui, output_json):
    """Inspect sessions."""
    # Determine mode
    if tui is None:
        # Auto-detect
        use_tui = should_show_tui() and not output_json
    else:
        # Explicit flag
        use_tui = tui and not output_json
    
    if use_tui:
        run_inspect_tui()
    else:
        # Text mode
        console = get_console(force=output_json is False)
        show_text_output(console)
```

---

## 4. Rich Tables for Diff Display

### Complete Diff Table Implementation

```python
from dataclasses import dataclass
from typing import List
from rich.console import Console
from rich.table import Table

@dataclass
class TaskResult:
    """Result of a task run."""
    name: str
    host: str
    changed: int
    failed: int
    ok: int
    skipped: int

@dataclass
class DiffIndicator:
    """Diff status for a task."""
    status: str  # 'improved', 'regressed', 'unchanged'
    color: str

def compute_diff(r1: TaskResult, r2: TaskResult) -> DiffIndicator:
    """Compute diff status between two task results."""
    # Check for failures
    if r2.failed > r1.failed:
        return DiffIndicator('regressed', 'red')
    if r2.failed < r1.failed:
        return DiffIndicator('improved', 'green')
    
    # Check for changes
    if r2.changed > r1.changed:
        return DiffIndicator('regressed', 'yellow')
    if r2.changed < r1.changed:
        return DiffIndicator('improved', 'green')
    
    return DiffIndicator('unchanged', 'dim')

def create_diff_table(
    run1_results: List[TaskResult],
    run2_results: List[TaskResult],
    title: str = "Session Comparison"
) -> Table:
    """
    Create a Rich table comparing two session runs.
    
    Columns:
    - Task/Host: Task and host name
    - Run 1: Results from first run
    - Run 2: Results from second run
    - Status: Diff indicator (improved/regressed/unchanged)
    """
    table = Table(title=title, show_lines=True)
    
    # Header row
    table.add_column("Task/Host", style="cyan", no_wrap=True, width=30)
    table.add_column("Run 1", justify="right", style="white", width=20)
    table.add_column("Run 2", justify="right", style="white", width=20)
    table.add_column("Status", justify="center", width=15)
    
    # Data rows
    for r1, r2 in zip(run1_results, run2_results):
        diff = compute_diff(r1, r2)
        
        # Format task/host
        task_host = f"{r1.name}\n[dim]{r1.host}[/dim]"
        
        # Format results
        run1_str = f"✓{r1.ok} ○{r1.changed} ✗{r1.failed} ⊘{r1.skipped}"
        run2_str = f"✓{r2.ok} ○{r2.changed} ✗{r2.failed} ⊘{r2.skipped}"
        
        # Format status
        status_str = f"[{diff.color}]{diff.status}[/{diff.color}]"
        
        table.add_row(task_host, run1_str, run2_str, status_str)
    
    # Summary row
    total_diff = compute_summary_diff(run1_results, run2_results)
    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        format_summary(run1_results),
        format_summary(run2_results),
        f"[{total_diff.color}]{total_diff.status}[/{total_diff.color}]"
    )
    
    return table

def format_summary(results: List[TaskResult]) -> str:
    """Format summary statistics."""
    total_ok = sum(r.ok for r in results)
    total_changed = sum(r.changed for r in results)
    total_failed = sum(r.failed for r in results)
    return f"✓{total_ok} ○{total_changed} ✗{total_failed}"
```

---

## 5. Readonly Textual TUI

### Readonly Session Viewer

**Evidence** ([Textual docs](https://textual.textualize.io/api/app)):

```python
from textual.app import App, ComposeResult
from textual.widgets import Tree, Footer, Header, Static
from textual.containers import Container

class ReadonlySessionViewer(App):
    """
    Readonly TUI for browsing session data.
    
    No run/re-run controls - only navigation and search.
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #session-tree {
        width: 1/3;
        dock: left;
    }
    
    #event-log {
        width: 2/3;
        dock: right;
    }
    
    .readonly {
        text-style: italic;
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("/", "search", "Search"),
        ("f", "filter", "Filter"),
    ]
    
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self.session_data = None
    
    def compose(self) -> ComposeResult:
        """Compose the readonly TUI."""
        yield Header()
        yield Container(
            Tree(id="session-tree", label="Session Tasks"),
            Static(id="event-log", classes="readonly"),
            id="main-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Load session data on mount."""
        self.load_session()
        self.populate_tree()
    
    def load_session(self) -> None:
        """Load session data from artifact."""
        # This is readonly - no write operations
        self.session_data = read_session(self.session_id)
    
    def populate_tree(self) -> None:
        """Populate the session tree."""
        tree = self.query_one("#session-tree", Tree)
        tree.clear()
        
        # Add nodes for each task
        for play in self.session_data.plays:
            play_node = tree.root.add(play.name, data=play)
            for task in play.tasks:
                task_node = play_node.add(task.name, data=task)
                for host in task.hosts:
                    task_node.add(host.name, data=host)
    
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection - show details."""
        node = event.node
        event_log = self.query_one("#event-log", Static)
        
        # Show event details (readonly)
        if node.data:
            event_log.update(self.format_event_details(node.data))
    
    def format_event_details(self, data) -> str:
        """Format event details for display."""
        # Implementation depends on data structure
        return f"Task: {data.name}\nStatus: {data.status}"
    
    # Readonly - no run/re-run actions
    
    def action_refresh(self) -> None:
        """Refresh session data."""
        self.load_session()
        self.populate_tree()
    
    def action_search(self) -> None:
        """Search within session."""
        # Open search overlay
        pass
    
    def action_filter(self) -> None:
        """Filter session view."""
        # Open filter overlay
        pass

def run_inspect_tui(session_id: str = None):
    """Entry point for TUI mode."""
    if session_id:
        app = ReadonlySessionViewer(session_id)
    else:
        # Session selection screen
        app = SessionSelectionScreen()
    app.run()
```

### Key Readonly Design Principles:

1. **No Action Buttons**: Only navigation controls (no run, re-run, pause, stop)
2. **Readonly Data Display**: Show session data, not modify it
3. **Navigation and Search**: Allow exploring the session tree
4. **Event Log**: Show raw event stream
5. **Filtering**: Allow filtering by task/host/status

---

## 6. Pipe-Friendly Output

### JSON Mode

**Evidence** ([from sonic-net/sonic-utilities](https://github.com/sonic-net/sonic-utilities/blob/master/show/muxcable.py#L687)):

```python
@click.command()
@click.argument('session_id', required=False, default=None)
@click.option('--json', 'output_json', is_flag=True, help='JSON output')
@click.pass_context
def inspect(ctx, session_id, output_json):
    """Inspect sessions."""
    if session_id:
        # Show specific session
        session = get_session(session_id)
        
        if output_json:
            # JSON output
            console.print_json(data=session.dict())
        else:
            # Rich table
            console.print(create_session_table(session))
    else:
        # List all sessions
        sessions = list_sessions()
        
        if output_json:
            console.print_json(data=[s.dict() for s in sessions])
        else:
            console.print(create_sessions_table(sessions))
```

### JSONL for Event Streams

**Evidence** ([Rich Console.print_json](https://github.com/ImKKingshuk/LockKnife/blob/main/lockknife_headheadless_cli/forensics.py#L126)):

```python
@inspect.command()
@click.argument('session_id')
@click.option('--jsonl', is_flag=True, help='Stream events as JSONL')
@click.pass_context
def show(ctx, session_id, jsonl):
    """Show session details with event stream."""
    session = get_session(session_id)
    
    if jsonl:
        # Stream events as JSONL
        for event in session.get_events():
            # One JSON object per line
            console.print_json(data=event.dict())
    else:
        # Show session summary
        console.print(create_session_summary(session))
```

### Multiple Output Formats

**Evidence** ([from PaddleFlow](https://github.com/PaddlePaddle/PaddleFlow/blob/develop/client/paddleflow/cli/cli.py#L41)):

```python
from enum import Enum

class OutputFormat(Enum):
    TABLE = "table"
    JSON = "json"
    CSV = "csv"

@click.group()
@click.option('--output', 
    type=click.Choice(['table', 'json', 'csv']),
    default='table',
    help='Output format')
@click.pass_context
def cli(ctx, output):
    """CLI with multiple output formats."""
    ctx.obj['output_format'] = OutputFormat(output)

@cli.command()
@click.pass_context
def list(ctx):
    """List sessions."""
    sessions = get_sessions()
    output_format = ctx.obj['output_format']
    
    if output_format == OutputFormat.TABLE:
        console.print(create_sessions_table(sessions))
    elif output_format == OutputFormat.JSON:
        console.print_json(data=[s.dict() for s in sessions])
    elif output_format == OutputFormat.CSV:
        for s in sessions:
            print(f"{s.id},{s.name},{s.status}")
```

---

## 7. Pager Integration

### Using click.echo_via_pager

**Evidence** ([from Click docs](https://click.palletsprojects.com/) and [real-world code](https://github.com/dask/dask/blob/main/dask/cli.py#L157)):

```python
import click

@click.command()
@click.option('--pager/--no-pager', default=None, help='Use pager')
def inspect_list(pager):
    """List all sessions (potentially long output)."""
    sessions = get_sessions()
    
    if pager or (pager is None and sys.stdout.isatty()):
        # Use pager for TTY
        output = format_sessions_as_text(sessions)
        click.echo_via_pager(output)
    else:
        # Direct output
        console = get_console()
        console.print(create_sessions_table(sessions))
```

### pydoc.pager Alternative

**Evidence** ([from Cerebras/modelzoo](https://github.com/Cerebras/modelzoo/blob/main/src/cerebras/modelzoo/cli/model_info_cli.py#L125)):

```python
import pydoc

@click.command()
@click.option('--no-pager', is_flag=True, help='Disable pager')
def show_long_output(no_pager):
    """Show long output with optional pager."""
    if no_pager:
        print(output)
    else:
        pydoc.pager(output)
```

### Rich Console Capture + Pager

```python
from rich.console import Console

def show_with_pager(console: Console, renderable, pager: bool = True):
    """Show rich output with pager support."""
    if pager and sys.stdout.isatty():
        # Capture Rich output to string
        with console.capture() as capture:
            console.print(renderable)
        output = capture.get()
        
        # Page through string
        click.echo_via_pager(output)
    else:
        # Direct output
        console.print(renderable)
```

---

## Real-World Patterns Summary

| Use Case | Pattern | Tool |
|----------|---------|------|
| **Basic CLI** | Click groups, subcommands | Click |
| **Complex CLI** | Typer with type hints | Typer |
| **TTY detection** | `sys.stdout.isatty()` | sys |
| **Rich output** | `Console.print()` | Rich |
| **Pipe-friendly** | `--json` flag, `console.print_json()` | Rich + Click |
| **Event stream** | JSONL format (one JSON per line) | Custom |
| **Pager** | `click.echo_via_pager()` | Click |
| **Tables** | `Table`, columns, rows | Rich |
| **Readonly TUI** | `App.compose()`, Trees, Static | Textual |
| **Multiple formats** | `--output` with `click.Choice()` | Click |

---

## OPEN QUESTIONS

### OQ1: Should `aom inspect` default to TUI or text mode?

**Options**:
- A) **Auto-detect**: TUI if TTY, text if piped
- B) **Default TUI**: Always show TUI unless `--text` or `--json`
- C) **Default text**: Always show text unless `--tui`

**Recommendation**: **Option A (Auto-detect)** because:
- Matches user expectations
- Scriptable (respects pipes)
- Explicit override with flags

**Implementation**:
```python
@click.command()
@click.option('--tui/--text', default=None, help='Force mode')
@click.option('--json', is_flag=True, help='JSON output')
@click.pass_context
def inspect(ctx, tui, json):
    # Determine mode
    if tui is False or json:
        use_tui = False
    elif tui is True:
        use_tui = True
    else:
        # Auto-detect
        use_tui = sys.stdout.isatty()
    
    if use_tui:
        run_inspect_tui()
    else:
        run_text_output(json=json)
```

### OQ2: How to handle long table output - auto-pager or require --pager?

**Options**:
- A) **Auto-pager**: Always page when output exceeds terminal height
- B) **Explicit pager**: Use `--pager` flag to enable
- C) **Smart pager**: Auto-pager in TUI mode, no pager with --json

**Recommendation**: **Option C (Smart pager)** because:
- Rich tables in terminal benefit from pager
- JSON output should be direct (piped to jq, etc.)
- Text mode respects user's pager choice

**Implementation**:
```python
def show_table(console, table, use_pager=False, in_tty=True):
    """Show table with smart pager."""
    if use_pager and in_tty:
        with console.capture() as capture:
            console.print(table)
        click.echo_via_pager(capture.get())
    else:
        console.print(table)
```

### OQ3: How to structure readonly TUI vs full TUI?

**Options**:
- A) **Separate app classes**: `ReadonlySessionViewer` vs `FullSessionRunner`
- B) **Single app with mode flag**: `App(readonly=True)` vs `App(readonly=False)`
- C) **Shared components**: Common screens/widgets, different controls

**Recommendation**: **Option C (Shared components)** because:
- DRY principle
- Same tree/log panels
- Only difference is buttons/actions

**Implementation**:
```python
# Shared components
class SessionTree(Tree):
    """Session tree - shared between readonly and full."""
    pass

class EventLog(Static):
    """Event log - shared."""
    pass

# Readonly app
class ReadonlySessionViewer(App):
    def compose(self):
        yield Header()
        yield Container(SessionTree(), EventLog())
        yield Footer()  # Navigation only
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

# Full app with controls
class FullSessionRunner(App):
    def compose(self):
        yield Header()
        yield Container(SessionTree(), EventLog())
        yield ActionControls()  # Run, Re-run, etc.
        yield Footer()  # Full bindings
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "run", "Run"),
        ("s", "stop", "Stop"),
    ]
```

### OQ4: JSON output format - full objects or summary?

**Options**:
- A) **Full objects**: `--json` outputs complete session data
- B) **Summary**: `--json` outputs summary table as JSON
- C) **Both**: `--json` (summary) and `--json-full` (complete)

**Recommendation**: **Option A (Full objects)** because:
- JSON consumers expect full data
- Can filter with jq
- Consistency across commands

**Implementation**:
```python
@inspect.command()
@click.option('--json', is_flag=True, help='JSON output')
def list(json):
    sessions = get_sessions()
    
    if json:
        # Full JSON output
        console.print_json(data=[s.dict() for s in sessions])
    else:
        # Rich table
        console.print(create_sessions_table(sessions))
```

### OQ5: Should we use Typer or Click for this CLI?

**Comparison**:

| Feature | Click | Typer |
|---------|-------|-------|
| Type hints | Manual | Automatic |
| Complexity | Handles complex CLIs well | Simpler, but less control |
| Subcommands | `@group`, `chain=True` | `typer.Typer()`, `add_typer()` |
| Maturity | Mature, stable | Newer, actively developed |
| Rich integration | Works well | Works well |
| Learning curve | Steeper | Easier |

**Recommendation**: **Click** because:
- Complex CLI structure (multiple subcommands)
- Chain commands (`aom inspect list --tui`)
- Better control over help text
- More examples in codebase

**Example Click structure**:
```python
@click.group()
def cli():
    """Ansible Output Monitor."""
    pass

@cli.group()
def inspect():
    """Inspect sessions."""
    pass

@inspect.command()
def list():
    """List sessions."""
    pass

@inspect.command()
def diff():
    """Compare sessions."""
    pass
```

---

## Final Recommendations

1. **Use Click** for CLI framework (mature, handles subcommands well)
2. **Rich Console** for text output (tables, colors, JSON)
3. **Auto-detect TTY** for TUI vs text mode
4. **Separate readonly TUI app** for `inspect` command
5. **JSON output with --json flag** (full objects)
6. **Smart pager**: use pager for tables in TTY, no pager for JSON
7. **Shared components** between readonly and full TUI

