# GNU General Public License v3.0-or-later
DOCUMENTATION = r"""
---
module: confirm
short_description: Per-host interactive confirmation (AOM-aware)
description:
  - Prompts once per host (does not bypass the host loop). Under the AOM monitor,
    the prompt is shown by AOM and the answer routed back over a control channel.
    Run without AOM, it falls back to reading the controller's stdin like
    ansible.builtin.pause.
options:
  prompt:
    description: Prompt text shown to the operator (templated per host).
    type: str
    required: false
author:
  - AOM
"""

EXAMPLES = r"""
- name: Confirm deployment per host
  aom.interactive.confirm:
    prompt: "Deploy to {{ inventory_hostname }}? "
"""

RETURN = r""" # """
