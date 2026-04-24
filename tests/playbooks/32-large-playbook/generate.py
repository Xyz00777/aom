#!/usr/bin/env python3
"""Generate a large playbook for memory bounds testing."""

plays = 50
tasks_per_play = 200

print("---")
for p in range(plays):
    print(f"- name: Play {p}")
    print("  hosts: webservers")
    print("  gather_facts: false")
    print("  tasks:")
    for t in range(tasks_per_play):
        print(f"    - name: Task {p}-{t}")
        print("      ansible.builtin.debug:")
        print(f'        msg: "play {p} task {t}"')
