"""EventSource adapters: producers of run events for a Renderer.

See ``ARCHITECTURE.md §4.2`` for the protocol contract and the layer
map. The two production drivers are:

* :class:`ansible_aom.drivers.live.LiveDriver` — spawns
  ``ansible-playbook`` and pumps its JSONL output.
* :class:`ansible_aom.drivers.replay.ReplayDriver` — re-emits a
  previously recorded session through the same Renderer surface.
"""
