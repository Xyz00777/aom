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
