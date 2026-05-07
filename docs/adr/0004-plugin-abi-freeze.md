# ADR 0004 — Plugin ABI freeze (v1.3.6)

**Status:** Accepted (additive extensions in v1.4.2 — see end)
**Date:** 2026-05-06 (extended 2026-05-07)
**Tags:** plugins, abi, stability, sandhi, v1.3.6

> **2026-05-07 — v1.4.2 additive extensions:** the freeze's
> "additions are allowed" envelope (see Decision § below) covers
> the v1.4.2 surfaces. Two new public symbols
> (`plugin_register_normal_prefix_key`, `plugin_buf_load_file`),
> one new key constant (`KEY_G`), one new action constant
> (`ACT_MOVE_FILE_START`), plus the long-stubbed `gg` motion now
> dispatched via the generalized prefix path. **No frozen-from-1.3.6
> symbol changed shape**; consumers compiling against the 1.3.6
> surface continue to compile and run unchanged. See
> [§ v1.4.2 additive extensions](#v142-additive-extensions-2026-05-07)
> at the end of this ADR.

---

## Context

[ADR 0003](0003-cyrius-plugin-system.md) accepted the Cyrius plugin
system as a direction and committed to **prototyping the ABI via
the v1.4.0 LSP client** rather than designing in vacuum. Two
intermediate steps deferred the freeze:

- **v1.3.4** landed `src/plugin.cyr` — the 6-hook registry +
  registration API + fire/lookup/collect helpers — and wired
  `post_save` + `post_change` into core dispatch.
- **v1.3.5** wired the remaining four fire-points
  (`status_segment`, `normal_key`, `ex_command`,
  `diagnostic_provider`) into `render_status` / `editor_dispatch` /
  `command_execute` / `render_frame`, and shipped
  `src/plugins/trailing_ws.cyr` as the first working plugin
  (exercises 3 of 6 hooks: post_change + diagnostic_provider +
  status_segment).

With all six hooks active and at least one real consumer pinning
their behavior, the ABI's surface area has stopped shifting. The
v1.3.5 ADR 0003 § Plan called for a follow-up ADR (0004 or higher)
that "freezes the ABI surface against what shipped." This is that
ADR.

## Decision

The cyim plugin ABI surface — function names, parameter
signatures, struct layouts, severity constants — listed below is
**frozen** at v1.3.6. Within the cyim 1.x major-version series:

- **No backwards-incompatible changes.** A plugin compiling
  against the cyim 1.3.6 ABI continues to compile and run
  semantically unchanged against any later 1.x patch / minor.
- **Additions are allowed.** New hook types may land via future
  ADRs; new helper functions may land in `src/plugin.cyr` as
  needed; new severity levels may be appended to the `DIAG_*`
  enum.
- **Breaking changes require a major-version bump (cyim 2.x)**
  per the first-party-standards versioning policy. cyim 2.0
  may rename, retype, or remove any ABI symbol; intermediate
  1.x releases may not.

## Frozen surface

### Hook registration (called by plugins at init time)

Six functions in `src/plugin.cyr`. All take a function pointer
(`fp`) as their primary argument; keyed hooks take an additional
`key` or `name` argument. Return value is `0` on success,
`0 - 1` on alloc failure (treat as fatal in plugin-init code —
cyim's `plugin_init()` is responsible for keeping the registries
non-null at this point).

```cyrius
plugin_register_post_save_hook(fp)
plugin_register_post_change_hook(fp)
plugin_register_status_segment(fp)
plugin_register_diagnostic_provider(fp)
plugin_register_normal_key(key, fp)        # `key` is a single byte 0..255
plugin_register_ex_command(name, fp)       # `name` is a NUL-terminated cstring
```

**Frozen invariants:**

- Every `register_*` call appends to its registry vec without
  deduplication. Plugins may register multiple callbacks for the
  same hook; cyim fires all of them in registration order.
- Built-ins win on conflict for keyed hooks (`normal_key`,
  `ex_command`). Plugin lookup is reached only after the
  built-in keymap / command table misses. ADR 0003 §3 records
  the rationale (modal grammar is the inheritance — plugins
  extend the dispatch table, never override it).
- `plugin_init()` is idempotent (calling twice does not duplicate
  registrations). Plugin-init helpers like `trailing_ws_init()`
  ARE NOT idempotent — calling twice double-registers. Plugins
  are expected to be initialized once per process from
  `src/main.cyr:main()`.

### Callback signatures

Each hook's `fp` has a fixed signature. Plugin authors must
match these exactly; mismatched signatures will compile but
crash at runtime when cyim invokes the callback via
`fncall<N>()`.

```cyrius
fn post_save_cb(s, path) -> 0           # post_save_hook
fn post_change_cb(s) -> 0               # post_change_hook
fn status_segment_cb(s) -> cstring      # status_segment (return 0 to skip)
fn diagnostic_cb(s, b, out_vec) -> 0    # diagnostic_provider
fn normal_key_cb(s) -> action_id        # normal_key (returns ACT_* enum value)
fn ex_command_cb(s) -> exit_code        # ex_command (0 = success, <0 = error)
```

**`s`** is the cyim editor state pointer. Plugins use the
exposed accessors (`editor_buf`, `editor_mode`, `editor_cursor`,
etc.) to read state.

**`path`** in `post_save_cb` is the file path the buffer was
saved to (NUL-terminated cstring; lifetime: caller-owned, valid
until next save).

**`b`** in `diagnostic_cb` is the active buffer pointer. Provider
walks buffer content as needed and appends `diag_new(...)`-built
records to `out_vec`.

**`out_vec`** in `diagnostic_cb` is a vec the caller (cyim's
`_plugin_render_collect_diagnostics`) owns. The vec is freshly
allocated per render frame; entries pushed are inspectable via
`plugin_last_diags()` after the frame collect completes.

### Diagnostic record (24 B)

Frozen layout for diag entries pushed onto the
`diagnostic_provider` out_vec:

```text
diag (24 B):
  +0   line       int   (1-indexed line number)
  +8   severity   int   (one of DIAG_HINT / DIAG_INFO / DIAG_WARNING / DIAG_ERROR)
  +16  msg_ptr    ptr   (NUL-term cstring; provider owns lifetime,
                         valid for at least the current render frame)
```

Constructor and accessors in `src/plugin.cyr`:

```cyrius
diag_new(line, severity, msg) -> diag_ptr
diag_line(d)                  -> int
diag_severity(d)              -> int
diag_msg(d)                   -> cstring
```

**Frozen invariants:**

- Layout is 24 B, `{line, severity, msg_ptr}` in that order.
  Future fields (column ranges, source-id, fix suggestions) get
  appended to a new struct version, not retrofit into this one.
- Accessors are stable; plugin code reading `diag_line(d)` etc.
  works across cyim 1.x.

### Severity constants

```cyrius
var DIAG_HINT    = 0
var DIAG_INFO    = 1
var DIAG_WARNING = 2
var DIAG_ERROR   = 3
```

Numeric values are stable. Higher numbers are more severe;
plugin code performing comparisons (e.g.
`if (diag_severity(d) >= DIAG_WARNING) { ... }`) is portable.

### Status segment vec

`_plugin_collect_status_segments(s, out_buf)` is exposed for
tests; production code (cyim's `render_status`) calls it with a
fresh gap buffer per render. Plugin authors typically don't call
it directly. Listed for completeness; **not** part of the
freeze contract — this helper may evolve as render-side
integration tightens at v1.4.0+.

### Per-frame diagnostic accessor

```cyrius
plugin_last_diags() -> vec_ptr
```

Returns the vec populated by `_plugin_render_collect_diagnostics`
at the most recent render frame. Vec is replaced per frame; do
not cache the returned pointer across frames. Tests + future
render-side inline-paint integration consume this.

## Compatibility envelope

**Stable across cyim 1.x:**

- All hook registration function names + signatures (the 6
  listed above)
- All callback signatures (the 6 fp shapes)
- The 24 B diag record layout (`+0 line`, `+8 severity`,
  `+16 msg_ptr`)
- The 4 `DIAG_*` severity constant values (0..3)
- The numeric semantics: built-ins win on conflict; multiple
  registrations fire in order; `status_segment` returning 0
  skips the segment; `diagnostic_provider` `out_vec` lifetime
  is per-frame
- `plugin_init()` idempotency
- `plugin_last_diags()` accessor

**Subject to expansion (additions only) within cyim 1.x:**

- New hook types (require ADR per ADR 0003 §3 expansion policy)
- New helper functions in `src/plugin.cyr`
- New `DIAG_*` severity values appended after `DIAG_ERROR`
- New buffer / state accessors (`editor_*`, `buf_*`) usable
  from plugins

**Reserved for cyim 2.x (breaking changes need a major bump):**

- Renaming or removing any frozen ABI symbol
- Reordering / retyping the 24 B diag record fields
- Reassigning `DIAG_*` constant values
- Changing built-ins-win semantics on keyed hooks
- Changing the per-frame diag vec lifetime contract

## What's NOT frozen (and why)

The following ship in v1.3.5/1.3.6 but are **not** part of the
freeze; they may shift in 1.x patches:

- **Internal `_plugin_*`-prefixed helpers** (`_plugin_fire_*`,
  `_plugin_lookup_*`, `_plugin_collect_*`,
  `_plugin_render_collect_diagnostics`,
  `_plugin_keyed_record_new`, `_plugin_buf_append_cstr`,
  `_plugin_ex_name_eq`). These are internal call sites, not
  consumed by plugin authors. The leading underscore is the
  contract.
- **Registry vec layouts** — internal data structures backing
  the registries. Plugins interact via the public registration
  API, not by reaching into `_plugin_*_hooks` globals.
- **Render-side inline diag paint** — v1.3.5 collects diags
  per frame but doesn't paint markers in the buffer view.
  cyim-lsp at v1.4.0 will land the visual surface; the visual
  representation (gutter markers, line underlines, color
  scheme) is not frozen until then.
- **Plugin manifest convention** — the `[plugins.<name>]` block
  shape in `cyrius.cyml` (ADR 0003 §4). Currently uses
  `[deps.<name>]` syntactic equivalence; the named-section
  variant lands when upstream cyrius adds first-class parsing.

## Consequences

### Positive

- **Plugin authors can target v1.3.6 with confidence.**
  cyim-lsp's design choices for v1.4.0 don't risk being
  obsoleted by ABI shifts within 1.x. Same applies to any
  future plugin (snippet engine, color-scheme picker,
  formatter wrapper, etc.) that wants to ship.
- **External plugin promotion is unblocked.** Once the
  `[plugins]` manifest shape is settled with cyrius upstream,
  trailing_ws can move from `src/plugins/trailing_ws.cyr`
  inline into a `MacCracken/cyim-trailing-whitespace` repo
  via the sandhi pattern. Other plugins follow.
- **CI gate hardening.** ABI tests in `tests/plugin.tcyr` +
  `tests/trailing_ws.tcyr` now serve as compatibility guards;
  any change that breaks them in a 1.x patch is a regression
  to revert, not a redesign to absorb.

### Negative

- **2.x is forever distant.** Promising no breaking changes
  through 1.x means any abi mistake we missed surfaces only
  via additions (workaround helpers, parallel APIs) until 2.0.
  This is the standard compatibility cost of any frozen ABI;
  the alternative (no freeze) is worse.
- **Hook expansion gets ADR overhead.** Adding a new hook type
  now requires writing an ADR. This is intentional friction
  per ADR 0003 §3 — keeps plugins composable, prevents the
  "too many hooks" failure mode that blew up vim plugin
  ecosystems. Cost to cyim is low (an ADR is a single doc
  commit); benefit (stable hook surface) is durable.

### Neutral

- **The freeze is documented, not mechanically enforced.** No
  CI gate validates that `src/plugin.cyr` symbol set hasn't
  drifted. A future ADR could add an api-surface snapshot to
  CI (cyrius itself ships
  `docs/api-surface.snapshot` in its own repo as precedent).
  For v1.3.6, the docs + `tests/plugin.tcyr` + reviewer
  diligence are the gate.

## Alternatives considered

### A. Defer the freeze to v1.4.0 (after cyim-lsp ships)

The original ADR 0003 plan called for the freeze to happen
"after the LSP forces ABI choices." Argument for: cyim-lsp
is a much larger consumer than trailing_ws and would surface
ABI gaps the 3-hook proving ground misses.

**Rejected because:** v1.3.5 already exercises 3 of 6 hooks
end-to-end, and the remaining 3 (post_save, normal_key,
ex_command) have well-understood semantics from the v1.3.4
scaffold + v1.3.5 wire-up. Waiting until v1.4.0 means
cyim-lsp design choices either (a) get built against an
unfrozen ABI and risk re-design later, or (b) freeze the ABI
de facto without an ADR, which is the failure mode this
series exists to prevent. Better to freeze now and let
cyim-lsp build confidently against the contract; if v1.4.0
surfaces a gap, ADR 0005 records the addition.

### B. Freeze a smaller subset (post_save + post_change only)

Argument: only the two hooks v1.3.4 wired have been
"battle-tested" by the .tcyr suite + the 1.3.4 → 1.3.5
extension cycle. Freezing only those leaves more room to
iterate on the others.

**Rejected because:** the v1.3.5 wire-ups were not
speculative — each fire-point integrates with cyim's existing
dispatch / render machinery in well-understood places, and
trailing_ws has exercised three of them in production. A
partial freeze creates a confusing two-tier ABI ("these 2
hooks are stable, those 4 might change") that erodes the
confidence the freeze is meant to provide. Either freeze the
whole surface or none of it.

### C. Don't freeze at all; rely on convention

Argument: cyim is one repo, plugins live in cyim's tree
(trailing_ws) or in repos under MacCracken/* (future ones).
Coordinated changes across all consumers are cheap; an
explicit ABI freeze is bureaucratic overhead.

**Rejected because:** even with coordinated changes,
plugin-author cognitive overhead matters. "Will my v1.3.5
plugin still compile against v1.3.7?" is a question that
should have a documented answer, not a "probably yes, ask
@MacCracken" answer. The ADR is the documented answer.

## See also

- [ADR 0003 — Cyrius plugin system](0003-cyrius-plugin-system.md)
  (the design decision; this ADR builds on its surface listing)
- [ADR 0001 — Trust model](0001-trust-model.md) (the freeze
  doesn't change cyim's trust model; plugins are still trusted
  code per the interactive-local-user assumption)
- [`docs/architecture/001-plugin-system.md`](../architecture/001-plugin-system.md)
  (architectural invariants — hook surface, modal-grammar
  protection, fire-point semantics, post_change firing rule)
- [`src/plugin.cyr`](../../src/plugin.cyr) (the ABI itself —
  the source of truth this ADR freezes)
- [`src/plugins/trailing_ws.cyr`](../../src/plugins/trailing_ws.cyr)
  (the v1.3.5 worked example demonstrating the frozen ABI)
- [`tests/plugin.tcyr`](../../tests/plugin.tcyr) +
  [`tests/trailing_ws.tcyr`](../../tests/trailing_ws.tcyr) (the
  test-side expression of the frozen contract; regressions
  here are ABI breakages within 1.x)

## v1.4.2 additive extensions (2026-05-07)

The freeze's "additions are allowed" envelope explicitly permits
new helper functions, new severity values, and new hook types
without bumping to 2.0. v1.4.2 exercises that envelope to give
cyim-lsp 1.1.0 the surfaces it needs to activate features that
were stubbed at 1.0.x:

### Added — registration

- `plugin_register_normal_prefix_key(prefix, key, fp)` — register
  a two-byte NORMAL-mode sequence. Used by cyim-lsp 1.1.0 to bind
  `gd` (`(KEY_G, 'd', _cyim_lsp_gd)`) and `gr` (`(KEY_G, 'r',
  _cyim_lsp_gr)`). The fp signature mirrors `plugin_register_normal_key`:
  `fn(s) -> action_id`. Plugin-returned actions flow through
  cyim's standard motion / edit pipelines via `editor_step`.
- Constraint: plugin prefix-keys cannot drive mode transitions
  (the prefix dispatch path returns immediately, bypassing the
  MODE_NORMAL transition guards). Plugins needing mode changes
  use `plugin_register_ex_command`. Documented in `src/mode.cyr`'s
  `editor_dispatch` comment block.

### Added — operations

- `plugin_buf_load_file(s, path)` — load a NUL-terminated cstring
  path into a new buffer + switch the editor's active buffer to
  it. Wraps the same dedup / buflist / window-update bookkeeping
  `:e <file>` uses; both paths share the new
  `_buf_load_file_into_active(s, path)` helper extracted from
  `_cmd_e` (behaviour-neutral refactor). Returns buf ptr on
  success, 0 on failure with `editor_last_error` set
  (`ERR_NO_FILE_NAME`, `ERR_FILE_NOT_FOUND`, `ERR_FILE_TOO_LARGE`).
  Used by cyim-lsp 1.1.0's cross-file goto-def: load the destination
  file from the LSP response URI, then `buf_move(b, dest_offset)`
  to jump.

### Added — built-ins

- `KEY_G = 103` — new prefix constant for the generalized
  prefix-dispatch path.
- `ACT_MOVE_FILE_START = 109` — finally wired (the function
  `motion_file_start` shipped as a stub in M1 with the comment
  "Multi-byte input dispatch is not yet wired"; v1.4.2's
  generalization closes that). `motion_apply` routes
  `ACT_MOVE_FILE_START` to `motion_file_start`.

### Changed — internals only

- `editor_dispatch` (`src/mode.cyr`) — prefix handling
  generalized from the special-case `if (editor_prefix(s) ==
  KEY_CTRL_W) { ... }` to `if (editor_prefix(s) != 0) { ... }`
  with branches per latched prefix value (Ctrl-W → window nav,
  KEY_G → built-in `gg` + plugin lookup, anything else → plugin
  lookup only). Built-ins still win on conflict per ADR 0003 §3
  — verified by test: registering `(KEY_G, 'g', fp)` is shadowed
  by the built-in `ACT_MOVE_FILE_START`.

### Conflict resolution unchanged

The ADR 0003 §3 rule "built-ins always win" carries over to
prefix-keys. v1.4.2 wires it the same way as single-byte
NORMAL-mode keys: the dispatch path checks the built-in first
(currently `gg`), and only consults the plugin lookup if the
built-in branch declines.

### What this *doesn't* do

- **No popup / list-display ABI.** cyim-lsp 1.1.0+'s `:lsp-find-refs`
  quickfix list still surfaces the count in the status bar only.
  The popup-overlay subsystem (`plugin_list_display`) needs a new
  mode + render-time overlay drawing + j/k/Enter/Esc key handling
  — that's the size of a minor release, not a patch. Targeted for
  cyim 1.5.0.
- **No new diag severity values.** `DIAG_*` enum unchanged at
  v1.4.2.
- **No new hook types.** The six hooks frozen in v1.3.6 remain
  the canonical surface; v1.4.2's additions are *registrations*
  against existing hook types (the prefix-key extension lives
  alongside `plugin_register_normal_key`) and an *operation*
  (`plugin_buf_load_file`).

### Coordination

- cyim-lsp 1.1.0 picks up these surfaces via the bundled
  `lib/cyim-lsp.cyr` distfile (which doesn't itself change at
  1.0.3 → 1.1.0; the change is in the consumer-side glue
  `src/plugins/lsp_glue.cyr` that calls `plugin_register_normal_prefix_key`
  / `plugin_buf_load_file` from `cyim_lsp_init()`).
- cyim 1.4.x stays open for further additive extensions; cyim 1.5.0
  earns its minor bump via `plugin_list_display` (the popup
  subsystem).
