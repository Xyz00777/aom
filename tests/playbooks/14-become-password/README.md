# Become Password Prompt Test

This playbook tests detection of privilege escalation (become) password prompts.

## Running

Run the playbook with become password prompt:

```bash
aom site.yml -i ../inventory.ini --ask-become-pass
```

Expected prompt: `BECOME password:`

## Variant: Defaults to SSH Password

When both SSH password and become password are requested, Ansible may
default the become password to the SSH password:

```bash
aom site.yml -i ../inventory.ini --ask-pass --ask-become-pass
```

Expected prompt: `BECOME password[defaults to SSH password]:`

## Purpose

Tests that ansible-aom can detect and respond to become/sudo password
prompts during playbook execution.