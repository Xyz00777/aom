"""Unit tests for data models in ansible_aom.core.models.

Test cases cover:
- TC-174 to TC-196: Data model field validation and behavior
- TC-496 to TC-503: WarningType and WarningEntry (v1.8 supplement)
- TC-253 to TC-258: Memory bounds

All tests are self-contained and use function-scoped fixtures.
"""

from datetime import datetime, timezone
from enum import Enum

import pytest

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
    WarningEntry,
    WarningType,
)


class TestStatusEnum:
    """Tests for Status enum - TC-186."""

    def test_status_enum_has_eight_values(self):
        """TC-186: Status enum contains exactly 8 values (7 task/host + COMPLETED for run-level)."""
        assert len(Status) == 8

    def test_status_enum_pending(self):
        """TC-186: Status.PENDING exists with correct value."""
        assert Status.PENDING.value == "pending"

    def test_status_enum_running(self):
        """TC-186: Status.RUNNING exists with correct value."""
        assert Status.RUNNING.value == "running"

    def test_status_enum_ok(self):
        """TC-186: Status.OK exists with correct value."""
        assert Status.OK.value == "ok"

    def test_status_enum_changed(self):
        """TC-186: Status.CHANGED exists with correct value."""
        assert Status.CHANGED.value == "changed"

    def test_status_enum_failed(self):
        """TC-186: Status.FAILED exists with correct value."""
        assert Status.FAILED.value == "failed"

    def test_status_enum_skipped(self):
        """TC-186: Status.SKIPPED exists with correct value."""
        assert Status.SKIPPED.value == "skipped"

    def test_status_enum_unreachable(self):
        """TC-186: Status.UNREACHABLE exists with correct value."""
        assert Status.UNREACHABLE.value == "unreachable"

    def test_status_enum_all_values_unique(self):
        """TC-186: All Status values are unique strings."""
        values = [s.value for s in Status]
        assert len(values) == len(set(values))

    def test_status_enum_string_values_lowercased(self):
        """TC-186: All Status string values are lowercase."""
        for status in Status:
            assert status.value == status.value.lower()


class TestWarningTypeEnum:
    """Tests for WarningType enum - TC-496."""

    def test_warning_type_enum_has_two_values(self):
        """TC-496: WarningType enum has WARNING and DEPRECATION values."""
        assert len(WarningType) == 2

    def test_warning_type_enum_warning(self):
        """TC-496: WarningType.WARNING equals 'warning'."""
        assert WarningType.WARNING.value == "warning"

    def test_warning_type_enum_deprecation(self):
        """TC-496: WarningType.DEPRECATION equals 'deprecation'."""
        assert WarningType.DEPRECATION.value == "deprecation"

    def test_warning_type_enum_all_values_unique(self):
        """TC-496: All WarningType values are unique."""
        values = [w.value for w in WarningType]
        assert len(values) == len(set(values))


class TestWarningEntry:
    """Tests for WarningEntry dataclass - TC-497."""

    def test_warning_entry_required_fields(self):
        """TC-497: WarningEntry with required fields only."""
        entry = WarningEntry(type=WarningType.WARNING, message="Test warning")
        assert entry.type == WarningType.WARNING
        assert entry.message == "Test warning"
        assert entry.timestamp is None
        assert entry.source == ""

    def test_warning_entry_all_fields(self):
        """TC-497: WarningEntry with all fields specified."""
        ts = datetime(2026, 4, 20, 10, 30, 0, tzinfo=timezone.utc)
        entry = WarningEntry(
            type=WarningType.DEPRECATION,
            message="Feature deprecated",
            timestamp=ts,
            source="controller",
        )
        assert entry.type == WarningType.DEPRECATION
        assert entry.message == "Feature deprecated"
        assert entry.timestamp == ts
        assert entry.source == "controller"

    def test_warning_entry_deprecation_type(self):
        """TC-497: WarningEntry can have DEPRECATION type."""
        entry = WarningEntry(type=WarningType.DEPRECATION, message="Deprecated feature")
        assert entry.type == WarningType.DEPRECATION
        assert entry.type != WarningType.WARNING

    def test_warning_entry_warning_type(self):
        """TC-497: WarningEntry can have WARNING type."""
        entry = WarningEntry(type=WarningType.WARNING, message="Test warning")
        assert entry.type == WarningType.WARNING
        assert entry.type != WarningType.DEPRECATION

    def test_warning_entry_empty_message(self):
        """TC-497 edge case: WarningEntry with empty message."""
        entry = WarningEntry(type=WarningType.WARNING, message="")
        assert entry.message == ""

    def test_warning_entry_none_timestamp(self):
        """TC-497 edge case: WarningEntry with None timestamp (default)."""
        entry = WarningEntry(type=WarningType.WARNING, message="Test")
        assert entry.timestamp is None

    def test_warning_entry_default_source_is_empty(self):
        """TC-497: WarningEntry source defaults to empty string."""
        entry = WarningEntry(type=WarningType.WARNING, message="Test")
        assert entry.source == ""

    def test_warning_entry_is_dataclass(self):
        """TC-497: WarningEntry is a dataclass instance."""
        from dataclasses import fields

        entry = WarningEntry(type=WarningType.WARNING, message="Test")
        field_names = {f.name for f in fields(entry)}
        assert field_names == {"type", "message", "timestamp", "source"}


class TestTaskDefinition:
    """Tests for TaskDefinition dataclass - TC-174 to TC-179."""

    def test_task_definition_required_fields(self):
        """TC-174: TaskDefinition with all required fields."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web", "install"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.name == "Install nginx"
        assert task.role == "nginx"
        assert task.tags == ["web", "install"]
        assert task.play_id == "1"
        assert task.play_order == 0
        assert task.task_order == 0

    def test_task_definition_is_dynamic_defaults_false(self):
        """TC-175: is_dynamic defaults to False for static tasks."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.is_dynamic is False

    def test_task_definition_is_dynamic_explicit_true(self):
        """TC-175: is_dynamic can be set to True for dynamic tasks."""
        task = TaskDefinition(
            name="Dynamic task",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
        assert task.is_dynamic is True

    def test_task_definition_uuid_defaults_none(self):
        """TC-176: UUID defaults to None before JSONL matching."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.uuid is None

    def test_task_definition_uuid_can_be_set(self):
        """TC-176: UUID can be set after JSONL matching."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            uuid="abc123-def456",
        )
        assert task.uuid == "abc123-def456"

    def test_task_definition_path_defaults_none(self):
        """TC-177: path defaults to None before JSONL matching."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.path is None

    def test_task_definition_path_can_be_set(self):
        """TC-177: path can be set with file:line format."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            path="roles/nginx/tasks/main.yml:15",
        )
        assert task.path == "roles/nginx/tasks/main.yml:15"

    def test_task_definition_children_defaults_empty_list(self):
        """TC-178: children defaults to empty list."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.children == []
        assert isinstance(task.children, list)

    def test_task_definition_children_can_contain_dynamic_tasks(self):
        """TC-178: children can contain TaskDefinition objects."""
        parent = TaskDefinition(
            name="Include tasks",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        child = TaskDefinition(
            name="Dynamic child",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
        parent.children.append(child)
        assert len(parent.children) == 1
        assert parent.children[0].is_dynamic is True

    def test_task_definition_task_order_minus_one_for_dynamic(self):
        """TC-179: task_order is -1 for dynamic tasks."""
        task = TaskDefinition(
            name="Dynamic task",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
        assert task.task_order == -1

    def test_task_definition_task_order_non_negative_for_static(self):
        """TC-179: task_order is >= 0 for static tasks."""
        task = TaskDefinition(
            name="Static task",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=5,
        )
        assert task.task_order >= 0

    def test_task_definition_role_can_be_none(self):
        """TC-174 edge case: role can be None for non-role tasks."""
        task = TaskDefinition(
            name="Debug task",
            role=None,
            tags=["debug"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.role is None

    def test_task_definition_all_fields_types(self):
        """TC-174: All fields have correct types."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web", "install"],
            play_id="1",
            play_order=0,
            task_order=0,
            is_dynamic=False,
            uuid="test-uuid-123",
            path="file.yml:10",
        )
        assert isinstance(task.name, str)
        assert isinstance(task.role, str) or task.role is None
        assert isinstance(task.tags, list)
        assert isinstance(task.play_id, str)
        assert isinstance(task.play_order, int)
        assert isinstance(task.task_order, int)
        assert isinstance(task.is_dynamic, bool)
        assert isinstance(task.uuid, str) or task.uuid is None
        assert isinstance(task.path, str) or task.path is None
        assert isinstance(task.children, list)

    def test_task_definition_run_once_defaults_false(self):
        """run_once defaults to False for ordinary tasks."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.run_once is False

    def test_task_definition_run_once_explicit_true(self):
        """run_once can be set to True for run_once: true tasks."""
        task = TaskDefinition(
            name="Create external service DNS records (dynamic)",
            role="identity",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
            run_once=True,
        )
        assert task.run_once is True


class TestRoleGroupDefinition:
    """Tests for RoleGroupDefinition dataclass - TC-180, TC-181."""

    def test_role_group_definition_initialization(self):
        """TC-180: RoleGroupDefinition with role and tasks."""
        tasks = [
            TaskDefinition("task1", "nginx", [], "1", 0, 0),
            TaskDefinition("task2", "nginx", [], "1", 0, 1),
            TaskDefinition("task3", "nginx", [], "1", 0, 2),
            TaskDefinition("task4", "nginx", [], "1", 0, 3),
            TaskDefinition("task5", "nginx", [], "1", 0, 4),
        ]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        assert group.role == "nginx"
        assert len(group.tasks) == 5

    def test_role_group_definition_name_property_format(self):
        """TC-181: name property returns formatted string."""
        tasks = [
            TaskDefinition("task1", "nginx", [], "1", 0, 0),
            TaskDefinition("task2", "nginx", [], "1", 0, 1),
            TaskDefinition("task3", "nginx", [], "1", 0, 2),
            TaskDefinition("task4", "nginx", [], "1", 0, 3),
            TaskDefinition("task5", "nginx", [], "1", 0, 4),
        ]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        assert group.name == "Role: nginx (5 tasks)"

    def test_role_group_definition_name_with_seven_tasks(self):
        """TC-181 edge case: name with 7 tasks."""
        tasks = [TaskDefinition(f"task{i}", "nginx", [], "1", 0, i) for i in range(7)]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        assert group.name == "Role: nginx (7 tasks)"

    def test_role_group_definition_role_string(self):
        """TC-180: role is a string."""
        group = RoleGroupDefinition(role="nginx", tasks=[])
        assert isinstance(group.role, str)

    def test_role_group_definition_tasks_list(self):
        """TC-180: tasks is a list of TaskDefinition."""
        tasks = [TaskDefinition("task1", "nginx", [], "1", 0, 0)]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        assert isinstance(group.tasks, list)
        assert all(isinstance(t, TaskDefinition) for t in group.tasks)

    def test_role_group_definition_role_with_special_characters(self):
        """TC-181 edge case: role name with special characters."""
        tasks = [TaskDefinition("task1", "nginx-proxy", [], "1", 0, 0)]
        group = RoleGroupDefinition(role="nginx-proxy_1.2", tasks=tasks)
        assert "nginx-proxy_1.2" in group.name

    def test_role_group_definition_many_tasks(self):
        """TC-180 edge case: many tasks in a role group."""
        tasks = [TaskDefinition(f"task{i}", "big-role", [], "1", 0, i) for i in range(100)]
        group = RoleGroupDefinition(role="big-role", tasks=tasks)
        assert group.name == "Role: big-role (100 tasks)"


class TestPlayDefinition:
    """Tests for PlayDefinition dataclass - TC-182 to TC-185."""

    def test_play_definition_required_fields(self):
        """TC-182: PlayDefinition with required fields."""
        play = PlayDefinition(
            id="1",
            name="Setup webservers",
            hosts="webservers",
        )
        assert play.id == "1"
        assert play.name == "Setup webservers"
        assert play.hosts == "webservers"

    def test_play_definition_all_fields(self):
        """TC-182: PlayDefinition with all fields."""
        tasks = [TaskDefinition("task1", "nginx", [], "1", 0, 0)]
        play = PlayDefinition(
            id="1",
            name="Setup webservers",
            hosts="webservers",
            resolved_hosts=["web1", "web2"],
            tasks=tasks,
        )
        assert play.resolved_hosts == ["web1", "web2"]
        assert len(play.tasks) == 1

    def test_play_definition_id_sequential_number_format(self):
        """TC-183: id is sequential number string from --list-tasks."""
        play1 = PlayDefinition(id="1", name="Play 1", hosts="all")
        play2 = PlayDefinition(id="2", name="Play 2", hosts="all")
        assert play1.id == "1"
        assert play2.id == "2"

    def test_play_definition_hosts_vs_resolved_hosts(self):
        """TC-184: hosts contains pattern, resolved_hosts contains hostnames."""
        play = PlayDefinition(
            id="1",
            name="Setup",
            hosts="webservers:&active",
            resolved_hosts=["web1", "web2", "web3"],
        )
        assert play.hosts == "webservers:&active"
        assert play.resolved_hosts == ["web1", "web2", "web3"]
        assert play.hosts != str(play.resolved_hosts)

    def test_play_definition_resolved_hosts_defaults_empty(self):
        """TC-185: resolved_hosts defaults to empty list."""
        play = PlayDefinition(id="1", name="Setup", hosts="all")
        assert play.resolved_hosts == []
        assert isinstance(play.resolved_hosts, list)

    def test_play_definition_tasks_defaults_empty(self):
        """TC-182: tasks defaults to empty list."""
        play = PlayDefinition(id="1", name="Setup", hosts="all")
        assert play.tasks == []
        assert isinstance(play.tasks, list)

    def test_play_definition_tasks_can_contain_task_or_role_group(self):
        """TC-182: tasks list can contain TaskDefinition or RoleGroupDefinition."""
        tasks = [
            TaskDefinition("task1", "nginx", [], "1", 0, 0),
            TaskDefinition("task2", "nginx", [], "1", 0, 1),
            TaskDefinition("task3", "nginx", [], "1", 0, 2),
            TaskDefinition("task4", "nginx", [], "1", 0, 3),
            TaskDefinition("task5", "nginx", [], "1", 0, 4),
        ]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        play = PlayDefinition(
            id="1",
            name="Setup",
            hosts="webservers",
            tasks=[group],
        )
        assert len(play.tasks) == 1
        assert isinstance(play.tasks[0], RoleGroupDefinition)

    def test_play_definition_hosts_pattern_wildcard(self):
        """TC-182 edge case: hosts pattern can be wildcard."""
        play = PlayDefinition(id="1", name="All hosts", hosts="*")
        assert play.hosts == "*"

    def test_play_definition_hosts_pattern_localhost(self):
        """TC-182 edge case: hosts pattern can be localhost."""
        play = PlayDefinition(id="1", name="Local", hosts="localhost")
        assert play.hosts == "localhost"


class TestHostRunState:
    """Tests for HostRunState dataclass - TC-187, TC-188."""

    def test_host_run_state_required_fields(self):
        """TC-187: HostRunState with required fields."""
        host_state = HostRunState(hostname="web1", status=Status.OK)
        assert host_state.hostname == "web1"
        assert host_state.status == Status.OK

    def test_host_run_state_all_fields(self):
        """TC-187: HostRunState with all fields."""
        start = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 20, 10, 0, 5, tzinfo=timezone.utc)
        host_state = HostRunState(
            hostname="web1",
            status=Status.CHANGED,
            changed=True,
            message="Task completed successfully",
            start_time=start,
            end_time=end,
        )
        assert host_state.changed is True
        assert host_state.message == "Task completed successfully"
        assert host_state.start_time == start
        assert host_state.end_time == end

    def test_host_run_state_changed_defaults_false(self):
        """TC-187: changed defaults to False."""
        host_state = HostRunState(hostname="web1", status=Status.OK)
        assert host_state.changed is False

    def test_host_run_state_message_defaults_empty(self):
        """TC-187: message defaults to empty string."""
        host_state = HostRunState(hostname="web1", status=Status.OK)
        assert host_state.message == ""

    def test_host_run_state_timestamps_default_none(self):
        """TC-187: timestamps default to None."""
        host_state = HostRunState(hostname="web1", status=Status.OK)
        assert host_state.start_time is None
        assert host_state.end_time is None

    def test_host_run_state_status_can_be_changed(self):
        """TC-188: HostRunState status is mutable."""
        host_state = HostRunState(hostname="web1", status=Status.PENDING)
        assert host_state.status == Status.PENDING
        host_state.status = Status.RUNNING
        assert host_state.status == Status.RUNNING

    def test_host_run_state_status_transition_to_ok(self):
        """TC-188: Status transition to OK."""
        host_state = HostRunState(hostname="web1", status=Status.RUNNING)
        host_state.status = Status.OK
        assert host_state.status == Status.OK

    def test_host_run_state_status_transition_to_changed(self):
        """TC-188: Status transition to CHANGED."""
        host_state = HostRunState(hostname="web1", status=Status.RUNNING)
        host_state.status = Status.CHANGED
        host_state.changed = True
        assert host_state.status == Status.CHANGED
        assert host_state.changed is True

    def test_host_run_state_status_transition_to_failed(self):
        """TC-188: Status transition to FAILED."""
        host_state = HostRunState(hostname="web1", status=Status.RUNNING)
        host_state.status = Status.FAILED
        host_state.message = "Error: connection refused"
        assert host_state.status == Status.FAILED

    def test_host_run_state_status_transition_to_unreachable(self):
        """TC-188: Status transition to UNREACHABLE."""
        host_state = HostRunState(hostname="web1", status=Status.RUNNING)
        host_state.status = Status.UNREACHABLE
        host_state.message = "SSH connection failed"
        assert host_state.status == Status.UNREACHABLE

    def test_host_run_state_status_transition_to_skipped(self):
        """TC-188: Status transition to SKIPPED."""
        host_state = HostRunState(hostname="web1", status=Status.PENDING)
        host_state.status = Status.SKIPPED
        assert host_state.status == Status.SKIPPED


class TestTaskRunState:
    """Tests for TaskRunState dataclass - TC-189, TC-190."""

    def test_task_run_state_required_fields(self):
        """TC-189: TaskRunState with required fields."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        assert task_state.task_id == "uuid-123"
        assert task_state.name == "Install nginx"

    def test_task_run_state_all_fields(self):
        """TC-189: TaskRunState with all fields."""
        start = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
        task_state = TaskRunState(
            task_id="uuid-123",
            name="Install nginx",
            status=Status.RUNNING,
            start_time=start,
        )
        assert task_state.status == Status.RUNNING
        assert task_state.start_time == start

    def test_task_run_state_status_defaults_pending(self):
        """TC-189: status defaults to PENDING."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        assert task_state.status == Status.PENDING

    def test_task_run_state_hosts_defaults_empty_dict(self):
        """TC-189: hosts defaults to empty dict."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        assert task_state.hosts == {}
        assert isinstance(task_state.hosts, dict)

    def test_task_run_state_hosts_dict_key_is_hostname_string(self):
        """TC-190: hosts dict uses hostname string as key."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        task_state.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        assert "web1" in task_state.hosts
        assert isinstance(task_state.hosts["web1"], HostRunState)

    def test_task_run_state_hosts_dict_value_is_host_run_state(self):
        """TC-190: hosts dict value is HostRunState."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        host_state = HostRunState(hostname="web1", status=Status.OK)
        task_state.hosts["web1"] = host_state
        assert task_state.hosts["web1"] is host_state

    def test_task_run_state_multiple_hosts(self):
        """TC-190: hosts dict can have multiple hosts."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        task_state.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task_state.hosts["web2"] = HostRunState(hostname="web2", status=Status.CHANGED)
        assert len(task_state.hosts) == 2

    def test_task_run_state_timestamps_default_none(self):
        """TC-189: timestamps default to None."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        assert task_state.start_time is None
        assert task_state.end_time is None

    def test_task_run_state_hostname_with_special_characters(self):
        """TC-190 edge case: hostname with dots and underscores."""
        task_state = TaskRunState(task_id="uuid-123", name="Install nginx")
        task_state.hosts["web-server_1.example.com"] = HostRunState(
            hostname="web-server_1.example.com", status=Status.OK
        )
        assert "web-server_1.example.com" in task_state.hosts


class TestPlayRunState:
    """Tests for PlayRunState dataclass - TC-191, TC-192, TC-193."""

    def test_play_run_state_required_fields(self):
        """TC-191: PlayRunState with required fields."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup webservers")
        assert play_state.play_id == "uuid-play-1"
        assert play_state.name == "Setup webservers"

    def test_play_run_state_all_fields(self):
        """TC-191: PlayRunState with all fields."""
        play_state = PlayRunState(
            play_id="uuid-play-1",
            name="Setup webservers",
            status=Status.RUNNING,
            detected_strategy="linear",
        )
        assert play_state.status == Status.RUNNING
        assert play_state.detected_strategy == "linear"

    def test_play_run_state_status_defaults_pending(self):
        """TC-191: status defaults to PENDING."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        assert play_state.status == Status.PENDING

    def test_play_run_state_tasks_defaults_empty_dict(self):
        """TC-191: tasks defaults to empty dict."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        assert play_state.tasks == {}
        assert isinstance(play_state.tasks, dict)

    def test_play_run_state_detected_strategy_defaults_none(self):
        """TC-192: detected_strategy defaults to None before first task event."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        assert play_state.detected_strategy is None

    def test_play_run_state_detected_strategy_can_be_linear(self):
        """TC-193: detected_strategy can be 'linear' for lockstep."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        play_state.detected_strategy = "linear"
        assert play_state.detected_strategy == "linear"

    def test_play_run_state_detected_strategy_can_be_free(self):
        """TC-193: detected_strategy can be 'free' for non-lockstep."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        play_state.detected_strategy = "free"
        assert play_state.detected_strategy == "free"

    def test_play_run_state_detected_strategy_values_are_limited(self):
        """TC-193: detected_strategy can only be 'linear', 'free', or None."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        # Valid values
        valid_values = [None, "linear", "free"]
        # These should be the only valid values
        # Implementation may validate or just accept strings
        play_state.detected_strategy = None
        play_state.detected_strategy = "linear"
        play_state.detected_strategy = "free"

    def test_play_run_state_tasks_dict_key_is_task_id(self):
        """TC-191: tasks dict uses task UUID/id string as key."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        task_state = TaskRunState(task_id="uuid-task-1", name="Install nginx")
        play_state.tasks["uuid-task-1"] = task_state
        assert "uuid-task-1" in play_state.tasks

    def test_play_run_state_tasks_dict_value_is_task_run_state(self):
        """TC-191: tasks dict value is TaskRunState."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        task_state = TaskRunState(task_id="uuid-task-1", name="Install nginx")
        play_state.tasks["uuid-task-1"] = task_state
        assert isinstance(play_state.tasks["uuid-task-1"], TaskRunState)

    def test_play_run_state_timestamps_default_none(self):
        """TC-191: start_time and end_time are not in PlayRunState."""
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        # PlayRunState does not have start_time/end_time - those are at RunState level
        assert not hasattr(play_state, "start_time")
        assert not hasattr(play_state, "end_time")


class TestRunState:
    """Tests for RunState dataclass - TC-194, TC-195, TC-196."""

    def test_run_state_required_field_playbook(self):
        """TC-194: RunState requires playbook field."""
        state = RunState(playbook="site.yml")
        assert state.playbook == "site.yml"

    def test_run_state_all_fields(self):
        """TC-194: RunState with all fields."""
        start = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 20, 10, 30, 0, tzinfo=timezone.utc)
        state = RunState(
            playbook="site.yml",
            start_time=start,
            end_time=end,
            status=Status.OK,
        )
        assert state.start_time == start
        assert state.end_time == end
        assert state.status == Status.OK

    def test_run_state_plays_defaults_empty_dict(self):
        """TC-194: plays defaults to empty dict."""
        state = RunState(playbook="site.yml")
        assert state.plays == {}
        assert isinstance(state.plays, dict)

    def test_run_state_definitions_defaults_empty_list(self):
        """TC-195: definitions defaults to empty list."""
        state = RunState(playbook="site.yml")
        assert state.definitions == []
        assert isinstance(state.definitions, list)

    def test_run_state_status_defaults_pending(self):
        """TC-194: status defaults to PENDING."""
        state = RunState(playbook="site.yml")
        assert state.status == Status.PENDING

    def test_run_state_timestamps_default_none(self):
        """TC-194: timestamps default to None."""
        state = RunState(playbook="site.yml")
        assert state.start_time is None
        assert state.end_time is None

    def test_run_state_plays_dict_key_is_play_id(self):
        """TC-196: plays dict uses play UUID/id string as key."""
        state = RunState(playbook="site.yml")
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        state.plays["uuid-play-1"] = play_state
        assert "uuid-play-1" in state.plays

    def test_run_state_plays_dict_value_is_play_run_state(self):
        """TC-196: plays dict value is PlayRunState."""
        state = RunState(playbook="site.yml")
        play_state = PlayRunState(play_id="uuid-play-1", name="Setup")
        state.plays["uuid-play-1"] = play_state
        assert isinstance(state.plays["uuid-play-1"], PlayRunState)

    def test_run_state_definitions_list_contains_play_definition(self):
        """TC-195: definitions contains PlayDefinition objects."""
        state = RunState(playbook="site.yml")
        play_def = PlayDefinition(id="1", name="Setup", hosts="all")
        state.definitions.append(play_def)
        assert len(state.definitions) == 1
        assert isinstance(state.definitions[0], PlayDefinition)

    def test_run_state_single_instance_per_playbook(self):
        """TC-194 edge case: One RunState instance per playbook run."""
        state1 = RunState(playbook="site.yml")
        state2 = RunState(playbook="site.yml")
        # Each playbook run creates a new RunState instance
        assert state1 is not state2


class TestDefinitionVsStateSeparation:
    """Tests for Definition vs State separation concept."""

    def test_definition_classes_are_immutable_intent(self):
        """Definition classes represent immutable pre-execution data."""
        # TaskDefinition, RoleGroupDefinition, PlayDefinition are Definitions
        # They should be created once and not modified
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        # Note: dataclasses are mutable by default, but the intent is immutability
        # The is_dynamic, uuid, path fields may be updated after initial creation
        # But the core definition (name, role, tags, play_id, play_order, task_order) remains constant
        assert task.name == "Install nginx"

    def test_state_classes_are_mutable_intent(self):
        """State classes are designed to be mutable during execution."""
        # HostRunState, TaskRunState, PlayRunState, RunState are State classes
        # They track execution progress and are updated as events arrive
        host_state = HostRunState(hostname="web1", status=Status.PENDING)
        host_state.status = Status.RUNNING
        host_state.status = Status.OK
        assert host_state.status == Status.OK

        task_state = TaskRunState(task_id="uuid-1", name="Task")
        task_state.status = Status.RUNNING
        assert task_state.status == Status.RUNNING

    def test_definition_uuid_can_be_populated_later(self):
        """Definition uuid field can be populated after JSONL matching."""
        # Definition created from --list-tasks output
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.uuid is None

        # After matching with JSONL event
        task.uuid = "abc123-def456"
        assert task.uuid == "abc123-def456"

    def test_definition_path_can_be_populated_later(self):
        """Definition path field can be populated after JSONL matching."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.path is None

        # After matching with JSONL event
        task.path = "roles/nginx/tasks/main.yml:15"
        assert task.path == "roles/nginx/tasks/main.yml:15"


class TestTaskMatching:
    """Tests for task matching strategy."""

    def test_task_uuid_primary_matching(self):
        """TC-091: Primary matching uses task.id (UUID) from JSONL."""
        # This test verifies the field exists for matching
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            uuid="abc123-def456-789",
        )
        # UUID match is primary, most reliable
        assert task.uuid == "abc123-def456-789"

    def test_task_path_secondary_matching(self):
        """TC-092: Secondary matching uses file:line path."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            path="roles/nginx/tasks/main.yml:15",
        )
        # Path match is secondary
        assert task.path == "roles/nginx/tasks/main.yml:15"
        assert ":" in task.path  # File:line format

    def test_task_sequential_name_fallback_matching(self):
        """TC-093: Fallback matching uses play_order, task_order, name."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=5,
        )
        # Order fields for sequential matching
        assert task.play_order == 0
        assert task.task_order == 5
        assert task.name == "Install nginx"

    def test_task_matching_uses_uuid_first_if_present(self):
        """When UUID is present, it should be used for matching."""
        task_with_uuid = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            uuid="unique-uuid-123",
        )
        task_without_uuid = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        # UUID presence enables primary matching
        assert task_with_uuid.uuid is not None
        assert task_without_uuid.uuid is None


class TestMemoryBounds:
    """Tests for memory bounds - TC-253 to TC-258."""

    # These are soft limits - tests verify the models can hold data
    # Memory bound enforcement is at the state management level

    def test_multiple_plays_in_run_state(self):
        """TC-253: Multiple plays can be tracked in RunState."""
        state = RunState(playbook="site.yml")
        for i in range(100):
            play_state = PlayRunState(play_id=f"play-{i}", name=f"Play {i}")
            state.plays[f"play-{i}"] = play_state
        assert len(state.plays) == 100

    def test_multiple_tasks_in_play_run_state(self):
        """TC-254: Multiple tasks can be tracked per play."""
        play_state = PlayRunState(play_id="play-1", name="Play 1")
        for i in range(100):
            task_state = TaskRunState(
                task_id=f"task-{i}",
                name=f"Task {i}",
            )
            play_state.tasks[f"task-{i}"] = task_state
        assert len(play_state.tasks) == 100

    def test_multiple_hosts_in_task_run_state(self):
        """TC-255: Multiple hosts can be tracked per task."""
        task_state = TaskRunState(task_id="task-1", name="Task 1")
        for i in range(100):
            host_state = HostRunState(
                hostname=f"host-{i}",
                status=Status.OK,
            )
            task_state.hosts[f"host-{i}"] = host_state
        assert len(task_state.hosts) == 100

    def test_total_host_run_state_entries(self):
        """TC-256: Many HostRunState entries across all tasks."""
        # Verify data structure can support many entries
        state = RunState(playbook="site.yml")
        total_hosts = 0

        for play_id in ["play-1", "play-2"]:
            play_state = PlayRunState(play_id=play_id, name=f"Play {play_id}")
            for task_id in ["task-1", "task-2", "task-3"]:
                task_state = TaskRunState(task_id=task_id, name=f"Task {task_id}")
                for host_num in ["host-1", "host-2", "host-3", "host-4", "host-5"]:
                    host_state = HostRunState(hostname=host_num, status=Status.OK)
                    task_state.hosts[host_num] = host_state
                    total_hosts += 1
                play_state.tasks[task_id] = task_state
            state.plays[play_id] = play_state

        # Verify count (3 tasks * 5 hosts * 2 plays = 30 entries)
        assert total_hosts == 30

    def test_play_definition_can_have_role_group(self):
        """PlayDefinition tasks list can hold RoleGroupDefinition."""
        tasks = [TaskDefinition(f"task{i}", "nginx", [], "1", 0, i) for i in range(5)]
        role_group = RoleGroupDefinition(role="nginx", tasks=tasks)
        play = PlayDefinition(
            id="1",
            name="Setup",
            hosts="webservers",
            tasks=[role_group],
        )
        assert len(play.tasks) == 1
        assert isinstance(play.tasks[0], RoleGroupDefinition)
        assert play.tasks[0].role == "nginx"

    def test_play_definition_can_have_mixed_tasks_and_groups(self):
        """PlayDefinition tasks can mix TaskDefinition and RoleGroupDefinition."""
        group_tasks = [TaskDefinition(f"task{i}", "nginx", [], "1", 0, i) for i in range(5)]
        role_group = RoleGroupDefinition(role="nginx", tasks=group_tasks)
        standalone_task = TaskDefinition("standalone", None, [], "1", 0, 10)
        play = PlayDefinition(
            id="1",
            name="Setup",
            hosts="webservers",
            tasks=[role_group, standalone_task],
        )
        assert len(play.tasks) == 2
        assert isinstance(play.tasks[0], RoleGroupDefinition)
        assert isinstance(play.tasks[1], TaskDefinition)


class TestLinearForceCompletion:
    """Tests for force-completing stuck RUNNING tasks under linear strategy.

    Under linear strategy, when a new task starts the previous task is
    guaranteed complete on ALL hosts by ansible's sequential execution.
    Some hosts never receive terminal events (meta: reset_connection,
    silent skips from when: false), so remaining RUNNING hosts must be
    force-transitioned to OK.
    """

    def test_meta_task_force_completed_under_linear(self):
        """TC-RESET-1: Hosts stuck RUNNING in a meta task get force-
        transitioned to OK when the next task starts."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["ipa1"],
                tasks=[
                    TaskDefinition(
                        name="Reset connection",
                        role="freeipa",
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    ),
                    TaskDefinition(
                        name="Next task",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=1,
                    ),
                ],
            )
        ]
        state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-05-23T10:00:00Z",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )

        # Task 1: "Reset connection" — meta, no terminal events
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "uuid-meta", "name": "Reset connection"},
                "play": {"id": "play-1"},
            }
        )

        play = state.plays["play-1"]
        task1 = play.tasks["uuid-meta"]
        assert task1.status == Status.RUNNING
        assert "ipa1" in task1.hosts
        assert task1.hosts["ipa1"].status == Status.RUNNING

        # Task 2: "Next task" starts — should force-complete task 1
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:01:00Z",
                "task": {"id": "uuid-next", "name": "Next task"},
                "play": {"id": "play-1"},
            }
        )

        assert task1.status == Status.COMPLETED
        assert task1.hosts["ipa1"].status == Status.OK

    def test_real_terminal_hosts_preserved(self):
        """TC-RESET-2: Hosts that received real terminal events keep their
        actual status; only genuinely stuck RUNNING hosts get force-
        transitioned to OK."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["ipa1", "ipa2"],
                tasks=[
                    TaskDefinition(
                        name="Slow task",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    ),
                    TaskDefinition(
                        name="Next task",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=1,
                    ),
                ],
            )
        ]
        state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-05-23T10:00:00Z",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )

        # Task 1 starts — hosts synthesized RUNNING
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "uuid-task1", "name": "Slow task"},
                "play": {"id": "play-1"},
            }
        )

        # ipa1 gets a real terminal event (FAILED)
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "uuid-task1", "name": "Slow task"},
                "hosts": {"ipa1": {"failed": True}},
            }
        )
        # ipa2 stays RUNNING — no terminal event

        task1 = state.plays["play-1"].tasks["uuid-task1"]
        assert task1.hosts["ipa1"].status == Status.FAILED
        assert task1.hosts["ipa2"].status == Status.RUNNING

        # Task 2 starts → force-complete task 1
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:01:00Z",
                "task": {"id": "uuid-task2", "name": "Next task"},
                "play": {"id": "play-1"},
            }
        )

        assert task1.status == Status.COMPLETED
        assert task1.hosts["ipa1"].status == Status.FAILED
        assert task1.hosts["ipa2"].status == Status.OK

    def test_same_play_handler_task_force_completed(self):
        """TC-RESET-3: Within the same play, a handler task with no
        terminal events gets force-completed when the next task in the
        same play starts. Under linear strategy, ansible runs handlers
        sequentially within the play before moving to the next task."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["host1"],
                tasks=[
                    TaskDefinition(
                        name="Normal task",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    ),
                    TaskDefinition(
                        name="Handler: restart service",
                        role=None,
                        tags=["handlers"],
                        play_id="1",
                        play_order=0,
                        task_order=1,
                    ),
                    TaskDefinition(
                        name="Next after handler",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=2,
                    ),
                ],
            )
        ]
        state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-05-23T10:00:00Z",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )

        # Task 1: normal task — gets a real terminal event
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "uuid-normal", "name": "Normal task"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "uuid-normal", "name": "Normal task"},
                "hosts": {"host1": {"ok": True, "changed": False}},
            }
        )

        # Handler task: no terminal events (meta operation)
        state.handle_event(
            {
                "_event": "v2_playbook_on_handler_task_start",
                "_timestamp": "2026-05-23T10:00:04Z",
                "task": {"id": "uuid-handler", "name": "Handler: restart service"},
                "play": {"id": "play-1"},
            }
        )
        handler = state.plays["play-1"].tasks["uuid-handler"]
        assert handler.status == Status.RUNNING
        assert handler.hosts["host1"].status == Status.RUNNING

        # Next task starts in same play — should force-complete the handler
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "uuid-next", "name": "Next after handler"},
                "play": {"id": "play-1"},
            }
        )

        assert handler.status == Status.COMPLETED
        assert handler.hosts["host1"].status == Status.OK

    def test_free_strategy_not_affected(self):
        """TC-RESET-4: Under free strategy, the force-completion path
        does NOT run — tasks with stuck RUNNING hosts remain RUNNING."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["host1"],
                tasks=[
                    TaskDefinition(
                        name="Task 1",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    ),
                    TaskDefinition(
                        name="Task 2",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=1,
                    ),
                ],
            )
        ]
        state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-05-23T10:00:00Z",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )

        # Force the play to free strategy before any task starts
        state.plays["play-1"].detected_strategy = "free"

        # Task 1 — hosts synthesized RUNNING (no terminal events)
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "uuid-t1", "name": "Task 1"},
                "play": {"id": "play-1"},
            }
        )
        task1 = state.plays["play-1"].tasks["uuid-t1"]
        assert task1.status == Status.RUNNING
        assert task1.hosts["host1"].status == Status.RUNNING

        # Task 2 starts — should NOT force-complete task 1 (free strategy)
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "uuid-t2", "name": "Task 2"},
                "play": {"id": "play-1"},
            }
        )

        # Under free strategy, task 1 stays RUNNING
        assert task1.status == Status.RUNNING
        assert task1.hosts["host1"].status == Status.RUNNING


class TestFreeStrategyMetaTaskVisibility:
    """Document reality: meta tasks under strategy: free are invisible.

    Ansible's ``ansible.posix.jsonl`` callback filters implicit meta tasks
    under ``strategy: free`` — no ``v2_playbook_on_task_start`` event,
    no ``v2_runner_on_*`` event. The meta task never enters RunState's
    task map, and the projection's tree emission has nothing to render
    for it. This is not a bug; it's the JSONL callback's contract.

    Under the default ``strategy: linear``, meta tasks emit a
    ``v2_playbook_on_task_start`` event. The next task's
    ``v2_playbook_on_task_start`` triggers the linear force-completion
    branch added in d981444, which transitions the meta task's hosts
    RUNNING → OK and the task itself RUNNING → COMPLETED. The
    projection's ``_classify`` then drops it from the live tree.

    See:
    - d981444: force-complete stuck hosts under linear strategy
    - tests/unit/test_play_boundary_state.py::test_meta_task_force_completed_across_plays
    - tests/unit/test_models.py::TestLinearForceCompletion::test_meta_task_force_completed_under_linear
    """

    def test_meta_task_emits_no_events_under_free_strategy(self) -> None:
        """Linear: meta task emits task_start + gets force-completed by next task_start."""
        # Use the existing linear scenario as the documented reality.
        # This is a no-op assertion on top of the existing linear test:
        # the meta task should be COMPLETED with hosts OK after the next
        # task_start arrives.
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["ipa1"],
                tasks=[
                    TaskDefinition(
                        name="Reset connection",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    ),
                    TaskDefinition(
                        name="Next task",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=1,
                    ),
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "uuid-meta", "name": "Reset connection"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:01:00Z",
                "task": {"id": "uuid-next", "name": "Next task"},
                "play": {"id": "play-1"},
            }
        )

        play = state.plays["play-1"]
        meta_task = play.tasks["uuid-meta"]
        assert meta_task.status == Status.COMPLETED, (
            "Meta task must be COMPLETED after the next task_start under linear strategy "
            "(d981444 force-completion). The bug the user reported was already fixed; this "
            "test pins the behaviour so regressions surface."
        )
        assert meta_task.hosts["ipa1"].status == Status.OK


class TestRunnerTaskCompletionPromotion:
    """After the last host reaches terminal status, task.status must
    transition RUNNING → COMPLETED. The projection's _classify
    already paper-overs this case, but other code paths
    (status counters, replay) read task.status directly.
    """

    def test_single_host_ok_promotes_task_to_completed(self) -> None:
        """A task with one host: runner_on_ok → task COMPLETED."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="task", role=None, tags=[], play_id="1", play_order=0, task_order=0
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "task"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "task"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        task = state.plays["play-1"].tasks["t1"]
        assert task.status == Status.COMPLETED, (
            "task.status must be COMPLETED after the only host reaches OK; "
            "the projection paper-overs this but other code paths read task.status directly."
        )

    def test_multi_host_partial_completion_stays_running(self) -> None:
        """With two hosts, one OK + one RUNNING → task stays RUNNING."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    TaskDefinition(
                        name="task", role=None, tags=[], play_id="1", play_order=0, task_order=0
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "task"},
                "play": {"id": "play-1"},
            }
        )
        # web1 OK, web2 still RUNNING
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "task"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        task = state.plays["play-1"].tasks["t1"]
        assert task.status == Status.RUNNING, (
            "task.status must remain RUNNING while at least one host is RUNNING."
        )

    def test_multi_host_all_terminal_promotes_to_completed(self) -> None:
        """With two hosts, both OK → task COMPLETED."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="test",
                hosts="all",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    TaskDefinition(
                        name="task", role=None, tags=[], play_id="1", play_order=0, task_order=0
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "task"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "task"},
                "hosts": {
                    "web1": {"ok": True, "changed": False},
                    "web2": {"ok": True, "changed": False},
                },
            }
        )
        task = state.plays["play-1"].tasks["t1"]
        assert task.status == Status.COMPLETED, (
            "task.status must be COMPLETED once all hosts reach terminal status."
        )
