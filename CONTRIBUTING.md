# Contributing to AOM

AOM is in active development. Contributions that improve correctness,
documentation, tests, or the user experience are welcome.

## Before You Start

Read [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), and the
relevant part of [SPECIFICATION.md](SPECIFICATION.md). For a bug or feature
proposal, first check the [issue tracker](https://github.com/Xyz00777/aom/issues).

## Development Workflow

1. Set up the project with `uv sync --all-extras`.
2. Add or update a focused test before changing behavior.
3. Run `uv run pytest tests/ -q`, `uv run ruff check`, and
   `uv run mypy src/ansible_aom` before submitting work.
4. Keep changes scoped, document user-facing behavior, and preserve the
   core-to-infrastructure dependency direction described in `ARCHITECTURE.md`.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report security
issues using the process in [SECURITY.md](SECURITY.md), not the public tracker.
