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

from ansible_collections.ansible.posix.plugins.callback import jsonl


class CallbackModule(jsonl.CallbackModule):
    CALLBACK_NAME = "aom_jsonl"

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
