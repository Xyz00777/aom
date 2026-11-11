# Focused correctness and mutation review

This session reviewed core parsing/inspect behavior and session storage,
history lookup, and replay. Findings below were reproduced against the local
checkout before fixes. This was a scoped review, not a whole-program proof.

## Fixed findings

| Finding | Effect | Regression coverage |
|---|---|---|
| Historical JSONL values assumed to be objects; invalid UTF-8 decoded outside per-line recovery | An old recording could prevent a new live run from starting | `test_history_preserves_valid_events_around_malformed_lines`: preserve exact task profile, variable totals and loop counts around corrupt lines |
| Metadata readers assumed valid JSON meant a metadata object | Session discovery/loading/cleanup crashed on arrays, scalars or null; browsing/loading also crashed on invalid UTF-8 | `test_malformed_metadata_does_not_break_session_readers`: healthy neighbor remains discoverable, events remain readable, cleanup succeeds |
| Replay passed `latest` and prefixes directly to the exact-ID loader | Documented CLI selectors failed | CLI tests replay actual event payloads, reject ambiguous prefixes, and retain exact-ID recovery without metadata |
| Loop labels selected by truthiness | `0` and `False` disappeared; explicit empty/falsy labels lost precedence | Live log and inspect detail assertions use distinct label/fallback values |
| Incomplete JSON chunks were stripped before buffering | Spaces within string payloads disappeared | Exact round trip at every two-chunk split and with one-character chunks |
| ANSI summary test inherited `NO_COLOR` | A valid caller environment caused a false test failure | Color test explicitly removes that environment variable |

## Architectural map and invariants

- Live startup calls `session.history.find_previous_run` before spawning
  Ansible. Its two event miners now read bytes and reject invalid lines
  individually. Valid neighboring events still contribute to the prior.
- `session.store` owns disk reads and ID discovery. Rerun's existing resolver
  moved here so replay can reuse it. Exact replay directories still load
  without metadata; prefixes must be unique. These paths have CLI regressions.
- `core.text.loop_item_label` owns pure label selection for compact output and
  inspect. Renderer-specific escaping and async-poll formatting remain with
  their existing consumers. Both consumers have falsy-value regressions.
- `core.parser.JsonLineStream` keeps raw incomplete chunks and parses their
  combined representation. Existing carry overflow/recovery tests still apply.
- No event storage format, index schema, or dependency changes. No migration
  or rollback work is required. `events.jsonl` remains immutable.

## Mutation pilot

Triplum's `docs/plans/mutation-pilot.md` informed the approach: narrow the
scope, use nondegenerate fixtures and independent expected values, confirm
survivors against the full suite, and distinguish assertion failures from
exceptions. The Triplum measurements were read, not rerun here.

The pilot copied source, selected tests and required fixtures into `/tmp`,
verified `ansible_aom.__file__` pointed into that copy, and applied each
mutation separately. Each invocation used `pytest -n 0 --no-cov`; no nested
worker pools or mutation framework dependency was added. The focused baseline
was **295 passed**; excluding this session's regressions gave **262 passed**.

| Mutation | Existing focused tests | With regression tests |
|---|---|---|
| Buffer stripped rather than raw JSON chunk | survived | assertion failure |
| Drop falsy loop labels | survived | assertion failure |
| Ignore explicit loop label | survived | assertion failure |
| Remove loop-history object guard | survived | runtime exception |
| Remove duration-history object guard | survived | runtime exception |
| Stop catching loop-history UTF-8 errors | survived | runtime exception |
| Stop catching duration-history UTF-8 errors | survived | runtime exception |
| Remove session-list metadata object guard | survived | runtime exception |
| Remove metadata-loader object guard | survived | runtime exception |
| Remove history metadata object guard | survived | runtime exception |
| Pass unresolved replay selector to driver | survived | assertion failure |
| Drop actual variable duration from progress copy | survived | caught by existing ETA integration test |
| Change ETA warmup comparison from `<` to `<=` | survived | assertion failure after adding threshold test |

The seven runtime exceptions above are relevant resilience regressions, but
are not evidence of stronger numerical/output assertions. No collection error
or timeout was counted as a successful detection. This deliberately selected
sample is not a project-wide mutation score.

The progress-copy candidate was already covered by
`tests/integration/test_renderer_eta.py::test_fixed_floor_not_scaled_by_fast_variable_task`.
A separate baseline/mutant run confirmed that assertion fails; no duplicate test
was added. The genuine threshold gap now has a three-case test immediately
below, at, and above 10% completed work. A separate baseline/mutant run confirms
that only the changed comparison breaks it.

Full-suite confirmation in the copied-source environment was attempted too.
That environment had a failing rerun round-trip test with and without the
warmup mutation, so it was not a clean full-suite survival result. An initial
hook-fixture failure was traced to omitting the virtualenv from `PATH` and
removed from the experiment. The copied-source rerun failure remains
unexplained; it was not counted as a mutation detection. The real-checkout
full suite passed separately.

The focused experiment took roughly one second per invocation. Prefer selected
tests first, then add the real consumers before calling a survivor a coverage
gap. This session does not add a mutation runner or CI score gate.

## Follow-ups and limits

- Aggregate inspect detail was fixed in the second pass below. The TUI's
  separately tested first-host navigation default was preserved.
- Repeated task starts across serial batches need a clarified duration
  aggregation contract before changing behavior.
- Field-level malformed values inside otherwise valid event/metadata objects
  remain outside this patch's shape/encoding fixes.
- Independent fresh-context reviewers checked both areas and the final fixes.
  Claude `claude-opus-5-5` returned revoked-OAuth errors in both sandbox and host
  retries; it supplied no review conclusion or falsification evidence.
- The documented `.sisyphus/notepads/` and graphify graph are absent in this
  checkout; the `graphify` executable is also unavailable.

Useful upstream guidance: [Cosmic Ray tutorial](https://cosmic-ray.readthedocs.io/en/latest/tutorials/intro/index.html)
requires a working baseline; [Google's mutation-testing account](https://testing.googleblog.com/2021/04/mutation-testing.html)
describes filtering low-value mutations and focusing feedback. No tooling
compatibility claim is needed for this explicit-mutation pilot.

## Verification

Observed in the real checkout: **3,472 passed, 7 skipped, 3 xfailed,
1 xpassed**; total statement coverage **91.19%**. Ruff and mypy passed.
The expected-failure/pass categories were also present before these changes.
The test run used the README-required `ansible.posix` collection installed
under `/tmp/aom-review-collections`:

```sh
ANSIBLE_COLLECTIONS_PATH=/tmp/aom-review-collections \
PYTHONPATH=/tmp/aom-review-collections \
uv run pytest tests/ -q --cov=src/ansible_aom --cov-report=term
```

No CI run or PR is part of this local review session.


## Second pass: inspect behavior and index paths

Two additional defects were reproduced with failing regression tests, then fixed:

- Aggregate detail now chooses the first failed direct host, falling back to
  the first direct host. Explicit host selection wins. The shared pure selector
  runs before indexed event hydration, so aggregate detail fetches the selected
  host's payload rather than displaying a later healthy result. Task-highlight
  navigation keeps its existing first-host contract.
- All five SQLite read connections now convert filesystem paths into escaped
  file URIs. State directories containing `#`, `?`, or encoded-looking `%2F`
  text work with both absolute and relative paths. Read-only access remains
  `mode=ro`; no index schema, stored events, or rebuild policy changes.

The fixture design matters: two failed hosts have different messages, the
final result belongs to a healthy host, explicit healthy selections are tested,
and a nested task precedes two distinct healthy hosts in the fallback case.
The indexed TUI test reorders real fixture events so hydrating the task's last
result produces the wrong message. Each index reader has its own assertions:
counts, exact event payload, exact task ID, or exact scoped verbose lines.

An independent reviewer noticed that the original fallback fixture had only
one healthy host. Its disposition was **added verification**: a second healthy
host now distinguishes first-host from last-host selection. The navigation
contract finding **changed the decision**: task highlighting was preserved.
The index reviewer found no further defects in the fix.

A separate scratch-copy experiment verified a **14-test baseline** and ten
semantic mutations, one at a time. Every mutation produced an assertion
failure; none relied on collection errors, crashes, or timeouts:

- Remove URI escaping at each of the five read connections independently.
- Choose the last healthy host instead of the first.
- Ignore failed-host preference, or choose the last failed host.
- Override an explicitly selected healthy host.
- Hydrate the task's last result instead of the selected failed host.

Observed full-suite result: **3,504 passed, 7 skipped, 3 xfailed, 1 xpassed**.
Ruff and mypy pass. No coverage target or mutation-score gate was added.
The test-quality preference is recorded in `AGENTS.md`.

Deferred: malformed numeric values inside an otherwise readable disposable
index can escape its fallback handling. Repeated serial task starts can also
produce negative durations in interrupted recordings; choosing summed, latest,
or elapsed-span durations needs a separate contract decision and cached-index
invalidation. These were not folded into the two focused fixes.

Filename handling follows [SQLite's URI rules](https://www.sqlite.org/uri.html)
and [Path.as_uri](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.as_uri).
