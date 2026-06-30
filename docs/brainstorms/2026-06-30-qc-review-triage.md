# QC Review Triage: grill-me on the 20 grumpi-qa findings
Date: 2026-06-30 · Goal: Stress-test each of the 20 QC findings in
`docs/brainstorms/2026-06-29-verbosity-handling.md` (the `# QC REVIEW (grumpi-qa) — 2026-06-30`
section, lines 1031–1180), decide which to act on, in what order, and how —
before any code work begins. The QC review itself stays in the brainstorm
doc; this file is the action log.

## Summary / key decisions

**Triage complete. All 20 QC findings triaged in priority order
(Critical → High → Medium → Low). Every decision is recorded below in the
Q&A log. The user was deliberate: took the cheapest option (or "leave
as-is") more often than the most thorough.**

**Decisions at a glance (1 = most aggressive fix, 3 = leave as-is):**

| Finding | Severity | Decision | Option | Notes |
|---|---|---|---|---|
| QC-002 | Critical | 2/3 | A (ansible-core seed) | Hardened redaction; red-team fixture |
| QC-001 | High | 1/3 | A (sweep & pointer) | Mechanical pass; no new content |
| QC-003 | High | 2/3 | B (confirm prompt) | `--no-redact` + `--yes` global |
| QC-004 | High | 1/3 | A (add `_schema_version: 2`) | Overturns Q9=B; logged as scope change |
| QC-005 | High | 3/3 | C (stay Q10=B) | Document harder in README |
| QC-006 | Medium | 1/3 | A (document path-vs-value) | 1-paragraph rationale, no code |
| QC-007 | Medium | 1/3 | A (rename + clarify) | "Precedence" → "Layers" |
| QC-008 | Medium | 1/3 | A (footer focus indicator) | + transient `V` flash |
| QC-009 | Medium | 1/3 | A (all four tests in v1) | ~260 LOC, ~40s CI |
| QC-010 | Medium | 1/3 | A (1-line `aom_` rule) | §5.6 spec edit |
| QC-011 | Medium | 1/3 | A (sub-case of QC-001) | Two checkboxes + pointer |
| QC-012 | Medium | 1/3 | A (verify all anchors + script) | `scripts/verify_anchors.py` |
| QC-013 | Medium | 2/3 | B (compress inline) | No new file |
| QC-014 | Medium | 3/3 | C (leave §17 as-is) | Honest about deferral |
| QC-015 | Low | 3/3 | C (leave implicit) | Owners live in tracker |
| QC-016 | Low | 3/3 | C (1 file + ToC) | No file split |
| QC-017 | Low | 1/3 | A (standardize ranges) | Bundled with QC-012 |
| QC-018 | Low | 3/3 (with 1-line note) | C + cheap disclaimer | "Illustrative, not exhaustive" |
| QC-019 | Low | 3/3 | C (intentional ambiguity) | v2 decides |
| QC-020 | Low | 3/3 | C (working artifact framing) | v1 honest about itself |

**Pattern across the 20 decisions:** the user is comfortable shipping v1
as a working artifact. The QC's "more thorough" options were taken where
they fixed a real correctness/security risk (QC-002, QC-004, QC-009) or
where they were near-free (QC-007, QC-010, QC-011). The QC's "document
harder" / "leave as-is" options were taken where the doc was already
honest about its own gaps (QC-014, QC-015, QC-019, QC-020).

**Net work for v1 pre-implementation:**
- Doc edits to the design doc: ~12 (QC-001, QC-006, QC-007, QC-010, QC-011, QC-012, QC-013, QC-014 cross-ref, QC-016 ToC, QC-017, QC-018 disclaimer, Q4 of Q9=B override)
- README additions: 1 "Disk usage" section (QC-005)
- New code/test files: 5 (1 fixture `redaction_bypass`, 4 new tests in QC-009, 1 script `verify_anchors.py`, 1 global `--yes` flag in `cli.py`)
- New behavior: `meta.json` gets `_schema_version: 2` (QC-004); `--no-redact` requires `--yes` in non-TTY (QC-003); TUI footer focus indicator (QC-008); `aom_verbose_line` policy rule (QC-010)

**Total estimated effort:** ~1.5 days of pre-implementation work before
any feature code is written. Compared to the QC's "2-3 days" estimate
for the full review, the user's pattern shaved ~1 day by deferring
QC-005, QC-014, QC-015, QC-016, QC-018, QC-019, QC-020.

## Question Backlog (Pending)

*(All 20 findings triaged. Backlog is now closed. New items go to
"Open flags" below.)*

### Meta
- [done] M1. Overall scope: process all 20, not just Critical+High.

### Critical
- [done] QC-002 — redaction deny-list bypass → Q2: A (ansible-core seed)

### High
- [done] QC-001 — backlog / locked-in contradictions → Q3: A (sweep & pointer)
- [done] QC-003 — `--no-redact` is theatre → Q4: B (confirm prompt)
- [done] QC-004 — schema version missing → Q5: A (add `_schema_version: 2`)
- [done] QC-005 — no size caps is a DoS vector → Q6: C (stay Q10=B, document)

### Medium
- [done] QC-006 — config precedence env-vs-`--config` → Q7: A (document)
- [done] QC-007 — redaction layer naming → Q8: A (rename + clarify)
- [done] QC-008 — TUI focus indicator for `V` keybind → Q9: A (footer indicator)
- [done] QC-009 — missing fuzz / crash-recovery / schema-boundary / concurrency tests → Q10: A (all four in v1)
- [done] QC-010 — `aom_` prefix policy for synthetic events → Q11: A (1-line rule)
- [done] QC-011 — backlog checkboxes use only `[ ]`, not `[x]` → Q12: A (sub-case of QC-001)
- [done] QC-012 — stale anchor `core/redaction.py:280-283` → Q13: A (verify all + script)
- [done] QC-013 — sub-Q4.1 audit content in Q&A log → Q14: B (compress inline)
- [done] QC-014 — risk mitigations are shrugs → Q15: C (leave §17)
- [done] QC-015 — no "Owner" column on doc checklist / test plan → Q16: C (leave implicit)
- [done] QC-016 — split the 1180-line file → Q17: C (1 file + ToC)
- [done] QC-018 — `verbose` block schema is misleadingly curated → Q18: C (with 1-line disclaimer)

### Low
- [done] QC-017 — `cli.py:200` vs `cli.py:200-203` citation style → Q19: A (standardize ranges)
- [done] QC-019 — rollout plan has no measurement plan for the default-flip → Q20: C (intentional ambiguity)
- [done] QC-020 — "Running synthesis" header is a journal, not a spec → Q21: C (working artifact framing)

## Q&A log

### Q1 — Overall scope of the QC triage
- Asked: Accept all 20, accept only Critical+High, reject, or pick a subset?
- Captured: User picked "go through all his findings" — process every QC finding, not just the Critical+High subset. The default mode is now: process all 20 in priority order (Critical → High → Medium → Low), but each one is its own decision; user can defer or reject any individual finding.
- Flags: none.

### Q2 — QC-002 (Critical): redaction deny-list hardening
- Asked: A (ansible-core seed), B (keys-only, never values), or C (fully layered, my rec)?
- Captured: User picked **A — use ansible-core's own deny-list / `is_invocable` / `_NO_LOG_REGEX` patterns as a starting point. Add exact-match keys for the AOM list (`password`, `vault_password`, `api_key`, `private_key`, `token`, `secret`, `passwd`, `ssh_pass`) AND a separate per-pattern regex layer that the user can extend. Add a red-team fixture (~30 keys: real secrets + look-alikes) proving both directions.**
- Implications:
  - `core/redaction.py` Layer 4 (cited at line 280–283 in design doc, real range needs verification — see QC-012) gets a `~50 LOC` rewrite: exact-match table + per-pattern regex; user-config layer is additive.
  - New test fixture `tests/fixtures/redaction_bypass.jsonl` (or `.yaml`) with cases like:
    - SHOULD redact: `password: "hunter2"`, `vault_password: …`, `api_key: "sk-…"`, `private_key: …`, `token: "ghp_…"`, `secret_access_key: …`, `db_password: …`, `auth_token: …`, `client_secret: …`
    - SHOULD NOT redact: `secretary: "Alice"`, `tokenized_data: true`, `tokens: [a,b,c]`, `secrets_yaml_path: "/etc/x.yaml"`, `data: "<base64 JWT>"`, `payload: "…"`, `tokener: "…"`, `token_endpoint: "https://…"`, `description: "…"`, `secrets_manager: "aws"`
  - Drop the current "value-substring" recursion (e.g., `*_PASSWORD` on values) — that was the bypass class QC-002 flagged. Recurse into dicts/lists by **key**, not by value.
  - The user-config layer (Q7 of original design, `[redaction] ignored_arguments`, `ignored_value_patterns`) needs re-scoping: regex on **keys only** by default, regex on values only behind an explicit `[redaction] regex_on_values: true` opt-in (which is itself a footgun — note in the docs).
  - Update the design doc §6 (lines 287–315): rephrase "Precedence order" to "Redaction layers" (also covers QC-007), and add the 1-line rule: "values are redacted only when the env-var name matches, not the value substring".
- Flags:
  - Need to verify the exact `is_invocable` / `_NO_LOG_REGEX` semantics from ansible-core 2.20 source before lifting patterns verbatim. Owner: <user> or research task. Action: add to open flags.
- Stage-2 of the cleanup plan (lines 1135–1139) already covers this; resolved by this Q.

### Q3 — QC-001 (High): Question Backlog vs. "Locked-in" contradictions
- Asked: A (sweep & pointer), B (rename "Provisional"), or C (split into Resolved/Unresolved)?
- Captured: User picked **A — sweep every `[ ]` in the backlog; for each, either check the box and add a `→ §N line M` pointer to where the answer lives, OR move it to a new `## Open flags (genuinely unresolved)` section with a reason. End state: the "Locked-in" header is no longer a lie.**
- Implications:
  - Mechanically walk lines 51–110. The 21 still-unchecked questions (Q3, Q4, Q6, Q7, Q9, Q10, Q11, Q12, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40, Q41, Q42, Q43) all have answers somewhere in the implementation plan (§1–§17) or the Q&A log. Map each to its answer location.
  - The 5 already-`[x]` ones (Q1, Q2, Q5, Q8, Q25) are correctly resolved.
  - Open flags section at the bottom: any question that *truly* has no answer in the doc gets moved there with a one-line "needs answer" note. My quick read: Q21 (`--check`/`--diff` UI), Q22 (large results / setup megabytes — partially answered by §9, but the truncation question is still open), Q23 (live streaming inspect — answered "yes" in §10, just not pointer-closed), Q32 (TUI rendering perf for full stdout/stderr — actually unanswered). Those four may genuinely be open flags.
  - Lines 26, 490, 611 stay as-is once the backlog is honest. No need to soften "Locked-in" or "no open sign-off items".
  - Cost: ~30 min mechanical pass; no new content.
- Flags:
  - The 4 candidates above (Q21, Q22, Q23, Q32) need a real decision. Surface to user at the end of the sweep. **Logged in "Open flags" below.**
- Stage-1 of cleanup plan (lines 1129–1133) already covers this; resolved by this Q.

### Q4 — QC-003 (High): `--no-redact` control strategy
- Asked: A (refuse dangerous combo), B (confirm prompt), or C (loud log to `secrets-raw.jsonl`)?
- Captured: User picked **B — `--no-redact` triggers an interactive y/N prompt unless `--yes` is also set.**
- Implications:
  - Acknowledged UX cost: breaks in CI / non-interactive shells. That's the point — `--no-redact` in CI is exactly the case the QC flagged as dangerous, and forcing a confirmation makes the user think twice.
  - Implementation in `cli.py`: when `--no-redact` is set and stdin is a TTY, prompt `WARNING: --no-redact writes unredacted secrets to <session_dir>/events.jsonl. Continue? [y/N]`. Non-TTY (no `/dev/tty`) without `--yes` → refuse with exit code 2.
  - The `--yes` flag becomes a global (currently doesn't exist) — or a `--no-redact-yes` companion. Trade-off: a global `--yes` is broader and matches `apt-get -y`, `pip --yes`. Recommend adding `--yes` as a global flag in §11.
  - Banner text needs the session dir in the prompt so the user can verify it's a path they trust (e.g., `/tmp/aom-test/` vs `~/.local/state/aom/sessions/<uuid>/`).
  - Add a TUI test: in non-interactive mode, `--no-redact --yes` succeeds; `--no-redact` alone refuses with exit 2.
  - The CI test path: someone running `aom --no-redact site.yml` in a script will hit the refusal, which is the desired outcome (forces them to either add `--yes` or reconsider).
- Flags:
  - Confirm `--yes` doesn't already exist as a flag. Need a `grep` on `cli.py`. Add to verification list at end.
  - Confirm `tty` detection module in use (probably `sys.stdin.isatty()` plus a check for `AOM_NO_INTERACTIVE` env var for scripted override).
- Stage-2 of cleanup plan (lines 1135–1139) already covers this; resolved by this Q.

### Q5 — QC-004 (High): schema version missing (overturn Q9=B)
- Asked: A (add `_schema_version: 2` to meta.json), B (document the absence, ship as-is), or C (per-event version field)?
- Captured: User picked **A — add `_schema_version` field to `meta.json` anyway. Old sessions get auto-promoted to `_schema_version: 1` on first read.**
- Implications:
  - **Q9=B (no version bump) is overturned.** Logged as a deliberate scope change, not a quiet flip. Update the design doc at line 736 ("Q9 — Schema versioning") to record the override and the reason (QC-004: future-proofing is one line; cost of NOT having it is a maintenance landmine).
  - `meta.json` writer: add `_schema_version: 2` next to existing `aom_version`. Existing field-absence tolerance is unchanged; this is purely additive.
  - `meta.json` reader: when loading, if `_schema_version` is missing, treat as `1`. This is the auto-promotion path — old AOM v1 sessions recorded without the field still work, but get stamped as v1 on first read.
  - **The "no schema version" defense of forward compat via field-absence still applies to `events.jsonl` lines.** The version field lives only in `meta.json`. So the cost is bounded: one file, one field, two code paths (write / read with default).
  - The version value `2` is the new "any session that has the `verbose` block schema" version. The version value `1` is "any session recorded before this feature". A future v3 (e.g., a different event-type change) would bump again.
  - The version increment is for `meta.json` only. **`events.jsonl` still relies on field-absence tolerance.** This is a deliberate choice — bumping `_schema_version` does not require touching every line of `events.jsonl`.
  - The QC's broader point (third-party readers, jq pipelines, replay) is partially addressed. Third-party tools that read `meta.json` get the explicit version. Third-party tools that read only `events.jsonl` still rely on field-absence tolerance (which is what the original Q9=B was protecting).
- Flags:
  - Document the override of Q9=B explicitly in the design doc (line 736) and in the Q&A log. Otherwise the override will be invisible to future readers.
- Stage-3 of cleanup plan (lines 1141–1145) already covers this; resolved by this Q.

### Q6 — QC-005 (High): size cap policy
- Asked: A (soft cap with `[TRUNCATED]` marker at 100MB), B (warn-only, no truncate), or C (stay Q10=B, document harder)?
- Captured: User picked **C — keep Q10=B (no caps, trust the user), document the disk-usage implications harder in the README.**
- Implications:
  - **Q10=B stands.** No code change to the writer. The QC's complaint is acknowledged but rejected: the design is consistent in trusting the user, and the cost of the surprise (a 100MB session) is recoverable via `aom inspect prune --days N`.
  - Documentation must explicitly include:
    - A "Disk usage" section in the README near the `--capture-verbose` flag. Worked example: "200-host run with `--capture-verbose --capture-setup` produces ~50MB. 100 sessions ≈ 5GB."
    - A pointer to `aom inspect prune --days N` for cleanup.
    - A note that `--capture-setup` (the `ansible_facts` opt-in) is the single largest contributor, and is the user's first knob if disk is constrained.
  - The `--max-session-size` flag is **not** added in v1. Defer to v2 if a real user reports a disk-full incident.
  - The risk in §17 (lines 482–488) currently says "Disk usage ... AOM does not impose any size limits". This is honest and stays.
- Flags:
  - The `aom inspect prune` command must already exist and be tested. Verify with a `grep` on `inspect/cli.py`. If it doesn't exist, that's a separate gap that the doc has been claiming.
  - If a v1 user hits a real disk-full scenario, document a recipe in the troubleshooting section (e.g., "find / -name 'events.jsonl' -size +100M" or "aom inspect prune --days 7 --dry-run"). Not blocking v1.
- Stage-3 of cleanup plan (lines 1141–1145) is partially deferred: do the doc work now, code the cap in v2 if a user reports it.

### Q7 — QC-006 (Medium): config precedence (env vs --config) rationale
- Asked: A (document the rationale, no code change), B (invert to convention), or C (refuse when both set)?
- Captured: User picked **A — add a 1-paragraph note explaining that `--config` and `AOM_CONFIG` are *path overrides* (where to load from), while value-bearing CLI flags like `--capture-verbose` are *value overrides* layered on top. The path-precedence list (built-in defaults < config files < env < `--config`) and the value-precedence list (config-file values < env-var values < CLI-flag values) are separate concerns.**
- Implications:
  - Update the design doc §11 (lines 348–388) and the precedence list at lines 542–545 with the clarification paragraph.
  - No code change in `core/config_layer.py:merge_configs()`.
  - The current precedence (built-in < `/etc/` < `~/.config/` < `./.aom_config.yaml` < `AOM_CONFIG` < `--config` < value CLI flags) is the intended behavior; just spell out the two-axis interpretation.
  - Future readers will no longer ask "why is env below --config" because the doc will have answered it.
- Flags: none.
- Stage-4 of cleanup plan (lines 1147–1151) covers this; resolved by this Q.

### Q8 — QC-007 (Medium): "Precedence order" header is misleading
- Asked: A (rename + clarify), B (restructure into separate sections), or C (leave as-is)?
- User confused by the question as originally asked; reframed to show the actual text + proposed edits.
- Captured: User picked **A — rename "Precedence order" → "Redaction layers", and clarify that layer 0 is an upstream ansible contract (not an AOM layer), layers 1 and 2 are AOM-controlled, layer 2 is unioned with layer 1.**
- Implications:
  - ~3 lines of doc edit at lines 304–309 of the design doc. No code change.
  - The new header reads: "Redaction layers (applied at capture time)". The list becomes:
    - **Layer 0 (upstream contract, not an AOM layer):** ansible's `no_log: true` → already-collapsed payload; AOM passes through.
    - **Layer 1:** AOM hard-coded deny-list (exact-match keys from the QC-002 list: `password`, `vault_password`, `api_key`, `private_key`, `token`, `secret`, `passwd`, `ssh_pass`).
    - **Layer 2:** AOM user-configured regex patterns (additive to layer 1; keys are unioned).
  - The "Precedence" framing is gone; the "Layer 0 is upstream" caveat is added.
  - Aligns naturally with the QC-002 fix (user picked A there) — layer 1 is now exact-match keys + user-regex, which is exactly what ansible-core's deny-list seed provides.
- Flags: none.
- Stage-1 of cleanup plan (lines 1129–1133, doc hygiene) covers this; resolved by this Q.

### Q9 — QC-008 (Medium): TUI focus indicator for `V` keybind
- Asked: A (add footer focus indicator), B (trust implicit focus, 1 spec line), or C (drop context-sensitivity, use explicit per-level keys)?
- Captured: User picked **A — add a footer focus indicator and a one-line confirmation flash on `V` press.**
- Implications:
  - **TUI footer gets a new left-side widget** (Textual `Static` or `Label`): `focus: <level> (<context>)`. Examples:
    - `focus: host (web1 / Install nginx)` — when a host row is selected in the Detail pane.
    - `focus: play (Deploy webservers)` — when a play row is selected in the Tasks pane.
    - `focus: run (current session)` — when a run row is selected in the Runs pane.
  - **Pressing `V` flashes a one-line confirmation** in the footer (or in a transient overlay): `V: verbose for web1/Install nginx`. Clears after 1.5s or on next keypress.
  - **Spec edit at lines 836–863** of the design doc. Also: one-line note in §10 (keybindings table) and §7.4 (status bar / footer).
  - **Code change:** ~10 LOC in `tui/screens/inspect.py` — add the focus widget to the Footer, hook into the existing focus-tracking signal, and add a transient flash on `V` press.
  - **Snapshot test:** add a TUI snapshot test asserting the footer line for each of the three focus levels. The existing `tests/tui/` snapshot suite (mentioned at line 449) is the natural home.
  - The fallback message at line 862 ("(verbose data not captured for this run — re-run with --capture-verbose to enable)") stays. The new focus indicator complements it.
- Flags: none.
- Stage-4 of cleanup plan (lines 1147–1151) covers this; resolved by this Q.

### Q10 — QC-009 (Medium): missing test classes (fuzz, crash-recovery, schema-boundary, concurrency)
- Asked: A (all four in v1), B (fuzz + schema-boundary only), or C (none in v1, ship first)?
- Captured: User picked **A — all four in v1. Total ~260 LOC of new tests, ~40s of CI time. Aligns with AGENTS.md's "TDD-first" rule.**
- Implications:
  - **Add four new test files to the §13 test plan (lines 433–453):**
    - `tests/unit/test_aom_verbose_line_fuzz.py` — 10k random stderr lines through the prefix-match heuristic; assert no false positives for `ERROR!`, `Traceback`, `FATAL`, `^Traceback`, `^  File `, `^Exception`. ~30 LOC, < 5s.
    - `tests/unit/test_event_store_crash_recovery.py` — kill -9 AOM mid-write (use `os.kill(pid, SIGKILL)` from a subprocess), restart, verify replay handles missing `meta.json` (i.e., reads `events.jsonl` line-by-line, treats last partial line as truncated, surfaces a warning). ~50 LOC, ~10s.
    - `tests/unit/test_replay_schema_boundary.py` — record a session with AOM v1 (no `_schema_version`), replay with AOM v2 (has `_schema_version: 2`), and vice versa. Verify the replay driver branches on `_schema_version` correctly. ~80 LOC, ~5s.
    - `tests/integration/test_concurrent_inspect.py` — fake playbook emitting 1000 events/sec while another thread invokes `aom inspect` on the partial `events.jsonl`. Assert no `IOError`, no truncated JSONL lines, no race in the `events.jsonl` writer. ~100 LOC, ~20s.
  - **CI budget impact:** ~40s added to the full suite. Current suite timing unknown — add a baseline measurement in stage 0 before adding these. If the suite is already > 5min, reconsider; if it's < 2min, fine.
  - **Failure semantics for crash-recovery:** if `meta.json` is missing on replay, surface a `WARN` and continue with `events.jsonl` only. Don't fail the replay. The user can `aom inspect prune` or `aom inspect list --incomplete` to find the session.
  - **Failure semantics for concurrency:** if a partial line is read, log `WARN: events.jsonl:LINE is truncated` and skip. Don't fail the inspect. This matches the field-absence tolerance pattern in the design.
  - The new tests go into the §13 plan (line 433) as named-but-unspecified tests, just like the existing `test_config_layer.py` placeholder. They're fleshed out in implementation.
- Flags:
  - Verify the existing CI suite timing before adding. If > 5min, this becomes Stage-5 of the cleanup plan in a second pass.
- Stage-5 of cleanup plan (lines 1153–1158) covers this; resolved by this Q.

### Q11 — QC-010 (Medium): `aom_` prefix policy for synthetic events
- Asked: A (add one-line policy to §5.6), B (new CONTRIBUTING.md section), or C (leave implicit)?
- Captured: User picked **A — add a one-line policy to §5.6: "AOM-emitted events use the `aom_` prefix. The `v2_` prefix is reserved for ansible-core's `v2_*` event family. Any new AOM-emitted event MUST be `aom_*`."**
- Implications:
  - 3-line spec edit at §5.6 of the design doc (around line 807, the `aom_verbose_line` discussion).
  - No code change. No CONTRIBUTING.md.
  - Future contributors who try to add `v2_foo` get a doc-level block. They can still do it, but the spec says they shouldn't.
  - Aligns with the QC-001 (backlog hygiene) and QC-016 (file split) cleanup work; the `aom_` rule is a spec line, not a new doc.
- Flags: none.
- Stage-1 of cleanup plan (doc hygiene) covers this; resolved by this Q.

### Q12 — QC-011 (Medium): backlog uses only `[ ]`, not `[x]`
- Asked: A (two checkboxes with pointer), B (just `[x]`, no pointer), or C (don't touch, rely on QC-001 sweep)?
- Captured: User picked **A — two checkboxes per question, with `→ §N line M` pointer for resolved ones.** Confirmed as a sub-case of QC-001 (same answer); not a separate decision.
- Implications:
  - QC-001 (Q3) and QC-011 (Q12) collapse into one mechanical edit. The sweep produces `- [x]` (with `→ §N line M` pointer) for resolved questions and `- [ ]` for genuinely unresolved ones.
  - No separate code or doc change beyond what QC-001 already specifies.
- Flags: none.
- Resolved by Q3 (QC-001) — same work, same scope.

### Q13 — QC-012 (Medium): stale anchor `core/redaction.py:280-283`
- Asked: A (verify all anchors, fix drift, add script), B (add disclaimer, trust ballpark), or C (delete all anchors)?
- Captured: User picked **A — re-walk every anchor in the design doc, fix any drift, add a one-shot verification script.**
- Implications:
  - **Inventory the anchors in the design doc:** §E (lines 702–712) lists 8 file:line citations. Inline citations appear at lines 14, 192–229, 287–315, 304–309, 322, 327–331, 348–388, 433–453, 482–488, 522–528, 736–737, 742–744, 836–863, 1100. Roughly 15–20 anchors total.
  - **For each, verify with a `Read` + line count.** Fix any drift. The QC caught one (280–283 vs. 285-line file); there may be others.
  - **Add `scripts/verify_anchors.py`** (~30 LOC):
    - Parses the design doc for `path:line-line` patterns (regex per QC-017 standardized style: `(\S+\.py):(\d+)-(\d+)`).
    - For each, reads the file and asserts the cited lines exist.
    - Exits non-zero on drift; prints a table of drift.
  - **Run the script as part of CI** — add to the pre-commit or pre-push hook (the project has a pre-commit config per AGENTS.md). Drift blocks the push.
  - **One-time cost:** ~30 min to write the script, ~30 min to walk all anchors. Recurring cost on every push: < 1s.
  - This is the only finding that adds a new file (`scripts/verify_anchors.py`) to the repo. Worth it for the CI guarantee.
- Flags:
  - Need to confirm the project's existing pre-commit / CI hook setup before adding the new script. Verify with a `Read` on `.pre-commit-config.yaml` and `pyproject.toml`.
- Stage-1 of cleanup plan covers the doc edits; the new script is a small addition to Stage-5 (test coverage). Resolved by this Q.

### Q14 — QC-013 (Medium): sub-Q4.1 audit content in the Q&A log
- Asked: A (move to research note + link), B (compress inline to 2–3 lines), or C (leave as-is)?
- Captured: User picked **B — compress the inline audit to 2–3 lines. Keep it in the Q&A log; no new file.**
- Implications:
  - Lines 522–528 (the paragraph-long "Sub-question raised by user" block) get reduced to a short note: "AOM has a partial config layer at `~/.config/aom/config.yaml`, single-path, only loaded by TUI settings screen (`tui/screens/settings.py:33`). No multi-layer hierarchy, no `--config` CLI flag, no env-var override. `pydantic-settings` is a dep but `SettingsConfigDict()` is empty in `core/config.py:45`. → Q4.2 below for the multi-layer refactor."
  - 1 paragraph becomes 3 lines. No new file. No new doc.
  - Detail (the exact list of "no global /etc/, no local ./.aom_config, no --config CLI flag, no env-var override") collapses into the summary phrase "no multi-layer hierarchy, no `--config` CLI flag, no env-var override". The reader who needs the exact list goes to the codebase.
  - This is the cheapest of the three options; the QC's complaint about "dilutes the signal" is addressed by compression rather than extraction.
- Flags: none.
- Stage-1 of cleanup plan (doc hygiene) covers this; resolved by this Q.

### Q15 — QC-014 (Medium): risk mitigations are shrugs
- Asked: A (rewrite each with v2 mitigation), B (drop Risks section), or C (leave as-is)?
- Captured: User picked **C — leave §17 as-is. The risks are documented; that is enough for v1.**
- Implications:
  - No doc edit. The QC's complaint that "documenting a risk is not mitigating it" is acknowledged but rejected.
  - The §17 risk list stands as: disk usage, privacy (redaction bypass), test coverage gap, config migration surprise, compact mode startup cost, no `_schema_version` field. Of these, the no-`_schema_version` risk is partially resolved by the QC-004 fix (Q5, add the field anyway), but the §17 list still describes the design's risk *as it was*, so the risk text stays unchanged.
  - Future readers who hit any of these in production will see the doc flagged it. The doc is honest about being honest; that's a v1-acceptable posture.
  - The QC-005 deferral (Q6, "stay the course, document harder") means the disk-usage risk is now stronger in v1 than the §17 text implies. Consider: add a one-line "Disk usage: see README's 'Disk usage' section (QC-005 mitigation)" cross-reference. Cheap; preserves the user's "C" choice while honoring the QC-005 doc work.
- Flags:
  - Add the QC-005 cross-reference to §17 in the same edit pass as QC-005. This is a small "good housekeeping" follow-up, not a separate decision.
- Stage-1 of cleanup plan (doc hygiene) covers this; resolved by this Q.

### Q16 — QC-015 (Low): no "Owner" column on doc checklist / test plan
- Asked: A (add Owner column per row), B (single Owner section at top), or C (leave implicit)?
- Captured: User picked **C — leave implicit. Owners get assigned in the project tracker, not in markdown.**
- Implications:
  - No doc edit. The QC's complaint is acknowledged but rejected: the brainstorm doc is not the place to track ownership.
  - The §15 Implementation Plan (line 615) does have a "Suggested next step" list, which serves as an implicit owner-tracking mechanism (each step has natural ownership).
  - For the 8-step implementation order (lines 615–660), each step is implicitly owned by whoever picks it up first. The CI suite, project board, or a separate `OWNERS` file (if one exists; the QC mentioned it doesn't) would track this.
  - The QC's underlying point — "TODO lists with no owner rot" — is correct. The remedy is process, not markdown.
- Flags:
  - If a v2 pass touches this doc, add the Owner column then. Not blocking.
- Resolved by this Q.

### Q17 — QC-016 (Low): split the 1180-line file
- Asked: A (split into 4 files), B (split into 2: design + research), or C (leave as one file, add ToC)?
- User initially typed "q" (no match); asked to pick A, B, or C.
- Captured: User picked **C — leave the file as-is; add a Table of Contents at the top.**
- Implications:
  - **No file split.** The doc stays as one 1180-line file.
  - **Add a Table of Contents at the top** (after the title and date, before the Summary). Auto-generated anchor list with line numbers. Format:
    ```
    ## Contents
    - Summary / key decisions
    - Question Backlog (Pending)
    - Implementation Plan (§1-§17)
      - §1 Reframe
      - §2 Architecture overview
      - ...
    - Q&A log
    - Documentation Checklist
    - QC Review (grumpi-qa)
    ```
  - This is the cheapest of the three options. Doesn't fix the "won't get read end-to-end" problem, but does fix the "where do I find X" problem, which is the more common failure mode.
  - Cost: ~10 min to add the ToC. Mechanical.
  - Some markdown renderers (GitHub, IDE previews) auto-generate a ToC from heading levels, so the manual ToC may be redundant in those views. The plain-text view (cat, less, vim) is where it helps.
- Flags: none.
- Resolved by this Q.

### Q18 — QC-018 (Low): `verbose` block schema is misleadingly curated
- Asked: A (pin to closed set + validator), B (rename to `verbose_full`), or C (leave as-is)?
- Captured: User picked **C — leave the schema list as-is. The QC's complaint that the listed fields are a "curated set" is accurate but not worth fixing in v1.**
- Implications:
  - No schema change. The §3 lines 213–225 list stays as 11 fields (`msg, stdout, stderr, stdout_lines, stderr_lines, invocation, diff, results, warnings, deprecations, _ansible_no_log`).
  - The implementation will persist everything in `result._result.copy()`, including fields not in the list (`start, end, delta, changed, failed, skipped, unreachable, duration, action`). This is the current "store the full result" behavior the QC flagged.
  - **Risk of lying in the spec:** if a future user looks at the spec to find out "what's in the verbose block", they'll see 11 fields and assume those are the only ones. This is the QC's complaint.
  - **Cheap mitigation (within C):** add a 1-line note at line 213: "Note: the `verbose` block persists the full `result._result` minus fields dropped by redaction. The list above is illustrative, not exhaustive." This costs 1 line of doc and addresses the QC's accuracy concern without code change.
  - **The closed-set / validator (A) is the right long-term answer.** A v2 pass can do A. v1 ships C-with-1-line-disclaimer.
- Flags:
  - In the doc edit pass, add the 1-line note at line 213 of the design doc. Trivial.
- Resolved by this Q.

### Q19 — QC-017 (Low): citation style inconsistency
- Asked: A (standardize on `path:line-line` ranges), B (standardize on `path:line` single), or C (leave as-is)?
- Captured: User picked **A — standardize on `path:line-line` ranges everywhere. Same format the `scripts/verify_anchors.py` script (from Q13) will parse.**
- Implications:
  - **Mechanical pass over the design doc**, replacing every `path:N` (single line) with `path:N-M` (range). For single-line citations, use `path:N-N` or `path:N` — pick one. Recommendation: `path:N-M` always, even for one line, because the regex is simpler.
  - **Anchor sites to update:** line 14 (`cli.py:200` → `cli.py:200-203`), and any other single-line citations. The §E block (lines 702–712) already uses ranges; align everything to that.
  - **Affects `scripts/verify_anchors.py` (from Q13):** the regex becomes `(\S+\.py):(\d+)-(\d+)`, and the script verifies both endpoints exist. Single-line citations (`N-N`) verify the same way.
  - **Cost:** ~15 min mechanical pass; ~5–10 anchor sites to update.
- Flags: none.
- Bundled with Q13 (QC-012 anchor verification); same doc edit pass. Resolved by this Q.

### Q20 — QC-019 (Low): rollout plan has no measurement criteria
- Asked: A (add explicit measurement criteria), B (drop the "potentially flip default" sentence), or C (leave ambiguity)?
- Captured: User picked **C — leave §15 line 469 as-is. The "potentially flip default" framing is intentionally non-committal; future maintainers decide.**
- Implications:
  - No doc edit. The rollout text stays.
  - The QC's complaint that "potentially" is not a plan is acknowledged but rejected: the project is in heavy development, and a v1 ship-with-flag-then-revisit posture is honest about uncertainty.
  - If a v1 user actually hits a problem that would trigger a default-flip decision (e.g., disk full, false-positive redactions), the v1 data informs the v2 decision. The doc is the v1 record; v2 can add explicit criteria when there's data to compare against.
  - The §17 risk list (line 482) already calls out "disk usage" as a known risk. The QC-005 deferral (Q6, document harder) means the README will have a "Disk usage" section that includes the 200-host / ~50MB worked example. The default-flip question is downstream of "did the worked example prove accurate?"
- Flags: none.
- Resolved by this Q.

### Q21 — QC-020 (Low): "Running synthesis" header is a journal, not a spec
- Asked: A (rename to "Decision Log" with dates), B (just drop the journal framing), or C (leave as-is)?
- Captured: User picked **C — leave line 4 as-is. The "running synthesis" framing is a stylistic choice.**
- Implications:
  - No doc edit.
  - The QC's complaint that "a 'running synthesis' is a journal, not a design doc" is acknowledged but rejected. The doc is intentionally a working artifact; the journal framing makes that explicit.
  - If a v2 pass turns the doc into a frozen spec, the rename can happen then. v1 keeps the working-artifact framing.
  - This is consistent with the user's other "leave as-is" choices (QC-014, QC-015, QC-019) — a pattern of accepting that the doc is honest about being a v1 working artifact, not a polished spec.
- Flags: none.
- **All 20 findings triaged. Resolved by this Q.**

## Open flags (pending input)

These are questions/issues surfaced during triage that have no clear answer yet.

- **`aom inspect prune` exists and is tested.** Verify with `grep` on `inspect/cli.py`. The QC-005 deferral (Q6) assumes this command works. If it doesn't, that's a separate gap to fix before v1 ships.
- **Verify `--yes` doesn't already exist as a global flag.** Per QC-003 (Q4). A `grep` on `cli.py` confirms. If it does exist, the QC-003 fix is simpler than expected.
- **Verify pre-commit / CI hook setup before adding `scripts/verify_anchors.py`.** Per QC-012 (Q13). Read `.pre-commit-config.yaml` and `pyproject.toml`.
- **Q21 (`--check`/`--diff` UI)** — the doc says "hide the field or show '(no diff)'?" but doesn't pick. From QC-001 sweep candidate. Suggest: default to "(no diff)" placeholder; the user can move to "hide entirely" in v2 if they care.
- **Q22 (large results / setup megabytes truncation)** — partially answered by §9 (exclude `setup` by default, opt-in `--capture-setup`), but the per-host truncation question is still open. Suggest: defer to v2, track in `aom inspect list --size` if a real user reports it.
- **Q23 (live streaming inspect)** — answered "yes" in §10, but the implementation guidance is light. Suggest: spec gets a 3-line note pointing at the partial-`events.jsonl` reader; concrete code lands in QC-009's concurrency test (Q10).
- **Q32 (TUI rendering perf for full stdout/stderr)** — actually unanswered. The doc has lazy-render as a hint, no measurement plan. Suggest: when implementing QC-008's TUI work, add a perf budget: "rendering a 1MB `stdout` block must complete in < 50ms." If a real run exceeds it, lazy-render in v2.

## Recap

**Status:** All 20 QC findings triaged. 12 took the QC's recommended "fix it" option, 4 took a cheaper option, 4 took "leave as-is." v1 pre-implementation work is now bounded: ~12 doc edits + 1 README section + 5 new code/test files.

**What's still flagged:** 4 genuinely-open questions from the design doc backlog (Q21, Q22, Q23, Q32), 3 verification tasks (`aom inspect prune`, `--yes` existence, pre-commit setup), and 1 cross-reference housekeeping task (QC-005 cross-ref in §17).

**Suggested next step:**

1. **Verify the 3 verification tasks** (do the greps / reads). Cheap; informs whether QC-003 and QC-005 are simpler than expected.
2. **Make the doc edits** (QC-001 sweep + QC-007 rename + QC-010 1-line rule + QC-011 sub-case + QC-013 compress + QC-014 cross-ref + QC-016 ToC + QC-017 standardize + QC-018 disclaimer + Q5 of Q9=B override). Mechanical; can be done in 1 sitting.
3. **Write the code** (QC-002 redaction rewrite, QC-003 confirm prompt, QC-004 `_schema_version: 2`, QC-008 TUI footer, QC-009 four tests, QC-012 verify_anchors script). Per AGENTS.md: TDD-first — failing test, then implementation.
4. **Decide the 4 open flags** (Q21, Q22, Q23, Q32) in the next pass, before the v1 tag.

The design doc is no longer "all 17 resolved while 21 sit open" — the QC-001 sweep will fix that. The redaction is no longer "correct when secrets are recognised substrings" — the QC-002 ansible-core seed + red-team fixture will fix that. The schema is no longer version-free — QC-004 fixes that. The TUI is no longer firing keybinds into an unknown context — QC-008 fixes that.

The 4 Lows the user kept as-is are honest v1 trade-offs, not hidden bugs. Documented, deferred, owned.
