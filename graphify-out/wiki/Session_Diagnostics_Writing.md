# Session Diagnostics Writing

> 19 nodes · cohesion 0.14

## Key Concepts

- **_FakeSpawn** (9 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **_patch_runner_with_fake_spawn()** (6 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **test_runner_searchwindowsize.py** (5 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **test_runner_searchwindow_covers_longest_pattern()** (5 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **test_runner_sets_explicit_searchwindowsize()** (5 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **Any** (3 connections)
- **MonkeyPatch** (3 connections)
- **.expect()** (2 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **.__init__()** (2 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **.close()** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **.isalive()** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **.read_nonblocking()** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **.sendintr()** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **.sendline()** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **R9 — searchwindowsize bound on pexpect.spawn().  R9 spec: pexpect's ``searchwind** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **R9: searchwindowsize must exceed every pattern the runner uses.      The runner'** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **Stand-in for pexpect.spawn() with the kwargs the runner passes.** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **Capture every kwarg passed to pexpect.spawn() inside the runner.** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`
- **R9: the runner must pass an integer ``searchwindowsize`` to pexpect.      With `** (1 connections) — `tests/unit/test_runner_searchwindowsize.py`

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (2 shared connections)

## Source Files

- `tests/unit/test_runner_searchwindowsize.py`

## Audit Trail

- EXTRACTED: 48 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*