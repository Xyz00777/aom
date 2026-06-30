"""Session artifact storage and post-mortem summaries.

* :mod:`ansible_aom.session.store` — file I/O: SessionManager, the
  ``.aom`` artifact format, listing and pruning.
* :mod:`ansible_aom.session.summary` — pure post-mortem projections of
  a loaded session dict (failed/unreachable/changed host collectors,
  display summaries).

See ``ARCHITECTURE.md §3``.
"""
