# Command Not Found Test (Exit Code 127)

This test verifies ansible-aom behavior when ansible-playbook is not found.

## Test Procedure
1. Temporarily remove ansible-playbook from PATH:
   ```bash
   sudo mv /usr/bin/ansible-playbook /usr/bin/ansible-playbook.bak
   ```
2. Run: `aom 01-single-task-success/site.yml -i ../inventory.ini`
3. Expected: Exit code 127, RunState transitions to CRASHED
4. Restore: `sudo mv /usr/bin/ansible-playbook.bak /usr/bin/ansible-playbook`

## Expected Behavior
- App detects exit code 127
- RunState.status → CRASHED
- Error message displayed to user