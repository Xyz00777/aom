"""Task tree widget for AOM TUI.

Tree view showing Play/RoleGroup/Task/Host hierarchy.
See SPECIFICATION.md Section 7.1 for tree view details.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import TYPE_CHECKING

from textual.widgets import Tree

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
        # Clear existing tree
        self.root.remove_children()

        # Add plays
        for play_id, play_state in run_state.plays.items():
            play_node = self.root.add(play_state.name, data=play_id)

            # Add tasks under play
            for task_id, task_state in play_state.tasks.items():
                task_node = play_node.add(
                    task_state.name,
                    data=task_id,
                )

                # Add hosts under task
                for hostname, host_state in task_state.hosts.items():
                    task_node.add(hostname, data=hostname)
