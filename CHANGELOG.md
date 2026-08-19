# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `aom inspect --changes`: Non-interactive CLI report of all tasks that reported `changed: true` during a session, including role, file/line number (`path:line`), action module, executed command (`cmd`), message, stdout/stderr, and changed loop items.
- `aom inspect --changes --diff`: Option to display module before/after diffs for changed tasks to assist with playbook idempotency debugging.
- `aom inspect --warnings`: Non-interactive CLI report of all warnings and deprecations emitted during the session, with source file/line and host context.
- `--json` support for `aom inspect --changes` and `aom inspect --warnings` for programmatic inspection and CI integration.
- `--host`, `--play`, and `--task` filters for `aom inspect --changes` and `aom inspect --warnings`.
