# pyright: reportMissingImports=false

"""Failing tests for recursive role nesting in the tree view (Plan: recursive-nesting).

Bug summary (proved by the current implementation in ``core/tree.py``):

- ``_task_role`` uses a single-string role assignment. Preflight wins:
  when ``role: podman`` contains a runtime
  ``angie_ssl_terminator : Copy certificates`` event, the projection
  still attributes the task to ``podman``, never to
  ``angie_ssl_terminator``.
- ``_emit_runtime_play`` / ``_emit_pending_play`` only render ``role:``
  headers at depth=2 and hardcode tasks at depth=3. Role-in-role is
  structurally impossible.
- ``tui/widgets/task_tree.py`` walks at most one level into role
  children (``apply_state_icons``), so even if the projection were
  fixed, the TUI wouldn't pick up deeper task nodes on status updates.

These tests pin the *target* shape after the data-model-first fix
(``TaskRunState.parent_role``, recursive ``group_roles``, recursive
walk in ``TaskTree``). They MUST fail on the current code (proving the
bug) and MUST pass after T2-T7 land.

Convention follows ``tests/unit/test_tree_projection.py``,
``tests/unit/test_tree_ungrouped_roles.py``, and
``tests/unit/test_tree_classify_and_role_labels.py``: build the
``RunState`` inline, drive everything through
``TreeProjection.from_run_state(state).tree_lines(budget=...)``.
"""

from __future__ import annotations

from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
)
from ansible_aom.core.tree import TreeProjection


def _play_def(
    play_id: str, name: str, tasks: list, hosts: list[str] | None = None
) -> PlayDefinition:
    """Build a PlayDefinition with explicit resolved_hosts (default: web1)."""
    return PlayDefinition(
        id=play_id,
        name=name,
        hosts="all",
        resolved_hosts=hosts or ["web1"],
        tasks=tasks,
    )


def _fire_startup(
    state: RunState,
    play_id: str = "play-1",
    play_name: str = "play",
    ts: str = "2026-06-23T10:00:00Z",
) -> None:
    """Fire v2_playbook_on_start + v2_playbook_on_play_start."""
    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": ts})
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": ts.replace("10:00:00", "10:00:01"),
            "play": {"id": play_id, "name": play_name},
        }
    )


def _fire_running_task(
    state: RunState,
    task_id: str,
    task_name: str,
    host: str = "web1",
    play_id: str = "play-1",
) -> None:
    """Fire v2_playbook_on_task_start + v2_runner_on_start for a free-strategy fixture."""
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-23T10:00:02Z",
            "task": {"id": task_id, "name": task_name},
            "play": {"id": play_id},
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-06-23T10:00:03Z",
            "task": {"id": task_id, "name": task_name},
            "host": host,
        }
    )


def _fire_pending_task(
    state: RunState,
    task_id: str,
    task_name: str,
    play_id: str = "play-1",
) -> None:
    """Fire only v2_playbook_on_task_start (task is announced but not running)."""
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-23T10:00:02Z",
            "task": {"id": task_id, "name": task_name},
            "play": {"id": play_id},
        }
    )


def _line_summary(lines) -> list[tuple[int, str, str]]:
    """Return [(depth, kind, label), …] for stable assertions."""
    return [(ln.depth, ln.kind, ln.label) for ln in lines]


class TestNestedRoleRendersAsSubBranch:
    """A role that includes another role (``angie_ssl_terminator`` inside
    ``role: podman``) must render the inner role as its own ``role:``
    header under the outer role, not as a flat task list.

    Mirrors the user-reported tree from ``aom --tui``::

        play: Setup rootless Podman for Scrutiny web server
        └─ role: podman (40 tasks)
           └─ role: angie_ssl_terminator (M tasks)
              ├─ □ angie_ssl_terminator : Copy certificates …
              ├─ □ angie_ssl_terminator : Mark SSL terminator setup complete
              …
    """

    def test_nested_role_renders_as_sub_branch(self) -> None:
        podman_tasks = [
            TaskDefinition(
                name="angie_ssl_terminator : Copy certificates to target user directory",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=0,
            ),
            TaskDefinition(
                name="angie_ssl_terminator : Mark SSL terminator setup complete",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=1,
            ),
            TaskDefinition(
                name="angie_ssl_terminator : Ensure firewalld is running",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=2,
            ),
            TaskDefinition(
                name="angie_ssl_terminator : Deploy Angie Sidecar Quadlet (host network)",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=3,
            ),
            TaskDefinition(
                name="Configure podman network bridge",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=4,
            ),
        ]

        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Setup rootless Podman for Scrutiny web server",
                [RoleGroupDefinition(role="podman", tasks=podman_tasks)],
            )
        ]
        _fire_startup(
            state,
            play_id="play-1",
            play_name="Setup rootless Podman for Scrutiny web server",
        )

        _fire_running_task(
            state,
            "t1",
            "angie_ssl_terminator : Copy certificates to target user directory",
            host="web1",
        )
        for idx, suffix in enumerate(
            [
                "Mark SSL terminator setup complete",
                "Ensure firewalld is running",
                "Deploy Angie Sidecar Quadlet (host network)",
            ],
            start=2,
        ):
            _fire_pending_task(state, f"t{idx}", f"angie_ssl_terminator : {suffix}")

        lines = TreeProjection.from_run_state(state).tree_lines(budget=40)

        outer = [ln for ln in lines if ln.kind == "role" and "podman" in ln.label]
        assert outer, (
            f"missing outer role header; got {[(d, k, lbl) for d, k, lbl in _line_summary(lines)]}"
        )
        outer_depth = outer[0].depth

        inner = [ln for ln in lines if ln.kind == "role" and "angie_ssl_terminator" in ln.label]
        assert inner, (
            "inner role header 'role: angie_ssl_terminator' is missing — "
            "tasks are flattened under 'role: podman' instead of nesting "
            f"under a dedicated sub-branch. Got: "
            f"{[(d, k, lbl) for d, k, lbl in _line_summary(lines)]}"
        )
        assert inner[0].depth == outer_depth + 1, (
            "inner role must be exactly one level deeper than the outer "
            f"role; got inner depth={inner[0].depth}, outer depth={outer_depth}"
        )

        copy_cert = [ln for ln in lines if ln.kind == "task" and "Copy certificates" in ln.label]
        assert copy_cert, "running 'Copy certificates …' task is missing"
        assert copy_cert[0].depth == inner[0].depth + 1, (
            "task must sit one level deeper than the inner role header; "
            f"got task depth={copy_cert[0].depth}, inner depth={inner[0].depth}"
        )

        seq = _line_summary(lines)
        for i in range(len(seq) - 1):
            d1, k1, _ = seq[i]
            d2, k2, _ = seq[i + 1]
            if k1 == "role" and k2 == "role" and d2 == d1:
                raise AssertionError(
                    f"two consecutive role headers at depth={d1} with no "
                    f"task between them; tree={seq}"
                )


class TestArbitraryDepthRendersCorrectly:
    """A 5-level deep nesting must render with monotonically increasing
    depth (1, 2, 3, 4, 5, 6) on the active branch.

    Layout::

        Play → role A → role B → role C → role D (5 tasks) → task

    Under the current 4-level cap, the inner roles collapse and the
    branch cannot reach depth=6.
    """

    def test_arbitrary_depth_renders_correctly(self) -> None:
        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Deep nesting",
                [
                    RoleGroupDefinition(
                        role="A",
                        tasks=[
                            TaskDefinition(
                                name="B : level-two work",
                                role="A",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                            ),
                        ],
                    ),
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Deep nesting")

        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-23T10:00:02Z",
                "task": {"id": "t-leaf", "name": "D : leaf : actually do the thing"},
                "host": "web1",
            }
        )

        lines = TreeProjection.from_run_state(state).tree_lines(budget=60)
        seq = _line_summary(lines)

        kinds_at_depth = {d: k for d, k, _ in seq}
        for required_depth in (2, 3, 4, 5):
            assert required_depth in kinds_at_depth, (
                f"expected a role line at depth={required_depth}; "
                f"only saw kinds at depths {sorted(kinds_at_depth)}; "
                f"tree={seq}"
            )
            assert kinds_at_depth[required_depth] == "role", (
                f"depth={required_depth} should be a 'role' line, got "
                f"'{kinds_at_depth[required_depth]}'; tree={seq}"
            )
        assert 6 in kinds_at_depth, f"expected a task line at depth=6; tree={seq}"
        assert kinds_at_depth[6] == "task", (
            f"depth=6 should be a 'task' line, got '{kinds_at_depth[6]}'; tree={seq}"
        )

        leaf = next(ln for ln in lines if ln.depth == 6 and ln.kind == "task")
        assert "leaf" in leaf.label, f"leaf task label looks wrong: {leaf.label!r}"


class TestFlatRoleTasksUnchanged:
    """A single non-nested role must keep the existing depth=2/3/4 layout
    so the recursive-nesting fix doesn't regress the common case.
    """

    def test_regression_flat_role_tasks_unchanged(self) -> None:
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy webservers",
                [
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name="Install nginx",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                                path="nginx.yml:1",
                            ),
                            TaskDefinition(
                                name="Configure firewall",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=1,
                                path="nginx.yml:5",
                            ),
                        ],
                    )
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="deploy webservers")
        _fire_running_task(state, "t1", "Install nginx", host="web1", play_id="play-1")

        lines = TreeProjection.from_run_state(state).tree_lines(budget=25)
        seq = _line_summary(lines)

        assert seq[0][1] == "playbook", f"first line should be playbook, got {seq}"
        assert seq[1][1] == "play", f"second line should be play, got {seq}"
        assert seq[2][1] == "role", f"third line should be role, got {seq}"
        assert seq[2][0] == 2, f"role depth should stay 2, got {seq[2]}"

        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert task_lines, f"expected at least one task line, got {seq}"
        for tl in task_lines:
            assert tl.depth == 3, (
                f"flat-role regression: task depth should stay 3, got {tl.depth} for {tl.label!r}"
            )

        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert host_lines, f"expected at least one host line, got {seq}"
        for hl in host_lines:
            assert hl.depth == 4, (
                f"flat-role regression: host depth should stay 4, got {hl.depth} for {hl.label!r}"
            )

        assert all(d <= 4 for d, _, _ in seq), (
            f"flat-role regression: no line should exceed depth 4, got {seq}"
        )


class TestMixedConsecutiveAndNestedRoles:
    """A play with ``role: podman (40 tasks)`` containing one
    ``include_role: angie_ssl_terminator`` block of 8 tasks, then some
    podman-native tasks, then another ``include_role: helper`` block,
    must open and close role sub-branches at the right depths and keep
    sibling branches at consistent depths.
    """

    def test_mixed_consecutive_and_nested_roles(self) -> None:
        angie_tasks = [f"angie_ssl_terminator : angie task {i}" for i in range(1, 9)]
        helper_tasks = [f"helper : helper task {i}" for i in range(1, 4)]
        podman_native = [f"podman-native task {i}" for i in range(1, 3)]

        preflight_tasks = [
            TaskDefinition(
                name=name,
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=idx,
            )
            for idx, name in enumerate(angie_tasks)
        ]
        preflight_tasks += [
            TaskDefinition(
                name=name,
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=10 + idx,
            )
            for idx, name in enumerate(podman_native)
        ]
        preflight_tasks += [
            TaskDefinition(
                name=name,
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=20 + idx,
            )
            for idx, name in enumerate(helper_tasks)
        ]

        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Mixed nested roles",
                [RoleGroupDefinition(role="podman", tasks=preflight_tasks)],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Mixed nested roles")

        _fire_running_task(state, "t-angie-1", "angie_ssl_terminator : angie task 1", host="web1")
        for idx, name in enumerate(angie_tasks[1:3], start=2):
            _fire_pending_task(state, f"t-angie-{idx}", name)

        _fire_running_task(state, "t-pod-1", "podman-native task 1", host="web1")

        for idx, name in enumerate(helper_tasks, start=1):
            _fire_pending_task(state, f"t-helper-{idx}", name)

        lines = TreeProjection.from_run_state(state).tree_lines(budget=80)
        seq = _line_summary(lines)

        role_labels = [lbl for d, k, lbl in seq if k == "role"]
        assert any("podman" in lbl for lbl in role_labels), (
            f"missing outer 'role: podman' header; tree={seq}"
        )
        assert any("angie_ssl_terminator" in lbl for lbl in role_labels), (
            f"missing 'role: angie_ssl_terminator' sub-branch; tree={seq}"
        )
        assert any(lbl.startswith("role: helper") for lbl in role_labels), (
            f"missing 'role: helper' sub-branch; tree={seq}"
        )

        podman_depth = next(d for d, k, lbl in seq if k == "role" and "podman" in lbl)
        angie_depth = next(d for d, k, lbl in seq if k == "role" and "angie_ssl_terminator" in lbl)
        helper_depth = next(
            d for d, k, lbl in seq if k == "role" and lbl.startswith("role: helper")
        )
        assert angie_depth == podman_depth + 1, (
            f"angie sub-branch should be one level deeper than podman; "
            f"angie={angie_depth}, podman={podman_depth}"
        )
        assert helper_depth == podman_depth + 1, (
            f"helper sub-branch should be one level deeper than podman; "
            f"helper={helper_depth}, podman={podman_depth}"
        )

        for name in angie_tasks[:3]:
            tdepth = next(
                (d for d, k, lbl in seq if k == "task" and name.split(" : ", 1)[1] in lbl),
                None,
            )
            assert tdepth is not None, f"missing task line for {name!r}; tree={seq}"
            assert tdepth == angie_depth + 1, (
                f"task {name!r} at depth={tdepth}, expected angie_depth+1={angie_depth + 1}"
            )

        for name in helper_tasks:
            tdepth = next(
                (d for d, k, lbl in seq if k == "task" and name.split(" : ", 1)[1] in lbl),
                None,
            )
            assert tdepth is not None, f"missing task line for {name!r}; tree={seq}"
            assert tdepth == helper_depth + 1, (
                f"task {name!r} at depth={tdepth}, expected helper_depth+1={helper_depth + 1}"
            )

        pod_native_depth = next(
            d for d, k, lbl in seq if k == "task" and "podman-native task 1" in lbl
        )
        assert pod_native_depth == podman_depth + 1, (
            f"podman-native task at depth={pod_native_depth}, expected "
            f"podman_depth+1={podman_depth + 1}"
        )

        angie_idx = next(
            i for i, (_, k, lbl) in enumerate(seq) if k == "role" and "angie_ssl_terminator" in lbl
        )
        helper_idx = next(
            i for i, (_, k, lbl) in enumerate(seq) if k == "role" and lbl.startswith("role: helper")
        )
        assert angie_idx < helper_idx, (
            f"angie sub-branch should appear before helper sub-branch; "
            f"angie_idx={angie_idx}, helper_idx={helper_idx}"
        )


class TestTuiWidgetWalksRecursively:
    """``TaskTree.apply_state_icons`` indexes only one level into role
    children (``task_tree.py:184-188``). With nested roles, deeper task
    nodes are skipped during status updates, leaving them stuck at the
    PENDING icon. The fix must walk role children recursively.
    """

    def test_tui_widget_walks_recursively(self) -> None:
        from ansible_aom.core.icons import STATUS_ICONS
        from ansible_aom.tui.widgets.task_tree import TaskTree

        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Mixed roles",
                [
                    RoleGroupDefinition(
                        role="podman",
                        tasks=[
                            TaskDefinition(
                                name="podman native task",
                                role="podman",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                            ),
                            TaskDefinition(
                                name="angie_ssl_terminator : Copy certificates",
                                role="angie_ssl_terminator",
                                parent_role="podman",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=1,
                            ),
                        ],
                    )
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Mixed roles")

        _fire_running_task(
            state,
            "t-angie",
            "angie_ssl_terminator : Copy certificates",
            host="web1",
        )

        widget = TaskTree(label="main.yml")
        widget.populate_from_definitions(state.definitions)
        widget.apply_state_icons(state)

        after_labels: list[str] = []

        def _walk_after(node) -> None:
            label_text = node.label.plain if hasattr(node.label, "plain") else str(node.label)
            after_labels.append(label_text)
            for child in node.children:
                _walk_after(child)

        for play_node in widget.root.children:
            _walk_after(play_node)

        running_icon = STATUS_ICONS[Status.RUNNING]

        angie_labels = [lbl for lbl in after_labels if "Copy certificates" in lbl]
        assert angie_labels, (
            f"the nested angie task node never appears in the tree after "
            f"apply_state_icons. After labels: {after_labels}"
        )
        assert any(running_icon in lbl for lbl in angie_labels), (
            f"nested angie task not showing RUNNING icon after apply_state_icons; "
            f"expected '{running_icon}', got: {angie_labels}"
        )


class TestRuntimePodmanPrefixDoesNotDuplicateRoleHeader:
    """When runtime ``role:`` tasks arrive AFTER a sibling sub-branch has
    closed, ``_extend_role_path`` must not re-open the outer role as a
    fresh nesting level.

    Repro for the user-reported bug (verbatim from the user's TUI)::

        play: Setup rootless Podman for Scrutiny web server
        ├─ role: podman (32 tasks)
        │  └─ role: angie_ssl_terminator (12 tasks)
        │     └─ □ angie_ssl_terminator : Copy certs
        └─ role: podman (32 tasks)        ← BUG: same role re-opened
           ├─ □ podman : Wait for DNS
           ├─ □ podman : Install Podman
           └─ □ podman : Check if user X exists

    The duplicate ``role: podman`` header is emitted because
    ``_extend_role_path`` appends ``runtime_name_chain = ("podman",)``
    onto ``last_emitted_role_path = ("podman", "angie_ssl_terminator")``,
    yielding ``("podman", "angie_ssl_terminator", "podman")``. The
    existing ``_collapse_role_path`` only collapses CONSECUTIVE
    duplicates, so the non-consecutive trailing ``"podman"`` survives
    and the renderer treats it as a fresh nesting level — emitting
    ``role: podman`` a second time.

    The fix must extend the collapse to drop any element whose value
    already appeared earlier in the path (so ``(A, B, A)`` becomes
    ``(A, B)``, not just ``(A, B, A)``), and apply that final pass to
    the result of ``_extend_role_path``.
    """

    def test_runtime_podman_prefix_does_not_duplicate_role_header(self) -> None:
        # Preflight: a single sibling task, then ``role: podman`` with an
        # ``angie_ssl_terminator`` sub-branch. The preflight contains NO
        # podman-native tasks — so when the four ``podman : …`` events
        # arrive at runtime, they have nothing in preflight to attach
        # to and fall through to the runtime-only branch.
        # That branch uses ``last_emitted_role_path`` (the path of the
        # LAST preflight item emitted — the closing angie task at
        # ``("podman", "angie_ssl_terminator")``) as the preflight path
        # for the new task. ``_extend_role_path`` then prepends /
        # appends on top of that, producing the duplicate.
        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Setup rootless Podman for Scrutiny web server",
                [
                    TaskDefinition(
                        name="Set scrutiny user info from vars",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    ),
                    RoleGroupDefinition(
                        role="podman",
                        tasks=[
                            RoleGroupDefinition(
                                role="angie_ssl_terminator",
                                tasks=[
                                    TaskDefinition(
                                        name="angie_ssl_terminator : Select preferred certificate source",
                                        role="angie_ssl_terminator",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=1,
                                    ),
                                    TaskDefinition(
                                        name="angie_ssl_terminator : Copy certificates",
                                        role="angie_ssl_terminator",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=2,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ]

        _fire_startup(
            state,
            play_id="play-1",
            play_name="Setup rootless Podman for Scrutiny web server",
        )

        # The sibling task runs first.
        _fire_running_task(state, "t-sibling", "Set scrutiny user info from vars", host="web1")

        # Then the angie sub-branch runs and closes (the closing angie
        # task is the LAST preflight item — its role path is
        # ``("podman", "angie_ssl_terminator")``).
        _fire_running_task(
            state,
            "t-angie-1",
            "angie_ssl_terminator : Select preferred certificate source",
            host="web1",
        )
        _fire_pending_task(state, "t-angie-2", "angie_ssl_terminator : Copy certificates")

        # THEN the four podman-native tasks arrive at runtime. They have
        # no preflight siblings to attach to, so they fall into the
        # runtime-only branch — which uses
        # ``last_emitted_role_path`` (``("podman", "angie_ssl_terminator")``)
        # as the preflight path. With the buggy code, that produces
        # ``("podman", "angie_ssl_terminator", "podman")`` and renders
        # a duplicate ``role: podman`` header.
        _fire_pending_task(state, "t-podman-1", "podman : Wait for DNS resolution to be available")
        _fire_pending_task(
            state,
            "t-podman-2",
            "podman : Install Podman and passt (with retry for network issues)",
        )
        _fire_pending_task(state, "t-podman-3", "podman : Check if user alice already exists")
        _fire_pending_task(state, "t-podman-4", "podman : Ensure user alice exists")

        lines = TreeProjection.from_run_state(state).tree_lines(budget=80)
        seq = _line_summary(lines)

        # The user's reported bug: the OUTER ``role: podman`` header is
        # rendered, then ``role: angie_ssl_terminator``, then a DUPLICATE
        # ``role: podman`` is re-opened for the four runtime-arrival
        # podman tasks. Assert exactly one ``role: podman`` header —
        # the duplicate must NOT appear.
        podman_role_lines = [(d, lbl) for d, k, lbl in seq if k == "role" and "podman" in lbl]
        assert len(podman_role_lines) == 1, (
            f"exactly one 'role: podman' header expected (the duplicate "
            f"header is the bug); got {podman_role_lines}. Full tree: {seq}"
        )

        # The four podman-native runtime tasks must NOT be rendered
        # under a duplicate ``role: podman`` header at depth+1 of the
        # outer podman. They must share the same depth as angie's tasks
        # (all at depth angie_depth + 1), because the aggressive
        # collapse collapses the path from
        # ``("podman", "angie_ssl_terminator", "podman")`` to
        # ``("podman", "angie_ssl_terminator")`` and the renderer
        # places each runtime podman task at the same depth as angie's
        # tasks (depth under the angie sub-branch). What matters is
        # that there is NO second ``role: podman`` header at depth
        # ``podman_depth + 1``.
        podman_depth = podman_role_lines[0][0]
        # Find the inner angie header (if present) and confirm the
        # runtime podman tasks do NOT sit under a second podman header.
        angie_lines = [
            (d, lbl) for d, k, lbl in seq if k == "role" and "angie_ssl_terminator" in lbl
        ]
        for name in (
            "Wait for DNS",
            "Install Podman",
            "Check if user alice",
            "Ensure user alice",
        ):
            task_line = next(
                ((d, lbl) for d, k, lbl in seq if k == "task" and name in lbl),
                None,
            )
            assert task_line is not None, (
                f"runtime podman task {name!r} is missing from tree: {seq}"
            )
            # Must NOT be one level deeper than the podman header
            # (i.e. nested under a duplicate role: podman).
            assert task_line[0] != podman_depth + 1, (
                f"podman-native task {name!r} at depth={task_line[0]}, "
                f"which is exactly one level deeper than the outer "
                f"'role: podman' header at depth={podman_depth}. That "
                f"means a duplicate 'role: podman' header was emitted. "
                f"Full tree: {seq}"
            )
        # Sanity check: angie's tasks are present in the tree.
        assert angie_lines, (
            f"angie sub-branch must still render alongside the podman tasks; got {seq}"
        )


class TestPreflightDuplicateRoleHeaderBug:
    """Preflight ``RoleGroupDefinition`` whose ``role`` matches the inner
    ``TaskDefinition.role`` produces a duplicate ``role:`` header.

    Repro for the user-reported bug (verbatim from the user's TUI)::

        play: Deploy Keepalived for Proxmox VIP
        ├─ role: angie_ssl_terminator (7 tasks)
        │  └─ role: angie_ssl_terminator (7 tasks)   ← BUG: duplicate header
        │     ├─ □ Set sidecar user config
        │     ├─ □ Include setup tasks
        ├─ □ Deploy TLS certificates for sidecar     ← 5 siblings at depth 2
        ├─ □ Get the user ID for {{ ... }}
        ├─ □ Reload systemd daemon for user
        ├─ □ Enable and start angie-sidecar service
        └─ □ Include add_site tasks

    Root cause: ``iter_preflight_task_defs`` yields ``("X", "X")`` (no
    collapse) when ``TaskDefinition.role == RoleGroupDefinition.role``.
    ``_emit_pending_play`` then iterates that 2-element path and emits
    two ``role: X`` headers in a row. The runtime fix already exists
    in ``_extend_role_path`` via ``_collapse_role_path_aggressive``;
    this test pins the **preflight** side of the same fix.
    """

    def test_preflight_duplicate_role_header_bug(self) -> None:
        # The inner TaskDefinitions all have role="angie_ssl_terminator"
        # which MATCHES the enclosing RoleGroupDefinition's role. The
        # iterator yields ("angie_ssl_terminator", "angie_ssl_terminator")
        # for each — and the renderer must collapse that to a single
        # role header.
        inner_tasks = [
            TaskDefinition(
                name="Set sidecar user config",
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=0,
            ),
            TaskDefinition(
                name="Include setup tasks",
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=1,
            ),
        ]
        # 5 sibling tasks at the play level, also with role="angie_ssl_terminator"
        sibling_tasks = [
            TaskDefinition(
                name=name,
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=10 + idx,
            )
            for idx, name in enumerate(
                [
                    "Deploy TLS certificates for sidecar",
                    "Get the user ID for {{ sidecar_user }}",
                    "Reload systemd daemon for user",
                    "Enable and start angie-sidecar service",
                    "Include add_site tasks",
                ]
            )
        ]

        state = RunState(playbook="main.yml")
        # First play runs at runtime (a "ping" sentinel that satisfies
        # ``is_tree_visible()``). The angie play is the SECOND
        # definition and never gets a runtime play_start, so it
        # renders through ``_emit_pending_play`` — the code path
        # that walks ``iter_preflight_task_defs`` directly and is
        # the one that emits the duplicate role header. Firing
        # play_start for the angie play would route it through
        # ``_emit_runtime_play`` instead, which uses a different
        # path-assembly helper.
        state.definitions = [
            _play_def(
                "p0",
                "Setup",
                [
                    TaskDefinition(
                        name="Ping hosts",
                        role=None,
                        tags=[],
                        play_id="p0",
                        play_order=0,
                        task_order=0,
                    ),
                ],
            ),
            _play_def(
                "p1",
                "Deploy Keepalived for Proxmox VIP",
                [
                    RoleGroupDefinition(
                        role="angie_ssl_terminator",
                        tasks=inner_tasks + sibling_tasks,
                    )
                ],
            ),
        ]
        # Make ``is_tree_visible()`` return True: at least one task
        # must be announced at runtime. The angie play stays preflight
        # only because no play_start fires for "p1".
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-23T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-23T10:00:01Z",
                "play": {"id": "play-0", "name": "Setup"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-23T10:00:02Z",
                "task": {"id": "t-ping", "name": "Ping hosts"},
                "play": {"id": "play-0"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-23T10:00:03Z",
                "task": {"id": "t-ping", "name": "Ping hosts"},
                "host": "web1",
            }
        )

        lines = TreeProjection.from_run_state(state).tree_lines(budget=80)
        seq = _line_summary(lines)

        # The bug: TWO consecutive 'role: angie_ssl_terminator' headers
        # at the same depth with no task between them. Assert exactly ONE.
        angie_role_lines = [
            (d, lbl) for d, k, lbl in seq if k == "role" and "angie_ssl_terminator" in lbl
        ]
        assert len(angie_role_lines) == 1, (
            f"exactly one 'role: angie_ssl_terminator' header expected; "
            f"got {angie_role_lines}. Full tree: {seq}"
        )

        # The two inner tasks must appear under the (single) role header.
        role_depth = angie_role_lines[0][0]
        sidecar = next(
            ((d, lbl) for d, k, lbl in seq if k == "task" and "Set sidecar user config" in lbl),
            None,
        )
        include_setup = next(
            ((d, lbl) for d, k, lbl in seq if k == "task" and "Include setup tasks" in lbl),
            None,
        )
        assert sidecar is not None, f"missing 'Set sidecar user config' task: {seq}"
        assert include_setup is not None, f"missing 'Include setup tasks' task: {seq}"
        assert sidecar[0] == role_depth + 1, (
            f"'Set sidecar user config' should sit one level under the "
            f"role header; got depth={sidecar[0]}, role_depth={role_depth}"
        )
        assert include_setup[0] == role_depth + 1, (
            f"'Include setup tasks' should sit one level under the role "
            f"header; got depth={include_setup[0]}, role_depth={role_depth}"
        )

        # The 5 sibling tasks (mixed in with the inner tasks by
        # play_order — inner tasks come first) must all appear at the
        # same depth as the role header's children. They are NOT
        # nested under a duplicate role header at role_depth+1.
        for name_fragment in (
            "Deploy TLS certificates for sidecar",
            "Reload systemd daemon for user",
            "Enable and start angie-sidecar service",
            "Include add_site tasks",
        ):
            tline = next(
                ((d, lbl) for d, k, lbl in seq if k == "task" and name_fragment in lbl),
                None,
            )
            assert tline is not None, f"missing sibling task {name_fragment!r}: {seq}"
            assert tline[0] == role_depth + 1, (
                f"sibling task {name_fragment!r} should sit one level "
                f"under the role header at depth={role_depth}, not under "
                f"a duplicate role header; got depth={tline[0]}"
            )

        # No two consecutive role lines at the same depth — that's the
        # signature of the duplicate-header bug.
        for i in range(len(seq) - 1):
            d1, k1, _ = seq[i]
            d2, k2, _ = seq[i + 1]
            if k1 == "role" and k2 == "role" and d2 == d1:
                raise AssertionError(
                    f"two consecutive role headers at depth={d1} with no "
                    f"task between them; tree={seq}"
                )


class TestTaskLabelStripsRolePrefixAndPendingVisible:
    """Bug A: task labels include the runtime role prefix even though the
    role is already shown as a separate branch above.

    Bug B: budget truncation drops the tail (pending tasks), leaving the
    user with no visibility into future work. The truncation must
    reserve a line for an ``"and N more tasks"`` indicator so the user
    can see the running tasks AND know that pending work exists.
    """

    def test_task_label_strips_role_prefix_and_pending_visible(self) -> None:
        runtime_task_names = [
            "podman : Activate podman socket for API access",
            "podman : Wait for DNS resolution to be available",
        ]
        pending_task_names = [f"podman : pending task {idx}" for idx in range(1, 35)]
        all_runtime_names = runtime_task_names + pending_task_names

        preflight_tasks = [
            TaskDefinition(
                name="Activate podman socket for API access",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=0,
            ),
            TaskDefinition(
                name="Wait for DNS resolution to be available",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=1,
            ),
        ]

        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Setup rootless Podman",
                [RoleGroupDefinition(role="podman", tasks=preflight_tasks)],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Setup rootless Podman")

        for idx, name in enumerate(all_runtime_names, start=1):
            ts = f"2026-06-23T10:00:{idx + 2:02d}Z"
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": ts,
                    "task": {"id": f"t{idx}", "name": name},
                    "play": {"id": "play-1"},
                }
            )
            if name in runtime_task_names:
                state.handle_event(
                    {
                        "_event": "v2_runner_on_start",
                        "_timestamp": ts,
                        "task": {"id": f"t{idx}", "name": name},
                        "host": "web1",
                    }
                )

        lines = TreeProjection.from_run_state(state).tree_lines(budget=12)
        seq = _line_summary(lines)

        activate_line = next(
            ((d, lbl) for d, k, lbl in seq if k == "task" and "Activate podman socket" in lbl),
            None,
        )
        assert activate_line is not None, (
            f"running task 'Activate podman socket' missing from tree: {seq}"
        )
        activate_label = activate_line[1]
        assert "podman :" not in activate_label, (
            f"task label must NOT carry the 'podman : ' runtime prefix "
            f"(the role is already shown as a separate branch above); "
            f"got label={activate_label!r}. Full tree: {seq}"
        )
        assert "Activate podman socket for API access" in activate_label, (
            f"task label must keep the base name after stripping the "
            f"prefix; got label={activate_label!r}"
        )

        dns_line = next(
            ((d, lbl) for d, k, lbl in seq if k == "task" and "Wait for DNS" in lbl),
            None,
        )
        assert dns_line is not None, f"running task 'Wait for DNS' missing: {seq}"
        dns_label = dns_line[1]
        assert "podman :" not in dns_label, (
            f"task label must NOT carry the 'podman : ' runtime prefix; "
            f"got label={dns_label!r}. Full tree: {seq}"
        )

        more_indicator = next(
            (
                (d, lbl)
                for d, k, lbl in seq
                if k in ("task", "more")
                and ("more tasks" in lbl.lower() or "more pending" in lbl.lower())
            ),
            None,
        )
        pending_visible = any(k == "task" and lbl.startswith("pending task ") for d, k, lbl in seq)
        assert more_indicator is not None or pending_visible, (
            f"budget={12} but with 34 pending tasks behind 2 running, "
            f"the output must reserve a line for an 'and N more tasks' "
            f"indicator OR show at least one pending task. Got tree: {seq}"
        )
        if more_indicator is not None:
            label = more_indicator[1]
            assert "more" in label.lower() and "task" in label.lower(), (
                f"trailing indicator must mention pending work; got {label!r}"
            )
            assert any(ch.isdigit() for ch in label), (
                f"trailing indicator must report the count of dropped tasks; got {label!r}"
            )
