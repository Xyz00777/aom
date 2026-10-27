# GNU General Public License v3.0-or-later
# This file is a thin subclass of ``ansible.posix.jsonl`` (itself GPL-3.0+)
# and is therefore distributed under the same terms as AOM (GPL-3.0-or-later).
"""AOM's stdout callback: ``ansible.posix.jsonl`` plus per-item loop events.

``ansible.posix.jsonl`` intercepts only the aggregate result hooks
(``v2_runner_on_ok`` and friends) via ``__getattribute__``; the per-item
hooks ``v2_runner_item_on_*`` fall through to ``CallbackBase``'s no-op
implementations, so a loop arrives as a single aggregate event at the
very end. This subclass re-emits one JSONL event per loop item, in real
time, so AOM can stream per-item progress.

Each item event reuses the parent's exact envelope shape
(``{task, hosts: {host: <result>}}``) where ``hosts[host]`` is that one
item's result. The item events are *additive*: the parent still emits the
aggregate ``v2_runner_on_ok``/``v2_runner_on_failed`` at loop end with the
full ``results[]`` array, so consumers that read it are unaffected.

The ``DOCUMENTATION`` block must redeclare the parent's options
(``json_indent``, ``show_custom_stats``): callback options are loaded from
the active plugin's own documentation, and the parent's ``__init__`` reads
``get_option('json_indent')`` — without these the load crashes.
"""

from __future__ import annotations

DOCUMENTATION = """
    name: aom_jsonl
    type: stdout
    short_description: jsonl plus per-item loop events (for AOM)
    description:
      - Subclass of ansible.posix.jsonl that additionally emits
        v2_runner_item_on_ok/failed/skipped events for live loop streaming.
    requirements:
      - Set as stdout in config
    options:
      show_custom_stats:
        name: Show custom stats
        description: 'This adds the custom stats set via the set_stats plugin to the play recap'
        default: False
        env:
          - name: ANSIBLE_SHOW_CUSTOM_STATS
        ini:
          - key: show_custom_stats
            section: defaults
        type: bool
      json_indent:
        name: Use indenting for the JSON output
        description: 'If specified, use this many spaces for indenting in the JSON output.
          If not specified or <= 0, write to a single line.'
        default: 0
        env:
          - name: ANSIBLE_JSON_INDENT
        ini:
          - key: json_indent
            section: defaults
        type: integer
"""

import copy

from ansible_collections.ansible.posix.plugins.callback import jsonl


class CallbackModule(jsonl.CallbackModule):
    CALLBACK_NAME = "aom_jsonl"

    def _find_result_task(self, host, task):
        """Find the task_result dict for a (host, task) pair.

        In lockstep mode (linear, debug), the active task is the last one
        appended to the current play.

        In non-lockstep mode (free, host_pinned, etc.), tasks are tracked per
        host in ``self._task_map``. If a task was never queued to a worker
        (e.g. conditional ``meta`` tasks such as ``flush_handlers`` executed
        inline via ``_execute_meta``), ``v2_runner_on_start`` was never
        invoked. In that case, falling back to ``results[-1]['tasks'][-1]``
        would either raise ``IndexError`` (if tasks is empty) or corrupt the
        unrelated prior task. Create and return a new task structure instead.
        """
        key = (host.get_name(), task._uuid)
        if key in self._task_map:
            return self._task_map[key]
        if self._is_lockstep and self.results and self.results[-1]["tasks"]:
            return self.results[-1]["tasks"][-1]
        task_result = self._new_task(task)
        if self.results:
            self.results[-1]["tasks"].append(task_result)
        return task_result

    def _record_task_result(self, event_name, on_info, result, **kwargs):
        """Record task result, preserve ignore_errors, and safely prune _task_map.

        Ansible calls ``v2_runner_on_failed(result, ignore_errors=...)``;
        the parent routes every runner hook through this method with the
        extra kwargs, but drops ``ignore_errors`` on the floor. Without it a
        task that failed under ``ignore_errors: true`` is indistinguishable
        on the wire from a real failure. Merge the flag into ``on_info`` so
        it lands at the top level of the host result (next to ``failed``),
        where AOM's state machine reads it to classify the task as tolerated.

        Furthermore, in non-lockstep strategies (free), tasks not queued
        through ``_queue_task`` (such as skipped ``meta`` tasks) never
        entered ``self._task_map``. Upstream ``ansible.posix.jsonl`` does
        ``del self._task_map[key]`` unconditionally when ``not self._is_lockstep``,
        crashing with ``KeyError`` and failing callback dispatch. We use
        ``self._task_map.pop(key, None)`` to safely clean up.
        """
        if kwargs.get("ignore_errors"):
            on_info = dict(on_info, ignore_errors=True)

        host = result._host
        task = result._task

        result_copy = result._result.copy()
        result_copy.update(on_info)
        result_copy["action"] = task.action

        task_result = self._find_result_task(host, task)

        end_time = jsonl.current_time()
        task_result["task"]["duration"]["end"] = end_time
        if self.results:
            self.results[-1]["play"]["duration"]["end"] = end_time

        task_result_copy = copy.deepcopy(task_result)
        task_result_copy["hosts"][host.name] = result_copy

        if not self._is_lockstep:
            key = (host.get_name(), task._uuid)
            self._task_map.pop(key, None)

        self._write_event(event_name, task_result_copy)

    def v2_runner_on_start(self, host, task):
        """Emit the per-host start event WITH the host's name.

        The parent emits ``{task, hosts: {}}`` — the starting host lives
        only in its internal ``_task_map``, never on the wire. AOM's
        state machine needs ``event["host"]`` to mark that host RUNNING;
        without it, non-lockstep strategies (free, mitogen_*) never get
        per-host running state and the tree degrades to a static
        all-targets view. Mirrors the parent's bookkeeping exactly, but
        writes an annotated copy of the envelope so the shared
        ``task_result`` dict (later deep-copied into terminal events)
        stays untouched.
        """
        if self._is_lockstep:
            return
        key = (host.get_name(), task._uuid)
        task_result = self._new_task(task)
        self._task_map[key] = task_result
        self.results[-1]["tasks"].append(task_result)
        self._write_event("v2_runner_on_start", {**task_result, "host": host.get_name()})

    def v2_runner_item_on_ok(self, result):
        self._emit_item("v2_runner_item_on_ok", result)

    def v2_runner_item_on_failed(self, result):
        self._emit_item("v2_runner_item_on_failed", result)

    def v2_runner_item_on_skipped(self, result):
        self._emit_item("v2_runner_item_on_skipped", result)

    def _emit_item(self, name, result):
        """Write one JSONL event for a single completed loop item.

        Mirrors the parent's ``_record_task_result`` minus the bits that
        only make sense at loop end: it does NOT delete the ``_task_map``
        entry (the loop is still running) and does NOT stamp a task
        ``duration.end`` (the parent's aggregate handler does that when
        the whole loop finishes).
        """
        host = result._host
        task = result._task
        item_result = result._result.copy()
        item_result["action"] = task.action
        task_result = self._find_result_task(host, task)
        envelope = {
            "task": task_result["task"],
            "hosts": {host.name: item_result},
        }
        self._write_event(name, envelope)

    def v2_runner_retry(self, result):
        host = result._host
        task = result._task
        res = result._result or {}
        retries = res.get("retries", 0)
        attempts = res.get("attempts", 0)
        retries_left = retries - attempts
        task_result = self._find_result_task(host, task)
        task_info = (
            task_result["task"]
            if task_result and "task" in task_result
            else {"id": getattr(task, "_uuid", ""), "name": getattr(task, "name", "")}
        )
        envelope = {
            "task": task_info,
            "host": host.get_name(),
            "retries": retries,
            "attempts": attempts,
            "retries_left": retries_left,
        }
        self._write_event("v2_runner_retry", envelope)

    def v2_runner_on_async_poll(self, result):
        host = result._host
        task = result._task
        res = result._result or {}
        attempts = res.get("attempts", 0)
        remaining = res.get("remaining")
        task_result = self._find_result_task(host, task)
        task_info = (
            task_result["task"]
            if task_result and "task" in task_result
            else {"id": getattr(task, "_uuid", ""), "name": getattr(task, "name", "")}
        )
        envelope = {
            "task": task_info,
            "host": host.get_name(),
            "attempts": attempts,
            "remaining": remaining,
            "ansible_job_id": res.get("ansible_job_id"),
        }
        self._write_event("v2_runner_on_async_poll", envelope)
