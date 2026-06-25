"""Task tree widget for AOM TUI.

Tree view showing Play/RoleGroup/Task/Host hierarchy.
See SPECIFICATION.md Section 7.1 for tree view details.
"""

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ansible_aom.core.icons import STATUS_COLORS, STATUS_ICONS

if TYPE_CHECKING:
    from ansible_aom.core.models import RunState
    from ansible_aom.core.tree import TreeProjection
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
        task_index: dict[str, TreeNode[str]] = {}
        host_index: dict[tuple[str, str], TreeNode[str]] = {}

        def _walk(node: TreeNode[str]) -> None:
            data = node.data or ""
            if isinstance(data, str) and data.startswith("task:"):
                self._index_task_node(node, task_index, host_index)
            if node.children:
                for child in node.children:
                    _walk(child)

        for play_node in self.root.children:
            for child in play_node.children:
                _walk(child)

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

    def _index_task_node(
        self,
        task_node: TreeNode[str],
        task_index: dict[str, TreeNode[str]],
        host_index: dict[tuple[str, str], TreeNode[str]],
    ) -> None:
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

    def populate_from_projection(self, projection: "TreeProjection", budget: int) -> None:
        """Build the tree from a ``TreeProjection``'s already-truncated lines.

        Consumes the result of ``TreeProjection.tree_lines(budget)`` — which
        already includes the inner + outer footers from T2 and the
        ``(M remaining)`` role labels from T3. Maps each ``TreeLine`` to a
        Textual ``TreeNode`` with the right icon, color, and parent.

        Mapping:

        - ``kind="playbook"`` → the root; skipped (the widget's own root).
        - ``kind="play"`` → ``play_node = root.add(label)`` at depth 1.
        - ``kind="role"`` → ``role_node = parent.add(label)`` (parent is
          the enclosing play or, for nested roles, the enclosing role).
          Label carries the T3 ``(N tasks)`` or ``(M remaining)`` suffix.
        - ``kind="task"`` → ``task_node = parent.add(Text(icon + name))``
          with the status icon + colour from ``STATUS_ICONS`` /
          ``STATUS_COLORS``.
        - ``kind="host"`` → ``host_node = task_node.add(Text(icon + hostname))``
          (parent is the enclosing task).
        - ``kind="more"`` → ``parent.add_leaf(Text(label, style="dim italic"))``
          with ``allow_expand=False``. The inner + outer footers from T2
          hang off the spine as unexpandable leaves with dim-italic
          styling so they read as metadata, not as real tasks/roles.

        Parent-stack walk: a line at depth D is added under the most
        recent line at depth D-1. The outer footer (depth=0) goes under
        the root; the inner footer (depth = deepest visible task's depth)
        goes under the matching role/task. The depth-based parent
        selection handles nested roles automatically — a role at depth 3
        ends up under a role at depth 2, not directly under a play.

        The widget is rebuilt from scratch on every call (the TUI tree
        is short-lived per render so this is cheap).
        """
        self.root.remove_children()

        lines = projection.tree_lines(budget=budget)
        if not lines:
            return

        # parent_stack[i] is the most recent node at depth=i, where i=0
        # is the widget's root (depth 0 = playbook). Lines are pushed
        # onto the stack as they're added; the stack is popped when a
        # line's depth <= the stack top's logical depth.
        #
        # We track depth alongside the node so we can detect "go up"
        # transitions without relying on TreeNode.depth (which Textual
        # tracks by visual position, not the TreeLine semantic depth).
        parent_stack: list[tuple[int, TreeNode[str]]] = [(0, self.root)]

        for ln in lines:
            # Pop until the stack top is the parent at depth (ln.depth - 1).
            # If ln.depth == 0 the footer hangs off the root (depth 0).
            while len(parent_stack) > 1 and parent_stack[-1][0] >= ln.depth:
                parent_stack.pop()
            parent = parent_stack[-1][1]

            if ln.kind == "playbook":
                # The playbook is the root; already handled by __init__.
                continue
            if ln.kind == "play":
                # Play nodes always sit at depth 1 directly under the root.
                # Reset the stack so any leftover role/task ancestors from a
                # previous (closed) play don't bleed into this one.
                parent_stack = [(0, self.root)]
                node = self.root.add(ln.label, data=f"play:{ln.label}")
                parent_stack.append((1, node))
                continue
            if ln.kind == "role":
                label = Text(ln.label, style="cyan")
                role_key = ln.identity or ln.label
                node = parent.add(label, data=f"role:{role_key}")
                # Role identity is the depth anchor — push at ln.depth.
                parent_stack.append((ln.depth, node))
                continue
            if ln.kind == "task":
                icon = STATUS_ICONS.get(ln.status, "?") if ln.status is not None else "?"
                color = STATUS_COLORS.get(ln.status, "white") if ln.status is not None else "white"
                label = Text(f"{icon} {ln.label}", style=color)
                node = parent.add(label, data=f"task:{ln.label}")
                parent_stack.append((ln.depth, node))
                continue
            if ln.kind == "host":
                icon = STATUS_ICONS.get(ln.status, "?") if ln.status is not None else "?"
                color = STATUS_COLORS.get(ln.status, "white") if ln.status is not None else "white"
                label = Text(f"{icon} {ln.label}", style=color)
                parent.add(label, data=f"host:{ln.label}")
                # Hosts are leaves — do NOT push onto parent_stack.
                continue
            if ln.kind == "more":
                # Footer: dim-italic style so it reads as metadata, not a
                # real task. add_leaf = allow_expand=False, the right
                # semantic for an unexpandable "… and N more" indicator.
                label = Text(ln.label, style="dim italic")
                # Differentiate the inner vs outer footer in the data key
                # so tests can tell them apart. The outer footer is the
                # one at depth 0; everything else is "inner".
                footer_kind = "outer" if ln.depth == 0 else "inner"
                parent.add_leaf(label, data=f"more:{footer_kind}")
                # Footers are leaves — do NOT push onto parent_stack.
                continue
