"""Ansible infrastructure: subprocess, pexpect, JSONL callback wiring.

Contains the live ``ansible-playbook`` runner and the parallel
preflight (``--list-tasks`` + ``--list-hosts``) orchestrator. See
``ARCHITECTURE.md §3``.
"""
