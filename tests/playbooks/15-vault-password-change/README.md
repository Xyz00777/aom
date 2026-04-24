# Vault Password Change Test

This tests detection of vault password change prompts (rekey operation).

## Operations

These are ansible-vault CLI operations, not ansible-playbook:

### Encrypt a File

```bash
ansible-vault encrypt some-file --ask-vault-pass
```

Prompts for: `New Vault password:`, then `Confirm New Vault password:`

### Re-key an Encrypted File

```bash
ansible-vault rekey some-file
```

Prompts for:
1. `Vault password:` (current password)
2. `New Vault password:`
3. `Confirm New Vault password:`

## Purpose

Tests that ansible-aom can detect vault password change prompts if they
appear during playbook execution. While typically run via ansible-vault CLI,
the prompt detection may be needed if vault operations occur during playbooks.

## Note

No playbook file is needed for this test - these are CLI operations.
The application should be able to detect these prompt patterns if they
appear in PTY output.