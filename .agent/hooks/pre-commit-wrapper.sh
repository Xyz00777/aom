#!/usr/bin/env bash
# Wrapper to invoke pre-commit from a custom git hooks path.
# Installed by the shell hook when global core.hooksPath is set to a
# non-default location; pre-commit itself cannot target a custom path.
exec pre-commit run --hook-stage pre-commit "$@"