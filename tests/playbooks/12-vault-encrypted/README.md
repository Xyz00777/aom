# Vault-Encrypted Playbook Test

This playbook tests detection of vault password prompts.

## Setup

1. Encrypt the secrets file:
   ```bash
   ansible-vault encrypt vars/secrets.yml --ask-vault-pass
   ```
   Enter password: `testvault`

2. Or use vault-id variant:
   ```bash
   ansible-vault encrypt vars/secrets.yml --vault-id dev@prompt
   ```

## Running

Run the playbook with vault password prompt:

```bash
aom site.yml -i ../inventory.ini --ask-vault-pass
```

Expected prompt: `Vault password:`

For vault-id variant:

```bash
aom site.yml -i ../inventory.ini --vault-id dev@prompt
```

Expected prompt: `Vault password (dev):`

## Purpose

Tests that ansible-aom can detect and respond to vault password prompts
during playbook execution.