"""Task tree widget for AOM TUI.

Tree view showing Play/RoleGroup/Task/Host hierarchy.
See SPECIFICATION.md Section 7.1 for tree view details.
"""

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Tree

from ansible_aom.core.icons import STATUS_COLORS, STATUS_ICONS

if TYPE_CHECKING:
    from ansible_aom.core.models import RunState


# Tree node icons
TREE_COLLAPSED_ICON = "▶"  # Right triangle for collapsed node (U+25B6)
TREE_EXPANDED_ICON = "▼"  # Down triangle for expanded node (U+25BC)


def truncate_name(name: str, max_width: int) -> str:
    """Truncate name with ellipsis if too long.

    Args:
        name: The name to truncate
        max_width: Maximum width in characters

    Returns:
        Truncated name with … (U+2026) if needed, minimum 10 chars visible
    """
    if len(name) <= max_width:
        return name

    # Minimum 10 visible characters before ellipsis
    min_visible = 10
    if max_width < min_visible + 1:
        # Not enough space, show what we can
        return name[:max_width]

    # Show max_width - 1 chars + ellipsis
    visible_chars = max_width - 1
    return name[:visible_chars] + "…"


def compact_truncate(name: str, terminal_width: int) -> str:
    """Truncate for compact mode, leaving space for icons.

    Args:
        name: The name to truncate
        terminal_width: Terminal width in characters

    Returns:
        Truncated name, width - 20 chars maximum, minimum 10 chars visible
    """
    # Reserve 20 chars for icons and other UI elements
    max_name_width = terminal_width - 20

    # Minimum 10 chars visible
    if max_name_width < 10:
        max_name_width = 10

    return truncate_name(name, max_name_width)


class TaskTree(Tree[str]):
    """Tree widget showing play/task/host hierarchy with status icons."""

    DEFAULT_CSS = """
    TaskTree {
        height: 100%;
        width: 1fr;
    }
    """

    def __init__(
        self,
        label: str = "Playbook",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the task tree widget.

        Args:
            label: Root label for the tree
            name: Widget name
            id: Widget ID
            classes: Space-separated list of class names
            disabled: Whether the widget is disabled
        """
        super().__init__(
            label,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def populate_from_state(self, run_state: "RunState") -> None:
        """Populate tree from RunState data.

        Args:
            run_state: The RunState containing plays, tasks, and hosts
        """
        self.root.remove_children()

        for play_id, play_state in run_state.plays.items():
            play_node = self.root.add(play_state.name, data=play_id)

            for task_id, task_state in play_state.tasks.items():
                task_icon = STATUS_ICONS.get(task_state.status, "?")
                task_color = STATUS_COLORS.get(task_state.status, "white")
                task_label = Text(f"{task_icon} {task_state.name}", style=task_color)
                task_node = play_node.add(task_label, data=task_id)

                for hostname, host_state in task_state.hosts.items():
                    host_icon = STATUS_ICONS.get(host_state.status, "?")
                    host_color = STATUS_COLORS.get(host_state.status, "white")
                    host_label = Text(f"{host_icon} {hostname}", style=host_color)
                    task_node.add(host_label, data=hostname)

    def populate_from_definitions(self, definitions: list) -> None:
        """Build the initial tree skeleton from preflight definitions.

        Called once when ``set_definitions`` first lands. Subsequent
        state changes go through ``apply_state_icons`` which mutates
        node labels in place rather than rebuilding the tree.

        Idempotent: clears existing children first so a double-call
        (e.g. preflight retried) produces the same tree.
        """
        from ansible_aom.core.models import RoleGroupDefinition, TaskDefinition

        self.root.remove_children()

        for play_def in definitions:
            play_node = self.root.add(play_def.name, data=f"play:{play_def.id}")
            hosts = list(play_def.resolved_hosts) if play_def.resolved_hosts else []

            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    role_label = Text(f"▸ Role: {entry.role}", style="cyan")
                    role_node = play_node.add(role_label, data=f"role:{entry.role}")
                    for task_def in entry.tasks:
                        self._add_task_node(role_node, task_def, hosts)
                elif isinstance(entry, TaskDefinition):
                    self._add_task_node(play_node, entry, hosts)

    def _add_task_node(self, parent, task_def, hosts: list[str]) -> None:
        """Add a task node (and its host children) under ``parent``.

        Uses the PENDING icon as the initial state — events flipping in
        later via ``apply_state_icons`` will mutate the label in place.
        """
        from ansible_aom.core.models import Status

        icon = STATUS_ICONS.get(Status.PENDING, "?")
        color = STATUS_COLORS.get(Status.PENDING, "white")
        label = Text(f"{icon} {task_def.name}", style=color)
        task_node = parent.add(label, data=f"task:{task_def.name}")

        for hostname in hosts:
            host_label = Text(f"{icon} {hostname}", style=color)
            task_node.add(host_label, data=f"host:{hostname}")

    def apply_state_icons(self, run_state) -> None:
        """Mutate existing node labels in place to reflect current status.

        Walks ``run_state.plays`` and updates icons/colors on the
        matching tree nodes by matching task and host names. Nodes added
        dynamically by JSONL events that have no preflight match fall
        through silently — the next ``populate_from_state`` (legacy
        path) or future graft logic can pick them up.
        """
        # Index existing task nodes by their data key for O(1) lookup.
        task_index: dict[str, object] = {}
        host_index: dict[tuple[str, str], object] = {}
        for play_node in self.root.children:
            for child in play_node.children:
                # child may be a role node or a task node; walk one
                # level deeper for role children.
                data = child.data or ""
                if isinstance(data, str) and data.startswith("role:"):
                    for task_node in child.children:
                        self._index_task_node(task_node, task_index, host_index)
                else:
                    self._index_task_node(child, task_index, host_index)

        for play in run_state.plays.values():
            for task in play.tasks.values():
                key = f"task:{task.name}"
                node = task_index.get(key)
                if node is not None:
                    icon = STATUS_ICONS.get(task.status, "?")
                    color = STATUS_COLORS.get(task.status, "white")
                    node.set_label(Text(f"{icon} {task.name}", style=color))
                for hostname, host_state in task.hosts.items():
                    host_node = host_index.get((task.name, hostname))
                    if host_node is not None:
                        h_icon = STATUS_ICONS.get(host_state.status, "?")
                        h_color = STATUS_COLORS.get(host_state.status, "white")
                        host_node.set_label(Text(f"{h_icon} {hostname}", style=h_color))

    def _index_task_node(self, task_node, task_index: dict, host_index: dict) -> None:
        """Populate the task/host lookup tables for ``apply_state_icons``."""
        data = task_node.data or ""
        if not isinstance(data, str) or not data.startswith("task:"):
            return
        task_name = data[len("task:") :]
        task_index[data] = task_node
        for host_node in task_node.children:
            host_data = host_node.data or ""
            if isinstance(host_data, str) and host_data.startswith("host:"):
                hostname = host_data[len("host:") :]
                host_index[(task_name, hostname)] = host_node
