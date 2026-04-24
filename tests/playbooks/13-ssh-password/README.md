# SSH Password Prompt Test

This playbook tests detection of SSH password prompts.

## Running

Run the playbook with SSH password prompt:

```bash
aom site.yml -i ../inventory.ini --ask-pass
```

Expected prompt: `SSH password:`

## Notes

- This requires an SSH server configuration that prompts for password
- For unit tests, PTY stream fixtures provide the prompt string directly
- The inventory hosts (web1, web2, web3) are configured as local connections,
  so this test is primarily for verifying prompt detection logic

## Purpose

Tests that ansible-aom can detect and respond to SSH password prompts
during playbook execution.