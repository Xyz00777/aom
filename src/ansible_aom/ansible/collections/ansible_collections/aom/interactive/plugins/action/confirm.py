# GNU General Public License v3.0-or-later
"""Per-host confirmation action plugin.

Deliberately does NOT set BYPASS_HOST_LOOP, so ansible runs it once per host with
that host's templated args. Communicates with the AOM monitor via the control
directory named in ``AOM_PROMPT_CONTROL_DIR``: write an ``<id>.req`` JSON file,
block reading ``<id>.fifo`` for the answer. With no AOM (env var absent), fall back
to reading the controller's stdin.

Answer semantics: empty / yes / anything not in the abort set -> continue this
host; ``no`` / ``n`` / ``abort`` / ``cancel`` -> fail this host only.
"""

from __future__ import annotations

import json
import os
import time
import uuid

from ansible.plugins.action import ActionBase

_ABORT_WORDS = {"n", "no", "abort", "cancel"}
_ENV_VAR = "AOM_PROMPT_CONTROL_DIR"
_REQUEST_SUFFIX = ".req"
_FIFO_SUFFIX = ".fifo"


class ActionModule(ActionBase):
    # NOTE: intentionally no `BYPASS_HOST_LOOP = True` — that's the whole point.

    def run(self, tmp=None, task_vars=None):
        super_result = super().run(tmp, task_vars)
        del tmp  # unused
        prompt = self._task.args.get("prompt") or "Continue? "
        host = (task_vars or {}).get("inventory_hostname", "?")

        answer = self._collect_answer(prompt, host)

        result = dict(super_result)
        if answer.strip().lower() in _ABORT_WORDS:
            result.update(failed=True, msg="aborted by operator")
        else:
            result.update(changed=False, msg="confirmed")
        return result

    def _collect_answer(self, prompt, host):
        ctrl = os.environ.get(_ENV_VAR)
        if ctrl:
            try:
                return self._answer_via_channel(ctrl, prompt, host)
            except OSError:
                # Channel broke mid-handshake — fail open (continue) rather than
                # wedge the host forever.
                return ""
        return self._answer_via_stdin(prompt)

    def _answer_via_channel(self, ctrl, prompt, host):
        rid = uuid.uuid4().hex
        fifo = os.path.join(ctrl, rid + _FIFO_SUFFIX)
        os.mkfifo(fifo)
        try:
            payload = {"id": rid, "host": host, "prompt": prompt, "created": time.time()}
            tmp = os.path.join(ctrl, rid + _REQUEST_SUFFIX + ".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(payload))
            os.rename(tmp, os.path.join(ctrl, rid + _REQUEST_SUFFIX))
            # Blocks until AOM opens the FIFO for writing and sends the answer.
            with open(fifo, encoding="utf-8") as fh:
                return fh.readline().rstrip("\n")
        finally:
            try:
                os.unlink(fifo)
            except OSError:
                pass

    def _answer_via_stdin(self, prompt):
        # Bare run (no AOM): behave like pause. Clean under serial: 1.
        try:
            import sys

            sys.stdout.write(prompt)
            sys.stdout.flush()
            return sys.stdin.readline().rstrip("\n")
        except (EOFError, OSError):
            return ""
