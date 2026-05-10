# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.6.7] — 2026-05-09

**cyim-lsp 1.5.0 pickup — open-in-split for `:lsp-find-refs`,
plus arrow keys in list mode.**

Seventh bite of the 1.6.x catch-up cycle. Lands two carry-over
items at once because 1.6.7 hadn't been tagged yet when the
arrow-keys piece was scoped — bundling fits the same release
window:

1. **Open-in-split** — cyim-lsp 1.5.0's example-glue refactor
   activates cyim 1.6.6's `plugin_buf_load_file_split` ABI
   through two new ex-commands (`:lsp-find-refs-split` /
   `:lsp-find-refs-vsplit`).
2. **Arrow keys in list mode** — `editor_feed`'s CSI parser
   now routes `ESC [ A` / `ESC [ B` (Up / Down) to
   `_plugin_list_prev` / `_plugin_list_next` when
   `_plugin_list_active == 1`. Mirror of mode.cyr's existing
   j/k routing; closes the last 1.5.x deferred-polish carry-over.

cyim-lsp 1.5.0's `[lib]` source was unchanged (banner-only
distfile delta vs 1.4.0); the work is entirely in the example
glue and cyim's `src/plugins/lsp_glue.cyr` mirror.

User-visible: `:lsp-find-refs` (unchanged — replaces current
pane), `:lsp-find-refs-split` (new — splits horizontal, new pane
below, focus moves there), `:lsp-find-refs-vsplit` (new — splits
vertical, new pane right). Default in-place behaviour preserved
byte-for-byte; users on cyim < 1.6.6 with cyim-lsp 1.4.0 glue
continue to work without change.

### Changed

- **`cyrius.cyml`** — `[deps.cyim-lsp].tag = "1.5.0"` (was
  `"1.4.0"`). `cyrius deps` re-resolved; `lib/cyim-lsp.cyr`
  symlink now points at `~/.cyrius/deps/cyim-lsp/1.5.0/dist/cyim-lsp.cyr`
  (2425 lines, byte-identical to 1.4.0 modulo banner — `[lib]`
  unchanged).
- **`cyrius.lock`** — cyim-lsp sha updated; vyakarana sha
  unchanged.
- **`src/plugins/lsp_glue.cyr`** — mirror of cyim-lsp 1.5.0's
  example-glue refactor:
  - New module-level `_cyim_lsp_ref_split_mode` (i64; default
    0). Set by the entering ex-command, read by
    `_cyim_lsp_on_ref_select` at jump time.
  - Existing `_cyim_lsp_ex_find_refs` body extracted into
    `_cyim_lsp_ex_find_refs_with_mode(s, mode)` shared helper.
  - `_cyim_lsp_ex_find_refs(s)` thinned to a single line (sets
    mode 0 via the helper).
  - New `_cyim_lsp_ex_find_refs_split(s)` (mode 1) and
    `_cyim_lsp_ex_find_refs_vsplit(s)` (mode 2).
  - `_cyim_lsp_on_ref_select` branches: mode 0 →
    `plugin_buf_load_file`, mode 1/2 →
    `plugin_buf_load_file_split(..., SPLIT_HORIZONTAL/SPLIT_VERTICAL)`.
  - `cyim_lsp_init` registers the two new ex-commands
    (`:lsp-find-refs-split`, `:lsp-find-refs-vsplit`) alongside
    the existing four.

### Added — arrow keys in list mode

- **`src/driver.cyr` `editor_feed`** — when
  `_plugin_list_active == 1`, the CSI dispatch routes `ESC [ A`
  (Up) to `_plugin_list_prev` and `ESC [ B` (Down) to
  `_plugin_list_next`. Left / Right finals (`C` / `D`) are
  swallowed (consumed without effect) since a single-column
  picker has no horizontal navigation. Outside list mode the
  existing `motion_apply(ACT_MOVE_*)` routing is unchanged.
- **`tests/plugin.tcyr` extended 109 → 125 assertions** (+16
  across 5 new groups for the arrow-key surface):
  - Down advances index (and clamps at `count - 1`).
  - Up moves index back (and clamps at 0).
  - Left/Right swallowed (no list-index change, no buffer
    mutation).
  - After list dismiss, arrow keys resume motion routing
    (regression guard for the active-leaf case).
  - Lone ESC outside a CSI head still routes as a single byte
    (no 3-byte lookahead overrun — preserves
    INSERT-mode-exit semantics).

### Status

- **No new cyim ABI surface.** The `plugin_buf_load_file_split`
  ABI shipped in 1.6.6; this cut just consumes it. Plugin ABI
  freeze (1.3.6 / ADR 0004) holds.
- **Default behaviour preserved.** `:lsp-find-refs` (and `gr`
  via the prefix-keymap) continues to load in-place — the
  mode-0 branch is byte-equivalent to pre-1.6.7 logic.
- **Arrow-key surface is parity-only.** j/k continue to work
  unchanged in list mode (mode.cyr handles the byte-level
  dispatch); arrow keys now do the same via editor_feed. No
  user-visible regression for either input style.
- **Open-in-split is currently ex-command-only.** Keymap
  bindings for `:lsp-find-refs-split` / `:lsp-find-refs-vsplit`
  (e.g. `gR`, `gv`, etc.) are deferred — would land via either
  a `.cyimrc` keymap surface or a future cyim-lsp glue update.

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,214,656 B** (+776 over 1.6.6's
  1,213,880 B). Deltas:
  - cyim-lsp 1.5.0 pickup (~648 B): helper extraction net-zero
    + two thin-wrapper ex-commands ~160 B + on_select branch
    ~200 B + register calls ~150 B + `_cyim_lsp_ref_split_mode`
    module global ~16 B + scaffolding.
  - Arrow-key routing (~128 B): the `_plugin_list_active == 1`
    branch in `editor_feed`'s CSI dispatch + the two
    `_plugin_list_*` calls.

### Verification

- `cyrius deps` — re-resolved, lock updated.
- `cyrius test` — **22 suites, 1150 assertions PASS** (+16 vs
  1.6.6 — all in `tests/plugin.tcyr`'s new arrow-key groups;
  the cyim-lsp 1.5.0 pickup is exercised via the lsp smoke
  harness at runtime).
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 24 src files, 0 warnings each.
- `cyrfmt --check` — 24 files clean.
- `tests/cli_smoke.sh` — 118 PASS.
- `tests/integration_smoke.py` — all PASS.
- `cyrius smoke tests/smcyr/lsp_fold.smcyr` — 1 PASS.
- `CYRIUS_DCE=1 cyrius build` — clean.

## [1.6.6] — 2026-05-09

**Plugin ABI: `plugin_buf_load_file_split(s, path, direction)`.**

Sixth bite of the 1.6.x catch-up cycle. Adds an additive plugin
ABI for opening a file in a new split window — the cyim side of
the "open-in-split" carry-over from 1.5.x deferred polish. Same
dedup + load-or-reuse semantics as `plugin_buf_load_file`, but
splits the active window first and moves focus to the new leaf.

Two new public constants pin the direction surface:
`SPLIT_HORIZONTAL = 0` (new pane below; matches `:sp`),
`SPLIT_VERTICAL = 1` (new pane right; matches `:vsp`). Unknown
values default to horizontal so a future `SPLIT_TAB` /
`SPLIT_FLOAT` etc. doesn't silently break this call site.

cyim-lsp follow-up at 1.5.0 will consume this — `_cyim_lsp_on_ref_select`
gains a "split" hint and routes through the new ABI when the
caller wants to keep the current buffer visible. That's a
separate cyim-lsp cut + cyim 1.6.x pickup.

**Additive ABI** per ADR 0004's freeze envelope: nothing
existing changed shape. `plugin_buf_load_file` stays unchanged;
the freeze guarantees consumers compiled against cyim 1.3.6+
continue to work without touching `lsp_glue.cyr` or any other
plugin source.

### Added

- **`plugin_buf_load_file_split(s, path, direction)` in
  `src/plugin.cyr`** (~85 lines). Public ABI that:
  1. Validates `path != 0`; sets `ERR_NO_FILE_NAME` on null.
  2. Initializes the buflist via `bl_init`.
  3. Resolves to a buflist index — dedups via `_cmd_find_path`
     when path is already loaded; loads from disk via
     `buf_new` + `buf_load_file` otherwise. Path-not-found,
     too-large, and read-error all set the appropriate
     `ERR_*` and return 0.
  4. Maps `direction` to window.cyr's internal split type
     (`WIN_SPLIT_H = 1` / `WIN_SPLIT_V = 2`). Literal integers
     used inline rather than the named constants because Cyrius
     is single-pass and `motion.tcyr` / `dispatch.tcyr` include
     `plugin.cyr` without `window.cyr` — referencing the named
     constants would break their compile. The mapping is
     asserted by the new tests in `plugin.tcyr` (which DOES
     include `window.cyr`).
  5. Calls `window_split_active(s, split_type)`. If the split
     fails (degenerate window state, no active leaf), falls
     back to the in-place load behaviour of
     `plugin_buf_load_file` — caller never gets a silent
     no-op.
  6. Walks the parent of the original active leaf to find the
     new sibling (always `child_b` of the freshly created
     split node), points its `buf_idx` at the loaded file,
     moves `editor_set_active_leaf` to it.
  7. Returns the buf ptr.
- **`SPLIT_HORIZONTAL = 0` / `SPLIT_VERTICAL = 1`** — public
  constants for the direction parameter. Documented at the
  ABI surface listing in plugin.cyr's header.
- **`tests/plugin.tcyr` extended 88 → 109 assertions** (+21
  across 7 new groups for the split ABI):
  - Constants (2 assertions): `SPLIT_HORIZONTAL == 0`,
    `SPLIT_VERTICAL == 1`.
  - Horizontal split (8 assertions): pre-state is single leaf,
    post-load buflist grows, active buffer == loaded buf, root
    becomes a split node, active leaf changed and is now a
    leaf whose parent is the split.
  - Vertical split (1 assertion): split type stored at
    `load64(root)` is `WIN_SPLIT_V` (2).
  - Unknown direction (1 assertion): defaults to
    `WIN_SPLIT_H` (1).
  - Dedup against existing buflist entry (3 assertions):
    second split-load reuses the buf; buflist count unchanged.
  - Missing file (3 assertions): returns 0, `ERR_FILE_NOT_FOUND`
    set, no split happened (root still single leaf).
  - NULL path (2 assertions): returns 0, `ERR_NO_FILE_NAME`
    set.
  - Variables namespaced as `sp_h` / `sp_v` / `sp_unk` /
    `sp_dd` / `sp_miss` to avoid collision with the existing
    `s7` / `s8` / etc. function-scoped declarations later in
    `plugin.tcyr`'s `plugin_list_display` group (Cyrius vars
    are function-scoped per CLAUDE.md).

### Changed

- **`src/plugin.cyr` ABI surface header** — added the new
  function and two constants to the comment listing of public
  surface.

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,213,880 B** (+1,024 over
  1.6.5's 1,212,856 B). Delta is the
  `plugin_buf_load_file_split` body (~700 B after DCE) +
  the two new public-constant globals (~24 B each) +
  scaffolding around the new dispatch path.

### Status

- **No cyim-lsp consumer yet.** cyim-lsp 1.5.0 (planned) will
  thread a "split" hint through `_cyim_lsp_on_ref_select` and
  route through this ABI for the open-in-split UX. Until then,
  the new ABI is dormant — exercised only by `tests/plugin.tcyr`,
  not by any user-facing keybinding.
- **Plugin ABI freeze (ADR 0004) holds.** This is purely
  additive: `plugin_buf_load_file` stays unchanged, and the
  new function + constants are net new symbols.

### Verification

- `cyrius test` — **22 suites, 1134 assertions PASS** (+21
  vs 1.6.5).
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 24 src files (incl. plugins/lsp_glue.cyr),
  0 warnings each.
- `cyrfmt --check` — 24 files clean.
- `tests/cli_smoke.sh` — 118 PASS.
- `tests/integration_smoke.py` — all PASS.
- `cyrius smoke tests/smcyr/lsp_fold.smcyr` — 1 PASS.
- `CYRIUS_DCE=1 cyrius build` — clean.

## [1.6.5] — 2026-05-09

**cyim-lsp 1.4.0 pickup — reference previews in `:lsp-find-refs`.**
Fifth bite of the 1.6.x catch-up cycle. cyim-lsp 1.4.0 added
`lsp_ref_preview(uri, line, max_chars)` as its second real
`[lib]` source change of the 1.x line; cyim 1.6.5 picks it up
and updates `_cyim_lsp_label_for_ref` to append the preview
snippet after `filename:line:col`. Closes the long-standing
"reference previews" carry-over from cyim's 1.5.x deferred
polish list.

User-visible change: pressing `gr` over a Cyrius symbol now
shows each reference as `filename:line:col  source-snippet-here`
(leading whitespace stripped, capped at 80 bytes). Files >1 MiB
or out-of-range lines surface the bare `filename:line:col`
(graceful fallback identical to 1.6.4 output).

### Changed

- **`cyrius.cyml`** — `[deps.cyim-lsp].tag = "1.4.0"` (was
  `"1.3.0"`). `cyrius deps` re-resolved; `lib/cyim-lsp.cyr`
  symlink now points at `~/.cyrius/deps/cyim-lsp/1.4.0/dist/cyim-lsp.cyr`
  (2425 lines, was 2305 at 1.3.0).
- **`cyrius.lock`** — cyim-lsp sha updated; vyakarana sha
  unchanged.
- **`src/plugins/lsp_glue.cyr`** — `_cyim_lsp_label_for_ref(uri,
  line, char)` now calls `lsp_ref_preview(uri, line, 80)` and
  appends the result after the coordinates separated by two
  spaces. Header comment "cyim-lsp bundle helpers consumed"
  lists the new helper alongside `lsp_uri_decode`. Mirror of
  cyim-lsp 1.4.0's `docs/examples/cyim_glue.cyr` reference glue
  change. Falls through cleanly when `lsp_ref_preview` returns
  0: `pl > 0` guards both the separator and the copy loop, so
  the label is byte-identical to 1.6.4's output in the
  no-preview-available case.

### Status

- **No new cyim ABI surface.** `lsp_ref_preview` is a
  cyim-lsp `[lib]` symbol — cyim's plugin ABI freeze (1.3.6 /
  ADR 0004) holds.
- **Minimum cyrius-lsp behaviour unchanged.** The reference
  glue still works against any LSP server that responds to
  `textDocument/references`; the preview helper just reads
  the file directly off disk.

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,212,856 B** (+2,160 over
  1.6.4's 1,210,696 B). Delta is the `lsp_ref_preview` call
  site in `_cyim_lsp_label_for_ref` (~200 B), the appended
  preview-copy branch (~600 B), and the `lsp_ref_preview` body
  pulled in from cyim-lsp 1.4.0's expanded distfile (~1,360 B
  after DCE — the helper isn't large but its file_read_all
  callout pulls extra io.cyr surface that DCE retains).

### Performance

References-picker label format runs once per `gr` invocation —
not on the highlight hot path. The added file_read_all per
reference is bounded by 1 MiB and N references typical < 50,
so the cumulative read cost for a typical `gr` is < 50 MiB
in the worst case (cold disk reads) and effectively zero for
warm cache. No new bench numbers needed; existing benches
unaffected.

### Verification

- `cyrius deps` — re-resolved, lock updated.
- `cyrius test` — **22 suites, 1113 assertions PASS**, 0 fail
  (unchanged vs 1.6.4 — the label change is exercised through
  the lsp smoke harness at runtime, not via tcyr).
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 23 src files + 1 plugin file (lsp_glue.cyr),
  0 warnings each.
- `cyrfmt --check` — 24 files clean.
- `tests/cli_smoke.sh` — 118 PASS.
- `tests/integration_smoke.py` — all PASS.
- `cyrius smoke tests/smcyr/lsp_fold.smcyr` — 1 PASS.
- `CYRIUS_DCE=1 cyrius build` — clean.

## [1.6.4] — 2026-05-09

**Basename-driven language detection.** Closes the dockerfile /
makefile gap that 1.6.2's `tests/lang.tcyr` pinned as
`-> "plain"`. vyakarana ships grammars for both, and for shell
rc dotfiles the `.sh` / `.bash` extension probe was never going
to catch (`.bashrc`, `.zshrc`, `.profile` aren't extension-
keyed). 1.6.4 adds a basename probe that runs *before* the
extension table.

### Added

- **`lang_basenames(i)` in `src/lang.cyr`** — parallel to
  `lang_exts(i)`, returns space-separated **case-sensitive**
  basenames per language. Populated for three indices:
  - shell (`.bashrc .bash_profile .bash_aliases .zshrc
    .zprofile .zshenv .profile`),
  - dockerfile (`Dockerfile dockerfile Containerfile
    containerfile`),
  - makefile (`Makefile makefile GNUmakefile` — GNU Make's
    documented lookup order).
- **`_lang_path_basename_eq(path, name)`** — case-sensitive
  equality with directory-boundary check. Char before the
  basename must be `/` (47) or path-start; `foo.Dockerfile` and
  `xMakefile` are correctly rejected.
- **`_lang_path_has_any_basename(path, list)`** — walks the
  space-separated list inline, mirrors
  `_lang_path_has_any_ext`'s no-allocation shape (64 B local
  buffer is enough for any sane basename).
- **`detect_language_from_path` runs basename probe first**,
  extension probe second. Ordering matters: a literal
  `Dockerfile` shouldn't fall through to `.dockerfile`-as-
  extension (which would case-fold to "dockerfile" and mismatch
  every grammar's extension list anyway).
- **`tests/lang.tcyr` extended 77 → 103 assertions** (+26 net):
  4 new test groups for 1.6.4 — basename routing (11
  assertions), directory-prefix paths (5), boundary correctness
  (5: `foo.Dockerfile`, `xMakefile`, `notbashrc`, `MAKEFILE`,
  `DOCKERFILE` — all "plain"), probe ordering (2:
  `Dockerfile.txt -> plain`, `Dockerfile.json -> json`). The
  pre-1.6.4 dockerfile / makefile fall-through assertions
  flipped from `-> "plain"` to their proper grammar names; two
  remaining assertions confirm the shell rc dotfiles excluded
  from the basename list (`.bash_logout`, `.zlogin`) still fall
  to "plain", as a defensive regression-guard against future
  list growth.

### Changed

- **`src/lang.cyr` header comment** rewritten to document the
  dual-probe shape: basename probe (case-sensitive,
  directory-boundary checked) runs first; extension probe
  (case-insensitive suffix) second. Examples updated to include
  `Dockerfile` and `subdir/.bashrc`.

### Conventions encoded (1.6.4)

- **Case sensitivity is the basename probe's contract.** GNU
  Make's lookup order distinguishes `Makefile` from `makefile`
  from `GNUmakefile`; Docker's spec is case-sensitive on
  `Dockerfile`. Encoding all canonical capitalizations
  explicitly is more honest than case-folding.
- **Excluded by design** (rarely customized; line-length cap on
  `lang_basenames`): `.bash_logout`, `.zlogin`, `.zlogout`. Add
  back if a user asks.
- **`Justfile` / `Containerfile`** — `Containerfile` is in (it's
  Docker's Podman alias). `Justfile` isn't — vyakarana doesn't
  ship a grammar for it, so there's no destination to route to.

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,210,696 B** (+1,800 over
  1.6.3's 1,208,896 B). Delta is `lang_basenames` if-chain
  (~600 B), `_lang_path_basename_eq` (~500 B),
  `_lang_path_has_any_basename` (~700 B). The basename probe
  added one extra walk per `detect_language_from_path` call,
  but that's one-shot per file open — not on the highlight hot
  path.

### Verification

- `cyrius test` — **22 suites, 1113 assertions PASS** (+26 over
  1.6.3 — net of +27 added in lang.tcyr minus -1 from the
  dropped fall-through verification group's reorganization).
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 23 src files, 0 warnings each.
- `cyrfmt --check` — 23 files clean.
- `tests/cli_smoke.sh` — 118 PASS.
- `tests/integration_smoke.py` — all PASS.
- `cyrius smoke tests/smcyr/lsp_fold.smcyr` — 1 PASS.
- `CYRIUS_DCE=1 cyrius build` — clean.

## [1.6.3] — 2026-05-09

**cyim-lsp 1.3.0 pickup.** Third bite of the 1.6.x catch-up
channel. cyim-lsp 1.3.0 is the toolchain-bump tag that publishes
the `cyrius.cyml [package].cyrius = 5.10.10` edit cyim 1.6.1
made in-tree. Pure infrastructure cut on the cyim-lsp side — no
`[lib]` source change, no example-glue change, no behaviour
delta. cyim's pickup is correspondingly minimal: one tag bump in
`cyrius.cyml`, one `cyrius deps`, gates re-verified.

The cyim-lsp distfile resolved at the new tag is byte-identical
to 1.2.1 modulo the version banner (2305 lines unchanged), so
cyim's binary is byte-identical to 1.6.2's: **1,208,896 B**.

### Changed

- **`cyrius.cyml`** — `[deps.cyim-lsp].tag = "1.3.0"` (was
  `"1.2.1"`). `cyrius deps` re-resolved; `lib/cyim-lsp.cyr`
  symlink now points at `~/.cyrius/deps/cyim-lsp/1.3.0/dist/cyim-lsp.cyr`.
- **`cyrius.lock`** — cyim-lsp sha updated; vyakarana sha
  unchanged.

### Status

- **No cyim source changes.** This is a banner-only consumer
  pickup. `src/plugins/lsp_glue.cyr`, all `[lib]` symbols, and
  every test stay byte-identical to 1.6.2.
- **ABI freeze** (1.3.6 / ADR 0004) holds. cyim-lsp 1.3.0 didn't
  touch the bundle; the freeze envelope wasn't tested by this
  cut.

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,208,896 B** (byte-identical
  to 1.6.2 — the cyim-lsp distfile didn't change shape, only the
  banner string). Recorded for the audit trail; no delta to
  explain.

### Verification

- `cyrius deps` — re-resolved, lock updated.
- `cyrius test` — **22 suites, 1087 assertions PASS**, 0 failures
  (unchanged from 1.6.2).
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 23 src files, 0 warnings each (per-file iteration).
- `cyrfmt --check` — 23 files clean.
- `tests/cli_smoke.sh` — 118 PASS.
- `tests/integration_smoke.py` — all PASS.
- `cyrius smoke tests/smcyr/lsp_fold.smcyr` — 1 PASS.
- `CYRIUS_DCE=1 cyrius build` — clean.

## [1.6.2] — 2026-05-09

**Grammar-routing catch-up — 11 → 45 languages.** Second bite of
the 1.6.x catch-up channel. 1.6.1 pulled in vyakarana 2.2.1's
distfile (with all 45 grammars compiled into the binary) but
cyim's `src/lang.cyr` extension table still routed only the
original 10 — leaving 35 grammars linked but unreachable from
`detect_language_from_path`. 1.6.2 wires them.

### Added

- **34 new language entries in `src/lang.cyr`**: `cyml` (dedicated
  grammar — moves from "toml" routing), `markdown`, `cpp`,
  `csharp`, `css`, `scss`, `html`, `xml`, `go`, `java`, `kotlin`,
  `swift`, `ruby`, `php`, `lua`, `haskell`, `ocaml`, `elixir`,
  `crystal`, `julia`, `zig`, `nix`, `vue`, `svelte`, `powershell`,
  `sql`, `ini`, `graphql`, `protobuf`, `terraform`, `asm_x86_64`,
  `llvm_ir`, `dockerfile`, `makefile`. `LANG_COUNT` 11 → 45.
  Indices 0..10 preserved unchanged so `lang_index("...")` callers
  see the same numeric slots they did at 1.6.0.
- **34 grammar `.cyml` files in `grammars/`** — copied from
  vyakarana 2.2.1's repo so `highlight_init`'s binary-relative
  `grammars/` resolution finds the definitions at runtime. cyim's
  `grammars/` count 11 → 45.
- **`tests/lang.tcyr` extended 37 → 77 assertions** across two new
  groups: "1.6.2 grammar catch-up" (33 cases — one per new
  extension or extension family) and "dockerfile/makefile fall
  through" (2 cases — pinning the current "no basename detection"
  behavior so a future bite can flip the assertions when basename
  routing lands).

### Changed

- **`.cyml` routing moves from `toml` to dedicated `cyml` grammar.**
  The 1.6.0-era comment in `lang.cyr` flagged this as "an M2-future
  bite" because vyakarana didn't ship a CYML grammar yet. vyakarana
  2.2.1 does, so the routing tracks the dedicated grammar.
  `tests/lang.tcyr:22` updated: `.cyml -> cyml` (was `.cyml -> toml`).
- **`lang.cyr` header comments** rewritten to document the 1.6.2
  conflict-resolution decisions (`.cyml` move, `.s/.S/.asm`
  defaulting to `asm_x86_64`, dockerfile/makefile basename gap).
  Includes a "refactor when 46+" note: at 45 entries the if-chain
  pattern is the practical limit; future growth earns a parallel-
  global-array refactor or a vyakarana-metadata query, ADR'd
  before going.
- **`src/cli.cyr:529`** — wrapped a 127-char line spotted during
  this pass's per-file lint sweep. Pre-existing warning unrelated
  to 1.6.2's scope, but cheap to clean while in the file's mental
  cache. (See "Fixed" — the 1.6.1 lint claim was inaccurate.)

### Fixed

- **1.6.1 lint-cleanliness claim was inaccurate.** That release's
  verification reported "0 warnings" from `cyrius lint src/*.cyr`,
  but cyrlint takes one file per invocation — the glob only
  surfaced the first expanded path's result. 1.6.2 verifies via
  per-file iteration: 23 files, 0 warnings each (after the
  `cli.cyr:529` wrap above).

### Conflict-resolution decisions

- `.cyml` → `cyml` (was `toml`; dedicated grammar wins).
- `.s` / `.asm` → `asm_x86_64` (primary dev arch default;
  aarch64 routing waits for content sniff or a `.cyimrc`
  filetype override, neither of which ships in 1.6.x).
- `.zsh` → `shell` grammar (vyakarana's grammar is
  `.sh`/`.bash`-only, but zsh shares enough syntax to highlight
  cleanly through it; cyim retains the `.zsh` extension routing
  it shipped at 1.6.0).
- `.cyr` / `.tcyr` / `.bcyr` / `.fcyr` → `cyrius` (vyakarana's
  grammar metadata only declares `.cyr`/`.cyml`; cyim's local
  routing covers test/bench/fuzz harness extensions).
- `Dockerfile` / `Makefile` → `plain` (no extension, basename
  detection unimplemented in 1.6.x).

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,208,896 B** (+4,960 over 1.6.1's
  1,203,936 B). Delta is the 34 new `lang_name`/`lang_exts`
  if-chain entries (~145 B per language pair after DCE). Notably
  *no* delta from the new grammar `.cyml` files — those are
  loaded at runtime, not compiled into the binary.

### Performance

Bench numbers within sampling noise of 1.6.1 — the extension table
is walked once per file open (worst case 45 string-suffix compares
on a path miss), not on the highlight hot path:

| Bench | 1.6.1 | 1.6.2 |
|-------|------:|------:|
| `highlight_buf_1MB_cyrius` | 318 ms | 312 ms |
| `highlight_buf_cache_hit_x1000` | 17.5 µs | 16 µs |
| `render_build_line_80c_x1000` | 270 µs | 294 µs |

### Deferred to later 1.6.x

- **Basename-driven detection** (`Dockerfile`, `Makefile`,
  `.bashrc`, `Justfile`, etc.) — adds a second probe path
  alongside extension matching. Small surface, but distinct
  enough to deserve its own bite.
- **Architecture refactor of `lang.cyr`** — at 45 entries the
  if-chain is at its practical limit. Further growth (or the
  basename surface above) earns a refactor; ADR before going.

### Verification

- `cyrius test` — **22 suites, 1087 assertions PASS** (+40 vs 1.6.1).
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 23 files, 0 warnings (per-file iteration).
- `cyrfmt --check` — 23 files clean.
- `tests/cli_smoke.sh` — 118 PASS.
- `tests/integration_smoke.py` — all PASS.
- `cyrius smoke tests/smcyr/lsp_fold.smcyr` — 1 PASS.
- `CYRIUS_DCE=1 cyrius build` — clean.

## [1.6.1] — 2026-05-09

**Toolchain + vyakarana catch-up cut.** First step of the 1.6.x
catch-up channel: cyrius pin 5.9.16 → 5.10.10, vyakarana
1.0.2 → 2.2.1 (skipping every 1.x release in between — 14 minor
cuts). The only breaking surface across that vyakarana window is
the 2.0.0 `tokenize_source` removal, replaced by the streaming
primitive (`tokenize_stream_new` / `_feed` / `_finish` / `_free`).
cyim has a single call site (`src/highlight.cyr`); migration is
the documented 5-line dance plus a null-handle guard. cyim-lsp's
own toolchain pin moves in lockstep (5.9.16 → 5.10.10) but its
tag stays at 1.2.1; a 1.3.0 publish lands later in 1.6.x.

The 35 new vyakarana grammars (cpp, csharp, css, dockerfile,
elixir, go, graphql, haskell, html, ini, java, kotlin, lua,
makefile, markdown, ocaml, php, protobuf, ruby, scss, sql,
swift, xml, zig + powershell, crystal, julia, vue, svelte, nix,
terraform + asm_aarch64, asm_x86_64, llvm_ir, cyml) are linked
into the binary by the distfile but `src/lang.cyr`'s extension
table still routes only the original 10. Full extension-routing
catch-up is the 1.6.2 bite.

### Changed

- **`cyrius.cyml`** — `[package].cyrius` 5.9.16 → 5.10.10;
  `[deps.vyakarana].tag` 1.0.2 → 2.2.1. Local toolchain conformed
  via `cyriusly use 5.10.10` per the pin-authority rule.
- **`src/highlight.cyr`** — `tokenize_source(src, lang)` replaced
  by `tokenize_stream_new` + `_feed(s, src, strlen(src))` +
  `_finish(s, tb)` + `_free(s)`, with a `if (s == 0) { return 0; }`
  guard preserving 1.x's null-on-unregistered-grammar contract.
  Cache wiring at `buf_set_cache` unchanged. Header comments at
  `:9` and `:21` rewritten to describe the streaming shape.
- **`cyim-lsp/cyrius.cyml`** (sibling repo) — `[package].cyrius`
  5.9.16 → 5.10.10. No `[lib]` source change; consumer-side
  picks up the new toolchain without a tag bump (cyim's
  `[deps.cyim-lsp].tag` stays at `1.2.1`).

### Performance

Cold tokenize regresses as expected from vyakarana 2.0.0's
per-call alloc overhead — the streaming benefit (memory bound by
per-token state) only realizes for streaming consumers, and cyim
calls feed once with the whole buffer:

| Bench | 1.5.3 | 1.6.1 | Δ |
|-------|------:|------:|--:|
| `highlight_buf_1MB_cyrius` | 253 ms | 318 ms (avg of 3 runs) | **+25 %** |
| `highlight_buf_cache_hit_x1000` | 16 µs | 17.5 µs | **+10 %** |

Cache-hit path (the hot path during interactive editing) is
within sampling noise. 1MB cold is a one-shot at file open, so
the regression is invisible at the user-visible latency layer.
Full bench numbers logged in `tests/perf.bcyr` runs.

### Binary

- `build/cyim` (CYRIUS_DCE=1): **1,203,936 B** (+238,504 B over
  1.6.0's 965,432 B). Delta is dominated by vyakarana 2.2.1's
  45 bundled grammars vs 1.0.2's narrower set; `lib/vyakarana.cyr`
  is now 4,036 lines. The binary-size soft cap inherited from
  vyakarana's 1.13.0 ADR no longer applies cleanly to the
  consumer; reviewing in the 1.7.0 closeout.

### Verification

- `cyrius test` — **22 suites, 1047 assertions PASS**, 0 failures.
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 0 warnings.
- `cyrius bench` — completed; numbers above.
- `CYRIUS_DCE=1 cyrius build` — clean.

### Migration notes (for future readers)

The 1.x → 2.x recipe in vyakarana's CHANGELOG is mechanical for
single-call consumers. cyim's only complication was preserving
the v1.x null-on-unregistered-grammar contract: `tokenize_source`
returned 0 on unknown grammar names; `tokenize_stream_new` does
the same, but `_feed` / `_finish` would dereference a null handle.
The explicit `if (s == 0) { return 0; }` covers that.

## [1.6.0] — 2026-05-07

**Minor — VIM-style marks (`m<letter>` / `'<letter>`).**

The first feature minor of the post-1.5.x cycle. Single theme:
marks. Per-buffer (a-z) and global (A-Z) namespaces, set via
`m<letter>` and jumped via `'<letter>`. Vim-muscle-memory feature
that vim users miss within ~2 days. ~150 LOC plus tests.

### Added

- `src/marks.cyr` — new module. Per-buffer marks: vec of 24 B
  records `{buf_ptr, key, offset}`; linear lookup (max 26
  entries per buffer × few buffers — small enough for naive
  walk). Global marks: 26 × 16 B static array indexed by
  `key - 'A'`; each slot is `{buf_ptr, offset}`. Sentinel for
  "unset" is `buf_ptr == 0` — the static array's default-zero
  state is therefore already valid as "all unset", so callers
  that skip `marks_init()` (e.g. fuzz harnesses) see a coherent
  state.
- Public API: `marks_init()` / `marks_set(b, key, offset)` /
  `marks_get(b, key) -> off or -1` /
  `marks_set_global(key, b, offset)` /
  `marks_get_global(key) -> rec ptr or 0` / `marks_count(b)`.
- `KEY_M = 109` and `KEY_QUOTE = 39` constants in `src/mode.cyr`
  — joins the existing `KEY_CTRL_W` / `KEY_G` prefix family.
- `bl_find_by_buf(s, b)` helper in `src/buflist.cyr` — reverse
  lookup from buf pointer to buflist index (used by global-mark
  cross-buffer jumps to resolve `bl_set_active`).

### Changed — `src/mode.cyr`

- NORMAL-mode dispatch now latches `m` and `'` as prefixes
  (alongside `Ctrl-W` and `g`). Generalized prefix-resolution
  branch handles all four:
  - `m<a-z>` → `marks_set(editor_buf(s), key, buf_cursor(...))`
  - `m<A-Z>` → `marks_set_global(key, editor_buf(s), buf_cursor(...))`
  - `'<a-z>` → `buf_move` to `marks_get(b, key)`, clamped to
    `buf_len(b)` defensively (post-delete drift safety)
  - `'<A-Z>` → resolve global mark; if buffer differs, switch
    via `bl_find_by_buf` + `bl_set_active` + `window_set_buf_idx`,
    then `buf_move`. Defensive guard: only proceed if `target_b`
    is non-zero (defends against stale buf pointers from closed
    buffers).
- All four mark dispatches return `ACT_NONE`. Marks don't
  participate in the action pipeline — the mode-dispatch path
  performs the work directly.

### Wiring — `src/main.cyr`

- `include "src/marks.cyr"` after `cyimrc.cyr`, before `mode.cyr`
  (mode.cyr's prefix dispatch calls `marks_set` / `marks_get`,
  so marks.cyr must come first in the TU).
- `marks_init()` called from `main()` after `cyim_lsp_init()`.

### Tests

- New `tests/marks.tcyr` — 50 assertions across 19 test groups:
  init / round-trip / multiple marks / overwrite / cross-buffer
  isolation / out-of-range key rejection / unset-key sentinel /
  global set + get + override / global out-of-range / dispatch
  integration (m<letter> sets at cursor; '<letter> jumps;
  unset-mark jump no-op; post-EOF mark clamped to buf_len;
  m<digit> swallowed; '<digit> swallowed; m<UPPER> sets global;
  '<UPPER> jumps within same buffer).
- `fuzz/driver.fcyr` — added `include "src/marks.cyr"` before
  `mode.cyr`. Fuzz exercises the new prefix dispatch under
  random keystrokes; surfaced (and fixed) a NULL-buf-ptr corner
  case where `marks_get_global` would return a stale-zero record
  if `marks_init` hadn't run. Fix: changed sentinel from
  `offset == -1` to `buf_ptr != 0`; added defensive
  `target_b != 0` guard in mode.cyr's `'<UPPER>` branch.

### Verification

- `cyrius build` (DCE) — OK; binary 965,432 B (+7,712 B over
  v1.5.3's 957,720 B; deltas: marks.cyr (~3.5 KB after DCE) +
  mode.cyr prefix branches (~2 KB) + bl_find_by_buf (~200 B) +
  marks_init wiring (~50 B) + tests aren't in the binary).
- `cyrius test` — **21 suites all PASS** (+1 marks.tcyr; 50 new
  assertions). 88 plugin assertions unchanged.
- `cyrius fuzz` — 3 PASS (driver fuzz exercises the new prefix
  paths against 5K random keystrokes).
- `cyrius smoke` — 1 PASS (LSP harness still green).
- `cyrius bench` — perf within noise of v1.5.3 (mark ops aren't
  in any benched workload; binary growth is +7.7 KB).
- `cyrius lint` — 0 warnings on touched files.
- `build/cyim --version` — `cyim 1.6.0`.

### Plugin ABI freeze unchanged

No plugin ABI surface changes. `KEY_M` / `KEY_QUOTE` join the
constant family but don't shift any existing symbol. Mark
storage is module-internal; not part of the plugin ABI. Plugin
prefix-keys (`plugin_register_normal_prefix_key`) continue to
work — built-ins (Ctrl-W, gg, m, ') still win on conflict per
ADR 0003 §3.

### Limitations / future work

- **No edit-time mark adjustment.** Vim shifts marks across
  edits (insertion shifts later marks forward; deletion shifts
  back; deletion crossing a mark invalidates it). cyim 1.6.0
  stores raw offsets and clamps to `buf_len(b)` on jump
  (defensive against post-delete drift). Edit-tracking is a
  1.6.x patch candidate.
- **No persistence** (vim's `viminfo`). Marks live in memory
  for the cyim session. Persistence is post-1.6 if the surface
  earns it.
- **No special marks** (`'.` last-edit, `''` last-jump,
  `'<` / `'>` selection bounds, etc.). Vim's special-mark set
  is large; cyim 1.6.0 ships only the named marks (a-z A-Z).
- **No backtick variant** (`` `<letter> `` for exact column
  vs. `'<letter>` for line). cyim's `'<letter>` already lands
  at the exact recorded offset (cyim is byte-oriented; "line"
  vs "exact column" is a non-distinction). Single primitive
  is enough.
- **No `:marks` ex-command** to list all set marks. `marks_count`
  + a future iteration helper would back this; deferred to
  1.6.x if asked.

## [1.5.3] — 2026-05-07

**Closes 3 of 4 LOW closeout findings from v1.5.2's audit.**
F-CO-2 stays informational (refactor wait-for-third-consumer);
F-CO-1 / F-CO-3 / F-CO-4 all addressed.

### Changed

- `cyrius.cyml [deps.cyim-lsp].tag` 1.2.0 → 1.2.1.
- `lib/cyim-lsp.cyr` regenerated by `cyrius deps`. cyim-lsp 1.2.1
  is the first real bundle source change since 1.0.3 (+77 lines:
  `_lsp_hex_digit` + `lsp_uri_decode`).

### Closeout finding fixes

#### F-CO-1 — multi-iter bench

`tests/perf.bcyr` converted from single-iter to multi-iter
sampling for the noise-prone short-runtime benches. Mutating
benches (gap-buffer fills) keep single-iter (multi-iter would
need fresh buffers each round, complicating the harness for no
signal gain).

| Bench | Iters | Result |
|---|---|---|
| `render_build_line_80c_x1000` | 10 | 250μs avg (min=249, max=253). The +18% at 1.5.1 (252μs single-iter vs. 214μs M6 baseline) was 1-iter sampling noise — multi-iter shows the perf is stable. |
| `highlight_buf_cache_hit_x1000` | 10 | 15μs avg (min=15, max=16). Slight improvement over M6's 17μs. |
| `search_forward_10MB_worst_case` | 3 | 102.1ms avg (min=101.6, max=102.5). Improvement over M6's 108ms. |
| `search_forward_10MB_best_case` | 3 | 778ns avg. |
| `search_forward_10MB_worst_case_ic` | 3 | 163.3ms avg. |
| `buf_move_10K_cycles_10MB` | 3 | 46.975ms avg (min=44.8, max=49.9). Improvement over M6's 51ms. |

`BENCHMARKS.md` updated with multi-iter v1.5.3 row + commentary
on the F-CO-1 verdict (no real regression — sampling noise).

#### F-CO-3 — defensive prefix-clear in `plugin_list_display`

`src/plugin.cyr` `plugin_list_display(s, items, count, on_select)`
now calls `editor_set_prefix(s, 0)` at the top, defensively
clearing any latched NORMAL-mode prefix (e.g. `KEY_G` after `g`).
Unreachable today (the only caller — `:lsp-find-refs` / `gr` —
completes dispatch before yielding), but the guard closes the
corner case once.

`tests/plugin.tcyr` extended: 85 → 88 assertions (+3 for the
prefix-clear case: latch KEY_G pre-display, verify prefix is 0
post-display, dismiss cleanly).

#### F-CO-4 — URL-decode for `file://` URIs

`src/plugins/lsp_glue.cyr` cross-file branches now call
`lsp_uri_decode(uri + 7)` (cyim-lsp 1.2.1 public bundle helper)
instead of slicing `uri + 7` raw. Files with spaces / non-ASCII
/ percent-encoded paths now load correctly via cross-file
goto-def + refs quickfix. Two call sites updated:
- `_cyim_lsp_ex_goto_def` cross-file branch
- `_cyim_lsp_on_ref_select`

Both surface a typed status message on decode failure (alloc
only — malformed escapes literal-pass per `lsp_uri_decode`'s
contract, so most decode "failures" don't reach this path).

### Verification

- `cyrius build` (DCE) — OK; binary 957,720 B (+1,352 B over
  v1.5.2's 956,368 B; deltas: F-CO-3 prefix-clear (~80 B),
  F-CO-4 lsp_uri_decode call sites + status messages (~400 B),
  cyim-lsp 1.2.1's `lsp_uri_decode` + `_lsp_hex_digit` linked
  in (~870 B), F-CO-1 bench loops (~50 B in tests/, not in
  binary).
- `cyrius test` — 20 suites all PASS, 88 plugin assertions
  (+3).
- `cyrius fuzz` — 3 PASS.
- `cyrius smoke` — 1 PASS.
- `cyrius bench` — multi-iter sampling shows the v1.5.x cycle
  perf is within noise of M6 baseline; no regressions.
- `cyrius lint` — 0 warnings on touched files.
- `build/cyim --version` — `cyim 1.5.3`.

### v1.5.x cycle status — closed (actionable findings)

The 1.5.x cycle's actionable closeout findings are now all
addressed:
- ~~F-CO-1~~ ✅ multi-iter bench, no real regression
- F-CO-2 — informational; defer to 3rd consumer per
  wait-for-third rule
- ~~F-CO-3~~ ✅ defensive prefix-clear shipped
- ~~F-CO-4~~ ✅ URL-decode shipped (closes the deferred LSP
  polish row simultaneously)

Remaining deferred LSP polish (carry-over candidates for 1.5.x
patches or 1.6.0): reference previews, open-in-split, arrow keys
in list mode.

1.6.0 may now open. See
[`docs/development/roadmap.md`](docs/development/roadmap.md).

## [1.5.2] — 2026-05-07

**Closeout cut for the 1.5.x cycle. Pure verification — no
runtime behaviour changes.**

Per cyim's CLAUDE.md "Closeout Pass" policy ("Run a closeout
pass before tagging X.Y.0 or X.0.0. Ship as the last patch of
the current minor"). All 11 audit steps walked end-to-end;
findings filed in
[`docs/audit/2026-05-07-1.5x-closeout.md`](docs/audit/2026-05-07-1.5x-closeout.md).

### Closeout audit summary

All 11 CLAUDE.md closeout steps PASS:

1. **Full clean test + fuzz + smoke** — `rm -rf build && cyrius
   deps && cyrius build` clean; `cyrius test` 20 suites, ~973
   assertions across the tcyr suite (plugin.tcyr 33 → 85 across
   the 1.x cycle; +52 from 1.4.2 / 1.4.3 / 1.5.0 / 1.5.1);
   `cyrius fuzz` 3 PASS; `cyrius smoke` 1 PASS
   (`tests/smcyr/lsp_fold.smcyr`); `cyrius lint` 0 warnings on
   touched files.
2. **Benchmark baseline** — within noise of historical
   [`BENCHMARKS.md`](BENCHMARKS.md). One sub-finding (F-CO-1)
   re render_build_line; tracked.
3. **Dead-code audit** — 359 dead symbols. All expected
   (frozen ABI surface per ADR 0004 + DCE-stripped stdlib). 0
   cyim-source true-dead.
4. **Refactor pass** — F-CO-2 flagged: "load uri + jump to lc"
   pattern at 2 instances; defer extraction until 3rd consumer
   per cyim's wait-for-third rule.
5. **Code review pass** — walked 1.4.0..1.5.1 diff
   end-to-end. F-CO-3 flagged (defense-in-depth: prefix-clear
   on `plugin_list_display`). No missed guards / off-by-ones /
   silently-ignored errors.
6. **Cleanup sweep** — 2 stale comments updated in
   `src/plugin.cyr` (referenced pre-1.4.0 state). No orphaned
   files; no unused includes.
7. **Security re-scan** — 0 sys_system uses; all new `var
   buf[N]` bounded; no unchecked syscalls. F-CO-4 flagged:
   URL-decode for `file://` URIs (UX, not security).
8. **Downstream check** — cyim-lsp 1.2.0 folds cleanly. Smoke
   confirms protocol path works against a real `cyrius-lsp`.
9. **Doc sync** — CHANGELOG, state.md, roadmap (rewritten this
   pass), ADR 0004 (1.4.2 + 1.5.0 amendments) all in sync.
10. **Version verify** — VERSION / cyrius.cyml / version_str /
    CHANGELOG header / git tag / `--version` all align.
11. **Full clean build** — OK from `rm -rf build`.

### Severity summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 4 (F-CO-1, F-CO-2, F-CO-3, F-CO-4) |

All 4 LOW findings are tracked in
[`docs/development/roadmap.md`](docs/development/roadmap.md)'s
1.5.x cycle as patch-sized items to address before 1.6.0.

### Documentation

- **`docs/development/roadmap.md`** — rewritten this pass:
  closed-milestones list trimmed (M0–M7 + v1.0–v1.4 verbose
  descriptions removed); deferred LSP work organized into a
  v1.5.x cycle section; closeout findings tracked as 1.5.x
  patch items; demand-gated table refreshed (clipboard /
  terminal / macros / folding / marks / `:make` / plugin-system
  refusal).
- **`docs/audit/2026-05-07-1.5x-closeout.md`** — new audit doc.
  All 11 closeout steps documented end-to-end; findings logged;
  severity triage (0 CRITICAL / 0 HIGH / 0 MEDIUM / 4 LOW).
- **`src/plugin.cyr`** — two stale comment blocks updated to
  reflect 1.4.0+ reality (production wiring active via
  cyim-lsp + trailing_ws; render layer paints diags).

### Verification

- `cyrius build` (DCE) — OK; binary 956,368 B (byte-identical
  to v1.5.1 modulo `_VERSION_STR_CYIM` — pure verification cut,
  no runtime code changes; comment edits don't affect codegen).
- `cyrius test` — 20 suites all PASS, no regressions.
- `cyrius fuzz` — 3 PASS.
- `cyrius smoke` — 1 PASS.
- `cyrius bench` — runs clean.
- `cyrius lint` — 0 warnings on touched files.
- `build/cyim --version` — `cyim 1.5.2`.

### Coordination

The 1.4.x → 1.5.x arc is closed out. Next minor (1.6.0) opens
after the 4 closeout findings ship as 1.5.x patches (or are
explicitly accepted as deferred). See roadmap §
"v1.5.x Cycle — Deferred LSP Polish + Closeout".

## [1.5.1] — 2026-05-07

**cyim-lsp 1.2.0 pickup — `:lsp-find-refs` / `gr` becomes a
navigable quickfix picker.** Closes the last deferred LSP UI gap
and the last named consumer of cyim 1.5.0's `plugin_list_display`
ABI. Pressing `gr` over a Cyrius symbol now pops up a bottom-
anchored picker showing every reference site as
`filename:line:col`. j/k navigates, Enter loads the file
(`plugin_buf_load_file` dedups against the active buflist) and
jumps the cursor; Esc/q dismisses. The status-bar count fallback
from 1.4.x / 1.5.0 is gone.

### Changed

- `cyrius.cyml [deps.cyim-lsp].tag` 1.1.0 → 1.2.0.
- `lib/cyim-lsp.cyr` regenerated by `cyrius deps` (banner-only —
  the cyim-lsp `[lib]` source is unchanged across the 1.0–1.2
  series; same 2228 lines).
- `cyrius.lock` updated for the new dist sha.

### Updated — `src/plugins/lsp_glue.cyr`

- `_cyim_lsp_ex_find_refs(s)` rewritten — drops the
  `_cyim_lsp_refs_msg` static buffer + status-bar count format.
  New flow: parse the response into parallel
  `(uri, line, char)` vecs, build labels, stash payload in
  module globals, call `plugin_list_display(s, labels, count,
  &_cyim_lsp_on_ref_select)`. Empty-result case still surfaces
  `"lsp: no references found"` instead of an empty popup.
- New helpers (mirror cyim-lsp 1.2.0's reference glue):
  - `_cyim_lsp_parse_refs(body, blen, uris, lines, chars)` —
    walks the response array using the bundle's
    `_lsp_diags_find` / `_lsp_diag_parse_int` helpers.
  - `_cyim_lsp_label_for_ref(uri, line, char)` — formats
    `filename:line:col` (1-indexed display, last path segment
    of the URI).
  - `_cyim_lsp_on_ref_select(s, idx)` — `plugin_list_display`
    callback. Looks up `(uri, line, char)` at idx, calls
    `plugin_buf_load_file`, materializes content, converts
    `(line, char)` → byte offset, `buf_move`s.
- New module-level globals: `_cyim_lsp_refs_uris`,
  `_cyim_lsp_refs_lines`, `_cyim_lsp_refs_chars`. Single picker
  active at a time; second `:lsp-find-refs` replaces them
  cleanly per `plugin_list_display` semantics.

### Tests / verification

- `cyrius build` (DCE) — OK; binary 956,368 B (+2,856 B over
  v1.5.0's 953,512 B; deltas: refs parser + label builder +
  on_select callback + module globals).
- `cyrius test` — 20 suites all PASS, no regressions.
- `cyrius fuzz` — 3 PASS.
- `cyrius smoke` — 1 PASS (`tests/smcyr/lsp_fold.smcyr` still
  green; protocol path unchanged).
- `cyrius lint` — 0 warnings on touched files.
- `build/cyim --version` — `cyim 1.5.1`.

### What's now user-visible (full LSP surface)

With cyim 1.5.1 + cyim-lsp 1.2.0:

- `gd` over a symbol → goto-def (same-file: cursor moves; cross-
  file: file loads + cursor jumps).
- `gr` over a symbol → references quickfix popup; j/k/Enter to
  navigate + jump; Esc/q to dismiss.
- `:lsp-goto-def`, `:lsp-find-refs`, `:lsp-restart`, `:lsp-status`
  all continue to work; the keymap surfaces are additional, not
  replacements.
- Server-pushed diagnostics → status-segment counts + inline
  render via `diagnostic_provider`.
- `gg` (built-in start-of-file) wins on conflict against any
  plugin attempt to bind `(KEY_G, 'g')`.

### Still deferred (post-cyim 1.5.x)

- URL-encoded `file://` URIs (e.g. spaces) — paths with
  percent-encoded bytes won't load.
- Reference previews — labels show `filename:line:col` only;
  no source-line snippets.
- Open-in-split — selecting a ref switches the active buffer's
  window. Future cyim ABI extension.

## [1.5.0] — 2026-05-07

**Minor — `plugin_list_display` ABI: a bottom-anchored popup picker.**

Closes the third deferred ABI from cyim 1.4.2's ADR 0004 amendment
("`plugin_list_display` is the size of a minor release, not a
patch — popup-overlay subsystem"). v1.5.0 ships the picker with a
modest, focused shape: bottom-anchored, j/k/Enter/Esc/q surface,
single active list at a time, no nested stacking. cyim-lsp 1.1.x
or 1.2.0 will activate `:lsp-find-refs` as a navigable quickfix
on top.

### Added — plugin ABI

- `plugin_list_display(s, items, count, on_select)` — display a
  popup picker over the bottom of the buffer area. Items: a vec
  of NUL-term cstrings (caller-owned for the lifetime of the
  picker). on_select signature: `fn(s, index) -> 0`. Storage is
  module-global — only one list at a time; calling
  `plugin_list_display` while another list is up replaces the
  old (the old `on_select` is dropped without firing).
- `plugin_list_active()` / `_count()` / `_index()` / `_items()` —
  public accessors. Tests + the render layer use these instead of
  reaching into the underlying globals.
- Internal helpers: `_plugin_list_dismiss` / `_plugin_list_next` /
  `_plugin_list_prev` / `_plugin_list_select(s)`. Driven by
  `editor_dispatch`'s list-mode interception path; plugins
  normally don't call these.

### Added — dispatch interception

- `editor_dispatch` (`src/mode.cyr`) — at the very top, before
  any mode-specific dispatch, when `_plugin_list_active == 1`:
  - `j` / `k` → next / prev (clamped at 0 and count - 1)
  - `Enter` / `LF` → fire `on_select(s, current_index)` then dismiss
  - `Esc` / `q` → dismiss without firing
  - All other keys swallowed; return ACT_NONE so motion / edit
    pipelines stay no-ops and the buffer stays clean
  - **Order matters in `_plugin_list_select`:** dismiss first,
    then call `on_select` — lets the callback call
    `plugin_list_display` again for chained pickers without
    leaking active state.
- Arrow keys NOT bound at v1.5.0 (would require driver-side
  `editor_feed` changes). The j/k/Enter/Esc/q surface is the
  documented input set.

### Added — popup overlay rendering

- `_render_list_overlay(s, rows, cols)` (`src/render.cyr`) —
  drawn last in `render_frame`, after both buffer rows AND
  `render_status`. Overlays the bottom of the buffer area
  (rows-N..rows-1) while leaving the status row (row `rows`)
  visible. Window-start auto-scrolls to keep the current
  selection in view; cap at 10 visible rows.
- Reverse-video on the current row (`\x1b[7m`...`\x1b[0m`),
  padded to full width so the highlight extends edge-to-edge.
  Item labels truncated to `cols`.
- Terminal cursor parked at column 1 of the highlighted row, so
  the focus indicator matches the visible highlight (the buffer-
  cursor positioning above is overridden when list is active).
- Both single-window (`render_frame`) and multi-window
  (`_render_frame_multi`) paths invoke the overlay before
  returning.

### Tests

- `tests/plugin.tcyr` extended: 58 → 85 assertions (+27 across
  12 new groups — display latches state, j/k navigation, clamping,
  buffer untouched during list mode, Enter / LF fire on_select,
  Esc / q dismiss without firing, dispatch resumes normal mode
  after dismiss).
- `tests/perf.bcyr` — added `include "src/plugin.cyr"` (was the
  only test file missing the include; now matches the 15 others)
  and a `plugin_init()` call in `main()`. Required because
  `mode.cyr` references `_plugin_list_active` directly — narrow
  test files that include `mode.cyr` must also include
  `plugin.cyr` to satisfy the var ref. `cyrius bench tests/perf.bcyr`
  now runs clean.
- `cyrius test` — 20 suites all PASS.
- `cyrius fuzz` — 3 PASS.
- `cyrius bench` — runs clean across all 9 perf cases.
- `cyrius smoke` — 1 PASS (LSP harness still green).
- `cyrius lint` — 0 warnings on touched files.

### Verification

- `cyrius build` (DCE) — OK; binary 953,512 B (+3,064 B over
  v1.4.3's 950,448 B; deltas: list-display ABI + helpers
  (~600 B), dispatch interception block (~250 B),
  `_render_list_overlay` (~1.5 KB), padding / accessor
  scaffolding (~700 B)).
- `build/cyim --version` — `cyim 1.5.0`.
- ABI compatibility: `plugin_list_display` is additive — cyim 1.x
  ABI freeze (ADR 0004) holds. No frozen-from-1.3.6 symbol
  changed shape.

### Coordination — cyim-lsp 1.1.x / 1.2.0

- Today, `:lsp-find-refs` and `_cyim_lsp_gr` (cyim-lsp 1.1.0)
  surface only a count in the status bar. With cyim 1.5.0
  shipping, cyim-lsp can build per-reference cstring labels
  ("FILE:LINE:COL — preview"), call `plugin_list_display(s,
  labels, count, on_select)` where `on_select(s, idx)` looks up
  the corresponding `(uri, line, char)` from a parallel payload
  vec, calls `plugin_buf_load_file(s, dest_path)`, and
  `buf_move`s to the destination.
- Targeting cyim-lsp 1.1.x (additive within the 1.1 series) or
  1.2.0 (clean signaling that the consumer-side surface grew
  meaningfully).

## [1.4.3] — 2026-05-07

**cyim-lsp 1.1.0 pickup — `gd` / `gr` and cross-file goto-def
activate.** The 1.4.2 ABI extensions now have a live consumer:
cyim-lsp 1.1.0's reference glue uses
`plugin_register_normal_prefix_key` (binds `gd` → goto-def, `gr`
→ find-refs) and `plugin_buf_load_file` (cross-file definition
jumps). User-visible: pressing `g` then `d` over a Cyrius
symbol jumps to its definition; `g` then `r` shows reference
count; cross-file definitions actually jump to the destination
file (was: "cross-file jump deferred" status message).

### Changed

- `cyrius.cyml [deps.cyim-lsp].tag` 1.0.3 → 1.1.0.
- `lib/cyim-lsp.cyr` regenerated by `cyrius deps` (banner-only
  change — cyim-lsp's `[lib]` source unchanged at 1.1.0; same
  2228 lines).
- `cyrius.lock` updated for the new dist sha.

### Updated — `src/plugins/lsp_glue.cyr`

- Added `_cyim_lsp_gd(s)` and `_cyim_lsp_gr(s)` handlers — both
  delegate to the existing ex-command implementations
  (`_cyim_lsp_ex_goto_def`, `_cyim_lsp_ex_find_refs`) and return
  ACT_NONE so the prefix-dispatch pipeline gets a clean action_id.
- `_cyim_lsp_ex_goto_def(s)` cross-file branch — previously
  `editor_set_status(s, "lsp: definition in another file
  (cross-file jump deferred)"); return 0;`. Now strips `file://`
  prefix from the destination URI, calls
  `plugin_buf_load_file(s, dest_path)`, materializes the loaded
  buffer's content via `_cyim_lsp_buf_to_flat`, converts
  `(line, character)` to a byte offset via
  `lsp_pos_lc_to_offset`, and `buf_move`s the new buffer's
  cursor to the destination. Same-file branch unchanged.
- `cyim_lsp_init()` — registers `(KEY_G, 'd', _cyim_lsp_gd)` and
  `(KEY_G, 'r', _cyim_lsp_gr)` via `plugin_register_normal_prefix_key`.
  Built-ins win on conflict, so `gg` (cyim's
  `ACT_MOVE_FILE_START`) shadows any plugin attempt to bind
  `(KEY_G, 'g')`.

### Deferred (still waiting on cyim 1.5.0)

- **Reference quickfix list** — `:lsp-find-refs` and `gr`
  surface only a count in the status bar. The popup-overlay
  ABI (`plugin_list_display`) is a v1.5.0 minor; cyim-lsp 1.1.x
  or 1.2.0 will activate the navigable list on top.
- **URL-encoded `file://` URIs** — the cross-file branch slices
  bytes 7+ as the absolute path, no percent-decoding. Files
  with spaces / non-ASCII in paths won't load. Deferred until
  the corner case surfaces.

### Tests / verification

- `cyrius build` (DCE) — OK; binary 950,448 B (+560 B over
  1.4.2's 949,888 B; gd/gr handler bodies + prefix-key
  registrations + cross-file load + materialize-and-jump path).
- `cyrius test` — 20 suites all PASS (no regressions).
- `cyrius fuzz` — 3 PASS.
- `cyrius smoke` — 1 PASS (`tests/smcyr/lsp_fold.smcyr` from
  1.4.1 still green; protocol path unchanged).
- `cyrius lint` — 0 warnings on touched files.
- `build/cyim --version` — `cyim 1.4.3`.

## [1.4.2] — 2026-05-07

**Plugin ABI extensions — additive surface for cyim-lsp 1.1.0
to consume.** Two new public registrations + one operation,
plus the long-stubbed `gg` motion finally lands. All additive
per ADR 0004's freeze terms — no breaking changes to the 1.x
ABI surface.

### Added — plugin ABI

- `plugin_register_normal_prefix_key(prefix, key, fp)` — register
  a two-byte NORMAL-mode sequence (e.g. `(KEY_G, 'd')` → fp).
  Plugin fp signature: `fn(s) -> action_id`. Plugin-returned
  actions flow through cyim's standard motion / edit pipelines
  in `editor_step`. Built-ins win on conflict per ADR 0003 §3.
  Plugin prefix-keys are not permitted to drive mode transitions
  (the prefix dispatch returns immediately, bypassing
  MODE_NORMAL's transition guards) — plugins that need mode
  changes register an `ex_command` instead. Storage: 24 B record
  `{prefix, key, fp}` in `_plugin_normal_prefix_keys` vec.
- `plugin_buf_load_file(s, path)` — load a NUL-term cstring
  path into a new buffer + switch the editor's active buffer to
  it. Wraps the same dedup / buflist / window-update bookkeeping
  `:e <file>` uses. Returns the buf ptr on success, 0 on failure
  (sets `editor_last_error` for typed reporting:
  `ERR_NO_FILE_NAME`, `ERR_FILE_NOT_FOUND`, `ERR_FILE_TOO_LARGE`).
  Use case: cyim-lsp 1.1.0+ cross-file goto-def.

### Added — built-ins

- `ACT_MOVE_FILE_START = 109` — finally wired. `motion_apply`
  routes it to `motion_file_start` (returns position 0). The
  function existed since M1 as a stub; multi-byte input
  dispatch needed the v1.4.2 prefix-dispatch generalization
  before `gg` could resolve.
- `KEY_G = 103` — new prefix constant. NORMAL-mode `g` sets
  `editor_prefix(s)`; the next byte resolves: `gg` →
  `ACT_MOVE_FILE_START` (built-in), anything else falls
  through to plugin lookup.

### Changed — internals

- `editor_dispatch` (`src/mode.cyr`) — prefix handling
  generalized beyond the original Ctrl-W special case. When
  `editor_prefix(s)` is non-zero, dispatch on the prefix value:
  Ctrl-W → window navigation (unchanged); KEY_G → built-in `gg`
  + plugin lookup; any other prefix → plugin lookup only. The
  `if (editor_prefix(s) == KEY_CTRL_W)` block became
  `if (editor_prefix(s) != 0)` with branches per prefix value.
- `_buf_load_file_into_active(s, path)` (`src/command.cyr`,
  new) — extracted from `_cmd_e` so both `:e <file>` and
  `plugin_buf_load_file` share the dedup + load + buflist +
  window-update bookkeeping. `_cmd_e` now thin-wraps the
  helper. Behaviour-neutral refactor.
- `motion_file_start(b)` comment updated to reflect that
  multi-byte dispatch IS now wired (was: "not yet wired in
  mode.cyr").

### Tests

- `tests/plugin.tcyr` extended: 33 → 58 assertions (+25 across
  9 new test groups — prefix-key registration, lookup,
  dispatch flow, conflict resolution, plugin_buf_load_file
  load + dedup + missing-file + null-path error paths).
- `cyrius test` — 20 suites all PASS.
- `cyrius fuzz` — 3 PASS.
- `cyrius smoke` — 1 PASS (the cyim-lsp protocol harness from
  1.4.1 still green).
- `cyrius lint` — 0 warnings (touched files); pre-existing
  `src/cli.cyr` line-length warning unchanged.

### Verification

- `cyrius build` (DCE) — OK; binary 949,888 B (+1,872 B over
  v1.4.1's 948,016 B; deltas: prefix-key registry vec + record
  helper + lookup walker (~600 B), generalized dispatch path
  (~400 B), `_buf_load_file_into_active` extraction +
  plugin_buf_load_file wrapper (~700 B), wired
  ACT_MOVE_FILE_START / `motion_file_start` cases (~150 B)).
- `build/cyim --version` — `cyim 1.4.2`.
- ABI compatibility: cyim-lsp 1.0.3 (the live consumer) doesn't
  use the new ABIs yet; the additive surface is unlinked-but-
  present until cyim-lsp 1.1.0 picks it up. DCE will keep it
  out of the binary if no consumer references it (current
  binary delta reflects the test fixtures + extracted helper,
  not registry surface that has no caller).

### Coordination with cyim-lsp

- cyim-lsp 1.1.0 (planned next) will activate `gd` / `gr` via
  `plugin_register_normal_prefix_key(KEY_G, 'd', ...)` and
  `plugin_register_normal_prefix_key(KEY_G, 'r', ...)`, plus
  cross-file goto-def via `plugin_buf_load_file`. The current
  consumer-glue stubs (`_cyim_lsp_gd`, `_cyim_lsp_gr`) and the
  cross-file deferred path in `_cyim_lsp_ex_goto_def` become
  active.
- Reference quickfix list (`:lsp-find-refs` showing a
  navigable list) waits for cyim 1.5.0's `plugin_list_display`
  ABI — the popup-overlay subsystem is the size of a minor
  release, not a patch.

## [1.4.1] — 2026-05-07

**Patch — picks up cyim-lsp 1.0.3's subprocess env fix; first
`cyrius smoke` harness lands.**

cyim-lsp 1.0.3 fixes the empty-envp regression that broke
`/usr/bin/env cyrius-lsp` lookup in v1.0.0–v1.0.2 (the child
had no `PATH`, so the default lazy-start path silently failed).
The bug was surfaced by writing the first end-to-end smoke
harness for the 1.4.0 fold-in — `tests/smcyr/lsp_fold.smcyr`,
which spawns cyrius-lsp via the bundled API and asserts the
initialize handshake completes. That harness is the
"fold-in dry-run against a real consumer" the v1.0.0 freeze
should have included (cyim-lsp ADR 0001 v1.0.2 amendment §
process consequence); now cyim has it.

### Changed

- `cyrius.cyml [deps.cyim-lsp].tag` 1.0.2 → 1.0.3.
- `lib/cyim-lsp.cyr` regenerated (symlink retargeted by
  `cyrius deps`); distfile 2163 → 2228 lines.
- `cyrius.lock` updated for the new dist sha.

### Added

- `tests/smcyr/lsp_fold.smcyr` (76 lines) — first cyim
  `.smcyr` harness. Exercises `lsp_client_start_default()` →
  spawn cyrius-lsp → initialize handshake → describe →
  clean stop → idempotent restart → clean stop. 13 assertions,
  all PASS under `cyrius smoke`. cyim's narrow tcyr suite
  validates the consumer-side glue compiles + registers; this
  smoke validates the wire actually carries traffic.

### Verification

- `cyrius build` — OK; binary 948,016 B (+800 B over 1.4.0's
  947,216 B; +800 B is the `_lsp_proc_envp_from_self` helper +
  /proc/self/environ read path inherited from cyim-lsp 1.0.3).
- `cyrius test` — 20 suites all PASS (no regressions).
- `cyrius fuzz` — 3 PASS.
- `cyrius smoke` — **1 PASS**, 13/13 assertions. Confirms
  `[cyrius-lsp] initialized` in stderr — the server received
  + responded to our LSP initialize message.
- `cyrius lint` — 0 warnings on touched files (pre-existing
  `src/cli.cyr` line-length warning unchanged).

### Process

- The `tests/smcyr/` directory is now active (was scaffolded
  but empty). Future smoke harnesses for other surfaces land
  here and run under `cyrius smoke` alongside the .tcyr / .fcyr
  / .bcyr suites.

## [1.4.0] — 2026-05-07

**Minor release — first non-trivial external plugin folded in.**
cyim 1.4.0 picks up [cyim-lsp 1.0.2](https://github.com/MacCracken/cyim-lsp)
via the sandhi pattern: `[deps.cyim-lsp]` in `cyrius.cyml` pulls
the bundled distfile (`dist/cyim-lsp.cyr`) at tag `1.0.2`;
`include "lib/cyim-lsp.cyr"` brings the protocol/state code into
cyim's TU; `src/plugins/lsp_glue.cyr` (cyim-side glue, adapted
from cyim-lsp's reference at `docs/examples/cyim_glue.cyr`) wires
six hook callbacks + four `:lsp-*` ex-commands against cyim's
plugin ABI (frozen at 1.3.6 / ADR 0004).

This is the milestone the 1.3.x ABI work (1.3.4 plugin scaffold →
1.3.5 hook surface → 1.3.6 ABI freeze → 1.3.7 closeout) was
building toward. The bundle is genuinely self-contained per
cyim-lsp's ADR 0001 v1.0.2 amendment — every symbol resolves
against the bundle + cyrius stdlib with zero references to
cyim-side editor symbols. Result: narrow tests like
`tests/buffer.tcyr` continue to compile cleanly even with the
plugin TU folded in (the structural failure mode of the original
v1.0.0 fold-in attempt).

### Added

- `[deps.cyim-lsp]` in `cyrius.cyml` — git
  `https://github.com/MacCracken/cyim-lsp.git`, tag `1.0.2`,
  modules `["dist/cyim-lsp.cyr"]`. Mirrors the vyakarana entry
  shape.
- `lib/cyim-lsp.cyr` — symlink to `~/.cyrius/deps/cyim-lsp/1.0.2/dist/cyim-lsp.cyr`,
  resolved by `cyrius deps`. SHA recorded in `cyrius.lock`.
- `src/plugins/lsp_glue.cyr` (382 lines) — cyim-side glue:
  buffer materialization (`_cyim_lsp_buf_to_flat`), six hook
  callbacks (`_cyim_lsp_post_save`, `_cyim_lsp_post_change`,
  `_cyim_lsp_status_segment`, `_cyim_lsp_diagnostic_provider`,
  `_cyim_lsp_gd`/`_cyim_lsp_gr` reserved), four ex-command
  handlers (`_cyim_lsp_ex_restart`, `_cyim_lsp_ex_status`,
  `_cyim_lsp_ex_goto_def`, `_cyim_lsp_ex_find_refs`), and
  `cyim_lsp_init()` registering them all.
- `src/main.cyr` includes:
  - `include "lib/cyim-lsp.cyr"` after `lib/vyakarana.cyr`
  - `include "src/plugins/lsp_glue.cyr"` after `trailing_ws.cyr`
  - `cyim_lsp_init()` call after `trailing_ws_init()` in `main()`

### User-visible features

- **Diagnostics** — typing in a `.cyr` file lazily spawns
  `cyrius-lsp`, sends `textDocument/didOpen` / `didChange`
  notifications, and renders server-pushed `publishDiagnostics`
  inline (gutter glyphs / underlines per cyim's existing
  diagnostic-render layer) and as a status-segment count
  (`E:N W:M I:K H:L`).
- **`:lsp-restart`** — kill + respawn `cyrius-lsp`. Useful after
  upgrading the cyrius toolchain.
- **`:lsp-status`** — print server pid + describe state.
- **`:lsp-goto-def`** — `textDocument/definition` request,
  same-file cursor jump on response (cross-file deferred until
  cyim ships a `plugin-buf-load-file` ABI).
- **`:lsp-find-refs`** — `textDocument/references` request,
  status-bar count of reference sites (quickfix list deferred
  until cyim ships a `plugin-list-display` ABI).

### Tests / verification

- `cyrius test` — 20 suites all PASS (driver: 61, plugin: 33,
  trailing_ws: 24, plus 17 narrow .tcyr suites). Critical
  assertion: narrow tests like `tests/buffer.tcyr` compile
  cleanly with `lib/cyim-lsp.cyr` in the TU — the
  structural failure that blocked the v1.0.0 fold-in attempt
  is gone.
- `cyrius fuzz` — 3 PASS.
- `cyrius lint` — 0 warnings on all touched files (one
  pre-existing line-length warning in `src/cli.cyr` unchanged).
- `cyrius build` (DCE) — OK; `build/cyim 1.4.0` resolves
  `--version` correctly via the regenerated `src/version_str.cyr`.

## [1.3.7] — 2026-05-06

Patch release — **closeout pass before v1.4.0**. Final cyim-side
audit per CLAUDE.md's Closeout Pass policy ("Run a closeout pass
before tagging X.Y.0 ... Ship as the last patch of the current
minor"). No code changes — pure verification + dead-code-floor
record + doc sync. The 1.3.x ABI work (1.3.0 niyama flavors →
1.3.6 ABI freeze) is now closed out and v1.4.0 has a clean base
for cyim-lsp pickup.

cyim-lsp v0.1.0 scaffolded today as a sibling repo (`MacCracken/cyim-lsp`)
following the sandhi pattern; v1.4.0 picks it up once cyim-lsp's
v0.5.0 (publishDiagnostics → diagnostic_provider) ships per the
cyim-lsp roadmap.

### Closeout audit summary

All 11 closeout steps per CLAUDE.md passed:

1. **Full test + fuzz** — clean tree (`rm -rf build && cyrius
   deps && CYRIUS_DCE=1 cyrius build`); cyrius test 14 suites
   all PASS, driver smoke 20/20, cli_smoke 118/118, integration
   smoke PASS, cyrius fuzz 3/3, cyrius lint 0 warnings.
2. **Benchmark baseline** — deferred (cyim has no
   bench harness; benchmarks land at the v1.4.x perf-pass).
3. **Dead code audit** — see § Dead-code floor below.
4. **Refactor pass** — none warranted; 1.3.x additions occupy
   bounded slots (six `_dispatch_<verb>` parsers parallel-by-
   design; `_re_*` flavor dispatch is DCE-friendly; plugin
   fire-points are distinct).
5. **Code review** — walked diff `1.3.0..HEAD` end-to-end;
   no missed guards, off-by-ones, silently-ignored errors.
6. **Cleanup sweep** — no stale comments, no orphaned files,
   no unused includes. Empty `docs/development/issues/`
   (only `archive/` subdir from BUG-001 retirement).
7. **Security re-scan** — no new `sys_system` / `exec` /
   unchecked syscalls in 1.3.x diffs. 3 new `var buf[N]`
   declarations (all in `src/plugins/trailing_ws.cyr` and
   `src/render.cyr`), all bounded with documented use.
8. **Downstream check** — agnoshi / aethersafha still
   "Planned" in state.md consumers table; cyim-lsp v0.1.0
   is now the first realised plugin consumer (scaffold
   only at this version).
9. **Doc sync** — CHANGELOG / roadmap / state / CLAUDE.md
   all current and consistent through this entry.
10. **Version verify** — `VERSION` 1.3.7, `cyrius.cyml`
    indirection via `${file:VERSION}`, `src/version_str.cyr`
    `_VERSION_STR_CYIM = "cyim 1.3.7\n"`, CHANGELOG header,
    intended git tag `1.3.7` all match.
11. **Full clean build** — passed (binary 899,488 B, byte-
    identical to v1.3.6).

### Dead-code floor

24 cyim-source functions are DCE-stripped from the binary as of
v1.3.7. Categorised:

**7 plugin ABI public surface** (intentional — frozen at ADR 0004
for plugin authors; cyim itself doesn't call these):
`diag_line`, `diag_msg`, `diag_severity`, `plugin_last_diags`,
`plugin_register_ex_command`, `plugin_register_normal_key`,
`plugin_register_post_save_hook`, `_plugin_keyed_record_new`.

**17 legacy helpers** held over from M2-M4, stable across many
minors (kept; CLAUDE.md "wait for the third instance"):
`buf_cap`, `buf_gap`, `editor_cfg_line_numbers`,
`editor_cfg_tabstop`, `editor_drive`, `editor_last_error`,
`editor_run`, `editor_set_mode`, `lang_index`, `lang_is_valid`,
`motion_file_start`, `tty_cursor_hide`, `tty_cursor_show`,
`visual_selection_hi`, `visual_selection_lo`,
`window_count_leaves`.

No removals — both groups have plausible future consumers
(plugin authors for the public ABI; cyim's own future features
or cyim-lsp's eventual cursor-during-fetch indicator etc. for
the legacy helpers). Recording the floor here so future closeout
passes can compare.

### Notes

- **No source changes.** Pure verification cut.
- **No cyrius toolchain bump.** Pin stays at 5.9.16 (set in
  v1.3.6).
- **v1.4.0 unblocked, awaiting cyim-lsp v0.5.0.** The cyim-side
  pickup will be a 2-line change: `[plugins.cyim-lsp]` block in
  `cyrius.cyml` + `include "lib/cyim-lsp.cyr"` in `src/main.cyr`
  + `cyim_lsp_init()` call in `main()` after `plugin_init()` and
  `trailing_ws_init()`.

### Binary

- `build/cyim` — DCE build size: **899,488 B** (byte-identical
  to v1.3.6). No source changes; toolchain unchanged.

## [1.3.6] — 2026-05-06

Patch release — **plugin ABI frozen + cyrius pin 5.9.13 → 5.9.16**.
Two complementary cuts:

1. **ADR 0004 freezes the plugin ABI surface** at the v1.3.5
   shape. All six hook registration functions, their callback
   signatures, the 24 B diag record layout, and the four
   `DIAG_*` severity constants are now stable across cyim 1.x.
   Plugin authors (cyim-lsp at v1.4.0; future external plugins
   via the sandhi pattern) can target this contract with the
   confidence that backwards-incompatible changes wait for
   cyim 2.x. Hook expansion within 1.x continues to require an
   ADR per ADR 0003 §3.
2. **Cyrius toolchain bump 5.9.13 → 5.9.16**. Re-vendored
   `lib/fs.cyr` lost the `dir_walk_with_prunes` helper
   (introduced and removed upstream between 5.9.13 and 5.9.16)
   — cyim doesn't consume that function, so the removal is
   benign and DCE-stripped. Binary is **byte-identical** to
   v1.3.5 (899,488 B): the changed stdlib paths aren't consumed
   by cyim at all, so DCE delivers an exact match.

No source changes in cyim's own code. Pure doc cut + toolchain
re-vendor.

### Added

- **`docs/adr/0004-plugin-abi-freeze.md`** (350 lines) —
  formalises the frozen surface: hook registration functions,
  callback signatures, diag record layout, severity constants,
  compatibility envelope (stable across 1.x; additions allowed;
  breaking changes need 2.x). Documents what's NOT frozen
  (internal `_plugin_*` helpers, registry vec layouts,
  render-side inline diag paint) and three alternatives that
  were considered and rejected.

### Changed

- **Cyrius toolchain pin**: `5.9.13` → `5.9.16` in `cyrius.cyml
  [package].cyrius`. All gates green: cyrius test 33/33,
  cli_smoke 118/118, integration smoke PASS, cyrius fuzz 3/3,
  lint 0 warnings.
- Re-vendored `lib/fs.cyr` from the new toolchain.
  `dir_walk_with_prunes` removed (upstream churn; cyim doesn't
  consume it).

### Notes

- **No external plugin migration yet.** trailing_ws stays
  inline in `src/plugins/trailing_ws.cyr`. Promotion to a
  separate `cyim-trailing-whitespace` repo via the sandhi
  pattern remains gated on upstream cyrius adding first-class
  `[plugins.<name>]` parsing — currently we use the
  `[deps.<name>]` syntactic equivalence per ADR 0003 §4.
- **v1.4.0 unblocked.** With the ABI frozen, cyim-lsp can
  proceed: subprocess spawn of `cyrius-lsp`, JSON-RPC framing
  on pipes, `textDocument/didSave` via post_save_hook,
  `textDocument/didChange` via post_change_hook,
  `publishDiagnostics` via diagnostic_provider, status segment
  for diag count, `gd` / `gr` keymaps via normal_key, ex
  commands via `:lsp-restart` / `:lsp-status`. Lands as a new
  `MacCracken/cyim-lsp` repo with `[plugins.cyim-lsp]` in
  cyrius.cyml.

### Binary

- `build/cyim` — DCE build size: **899,488 B** (byte-identical
  to v1.3.5). The cyrius 5.9.13 → 5.9.16 stdlib paths cyim
  consumes are byte-equivalent after DCE; the changed paths
  (`dir_walk_with_prunes` removal, etc.) aren't consumed by
  cyim at all. Pure documentation cut from cyim's binary
  perspective.

## [1.3.5] — 2026-05-06

Patch release — **plugin ABI proven end-to-end** with the first
working plugin. Wires the four remaining hook fire-points into
cyim's render / mode-dispatch / command-parser paths
(`status_segment`, `normal_key`, `ex_command`,
`diagnostic_provider`) and ships the trailing-whitespace
highlighter (`src/plugins/trailing_ws.cyr`) as the proving-ground
consumer. All six hooks per ADR 0003 §3 are now active; the ABI
is one real plugin away from earning its v1.3.6 freeze (ADR 0004).

The trailing_ws plugin is intentionally inline in cyim's tree
rather than an external `cyim-trailing-whitespace` repo. v1.3.5
is the ABI's proving ground; once the surface freezes (1.3.6),
the plugin can promote to the sandhi pattern alongside vyakarana
and niyama.

CLAUDE.md's Work Loop step 3 + Closeout Pass step 1 now call out
`cyrius fuzz` explicitly so the v1.3.4 single-pass-include CI gap
doesn't bite anyone again.

### Added

- **`src/plugins/trailing_ws.cyr`** (140 lines) — first inline
  cyim plugin. Registers three hooks: `post_change_hook`
  recomputes the line-set on every buffer mutation,
  `diagnostic_provider` emits one `DIAG_HINT` entry per
  trailing-ws line, `status_segment` renders `TWS:N` (omits the
  segment when N == 0). Recompute is full-buffer-walk per
  change.
- **`trailing_ws_init()`** call in `src/main.cyr:main()` after
  `plugin_init()`.
- **DIAG_* constants** + **`diag_new(line, severity, msg)`**
  helper + accessors in `src/plugin.cyr`. The 24 B record shape
  pinned at v1.3.5.
- **`_plugin_render_collect_diagnostics(s)`** + **`plugin_last_diags()`**
  in `src/plugin.cyr` — fires every render frame from
  `render_frame`; populates a fresh diag vec globally for tests
  + future render-side inline-paint integration.
- **`tests/trailing_ws.tcyr`** (140 lines, 24 assertions across
  8 groups) — trailing-ws end-to-end behaviour.

### Changed

- **`src/render.cyr:render_status`** — appends plugin
  status_segment output after the dirty indicator, separated by
  ` | `.
- **`src/render.cyr:render_frame`** — calls
  `_plugin_render_collect_diagnostics(s)` once per frame.
- **`src/mode.cyr:editor_dispatch`** NORMAL-mode arm — falls
  through to `_plugin_lookup_normal_key(key)` after built-in
  keymap miss. Built-ins win on conflict per ADR 0003 §3.
- **`src/command.cyr:command_execute`** — falls through to
  `_plugin_lookup_ex_command(name)` after every built-in `:cmd`
  comparison misses. Materialises the cmdbuf bytes as NUL-term
  cstring for the lookup. Built-ins win.
- **Test files (4)**: `tests/{cyimrc,render,motion,dispatch}.tcyr`
  added `include "src/plugin.cyr"` immediately before
  `include "src/mode.cyr"` (single-pass-resolution).
- **CLAUDE.md** — Work Loop step 3 now reads "Test + benchmark +
  fuzz additions" with explicit guidance for src files in
  `driver/command/buffer/mode/edit/insert.cyr`. Closeout Pass
  step 1 broadened from "all `.tcyr` pass" to "all `.tcyr` pass;
  `cyrius fuzz` passes all `.fcyr` harnesses". Closes the
  v1.3.4-shipped-then-CI-failed-fuzz gap.
- **`tests/plugin.tcyr`** extended with 4 new groups (33 total
  assertions, was 27) — `editor_dispatch` routing unmapped
  NORMAL keys to plugins, built-ins-win invariant for `h`, ex
  parser routing `:test-ex` to plugin via `command_execute`,
  built-ins-win invariant for `:q`.

### Tests

- `cyrius test` — 11 test files (was 9) including new
  `trailing_ws.tcyr`; all PASS.
- Driver/dispatch summary: 20 PASS (was 19).
- `tests/cli_smoke.sh` 118/118, `integration_smoke.py` PASS,
  `cyrius fuzz` 3/3 PASS, `cyrius lint` 0 warnings.

### Notes

- **No cyrius toolchain bump.** Pin stays at 5.9.13.
- **All six hooks now have fire-points.** ABI is functionally
  complete per the v1.3.4 ADR 0003 §3 surface. v1.3.6 plan: ADR
  0004 freezes the ABI based on what 1.3.5 surfaced. v1.4.0:
  cyim-lsp builds against the frozen contract.
- **trailing_ws is inline, not external.** Promoting to a
  separate `cyim-trailing-whitespace` repo waits for: (a) the
  ABI freeze (1.3.6), and (b) `cyrius.cyml [plugins.<name>]`
  parsing in upstream cyrius.
- **Render-side inline paint of diags deferred.** v1.3.5
  populates `plugin_last_diags()` per frame but doesn't paint
  diag markers in the buffer view. cyim-lsp at v1.4.0 will land
  the visual surface.

### Binary

- `build/cyim` — DCE build size: **899,488 B** (+4,592 B over
  v1.3.4's 894,896 B). Trailing_ws plugin (~700 B) + 4 fire-
  point integrations (~3 KB across render.cyr / mode.cyr /
  command.cyr) + diag record helpers (~700 B). All four
  previously-DCE'd register/lookup/collect helpers now have
  active call sites and are linked in.

## [1.3.4] — 2026-05-06

Patch release — **plugin ABI scaffold** per [ADR 0003](docs/adr/0003-cyrius-plugin-system.md).
cyim is now plugin-ready: hook registries, register/fire/lookup
helpers, and post_save / post_change fire-points are wired into
cyim's core dispatch. No external plugin yet; the scaffold compiles
cleanly into the binary and exercises end-to-end via a new
`tests/plugin.tcyr` (27 assertions across 8 groups). The four
non-wired hooks (status_segment, normal_key, ex_command,
diagnostic_provider) have register / lookup / collect helpers in
place but no fire-point — those wire up in v1.3.5+ when a real
plugin (cyim-lsp at v1.4.0) surfaces what each hook needs.

The ABI surface is **provisional**, not frozen. ADR 0004 (planned
1.3.5+) freezes it after the first real consumer (cyim-lsp) drives
the design choices.

### Added

- **`src/plugin.cyr`** — 6-hook registry + register/fire/lookup/
  collect API per ADR 0003 §2. 230 lines. Hook types:
  `post_save_hook`, `post_change_hook`, `status_segment`,
  `normal_key`, `ex_command`, `diagnostic_provider`. Lazy-init
  via `plugin_init()` (idempotent). Keyed hooks store 24 B
  records `{key/name_ptr, len, fp}`; simple hooks store fp
  directly as i64.
- **`plugin_init()`** call in `src/main.cyr:main()` after
  `args_init()`, before any cyim setup.
- **`_plugin_fire_post_save(s, path)`** wired into `_cmd_w` after
  `editor_set_modified(s, 0)` in `src/command.cyr`. Fires for
  every successful `:w` / `:wq` / `:e <new-path>` save.
- **`_plugin_fire_post_change(s)`** wired into `editor_step` in
  `src/driver.cyr`. Fires only when `buf_version` increments
  during the step — non-mutating presses (motions, mode toggles)
  don't trigger.
- **`tests/plugin.tcyr`** (160 lines) — registers per-hook
  counter callbacks, drives editor sequences, asserts hooks
  fired (or didn't, for non-mutating cases). 27 assertions
  covering: registry init, registration append, post_change on
  insert, post_change quiet on motion, post_save arg threading,
  keyed lookup hit/miss, status_segment collection
  ("TEST" → 4 bytes appended), diagnostic provider walk,
  `plugin_init` idempotence.
- **`docs/architecture/001-plugin-system.md`** — first entry in
  the architecture series; documents ABI invariants, storage
  shape, fire-point semantics, post_change firing rule
  (`buf_version` delta), trust model, hook expansion policy.

### Changed

- **8 test files (`tests/{visual,buflist,dot,insert,command,search,window,undo}.tcyr`)
  + 1 fuzz file (`fuzz/driver.fcyr`)** added
  `include "src/plugin.cyr"` immediately before
  `include "src/command.cyr"`. Cyrius is single-pass; the
  fire-point references in command.cyr need plugin.cyr's
  function definitions to come earlier in the translation unit.
  Existing test assertions and fuzz invariants unchanged. (CI's
  `cyrius fuzz` gate caught driver.fcyr after the .tcyr fixes
  landed; same root cause, same one-line fix.)
- `src/driver.cyr:editor_step` captures `buf_version` pre-dispatch
  and compares post-apply for the post_change firing decision.
  Pure addition — no existing dispatch behaviour changed.

### Tests

- `tests/plugin.tcyr` — new file, 27 assertions all PASS.
- `cyrius test` — 9 test files (was 8) including the new
  plugin.tcyr; all PASS.
- Driver smoke (`run_*` bench / dispatch test): 19 PASS (was 18).
- `tests/cli_smoke.sh` 118/118 unchanged. `integration_smoke.py`
  PASS unchanged. `cyrius lint` 0 warnings.

### Notes

- **No cyrius toolchain bump.** Pin stays at 5.9.13 (set in
  v1.3.3).
- **No external plugin in this release.** v1.3.5 plan: trailing-
  whitespace POC plugin to prove the ABI end-to-end (validates
  status_segment + diagnostic_provider hooks). v1.3.6 plan: ADR
  0004 freezes the ABI surface based on what 1.3.5 needed.
  v1.4.0: cyim-lsp as the first non-trivial plugin.
- **Refusal §0 unchanged.** A Cyrius plugin is AOT-compiled and
  treated identically to cyim's own code — not an embedded
  scripting language. The cyim binary still has no interpreter,
  no eval, no plugin VM.

### Binary

- `build/cyim` — DCE build size: **894,896 B** (+4,544 B over
  v1.3.3's 890,352 B). Plugin scaffold (`src/plugin.cyr`) +
  fire-point wiring (~30 LOC across `command.cyr` and
  `driver.cyr`) accounts for the delta. The four non-wired
  hooks' register/lookup/collect helpers are linked but
  DCE-stripped until a plugin uses them.

## [1.3.3] — 2026-05-06

Patch release — **BUG-001 closed**. Cyrius toolchain bump
5.9.2 → 5.9.13 picks up the upstream `args_init()` fix that landed
in cyrius 5.9.5 (heap-backed 2 MB buffer, replacing the
4 KB stack buffer that silently truncated argv reads). cyim's
`_cli_args_reload_big()` workaround retires; the integration
smoke regression for BUG-001 stays in place as a guard.

The retirement is purely a code-removal cut on cyim's side: one
function deleted from `src/cli.cyr` (with its `_CLI_ARGS_BIG_CAP`
global and explanatory comment block), one call site removed
from `src/main.cyr`. No behavioral change for end users — the
`>4064 B <new>` argv path was already working against the
workaround; now it works against the upstream fix directly.

### Changed

- **Cyrius toolchain pin**: `5.9.2` → `5.9.13` in `cyrius.cyml
  [package].cyrius`. Picks up cyrius 5.9.5's `args_init()` fix
  + 5.9.6's `dir_list` use-after-free fix in
  `lib/fs.cyr` (incidental — cyim doesn't consume `dir_list`,
  DCE-stripped). Re-vendored `lib/args.cyr` and `lib/fs.cyr`
  from the new toolchain.

### Removed

- **`_cli_args_reload_big()`** in `src/cli.cyr` (15-line function
  + `_CLI_ARGS_BIG_CAP` global + 19-line BUG-001 comment block).
  Replaced unconditional 2 MB heap re-read of `/proc/self/cmdline`
  with reliance on cyrius 5.9.5+'s upstream-correct `args_init()`.
- **Workaround call site** in `src/main.cyr:239`:
  `_cli_args_reload_big();` line removed.

### Closed

- **BUG-001** (filed 2026-04-25, worked around 2026-04-26, fixed
  upstream 2026-05-06). Resolution lineage tracked in
  `docs/development/roadmap.md` § Closed Bugs and the archived
  upstream issue file at
  `docs/development/issues/archive/2026-05-06-cyrius-args-init-4kb-cap.md`.

### Tests

- All gates green against 5.9.13 with workaround removed: cyrius
  test 130/130, cli_smoke 118/118, integration smoke (BUG-001
  regression row included) PASS, cyrius lint 0 warnings.
- BUG-001 verified retired against three argv sizes — 4063 B,
  8 KB, 64 KB — all `cyim --replace` invocations succeed
  cleanly without the workaround helper.

### Notes

- **No 1.3.x roadmap items pending after this cut.** Pre-1.4.0
  slate: 1.3.4 plugin ABI scaffold (cyim-side hook plumbing per
  ADR 0003), 1.3.5 trailing-whitespace POC plugin (proves the
  ABI end-to-end), 1.3.6 ABI freeze in ADR 0004. v1.4.0 ships
  cyim-lsp as the first real plugin against the frozen ABI.

### Binary

- `build/cyim` — DCE build size: **890,352 B** (−4,400 B from
  v1.3.2's 894,752 B). The retirement saved ~600 B of
  `_cli_args_reload_big()` machinery; the rest is downstream
  benefit from cyrius 5.9.3-5.9.13 stdlib improvements (regex
  + niyama paths got tightened internally; cyim consumes them
  unchanged).

## [1.3.2] — 2026-05-06

Patch release — fuzzy substitute precision + `--fuzzy-edits=<n>`
modifier + closeout. Three things in one cut:

1. **Tight fuzzy match-end recovery.** v1.3.1 used `hit + plen` as
   the substitute span, which over-ate on deletion edits (the
   `fo` example consumed the trailing `\n` and merged lines) and
   under-ate on insertion edits. v1.3.2 walks candidate end
   positions in `[hit + max(0, plen - max_edits), hit + plen +
   max_edits]`, picks the one with minimum Levenshtein distance,
   tie-breaks by smallest L. Newline preservation: `fo` matched
   against pattern `foo` now picks L=2 (insertion edit, span
   doesn't cross `\n`) instead of L=3.
2. **`--fuzzy-edits=<n>` modifier** on the six pattern verbs.
   Currently `0` (exact-fuzzy), `1`, `2` (= niyama default) are
   most useful; niyama's max is bounded by the engine's k slot.
   Reject if paired with a non-fuzzy `--regex=` (parser-level,
   exit 2). The encoding stores `k+1` in `RegexOpts +8` so `k=0`
   is distinguishable from "user didn't set --fuzzy-edits".
3. **Closeout pass per CLAUDE.md.** Dead code audit, lint,
   security re-scan, doc sync. No structural changes — current
   dead-code floor is stable stdlib auto-prepend that DCE strips
   from the binary. Cyim source has a handful of unreferenced
   helpers (`tty_cursor_hide`, `editor_drive`, `motion_file_start`,
   `buf_cap`/`buf_gap`, etc.) — DCE'd out, not refactored speculatively.

### Added

- **`--fuzzy-edits=<n>`** modifier on `--grep`, `--grepfiles`,
  `--replace`, `--replace-all`, `--replace-files`,
  `--replace-files-all`. Threaded through six dispatchers + four
  `run_*` functions + `RegexOpts +8` slot (encoded as k+1) to
  `niyama_fuzzy_compile_opts(pat, k, 0)`. Default unchanged
  (niyama's `FUZZY_DEFAULT_K=2`).
- **`_fuzzy_span_end`** helper in `src/cli.cyr` — post-match
  candidate-length walk using `niyama_fuzzy_distance` for scoring.
  Cost: O(2k+1) substring materialisations per match, each
  driving an O(plen × candidate_len) DP inside niyama. Negligible
  at default k for typical patterns.
- **`Matcher` +32 slot** holds `max_edits` (effective k after
  `--fuzzy-edits` resolution; 2 if unset). `_matcher_max_edits(m)`
  accessor. Read by `_fuzzy_span_end` for the candidate window.
- **`Matcher` struct grew 32B → 40B.** Literal matchers leave the
  new slot zero. Negligible per-call cost.
- **Per-verb `--fuzzy-edits` validation**: parser rejects
  `--fuzzy-edits` without `--regex=fuzzy` (exit 2 + verb-prefixed
  message). Duplicate `--fuzzy-edits=` flags refused (exit 2).

### Changed

- **Behaviour change for fuzzy substitute on tied distances.**
  When two candidate spans achieve the same Levenshtein distance,
  v1.3.2 picks the smaller L (don't eat extra source bytes). For
  inputs where v1.3.1 collapsed `fop` to `X` (plen=3 approximation),
  v1.3.2 leaves the trailing byte: `fop` → `Xp`. Documented in
  `--help`'s flavor table; `cli_smoke.sh` case 87 updated.
- `_cli_substitute_regex` signature gained `max_edits` parameter
  (between `plen` and `new`). Internal-only; no consumer impact.
- `--help` flavor-table fuzzy row replaces v1.3.1's
  "imperfect for insert/delete" caveat with the v1.3.2 tight-span
  semantics. New `--fuzzy-edits=<n>` row added below.

### Tests

- `tests/cli_smoke.sh` — 4 new fuzzy cases (87b–87d): `--fuzzy-edits=0`
  forces exact-only fuzzy (proves k=0 distinguishes from "unset");
  `--fuzzy-edits` rejected without `--regex=fuzzy`; duplicate
  `--fuzzy-edits` refused. Case 87 updated to assert the new tight
  span (`fop` → `Xp`, was `X`). Suite total: 118 assertions (was 114).

### Notes

- **BUG-001 still unfixed upstream.** cyrius 5.9.2's `lib/args.cyr`
  still has `var buf[4096]` in `args_init()`. cyim's
  `_cli_args_reload_big()` workaround stays. Re-checked at v1.3.2
  closeout; will retire once cyrius patches.
- **Backreferences (`\1`)** still deferred per niyama's long-term
  security-against-misuse plan. Unchanged from v1.3.0/1.3.1.
- **No cyrius toolchain bump.** Pin stays at 5.9.2 (set in v1.3.0).
- **LSP client (v1.4.0) promoted from demand-gated.** cyrius-lsp
  is stable in the toolchain (`programs/cyrius-lsp.cyr`); cyim-side
  client lands as v1.4.0 — own milestone, not a 1.3.x patch.

### Binary

- `build/cyim` — DCE build size: **894,752 B** (+5,624 B over
  v1.3.1's 889,128 B). The fuzzy-edits parser arm × 6 dispatchers
  + the `_fuzzy_span_end` helper + `_regex_opts_set_fuzzy_edits` +
  the threading through 4 `run_*` functions account for the delta.
  niyama_fuzzy + unicode tables already linked.

## [1.3.1] — 2026-05-06

Minor release — `--regex=fuzzy` (Levenshtein) now ships across all six
pattern verbs. Closes the v1.3.0 deferral. niyama_fuzzy lacks the
`_search_at` and `_group_end` ABI the other engines expose; cyim
fakes them: `_search_at` via cstring-pointer arithmetic
(`niyama_fuzzy_search` reads NUL-terminated, so `s + from` is
equivalent to "start at offset"), and `_group_end` via the
compile-time pattern length stored in the `Matcher` struct's new
+24 slot. The plen approximation is exact for substitution edits
(matched span == pattern length) but imperfect for insertion /
deletion edits within `max_edits` — the substitute path eats
exactly `plen` source bytes regardless of whether the actual
matched span is `plen ± k`. Surfaced in `cyim --help`. Per the
plan: ship the intended scope; tighten in a follow-up if the
imperfection bites.

Default `max_edits = 2` (niyama's `FUZZY_DEFAULT_K`). No knob to
tune it on cyim's side yet — that lands when surface demand shows.

### Added

- **`--regex=fuzzy`** wiring across `--grep`, `--grepfiles`,
  `--replace`, `--replace-all`, `--replace-files`,
  `--replace-files-all`. New arms in `_matcher_regex`,
  `_re_search_at`, `_re_search`. `_flavor_validate` no longer
  rejects FLAVOR_FUZZY.
- **`Matcher` +24 slot** holds `plen` (compile-time pattern
  length). `_matcher_plen(m)` accessor. Used by FLAVOR_FUZZY's
  span approximation in `_cli_count_matches_m` and
  `_cli_substitute_regex` (both now compute `span_end =
  hit + plen` for fuzzy, clamped to slen; other flavors stay on
  exact `_re_group_end`).
- **`Matcher` struct grew 24B → 32B.** Literal matchers leave +24
  zeroed; regex matchers store plen there. Negligible per-call
  cost.
- **`--help` flavor table** updated: fuzzy row replaces the
  v1.3.0 "planned for v1.3.1" placeholder with shipping
  semantics + the substitute-imperfection caveat in plain
  English.

### Changed

- `_cli_substitute_regex` signature gained `plen` parameter
  (between `nfa` and `new`). Internal-only; no consumer impact.
- `_flavor_validate` unknown-flavor message reordered alphabetic
  (`bre, ere, fuzzy, pcre, re2, vim`) and dropped the
  `fuzzy: v1.3.1` parenthetical (fuzzy is now in the supported
  list).

### Tests

- `tests/cli_smoke.sh` — 6 new fuzzy cases (case 85 reused from
  v1.3.0's deferred-diagnostic slot, repurposed for exact-match;
  cases 85–90 cover single-edit substitution match, beyond-distance
  rejection, substitute-path roundtrip, count-path via
  `--expect-1`, multi-file `--grepfiles`, `--context=N`
  composition). Suite total: 114 assertions (was 103). Deletion-
  edit corner cases NOT asserted because their precise output is
  part of the documented "tighten later" surface.

### Binary

- `build/cyim` — DCE build size: **889,128 B** (+720 B over
  v1.3.0's 888,408 B). The fuzzy compile arm + the cstring-offset
  pseudo-`_search_at` + the plen-approximation `_group_end`
  inline at two call sites + the expanded `--help` flavor table
  (fuzzy row plus the substitute-imperfection caveat). Total
  <1 KB of new code; niyama_fuzzy + unicode tables already linked
  in v1.3.0.

### Notes

- **Substitute imperfection — known and bounded.** For deletion
  edits ("foo" pattern matched against "fo" at distance 1), the
  plen=3 span eats one extra byte past the actual match — which
  in practice can consume the `\n` and merge lines. For insertion
  edits ("foo" matched against "fooo"), the plen=3 span leaves
  one byte of the match in place. The bound is `± max_edits`
  bytes per match. To tighten: implement a post-match span search
  (binary-walk via repeated `niyama_fuzzy_match` calls on
  candidate substring lengths), OR get niyama to expose the
  internal `end_pos_buf` it already computes during search. The
  latter is the upstream fix; the former is the cyim-side
  workaround if niyama's ABI stays frozen.
- **Backreferences (`\1`)** still deferred per niyama's long-term
  security-against-misuse plan — unchanged from v1.3.0.

## [1.3.0] — 2026-05-06

Minor release — `--regex=<flavor>` now accepts four additional
engines (`bre`, `re2`, `pcre`, `vim`) via niyama 1.0.1, which folded
into cyrius stdlib at 5.9.0 per niyama's ADR 0011 fold trigger. cyim
consumes the fold via the documented sandhi pattern: `lib/niyama.cyr`
is pulled by explicit `include` in `src/main.cyr` rather than
`[deps].stdlib` auto-prepend (keeps consumers under the 2 MB
preprocess_out cap that motivated opt-in fold inclusion at cyrius
5.8.65). The ERE engine (cyrius stdlib Pike NFA) is unchanged and
remains the default ERE flavor.

`fuzzy` is recognized at the parser level but rejected with a
`v1.3.1` diagnostic — niyama_fuzzy lacks `_search_at`, so iterating
over multiple matches needs a wrapper layer that lands in v1.3.1.
Backreferences (`\1`-style) are deferred per niyama's long-term
security-against-misuse plan; not yet supported in any v1.3.0
flavor. Both caveats surfaced in `cyim --help` next to the flavor
table so script authors see them before hitting the engine.

### Added

- **`--regex=bre`** — POSIX-BRE via `niyama_bre_compile` /
  `_search_at` / `_group_end`. `\+` and `\?` quantifiers are GNU
  extensions, not POSIX-BRE — use `[c][c]*` or `\{1,\}` for
  one-or-more.
- **`--regex=re2`** — Google RE2 (`niyama_re2_*`); linear-time, no
  backreferences by design.
- **`--regex=pcre`** — PCRE-style (`niyama_pcre_*`); `\d`, `\w`,
  lookaround supported. No backreferences yet (deferred per niyama
  v1).
- **`--regex=vim`** — vim-regex flavor (`niyama_vim_*`); supports
  `\v` very-magic and `\V` very-nomagic mode prefixes. Default is
  vim's "magic" mode.
- **`niyama` stdlib fold** — `lib/niyama.cyr` (vendored
  byte-identical at cyrius 5.9.0) wired via explicit
  `include "lib/niyama.cyr"` in `src/main.cyr`. Required unicode
  normalization tables (`unicode/normalize`, `unicode/_normalize_data`,
  + categories/casefold) added to `[deps].stdlib` per the v5.8.49
  subdir-nested-stdlib resolution rule (`"unicode/<file>"` →
  `lib/unicode/<file>.cyr`).
- **Per-flavor dispatch helpers** (`_re_search_at`, `_re_search`,
  `_re_group_end`) in `src/cli.cyr` — single source of truth for
  engine selection so future flavor additions touch one site
  instead of every hot-path call.
- **`_flavor_validate` parser helper** — central rejection arm for
  unknown / deferred flavors. Each of the six pattern verbs
  (`--grep`, `--grepfiles`, `--replace`, `--replace-all`,
  `--replace-files`, `--replace-files-all`) now emits a uniform
  supported-list message naming all four shipping flavors plus the
  `fuzzy: v1.3.1` deferred note.
- **`_help_line` runtime-strlen helper** in `src/main.cyr` — the
  flavor-table rows in `--help` use `strlen()` instead of
  hand-counted byte literals so future caveats can edit text
  without re-counting.

### Changed

- `Matcher` struct's `+16` slot now stores the regex flavor (was
  unused for `MATCHER_REGEX` in v1.2.0). Hot-path helpers read it
  via the new `_matcher_flavor(m)` accessor.
- `_cli_substitute_regex` signature gained `flavor` parameter
  (between `src` and `nfa`). Internal-only function; no consumer
  impact.

### Tests

- `tests/cli_smoke.sh` — 10 new cases covering one end-to-end check
  per flavor on the most distinctive idiom for that engine,
  substitute-path roundtrip with flavor dispatch, count-path
  flavor dispatch via `--expect-1`, fuzzy-deferred gate (asserts
  the diagnostic includes "v1.3.1"), and a multi-file × cross-engine
  composition. Suite total: 103 assertions (was 84).
- Existing case 64 ("`--regex=pcre` unknown flavor") repurposed to
  `--regex=foobar` since `pcre` is now a real flavor; the parser
  arm stays exercised.

### Binary

- `build/cyim` — DCE build size: **888,408 B** (+518,640 B over
  v1.2.2's 369,768 B). The bulk is the niyama dist (~6.6 KLOC of
  engine code) plus the unicode normalization tables it pulls in
  even though fuzzy isn't exposed yet (niyama is one concatenated
  artifact). The flat 4-engine dispatch in `src/cli.cyr` adds
  <2 KB; everything else is folded library + unicode data. Future
  fuzzy expansion in v1.3.1 should add ~0 incremental binary cost
  (engine + tables already linked).

### Notes

- **Cyrius toolchain pin: `5.9.1` → `5.9.2`.** Required to unblock
  CI: cyrius 5.9.1's release tarball was missing the
  `lib/unicode/*.cyr` files cyim's `[deps].stdlib` resolves through
  v5.8.49 subdir-nested-stdlib syntax (`"unicode/<file>"` →
  `lib/unicode/<file>.cyr`). Local dev builds compiled fine because
  `~/.cyrius/lib/unicode/` was already present from a prior install;
  CI's clean install-from-tarball hit the gap on `cyrius deps`.
  Upstream packaging fixed in 5.9.2 — the tarball now includes the
  full `lib/unicode/` directory. Binary is byte-identical between
  5.9.1 and 5.9.2 builds (no codegen drift).
- niyama is consumed via the 5.9.x stdlib fold, not as an external
  dep — no `[deps.niyama]` block.

## [1.2.2] — 2026-05-06

Patch release — Cyrius toolchain bump 5.7.23 → 5.9.1, plus a
version-string cleanup so `cyim --version` can never silently drift
again. The `regex_*` ABI cyim consumes (`regex_compile`,
`regex_search`, `regex_search_at`, `regex_group_start`,
`regex_group_end`) is unchanged across the bump. niyama 1.0.1's
fold trigger fired at cyrius 5.9.0 so `lib/niyama.cyr` is now
vendored stdlib alongside `lib/regex.cyr` — wiring the additional
flavors (`bre`/`re2`/`pcre`/`fuzzy`/`vim`) into `--regex=<flavor>`
is queued as a v1.3.0 followup.

### Changed

- **Cyrius toolchain pin**: `5.7.23` → `5.9.1` in `cyrius.cyml
  [package].cyrius`. All tests, lint, and CLI/integration smokes
  pass byte-identically against the new toolchain.

### Added

- **`src/version_str.cyr`** (auto-generated) — single source of
  truth for the `cyim --version` literal and its byte length.
  `src/main.cyr`'s `print_version` reads `_VERSION_STR_CYIM` /
  `_VERSION_LEN_CYIM` instead of hardcoded literals.
- **`scripts/version-bump.sh`** — single entrypoint for version
  bumps. Writes `VERSION`, regenerates `src/version_str.cyr`
  unconditionally (idempotent under same-version invocation per
  the cyrius pattern), and inserts the `## [X.Y.Z]` CHANGELOG
  header after `## [Unreleased]`. Mirrors cyrius's own
  `scripts/version-bump.sh` + `src/version_str.cyr` pattern.

### Fixed

- **`cyim --version` no longer drifts on toolchain-only bumps.**
  v1.2.2 originally shipped with `print_version` still emitting
  `cyim 1.2.1` because the literal was hardcoded into
  `src/main.cyr` and the version-sync checklist
  (`VERSION` / `cyrius.cyml` / `CHANGELOG` header) didn't list a
  fourth surface; CI's version-sync gate caught it. Cleanup
  centralises the literal into the auto-generated
  `src/version_str.cyr`. CLAUDE.md's Work Loop step 7 + Closeout
  step 10 now point at `scripts/version-bump.sh` instead of
  enumerating the surfaces.

### Binary

- `build/cyim` — DCE build size: **369,768 B** (+13,344 B over
  1.2.1's 356,424 B). +13,264 B is stdlib drift between cyrius
  5.7.23 and 5.9.1; +80 B is the version-string cleanup (the
  literal moves from `src/main.cyr` into the new auto-generated
  `src/version_str.cyr` — same string content, slightly larger
  encoding once the include + var declarations land).

### Notes

- `cyrius audit` is broken in 5.9.1 install (`/home/macro/.cyrius/bin/check.sh`
  missing); individual gates (`build`, `test`, `fmt`, `lint`) all
  green, so this is an upstream packaging issue, not a cyim
  problem. Tracked for the next toolchain pickup.

## [1.2.1] — 2026-04-28

Patch release — two interactive-mode bugs surfaced once cyim got real
hands-on use after the 1.2.0 push. Both predated 1.2.0 but were latent
because the agent-drive surface (which dominates testing) doesn't go
through the TTY read path.

### Fixed

- **Enter key in INSERT mode now splits the line** (was: inserted CR
  byte 13 verbatim). Terminals send CR (byte 13) for the Enter key in
  raw mode; the pre-1.2.1 INSERT-mode dispatch had no special case so
  CR fell through to `ACT_INSERT_LITERAL` and was stuffed into the
  buffer as-is — rendering as nothing or `^M` and not actually
  splitting the line. v1.2.1 adds `ACT_INSERT_NEWLINE` (in
  `src/mode.cyr` and `src/insert.cyr`) and special-cases both
  `KEY_ENTER` (13/CR) and `KEY_LF` (10/LF) in INSERT mode to translate
  to a real LF (byte 10) insert. Verified by `dispatch.tcyr` and the
  `iAB<CR>CD<Esc>` end-to-end case in `dot.tcyr`.
- **Arrow keys in interactive mode now move the cursor instead of
  triggering destructive NORMAL-mode commands.** Pre-1.2.1 the TTY
  driver read 1 byte per syscall, so the 3-byte CSI escape sequence
  (e.g. arrow up = `ESC [ A`) got dispatched a byte at a time: ESC
  exited INSERT to NORMAL, `[` was unmapped, and `A`/`B`/`C`/`D`
  triggered vim's `A`/`B`/`C`/`D` (append-end-of-line, word-back,
  change-end-of-line, delete-end-of-line) — destructive in every
  direction. Fix: new `editor_feed(s, buf, len)` in `src/driver.cyr`
  scans the read buffer for `ESC [ <final>` CSI sequences and
  dispatches `ACT_MOVE_*` directly via `motion_apply` (consuming 3
  bytes per hit); `run_editor` and `run_headless` in `src/main.cyr`
  switched from a 1-byte read to an 8-byte read + `editor_feed`.
  Bare ESC stays an immediate mode-exit (dispatch unchanged).
  Limitation: if a CSI sequence is split across reads (rare on modern
  terminals; can happen on slow serial), the leading ESC dispatches
  alone — acceptable degenerate case; closes with a 1-byte
  look-ahead buffer in a follow-up. Verified by 6 new cases in
  `dot.tcyr` (`editor_feed: CSI arrow sequences move cursor without
  mode toggle`, `editor_feed: arrow keys work in INSERT mode without
  exiting`, `editor_feed: bare ESC still exits INSERT immediately`,
  `editor_feed: unknown CSI final byte gets swallowed`, plus the
  Enter-key end-to-end).

### Added

- `ACT_INSERT_NEWLINE` action constant in `src/mode.cyr`; `insert_newline(s)`
  helper in `src/insert.cyr`; `editor_feed(s, buf, len)` driver-side
  multi-byte processor in `src/driver.cyr`.

### Changed

- `src/main.cyr` `run_editor` and `run_headless` TTY read loops switched
  from a 1-byte to an 8-byte read buffer + `editor_feed` dispatch.
  Modern terminals deliver entire CSI sequences in one TTY frame, so
  the 8-byte buffer captures arrow / function / mouse codes as a unit.

### Tests

- `tests/dispatch.tcyr` — added `INSERT: Enter / LF -> INSERT_NEWLINE`
  group: asserts both `KEY_ENTER` (13/CR) and `KEY_LF` (10/LF) return
  `ACT_INSERT_NEWLINE` in INSERT mode and don't change mode.
- `tests/dot.tcyr` — added 5 driver-side groups: CSI arrow sequences
  in NORMAL move cursor without mode toggle (down/up/right/left);
  arrows in INSERT move cursor without exiting INSERT; bare ESC still
  exits INSERT immediately (regression guard); unknown CSI final byte
  gets swallowed (no destructive fallback); end-to-end Enter-key
  drive (`iAB<CR>CD<Esc>` produces `AB\nCD`).

### Binary

- `build/cyim` — DCE build size: **356,424 B** (+1,168 B over 1.2.0
  for `editor_feed` plus the 8-byte read buffer in main.cyr; v1.2.0
  was 355,256 B).

## [1.2.0] — 2026-04-28

Minor release — closes the v1.1.x grep-surface bundle by landing the
`--regex=<flavor>` modifier on the four pattern verbs (`--grep`,
`--grepfiles`, `--replace`, `--replace-all`) and the two file-sourced
variants (`--replace-files`, `--replace-files-all`). The upstream gate
lifted: cyrius 5.7.23 ships a Thompson NFA / Pike matcher in
`lib/regex.cyr` (engine landed at v5.7.18) alongside the original glob
helpers. cyim consumes the `regex_*` ABI directly.

Default behavior is unchanged — pattern verbs without `--regex=` still
treat the pattern as a literal substring (back-compat regression-guarded
by case 62 in `tests/cli_smoke.sh`). Adding `--regex=ere` switches to
the engine.

The internal shape is set up for future engines and future per-engine
options without rewrite — see ADR 0002 for the extensibility decision.
Additional engines (`bre`, `re2`, `pcre`, `fuzzy`, `vim`) will ship via
the [`niyama`](https://github.com/MacCracken/niyama) standalone Cyrius
lib (sandhi-pattern lifecycle: out-of-tree → 1.0.0 → foldable into
cyrius stdlib once consumer count earns it).

Also: cyrius toolchain pin bumped 5.7.13 → 5.7.23.

### Added

- `--regex=<flavor>` modifier on `--grep`, `--grepfiles`, `--replace`,
  `--replace-all`, `--replace-files`, and `--replace-files-all`.
  Today's only valid flavor: `ere` (cyrius stdlib `lib/regex.cyr`
  Pike NFA — POSIX-ERE-ish: char classes `\d`/`\w`/`\s`/`\b`,
  alternation `|`, groups `()`, quantifiers `* + ? {n,m}`, lazy
  quantifiers, anchors `^ $`). Default stays literal substring
  (no `--regex=` = back-compat byte-for-byte).
- Cyrius stdlib `regex` added to `cyrius.cyml [deps].stdlib`. DCE
  trims unreferenced regex symbols when `--regex=` is unused.
- `RegexOpts` struct (`src/cli.cyr`) — heap-allocated, 24 B, with
  reserved 8-byte slots for future per-engine flags (icase,
  multiline, dotall, ungreedy, etc.). Threaded through all six
  affected verbs so adding options later is a struct-field add,
  not a signature-change rewrite. See ADR 0002.
- `Matcher` struct (`src/cli.cyr`) — 24 B abstraction over
  literal-vs-regex hit detection. `_matcher_literal()` /
  `_matcher_regex()` constructors, `_matcher_kind()` /
  `_matcher_needle()` / `_matcher_nfa()` / `_matcher_nlen()`
  accessors. Per-call dispatch is a one-bit branch on kind;
  engine selection happens at compile time in `_matcher_regex()`.
- `_cli_count_matches_m(b, m)` and `_cli_substitute_m(src, m, new, mode)`
  matcher-dispatching variants of the existing literal helpers.
  Literal path delegates byte-for-byte to the v1.1.x functions —
  zero-regression guarantee for callers without `--regex=`.
  Regex path materializes the buffer once and walks
  `regex_search_at` iteratively (zero-width matches advance by 1
  byte per the standard regex idiom).
- `_cli_substitute_regex(src, nfa, new, mode)` — the regex
  substitution kernel, separate from the literal byte-by-byte
  loop so each can stay readable in isolation.
- ADR `docs/adr/0002-regex-extensibility-shape.md` — records the
  three load-bearing choices: surface form (`--regex=<flavor>`,
  not bare `--regex`), internal threading (`RegexOpts` struct, not
  primitive `flavor_id`), and naming convention (`FLAVOR_LITERAL =
  0`, flavors `>= 1`).

### Changed

- `_cli_grep_one` signature: `pattern` parameter replaced with
  `m` (Matcher). Matcher kind is hoisted before the per-line loop
  so the per-iteration cost is a single indexed compare, not a
  struct re-load. Literal path keeps the v1.1.x byte-by-byte scan
  unchanged; regex path materializes the line into a NUL-terminated
  scratch buffer per-line and calls `regex_search`. Per-line alloc
  is cheap at cyim's single-file CLI scale.
- `run_grep`, `run_grepfiles`, `run_replace`, `run_replace_files`
  signatures gain a `regex_flavor` trailing parameter (caller
  passes `FLAVOR_LITERAL` for back-compat literal path).
  `run_batch` and `run_write` are unchanged — `--batch` does not
  take `--regex=` in 1.2.0 (each pair is its own OLD/NEW;
  flavor-per-pair semantics deferred until demand surfaces).
- Six per-verb dispatch helpers extracted from `main.cyr`'s `main()`
  into `src/cli.cyr` as `_dispatch_grep` / `_dispatch_grepfiles` /
  `_dispatch_replace` / `_dispatch_replace_all` /
  `_dispatch_replace_files` / `_dispatch_replace_files_all`.
  Forced by Cyrius's per-function 64-return cap once each arm
  gained the `--regex=` parsing branches (six new returns per arm).
  No logic change — pure code motion. main.cyr now reads as a
  thin verb dispatcher.
- `cyim --help` output gains one line documenting `--regex=<flavor>`
  across the affected verbs.
- Cyrius toolchain pin bumped `5.7.13 → 5.7.23` in
  `cyrius.cyml [package].cyrius`. 5.7.23 is the first release that
  exposes the Pike NFA engine (added at v5.7.18) through the
  `regex_*` ABI: `regex_compile`, `regex_match`, `regex_search`,
  `regex_search_at`, `regex_group_start`/`_end`. No `regex_free` —
  the engine uses lazy bump-init via `_re_m_lazy_init` (compile
  once per process invocation; cyim's CLI shape suits that
  perfectly — one compile per verb call).

### Tests

- `tests/cli_smoke.sh` extended from 58 → 84 PASS assertions
  (cases 59–74 are the new v1.2.0 `--regex=` matrix):
  - 59: `--grep --regex=ere [0-9]+` digit class match.
  - 60: `--grep --regex=ere foo|qux` alternation.
  - 61: `--grep --regex=ere ^baz` anchor match.
  - 62: `--grep '[0-9]+'` (no `--regex=`) — literal-substring
    back-compat regression guard. Special chars must NOT be
    interpreted as regex when `--regex=` is absent. Exit 1
    (no match) confirms the literal path was taken.
  - 63: `--grep --regex=ere '['` invalid pattern → exit 2.
  - 64: `--grep --regex=pcre 'foo'` unknown flavor → exit 2
    (with the supported-flavor list in the error).
  - 65: `--grep --regex= 'foo'` empty flavor → exit 2.
  - 66: `--grep --regex=ere --regex=ere 'foo'` duplicate flag
    → exit 2 (mirrors the v1.1.3 dup-flag pattern).
  - 67: `--grepfiles --regex=ere '[0-9]+' f1 f2` multi-file
    regex match — `FILE:N:LINE` shape preserved.
  - 68: `--replace --regex=ere '[0-9]+' XXX FILE` unique
    digit-class substitution.
  - 69: `--replace-all --regex=ere '[0-9]+' N FILE` multi-
    occurrence digit substitution (proves the regex
    `regex_search_at` iteration loop advances correctly).
  - 70: `--replace --regex=ere '^one=' first= --expect-1 FILE`
    composes regex pattern with the count assertion (proves
    `_cli_count_matches_m` returns the regex-aware count).
  - 71: `--replace-files --regex=ere OLD_FILE NEW_FILE FILE`
    proves `--regex=` flows through the file-sourced OLD/NEW
    path. OLD file contents = `[0-9]+`; substitutes to `NUM`.
  - 72: `--replace-files-all --regex=ere` same shape, multi-
    occurrence.
  - 73: `--grep --regex=ere --context=1 ^baz FILE` composes
    `--regex` with the v1.1.4 `--context=N` modifier — pre/match/
    post emit shape unchanged.
  - 74: `--replace-all --regex=ere [0-9]+ N --wc=l FILE` composes
    `--regex` with the `--wc=l` modifier — `<lines> <file>`
    output unchanged.
- All 92 `.tcyr` test assertions still pass (no source-of-truth
  changes touched the editor-mode code paths).
- `tests/integration_smoke.py` unchanged — PTY-driven path
  doesn't touch the agent-drive verbs; 45 PASS assertions still
  green.

### Roadmap

- Additional regex engines (`bre`, `re2`, `pcre`, `fuzzy`, `vim`)
  ship via the niyama standalone Cyrius lib, foldable into stdlib
  per the sandhi v5.7.0 lifecycle once ≥2 long-horizon AGNOS-lineage
  consumers earn it. cyim's `--regex=<flavor>` parser-side
  automatically picks them up — extend the flavor-name switch in
  `_regex_flavor_id` and add a dispatch arm in `_matcher_regex`.
  No changes to the run_* signatures or the per-verb dispatch
  helpers. See `project_regex_engine_placement.md` (cross-repo
  placement decision) and ADR 0002 (cyim-side extensibility shape).
- Per-engine options (icase, multiline, dotall, ungreedy, backref
  in `--replace` NEW) extend `RegexOpts.reserved_flags` plus parser
  spelling additions. The exact spelling — separate `--regex-<name>`
  flags vs. comma-extended value `--regex=ere,icase` — is deferred
  until the second engine lands and use cases sharpen.

### Internal

- **Lint cleanup sweep across all 20 src files** to take CI from 42
  warnings to 0. Three categories of fix landed in 1.2.0:
  - **Section-header comments**: cyrius lint counts UTF-8 bytes, not
    visible characters. Box-drawing `─` (U+2500) is 3 bytes each, so
    section headers like `# ── Allocation ─────...` ran 130–200 bytes
    despite being only ~70 visible chars. Fix: trim the trailing
    `─` run, keep the leading `# ── <name>` marker. Visual section
    delineation preserved. Affects 27 lines across 12 files.
  - **Long syscall strings** (help text, error messages, usage
    strings >120 bytes): split into multiple `syscall(1, fd, "chunk", N)`
    writes at logical phrase boundaries. Cyrius has no string-
    continuation operator, so this is the canonical split shape.
    Affects 12 lines across `src/main.cyr` and `src/cli.cyr`.
  - **Multiple consecutive blank lines** at the v1.2.0 Matcher block
    insertion seam in `src/cli.cyr` line 279: collapsed to one.
- These warnings predated v1.2.0 (the box-drawing convention has been
  in cyim since M0); CI escalated lint from advisory to blocking
  after v1.1.4 shipped, surfacing them as a blocker on the v1.2.0
  push. Fixed in this release because v1.2.0 is the first one to hit
  the gate.

### Binary

- `build/cyim` — DCE build size: **355,256 B** (v1.2.0 added the
  Matcher + RegexOpts abstractions in `src/cli.cyr` plus six
  `_dispatch_<verb>` extraction functions plus the Pike NFA engine
  consumed from cyrius stdlib `lib/regex.cyr`; the lint cleanup
  added +424 B from syscall-split overhead vs the pre-cleanup
  354,832 B. v1.1.4 was 312,088 B, so +43,168 B total — the bulk
  is the engine itself, the cyim consumer code adds ~4 KB, the
  dispatch extraction is byte-neutral, the lint-cleanup syscall
  splits add ~400 B).

## [1.1.4] — 2026-04-27

Patch release — grep-surface expansion (split out of the v1.1.x bundle
ahead of the still-upstream-gated regex piece) plus a dogfood-driven
ergonomics addition. Three new agent-drive primitives:

- **`--grepfiles <pattern> <file...>`** — multi-file grep variant.
- **`--context=N`** modifier on `--grep` / `--grepfiles` — `grep -C N`-shaped
  context windows with overlap-merge and `--` group separators.
- **`--replace-files OLD_FILE NEW_FILE FILE`** (and `--replace-files-all`) —
  read OLD and NEW from file contents instead of argv. Closes the
  shell-escape friction surfaced in the v1.1.4 dogfood loop when
  splicing multi-line edits through `cyim --batch`.

Also: cyrius toolchain pin bumped 5.7.7 → 5.7.13.

### Added

- `cyim --grepfiles [--context=<n>] <pattern> <file...>` — multi-file
  variant of `--grep`. Output stays `FILE:N:LINE` (`grep -n` shape
  already disambiguates by filename, so multi-file is a natural
  extension). Exit 0 if any file matched, 1 if none, 2 on usage error,
  3 if any FILE is missing (fail-fast on first miss so callers learn
  about typos before partial output diverges). Implemented in
  `src/cli.cyr` as `run_grepfiles`, sharing `_cli_grep_one` with
  `run_grep`.
- `--context=<n>` modifier on `--grep` and `--grepfiles` — emits N
  lines before+after each match in `grep -C N` shape. Match lines stay
  `FILE:N:LINE`; context lines emit as `FILE-N-LINE` (matching
  `grep -n -C` exactly). Overlapping windows merge (no double-emit);
  non-adjacent groups within a file get a `--` separator; multi-file
  output gets a `--` between files. `--context=0` (or omitting the
  flag) preserves v1.1.0–v1.1.3 single-line-per-match output
  bytes-for-bytes. Symmetric only at first cut — asymmetric
  `--before` / `--after` deferred until demand surfaces.
- `cyim --replace-files OLD_FILE NEW_FILE FILE` (mode = REPLACE_FIRST_UNIQUE)
  and `cyim --replace-files-all OLD_FILE NEW_FILE FILE` (mode =
  REPLACE_ALL) — OLD and NEW are read from the named files (not argv).
  Modifier surface mirrors `--replace[-all]` exactly (`--wc[=l|=long]`,
  `--expect-N=<n>`, `--expect-1`); exit codes match too. Implemented
  via the new `_cli_slurp_file` helper plus a thin `run_replace_files`
  wrapper that delegates to the existing `run_replace`. Naming note:
  "files" refers to the I/O source for OLD/NEW (their content lives in
  files), **not** "replace across multiple files" — that shape can
  ship later if demand surfaces.

### Changed

- `cyim --grep` dispatch in `src/main.cyr` is now a modifier-parsing
  walk-all-argv loop (was: positional-only, no modifiers). The only
  modifier supported today is `--context=<n>`, but the parser uses the
  same duplicate-flag-guard pattern from v1.1.3 so future modifiers
  (e.g. `--regex=<flavor>` once the upstream NFA module lands) thread
  in mechanically.
- `run_grep` in `src/cli.cyr` gains a `context_n` parameter and now
  delegates to a shared `_cli_grep_one` core. `--context=0` produces
  output identical to the v1.1.3 `run_grep` byte-for-byte
  (regression-guarded by `cli_smoke.sh` case 39).
- Cyrius toolchain pin bumped `5.7.7 → 5.7.13` in
  `cyrius.cyml [package].cyrius`. 5.7.13 ships `lib/regex.cyr`, but
  the file's own header self-describes as *"Simple glob-style matching
  + literal search. Not full regex."* — this is **not** the NFA
  `re_compile` / `re_match` / `re_free` ABI the cyim plan referenced.
  The upstream gate for `--regex=<flavor>` is still in place. Roadmap
  escalates the regex piece from soft demand-gate to **hard
  pre-cyrius-5.7.x-EOL target** as a result.

### Tests

- `tests/cli_smoke.sh` extended from 35 → 58 cases (cases 33–49). New
  cases:
  - 33: `--grepfiles` two-file match (per-file `FILE:N:LINE` shape).
  - 34: `--grepfiles` no match anywhere → exit 1.
  - 35: `--grepfiles` missing FILE → exit 3 (fail-fast).
  - 36: `--grep --context=1` emits pre/match/post with `-` / `:`
    separators per `grep -n -C` shape.
  - 37: `--context=2` overlapping-window merge — no `--` between
    adjacent matches.
  - 38: `--context=1` non-adjacent groups → `--` separator present.
  - 39: `--context=0` produces output identical to no-flag (back-compat
    regression guard).
  - 40: `--context=<non-int>` → exit 2.
  - 41: duplicate `--context=` refused (mirrors v1.1.3 dup-flag pattern).
  - 42: `--grepfiles --context=N` → `--` between files (matches
    `grep -n -C N` cross-file behavior).
  - 43: `--replace-files` round-trips multi-line OLD/NEW through file
    paths.
  - 44: `--replace-files` empty OLD_FILE → exit 2.
  - 45: `--replace-files` missing OLD_FILE → exit 3.
  - 46: `--replace-files` non-unique OLD without `-all` → exit 5
    (delegates to `run_replace`).
  - 47: `--replace-files-all` succeeds where 46 fails.
  - 48: `--replace-files --expect-1` count mismatch → exit 6, FILE
    untouched (atomicity guard).
  - 49: `--replace-files --wc=l` prints `<lines> <file>` to stdout.
- All 92 `.tcyr` test assertions still pass (no source-of-truth
  changes; the `_cli_grep_one` refactor is behavior-preserving when
  `context_n=0`).
- `tests/integration_smoke.py` unchanged (PTY-driven path doesn't
  touch the new verbs); 45 PASS assertions still green.

### Roadmap

- The `--regex=<flavor>` modifier (the third leg of the original
  bundled grep-surface expansion) escalated from soft demand-gate to
  **hard pre-cyrius-5.7.x-EOL target** after the 5.7.13 review. The
  cyrius stdlib must ship the NFA `re_compile` / `re_match` /
  `re_free` ABI inside the 5.7.x series, not slip to 5.8.x or 6.x.
  When it lands, the cyim consumer side is mechanical — the v1.1.4
  parser already threads `--context=N` through the duplicate-flag-guard
  machinery, so adding `--regex=` on top is one more arm.

### Binary

- `build/cyim` (DCE): **312,088 B** (v1.1.3 was 300,640 B; +11,448 B
  for the line-index + ring-merge context implementation, the
  `--grepfiles` dispatch + `run_grepfiles`, the `--replace-files[-all]`
  dispatch + `_cli_slurp_file` + `run_replace_files`, and the
  associated `--help` text).

## [1.1.3] — 2026-04-26

Patch release — agent-drive paper cuts: silent last-wins on duplicate
modifier flags is replaced with explicit refusal (exit 2), and the
`cyim --help` description for `--grep` now states its matching flavor
("literal substring, not regex"). Both surfaced in the dogfood loop as
"two cyim observations to confirm next sweep" — neither was a bug, but
both made the surface ambiguous to a caller who couldn't be expected to
read source.

### Changed

- `cyim --help`: the `--grep <pattern> <file>` line now reads
  `(read-only; literal substring, not regex; emit FILE:N:LINE)`.
  Prior text didn't surface the matching flavor, so a caller reaching
  for `--grep '^foo'` might reasonably (but wrongly) expect a regex
  anchor instead of a literal `^` byte. The matching code itself is
  unchanged — `_cli_match_at` in `src/cli.cyr` was always pure
  byte-compare; the gap was documentation, not behavior.

### Fixed

- **Duplicate modifier flags now refused with exit 2** (was: silent
  last-wins). Modifier flags occupy single scalar slots in the parser:
  passing the same flag twice — or two flags from the same family —
  used to silently overwrite the earlier value, which made the surface
  ambiguous (and asymmetric with the existing "extra positional → exit
  2" guard from v1.1.1). v1.1.3 adds per-family `*_seen` guards across
  all four agent-drive verbs and emits `cyim: duplicate flag: --NAME`
  to stderr on the second occurrence.

  Family grouping (a duplicate within any family trips the check):
  - `--expect=<pat>` and `--expect-not=<pat>` — share the same scalar
    slot on `--write` and `--batch`; passing both is a duplicate.
  - `--expect-N=<n>` and `--expect-1` — share the same scalar slot on
    `--replace[-all]`; passing both is a duplicate.
  - `--wc` / `--wc=l` / `--wc=long` — same flag with optional value
    on `--write`/`--replace[-all]`/`--batch`.
  - `--all` — `--batch`-only global mode.

  Error message names the flag actually duplicated (so
  `--expect=foo --expect-not=bar` errors as `--expect-not`, since
  that's the second one parsed). Exit 2 reuses the existing
  "bad CLI args" slot — no new exit code introduced.

### Tests

- `tests/cli_smoke.sh` extended from 28 → 35 cases. New cases (26–32):
  - 26: duplicate `--expect=` on `--write` → exit 2.
  - 27: cross-family `--expect=` + `--expect-not=` on `--write` → exit 2.
  - 28: duplicate `--expect-1` on `--replace` → exit 2.
  - 29: cross-family `--expect-1` + `--expect-N=` on `--replace` → exit 2.
  - 30: duplicate `--wc` on `--write` → exit 2.
  - 31: duplicate `--all` on `--batch` → exit 2.
  - 32: `--grep '^foo'` regression — matches a line containing the
    literal `^foo` byte sequence and does **not** match a line
    containing only `foo` (would invert if `^` were a regex anchor).

### Binary

- `build/cyim` (DCE): **300,640 B** (v1.1.2 was 298,392 B; +2,248 B
  for 8 duplicate-flag guards across the four verbs plus the slightly
  longer `--grep` help string).

## [1.1.2] — 2026-04-26

Patch release — `--batch` agent-drive verb + cyrius toolchain bump to
5.7.7. Closes the cyim pain point in cyrius-bb's tooling field notes
(`tooling-pain-points.md`): "no multi-edit-in-one-call mode … a batch
mode (read a list of <old>=>new> pairs) would be cleaner for larger
refactors."

### Added

- `cyim --batch <file>` — apply N substitutions from stdin, save once.
  Stdin format: NUL-separated alternating tokens
  `OLD1\0NEW1\0OLD2\0NEW2\0…\0`. Token count must be even and ≥ 2;
  the stream must end with a NUL. Each pair applies in order to the
  in-memory buffer; the file is written **once** at the end. **Atomic**
  — failure mid-batch (pair K's OLD missing or non-unique) leaves
  FILE untouched on disk.

  Default per-pair semantics match `--replace`: OLD must be unique in
  the (in-progress) buffer at apply time, exit 5 if not. `--all`
  switches every pair to `--replace-all` (substitute every occurrence).

  Composes with the existing modifier surface:
  - `--wc[=l|=long]` — print `wc(1)` on the post-save buffer.
  - `--expect=<pat>` / `--expect-not=<pat>` — post-save assertion on
    the result; exit 6 on mismatch (file is already saved at that
    point — the assertion is a contract on the *final* result).

  Exit codes:
  - **0** — every pair applied; file saved
  - **1** — save failed
  - **2** — bad CLI args (missing FILE; malformed stdin: empty,
    odd token count, missing trailing NUL, empty OLD)
  - **3** — file not found
  - **4** — pair K's OLD not found in (in-progress) buffer
  - **5** — pair K's OLD occurs more than once and `--all` not passed
  - **6** — `--expect` / `--expect-not` mismatch on final buffer

  Closes the workflow gap noted in `tooling-pain-points.md` — the
  three-chained `--replace` block in cyrius-bb's `cyrius.cyml` rewrite
  is now one call. Stdin format byte-clean: handles em-dashes,
  newlines, the literal `=>` (the sigil the field-notes author
  proposed) — no escape ceremony required because separators are
  NUL bytes, not text.

  Sequel to v1.1.0's `--grep`/`--expect[-not]`/`--expect-N` primitives:
  v1.1.0 closed the *check* boundary jump (no more `cyim … && rg …`),
  v1.1.2 closes the *substitution* boundary jump (no more
  `cyim --replace … && cyim --replace … && …`).

### Changed

- Cyrius toolchain pin: `5.7.1` → `5.7.7` (in `cyrius.cyml [package].cyrius`).

### Tests

- `tests/cli_smoke.sh` extended from 10 → 28 cases. New cases
  (11–25) cover: single pair, sequential multi-pair, non-unique-OLD
  rejection without `--all` (with explicit on-disk atomicity check),
  `--all` global mode, mid-batch failure with on-disk atomicity check,
  empty stdin, odd token count, missing trailing NUL, empty OLD,
  `--expect` / `--expect-not` post-save semantics, interspersed
  modifiers, extra-positional rejection, and a multi-byte-Unicode
  (em-dash) round-trip via `--grep` post-substitution.

## [1.1.1] — 2026-04-26

Patch release — agent-drive CLI flag-parser fix.

### Fixed

- `--write`, `--replace`, `--replace-all`: modifier flags
  (`--wc[=l|=long]`, `--expect=<pat>`, `--expect-not=<pat>`,
  `--expect-N=<n>`, `--expect-1`) are now parseable in any position
  *after the verb*, including interleaved with the positionals or
  after them. v1.1.0 had a front-only modifier loop that bailed at
  the first non-flag arg, so:
  - `cyim --replace OLD NEW --expect-1 FILE` parsed `--expect-1` as
    `FILE` and dropped the real `FILE`, surfacing as exit-3
    `file not found` against the literal path `--expect-1`.
  - `cyim --write FILE --wc=l` silently dropped `--wc=l` (treated as
    a stray after-positional arg, exit 0 with no `wc` output).
  - `cyim --replace OLD NEW --expect-N=1 FILE` had the same shape as
    the `--expect-1` case.

  The fix walks the full argv after the verb, segregating recognized
  modifier flags vs positionals; an unexpected fourth positional
  yields `exit 2` with `unexpected extra argument` on stderr (was
  silently consumed before).

  Note: modifiers BEFORE the verb (`cyim --expect-1 --replace ...`)
  remain out-of-spec — `cyim --help` and the CLAUDE.md surface both
  document modifiers as living between the verb and the positionals.
  An unrecognized first arg falls through to the editor-launch path,
  the same as v1.1.0.

## [1.1.0] — 2026-04-26

Agent-drive CLI surface grows three structural-invariant primitives:
`--grep` (read-only line scan), `--expect` / `--expect-not` (post-write
shape assertion), `--expect-N` / `--expect-1` (pre-substitution count
assertion). Each closes a "tool boundary jump" that previously forced
scripts to chain `rg` / `wc` / `grep -c` around cyim — every check stays
in one binary, one decision, one exit code.

### Added

- `cyim --grep <pattern> <file>` — read-only line scan. Emits
  `FILE:N:LINE` (matches `grep -n` exactly: no spaces around the
  second colon) for every line containing `<pattern>` as a literal
  substring (same matching semantics as `--replace`'s `OLD` — no regex,
  byte-wise compare). Exit codes follow grep(1) convention:
  - **0** — at least one match
  - **1** — no match (file scanned cleanly, just nothing found)
  - **2** — usage error (missing args, empty pattern)
  - **3** — file not found

  Keeps the workflow inside cyim — no `rg` in `PATH`, no shell-escape
  ceremony for special characters in `<pattern>`. Lines without a
  trailing newline still emit (unlike a naive `while read line`).
- `--expect=<pat>` / `--expect-not=<pat>` modifiers on `--write`. After
  the new file content is saved, the resulting buffer is scanned for
  `<pat>`; mismatch returns **exit 6** with a message on stderr
  (`cyim --write: --expect pattern not found in result` or
  `cyim --write: --expect-not pattern present in result`). The file is
  saved either way — the assertion is a contract on the *result*, not
  a save gate. Composes with `--wc` in any order:
  `cyim --write --wc=l --expect="ROUTE_TABLE" handlers.cyr`.

  Closes the structural-invariant case: "after this rewrite,
  `TS_LEX_JSX_SKIP` MUST NOT appear" is now one call (one decision,
  one exit code), not a `cyim --write … && rg -q TS_LEX_JSX_SKIP …`
  chain that loses the connection between edit and check on failure.
- `--expect-N=<n>` / `--expect-1` modifiers on `--replace` and
  `--replace-all`. Asserts `OLD` occurs *exactly* `<n>` times in the
  file *before* substitution; mismatch returns **exit 6** without
  writing. `--expect-1` is sugar for `--expect-N=1`.
  - Takes precedence over the implicit unique/no-match rules — an
    explicit count assertion is the strongest contract the caller can
    express.
  - `--expect-N=0` is the "must be a no-op" idiom: succeeds without
    writing when `OLD` is absent (and honors `--wc` on the unchanged
    file); exits 6 if `OLD` is present.
  - Closes the silent-no-op gap: `--replace OLD NEW FILE` exits 4 when
    `OLD` is missing, but exit 4 is easy to miss in scripts. Pair with
    `--expect-1` and the assertion is explicit.
- `src/cli.cyr` — new helpers backing the surface:
  `_cli_argprefix(arg, prefix)` (modifier-suffix splitter for
  `--expect=…`), `_cli_atoi_nn(s)` (non-negative decimal parser for
  `--expect-N=…`), `_cli_write_buf_range(b, start, end, chunk, cap)`
  (chunked stdout writer for grep line emission — O(N/cap) syscalls
  instead of one per byte), `run_grep(pattern, file_path)` (the line
  walker; handles files without trailing newlines and empty files
  correctly).
- `tests/integration_smoke.py` — 18 new checks covering: `--grep` hit,
  miss, no-args, missing-file, empty-pattern, no-trailing-newline;
  `--write --expect` pass + miss; `--write --expect-not` pass + hit;
  `--wc` + `--expect` compose in either order; `--replace --expect-1`
  match + miss; `--replace-all --expect-N=N` match + mismatch;
  `--replace --expect-N=0` defensive no-op (both branches);
  malformed `--expect-N=<non-int>` exits 2.

### Changed

- Exit code **6** added for assertion failures (`--expect` /
  `--expect-not` / `--expect-N` mismatches). Codes 0–5 unchanged.
  `--grep` overloads exit 1 with grep(1)-conventional "no match"
  semantics — disjoint verb, no collision with the `--write`/`--replace`
  "save failed" meaning of 1.
- `run_write` signature: now `(file_path, wc_mode, expect_pat,
  expect_pol)`. Pass `0, 0` for the trailing pair to preserve pre-1.1
  behavior. `expect_pol`: `0` none, `1` must contain, `2` must not.
- `run_replace` signature: now `(old_str, new_str, file_path, mode,
  wc_mode, expect_n)`. Pass `-1` for `expect_n` to preserve pre-1.1
  behavior (no count assertion).
- Modifier parsing in `src/main.cyr` now uses a per-verb consume loop
  so `--wc`, `--expect`, `--expect-not`, `--expect-N`, `--expect-1`
  can appear in any order between the verb and its positional args.
  Pre-1.1 `--wc` placement (immediately after the verb) still works —
  the new behavior is a strict superset.

## [1.0.2] — 2026-04-26

`--wc` modifier on the agent-drive CLI ops + BUG-001 fix
(silent truncation of `cyim --replace` for `<new>` ≥ ~4 KB).

### Added

- `--wc` modifier may follow `--write`, `--replace`, or `--replace-all`.
  On a successful save, prints `wc(1)` output for the resulting file
  to stdout (matches GNU `wc`'s field order so it drops in for
  existing wrappers):
  - **bare** `--wc`     → `<lines> <words> <bytes> <file>\n`  (matches `wc <file>`)
  - `--wc=l`            → `<lines> <file>\n`                  (matches `wc -l <file>`)
  - `--wc=long`         → alias for `--wc=l`
  Modifier sits between the operation flag and its positional args:
  `cyim --write --wc <file>`,
  `cyim --replace --wc=l <old> <new> <file>`,
  `cyim --replace-all --wc <old> <new> <file>`.
- `src/cli.cyr` — `_cli_count_lines`, `_cli_count_words`,
  `_cli_print_wc` helpers. Word counter follows the POSIX `wc`
  whitespace set (space, tab, LF, VT, FF, CR).
- `tests/integration_smoke.py` — three new checks: `--write --wc`
  full output; `--write --wc=l` lines-only output; `--write --wc=long`
  alias.

### Changed

- `run_write` and `run_replace` now take a trailing `wc_mode`
  parameter (`0` silent, `1` full, `2` lines). Silent (`0`) is the
  pre-1.0.2 behaviour, so existing callers and the `cyim-edit` wrapper
  one-liners need no changes.

### Fixed

- **BUG-001 (P1):** `cyim --replace OLD NEW FILE` no longer falls
  through to a misleading "usage" error (exit 2) when the cmdline
  exceeds 4 KB. Root cause is in `cyrius/lib/args.cyr` —
  `args_init()` reads `/proc/self/cmdline` into a 4096 B stack buffer,
  so any cmdline beyond that gets truncated and `argc` undercounts.
  The upstream stdlib fix lands in cyrius/agnosticos and is re-vendored
  when ready (CLAUDE.md: `lib/` is vendored, never edited from this repo).

  Until then, `src/cli.cyr` ships `_cli_args_reload_big()` — a 2 MB
  heap buffer (Linux ARG_MAX, the kernel's hard cap on argv+envp
  combined) that re-reads `/proc/self/cmdline` and rebinds the
  `args.cyr` globals at startup. Verified at 8 KB and 64 KB NEW args;
  256 KB hits the kernel's per-arg `MAX_ARG_STRLEN` cap before cyim
  runs (out of our control). The workaround is additive (one syscall
  + one `alloc(2 MB)` per invocation) and is retired automatically
  once upstream cyrius lifts the 4096 B cap and we re-vendor.

- `tests/integration_smoke.py` — BUG-001 regression: `--replace`
  with an 8 KB NEW arg and a 64 KB NEW arg both succeed and produce
  the expected substituted file.

## [1.0.1] — 2026-04-25

Agent-drive surface, first-class.

### Added

- `cyim --write <file>` — read stdin, replace `<file>`'s contents
  with it. One syscall path: `buf_load_file` skipped, `buf_clear`
  + `buf_insert` from stdin chunks, `buf_save_file`. No dispatch
  detour. Use case: shell-script "Write the new content here, please."
- `cyim --replace <old> <new> <file>` — substitute the first
  occurrence of `<old>` with `<new>`. **`<old>` must be unique
  in the file.** If it occurs more than once, the command refuses
  with exit 5 (matches the Claude Code Edit invariant — pick a
  more specific OLD or use `--replace-all`).
- `cyim --replace-all <old> <new> <file>` — same, every
  occurrence. Returns exit 0 with the file rewritten regardless
  of count (zero matches still exits 4 — "OLD not found").
- `src/cli.cyr` — new module hosting the three runners +
  `_cli_drain_stdin`, `_cli_match_at`, `_cli_count_matches`,
  `_cli_substitute` helpers. Direct gap-buffer ops; no
  dispatch-chain detour because there's no edit-history /
  mode-state / undo to model — these are tools, not user edits.
- `tests/integration_smoke.py` — three new regression checks:
  `--write` round-trip, `--replace` unique-mode success +
  not-unique exit-5 refusal, `--replace-all` multi-substitution.

### Exit codes (consumer contract)

Mirrors `~/.local/bin/cyim-edit` so existing wrapper scripts can
collapse to `exec cyim --write "$@"` / `exec cyim --replace "$@"`
one-liners:

| Code | Meaning |
|------|---------|
| 0    | Success                                                |
| 1    | Save failed (disk full, permission denied)             |
| 2    | Bad CLI args (missing OLD/NEW/FILE, empty OLD)         |
| 3    | File not found                                         |
| 4    | OLD not found in FILE                                  |
| 5    | OLD occurs more than once and `--replace-all` not used |

### Daimon-orchestrated agent surface

CLAUDE.md's consumer story now points at four CLI shapes:

1. `cyim <file>` — interactive (humans).
2. `cyim --headless <file>` — keystroke stream (low-level agent
   drive, full editor semantics including search/undo/dot/visual).
3. `cyim --write <file>` — high-level "set file content" (matches
   the Claude Code `Write` tool shape).
4. `cyim --replace [--all] OLD NEW <file>` — high-level
   "find/replace" (matches the Claude Code `Edit` tool shape, with
   the same uniqueness invariant by default).

`~/.local/bin/cyim-write` and `cyim-edit` wrapper scripts can now
become `exec` shims; they predated the native surface.

### Receipts at v1.0.1

- DCE binary: 283,984 B (1.0.0 was 275,640 B; +8,344 B for the
  three new runners + helpers).
- 18 / 18 .tcyr suites pass.
- 18 integration checks (15 from 1.0.0 + 3 new for `--write` /
  `--replace` / `--replace-all`).
- 0 CRITICAL / HIGH / MEDIUM security findings (unchanged).

## [1.0.0] — 2026-04-25

First release. The M0–M7 work that started as the M0 scaffold
on 2026-04-25 lands as v1.0.0 the same day — every milestone's
output is in this release because we accumulated everything in
the `[Unreleased]` block and bumped at the close. Future
releases will follow the more typical "ship 0.X.Y patches
between minor bumps" cadence.

### Headline features (v1.0)

- **Modal editor** in the vim lineage: NORMAL / INSERT / COMMAND
  / SEARCH / SEARCH_BACK / VISUAL / VISUAL_LINE.
- **Gap-buffer** with full motion + edit surface.
- **Multi-buffer** registry with `:bn` / `:bp` / `:b N` / `:ls`.
- **Multi-window** splits (`:sp` / `:vsp`) with Ctrl-w h/j/k/l
  navigation and per-leaf status row.
- **Syntax highlighting** via [vyakarana](https://github.com/MacCracken/vyakarana)
  1.0.2 — 11 bundled grammars (c, cyrius, javascript, json,
  markdown, python, rust, shell, toml, typescript, yaml). Per-buffer
  tokenbuf cache keeps render frames at sub-microsecond cost on
  unchanged buffers.
- **Search** (`/` `?` `n` `N` `*` `#`) with case-fold via
  `:set ic`; naive byte-wise scan, no regex (no ReDoS class).
- **Undo / redo** (`u` / Ctrl-r) — snapshot-based, per buffer.
- **Visual mode** + single yank register: `y` / `d` / `p` / `P`.
- **Dot repeat** (`.`) replays the last insert session.
- **`:set` runtime config**: `ic` / `noic` / `number` /
  `nonumber` / `tabstop=N` / `maxfilesize=N`.
- **`.cyimrc`** flat-CYML config with palette overrides + the
  same editor options.
- **Headless / agent-drive** entry point — `editor_run(s, keys, n)`
  drives the same dispatch+apply chain a TTY consumer takes,
  exposed via `cyim --headless [<file>]` for shell scripts and
  agents. Reads keystroke bytes from stdin until EOF or
  `editor_quit`; no `tty_raw`, no alt-screen, no per-frame
  render. Recipe:
  `printf 'iEDIT\x1b:wq\r' | cyim --headless file.cyr`.
- **No embedded scripting language. Ever.** Configuration is
  data, not code. The bulk of vim's historical CVE surface
  (Vimscript injection, modeline RCE, plugin sandbox escapes)
  is structurally absent.

### Receipts at v1.0

- DCE binary: **274,656 B** (~10× smaller than vim, ~38× smaller
  than neovim).
- Source: **~4 200 LOC editor + ~5 100 LOC tests/fuzz/grammars**
  (~125× smaller than vim's editor core).
- **847 .tcyr assertions** across 18 suites.
- **15 integration checks** in `tests/integration_smoke.py` —
  14 PTY-driven (search / undo / dot / visual / multi-window /
  highlight) + 1 headless (subprocess pipe into `cyim
  --headless`).
- **3 fuzz harnesses** (gap-buffer, tokenizer, full-driver), all
  pass `cyrius fuzz`.
- **9 perf benches** in `tests/perf.bcyr` with M5 baseline + M6
  cache-hit win recorded in [`BENCHMARKS.md`](BENCHMARKS.md).
- Security audit: **0 CRITICAL / 0 HIGH / 0 MEDIUM** findings;
  8 LOW findings all triaged with rationale per
  [`docs/audit/2026-04-25-m7-audit.md`](docs/audit/2026-04-25-m7-audit.md).
  External CVE corpus survey at
  [`docs/security/2026-04-25-0day-corpus.md`](docs/security/2026-04-25-0day-corpus.md);
  trust-model ADR at [`docs/adr/0001-trust-model.md`](docs/adr/0001-trust-model.md).
- `cyrius lint` clean of correctness warnings; `cyrius fmt --check`
  clean across all `src/*.cyr`.
- **Dead-code floor at v1.0:** two unreferenced symbols
  retained: `tty_cursor_hide` and `tty_cursor_show`. Both are
  public ANSI helpers in [`src/tty.cyr`](src/tty.cyr); they're
  the natural wiring point for "hide cursor during repaint to
  avoid flicker" — a UX polish that's plausible-near-future.
  Total binary cost of the two: ~80 B. Recorded here so a
  future audit can decide whether to delete or wire.

### Late-bite addition (rolled into 1.0.0)

- `cyim --headless [<file>]` — the agent-drive surface promised
  by M1 ("the keymap dispatch is the API for both human + agent
  drivers") finally exposed at the CLI. The internal
  `editor_run` had been in the binary since M1 bite 6 but
  reachable only from `.tcyr` tests. Discovered missing when an
  external agent tried to shell out to cyim and found the
  TTY-only surface; added before the v1.0 tag so consumers
  shipping against 1.0.x have it from day one.
- Recipe (raw bytes; `printf` for ESC / CR):
  `printf 'iEDIT\x1b:wq\r' | cyim --headless file.cyr`
- `tests/integration_smoke.py` — new headless check via
  `subprocess.run` (no PTY needed); proves the
  load → drive → save → exit path round-trips.
- `docs/guides/usage.md` — "Headless / agent-drive" section
  added under Starting cyim.

### CI / release plumbing (v1.0 ship-prep)

- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` —
  ship-prep root files. SECURITY.md cross-references the M5/M7
  audit docs, the trust-model ADR, and explains what's in/out
  of scope for security reports.
- `.github/workflows/ci.yml` rewritten — modeled on owl's
  proven shape. Now has: `workflow_call` trigger (release.yml
  reuses it as a gate), ELF verify, `cyrius lint` per-file
  with non-cosmetic-warning hard fail, `cyrius test`,
  `cyrius fuzz`, `cyrius bench tests/perf.bcyr` (compile-only
  smoke), `python3 tests/integration_smoke.py` (PTY E2E), DCE
  parity check (re-runs PTY smoke against the `CYRIUS_DCE=1`
  binary), plus a separate `security` job (regression guards
  for /bin/sh, sys_system, F-1 control-byte sub, F-2 file-size
  cap, F-3 cmdbuf cap, oversized stack buffers per CLAUDE.md
  rule) and a `docs` job (required-files coverage + version
  consistency: VERSION = CHANGELOG section = cyrius.cyml
  `${file:VERSION}` indirection = `print_version` string in
  src/main.cyr).
- `.github/workflows/release.yml` rewritten — semver-tag
  trigger, full CI gate via `workflow_call`, version-verify
  job, build matrix (x86_64-linux today; matrix expands as the
  Cyrius toolchain gains targets), source tarball, SHA256SUMS,
  `softprops/action-gh-release@v2` with the release body pulled
  from the matching CHANGELOG section (auto-prerelease on
  `0.x` tags). Packaged artifact ships binary + grammars +
  README + LICENSE + CHANGELOG + VERSION + SECURITY.md; no
  vendored lib/ (consumers run `cyrius deps` themselves).

### Milestones rolled into v1.0

- **M0** (2026-04-25) — scaffold (boots / prints / exits).
- **M1** — gap-buffer + raw-mode TTY + modal dispatch (8 bites).
- **M2** — syntax highlighting via vyakarana (6 bites).
- **M3** — multi-buffer + splits + window navigation (6 bites).
- **M4** — search, undo, visual, `.` repeat, `:set` + `.cyimrc`
  (6 bites).
- **M5** — polish: docs, perf benches, fuzz, receipts (4 bites).
- **M6** — P(-1) hardening: tokenbuf cache, F-1/F-3/F-4 closures,
  cleanliness gate, refactor pass (6 bites).
- **M7** — Security audit: 0day CVE corpus survey, checklist
  re-walk, F-2 fix, trust-model ADR, M7.5 CVE verification pass
  (5 bites).

For per-milestone detail, see the M2-M7 sections below (preserved
from the [Unreleased] block at the time of release).

---

### Added (M2)
- `[deps.vyakarana]` block in `cyrius.cyml` — pinned to vyakarana
  1.0.2 via git tag; pulls `dist/vyakarana.cyr` into `lib/`.
- `grammars/` directory bundled from vyakarana (11 languages: c,
  cyrius, javascript, json, markdown, python, rust, shell, toml,
  typescript, yaml). Resolved at runtime via `/proc/self/exe` so
  the binary works regardless of cwd.
- `src/highlight.cyr` — vyakarana wrapper: `highlight_init`
  resolves grammars/ via /proc/self/exe and pre-loads bundled
  grammars (suppressing vyakarana's lazy cwd-relative bootstrap
  via `_grammars_bootstrapped = 1`). `highlight_buf(b, lang)`
  copies the gap-buffer to a NUL-terminated heap cstr and calls
  vyakarana's `tokenize_source`. `highlight_kind_at(tb, pos)`
  linear-scans for the token covering `pos`, returning a TK_*
  constant; falls back to `TK_WHITESPACE` on uncovered positions
  or a null tokenbuf.
- `tests/highlight.tcyr` — 31 assertions: unknown-lang returns 0,
  Cyrius `var x = 42` token-kind layout (KEYWORD/IDENT/OPERATOR/
  NUMBER/WHITESPACE), `fn main() { return 0; } # done` covering
  PUNCTUATION + COMMENT-to-EOL, double-quoted STRING literal,
  empty buffer is safe, null tokenbuf is safe.
- `src/lang.cyr` — extension-based language detection.
  `detect_language_from_path(path)` returns one of vyakarana's
  bundled grammar names (cyrius/shell/python/javascript/typescript/
  rust/c/toml/json/yaml) or `"plain"`. Case-insensitive on the
  extension; suffix match (not contains) so `.rsync` doesn't match
  `.rs`. NULL path safely returns `"plain"`.
- `tests/lang.tcyr` — 37 assertions over 8 groups: index lookup,
  cyim's own .cyr/.tcyr/.bcyr/.fcyr/.cyml mappings, every
  language's primary extension, case-insensitivity, full directory
  paths, no-extension misses, NULL path, suffix-vs-contains
  edge cases.
- `src/render.cyr` extended with the M2 highlighting layer:
  `theme_token_color(kind)` (ten-kind palette → 256-color ANSI
  index, -1 for "no color"); `render_build_line(b, line, cols, tb,
  out, max)` materializes one rendered line into a caller buffer,
  emitting fg-escape transitions and resets at kind boundaries with
  an unconditional reset before the trailing CRLF when a color is
  still active. `render_line` and `render_frame` gained a `tb`
  parameter — `tb == 0` is the plain fallback.
- `tests/render.tcyr` — 27 assertions: palette spot-checks, plain
  rendering (incl. empty buffer, empty interior line, `cols`
  truncation), highlighted `var x` byte-for-byte ANSI verification,
  trailing-comment final-reset path, empty interior line stays
  uncolored even with a tokenbuf.
- `src/main.cyr` wired through M2: detects language from
  `file_path` via `detect_language_from_path`, calls
  `highlight_init` once at startup, retokenizes the buffer per
  frame and threads the tokenbuf into `render_frame`. Per-frame
  retokenize is the M2 cost note (incremental retokenize lands at
  M5 perf if a real workload complains).
- `tests/integration_smoke.py` extended with one new check:
  opens `/tmp/cyim-smoke-fixture.cyr`, sends `:q!`, captures PTY
  output, asserts both `ESC[38;5;141m` (keyword fg) and `ESC[0m`
  (reset) appear in the render stream — proving end-to-end that
  syntax highlighting is firing through the live render path.
- `src/cyimrc.cyr` — flat-CYML config parser for palette
  overrides. `cyimrc_load_path(path)` reads the file and applies
  any `palette.<kind> = <code>` lines to a 10-slot table indexed
  by TK_*. `cyimrc_load()` loads `./.cyimrc` (XDG search comes at
  M4 when the config surface widens to keymaps + tab width + line
  numbers). `cyimrc_palette(kind)` returns the override value or
  -1; `theme_token_color` consults it before falling through to
  the bundled palette. Comments (`#`), blank lines, and arbitrary
  whitespace around `=` are tolerated; malformed values silently
  preserve the previous slot value.
- `tests/cyimrc.tcyr` — 22 assertions over 6 groups: missing-file
  is a no-op, basic palette overrides apply, `theme_token_color`
  honors them, comments/blank-lines/whitespace tolerance, malformed
  lines don't poison earlier good values, ident + punctuation
  overrides work too.

### Added (M3)
- `src/buflist.cyr` — buffer registry. `Buffer` record (24 B:
  `buf` / `file_path` / `modified`); editor state grew 64 → 80
  bytes for `buffer_list` (vec) + `active_buf_idx`. `bl_init`
  seeds the registry from the editor's current buf (idempotent;
  safe to call multiple times). `bl_add(buf, path)` appends
  without switching. `bl_set_active(i)` snapshots the editor's
  per-buffer fields into the previous slot, then loads the new
  slot — `editor_buf` / `editor_modified` / `editor_file_path`
  remain the fast-path read mirror so existing code is unaffected.
  `bl_next` / `bl_prev` wrap; no-op on a one-buffer registry.
- `src/command.cyr` — three new commands: `:bn` / `:bp` / `:b N`.
  `:b N` returns ERR_UNKNOWN_CMD on out-of-range or non-numeric
  argument.
- `tests/buflist.tcyr` — 52 assertions over 14 groups: lazy-init
  + idempotence, append-without-switch, snapshot/load round-trip
  preserves modified + file_path per buffer, out-of-range bad
  inputs leave state untouched, no-op switches, wrap-around for
  next/prev, single-buffer next/prev are safe no-ops, full
  end-to-end via `command_execute` for `:bn` / `:bp` / `:b N`,
  and `:ls` formatting (active marker, modified flag from live
  editor state, status cleared by next keystroke).
- `src/mode.cyr` — editor state grew 80 → 88 bytes for
  `status_message` (cstr or 0). `editor_status` /
  `editor_set_status` accessors. `editor_step` clears it at the
  top of every step so commands set it for exactly one render
  frame.
- `src/render.cyr` — `render_status` displays the message in
  place of the mode tag when present (truncated to `cols`).
- `src/command.cyr` — `:ls` writes the buffer registry into a
  static 4 KB scratch (`_cmd_ls_buf`) and pins it as the status
  message: `N[*]: path-or-[scratch] [+]?` per entry, ` | `
  separator, active marked with `*`, modified flag pulled from
  live editor state for the active slot.
- `src/window.cyr` — window tree skeleton. `Window` record
  (72 B): `type` (LEAF / SPLIT_H / SPLIT_V), `buf_idx`,
  `child_a` / `child_b`, `ratio` (out of `WIN_RATIO_FULL` =
  1000), and a four-i64 inline rect populated by `window_layout`.
  `window_new_leaf` / `window_new_split` allocate, accessors
  read each field, `window_layout` recursively assigns rects
  with a 1-cell minimum clamp on degenerate ratios,
  `window_count_leaves` / `window_collect_leaves` traverse
  depth-first, `window_leaf_at(row, col)` does point-in-rect
  lookup.
- `tests/window.tcyr` — 85 assertions over 14 groups: leaf
  construction, single-leaf full rect, h-split divides height,
  v-split divides width, nested splits compose, degenerate
  ratios clamp to 1 cell on both axes, leaf counting,
  depth-first leaf collection order, point-in-rect lookup,
  `window_init` lazy + idempotent, `window_split_active` for
  H and V (with parent links wired and a 3-leaf composite
  rect-fits assertion against an 80×24 frame), and
  `window_replace_child` rewire semantics.
- `src/window.cyr` extended with `parent` ptr (72 → 80 B per
  Window) + `window_replace_child(parent, old, new)` rewire
  helper. New editor-state integration:
  `editor_window_root` / `editor_active_leaf` accessors,
  `window_init(s)` (lazy + idempotent: builds a single LEAF
  root from `bl_active_index`), `window_split_active(s, type)`
  (replaces active leaf with a SPLIT containing two leaves of
  the same buf_idx; focus stays on the original leaf, now
  child_a).
- `src/mode.cyr` — editor state grew 88 → 104 bytes for the
  window-tree pair (`window_root` @ 88, `active_leaf` @ 96).
- `src/command.cyr` — new commands `:sp` and `:vsp` thin
  wrappers around `window_split_active`.
- `src/main.cyr` — `run_editor` now calls `window_init(s)`
  after `bl_init`, so the binary always lands on the
  multi-window render path.
- `src/render.cyr` — `render_build_line_naked` (CRLF-less
  line builder so each leaf places its lines via `tty_move`),
  `_render_leaf` (per-leaf retokenize + write, vim's `~` past
  EOF), `_render_frame_multi` (layout → walk leaves → status
  → cursor in active leaf). `render_frame` dispatches by
  `editor_window_root != 0`; legacy single-buffer path stays
  for the test suite.
- `src/mode.cyr` — multi-byte prefix state (`prefix_pending`
  at offset 104; editor state grew 104 → 112 B). New constants
  `KEY_CTRL_W = 23` and `ACT_WIN_LEFT/DOWN/UP/RIGHT` (400-403).
  `editor_dispatch` consumes Ctrl-w in NORMAL by setting the
  prefix and returning ACT_NONE; the next byte is interpreted
  with the prefix (mapped to ACT_WIN_* on h/j/k/l, otherwise
  swallowed as ACT_NONE).
- `src/window.cyr` — `window_navigate(s, dx, dy)` re-runs
  layout against an 80×23 default frame (cheap, idempotent),
  probes the cell adjacent to the active leaf's edge, and
  switches focus + buffer mirror via `bl_set_active` +
  `editor_set_active_leaf` if a different leaf covers that
  point. `window_apply` routes the four ACT_WIN_* ids;
  non-window actions return 0.
- `src/driver.cyr` — `editor_step` chain extended with
  `window_apply` after `command_apply`.
- `tests/window.tcyr` — 130 assertions total (20 new for
  close-active): last-leaf close sets `editor_quit`,
  split close moves focus to surviving sibling, nested split
  close replaces parent with sibling subtree, `:q` on dirty
  still refused, `:q` on clean leaf in a split closes that
  leaf without exiting, second `:q` exits when only one leaf
  remains.
- `src/window.cyr` — `window_close_active(s)`: collapses the
  active leaf out of its parent split (sibling becomes the
  surviving subtree); when the leaf IS the root,
  `editor_quit` is set so the main loop exits. Buffer
  registry is untouched — closed buffers stay accessible via
  `:ls` / `:b N`.
- `src/command.cyr` — `:q` / `:q!` / `:wq` route through
  `window_close_active` instead of setting `editor_quit`
  directly. Behaviour: `:q` closes the active leaf (dirty
  refusal preserved); `:q!` always closes; `:wq` saves then
  closes. `:e <path>` rewritten as registry-aware: previously
  refused on dirty current buffer; now adds the new file as
  a fresh registry slot, switches active to it, and preserves
  the previous buffer's modified state in its slot.
  `:e <already-open-path>` switches to the existing slot
  without re-reading.
- `src/render.cyr` — per-leaf status row at the bottom of
  every leaf rect (≥2 rows). Format: `[*N: path-or-[scratch] [+]?]`
  padded to rect_w; reverse-video (ESC[7m...ESC[0m) for the
  active leaf so the user can see at a glance which window
  has focus. Cursor positioning updated to clip at the
  content row (one above status), not the leaf's bottom edge.
- `tests/integration_smoke.py` — extended with the M3
  multi-window check: opens file A, vsplits, `:e B`,
  Ctrl-w l, `:sp`, `:e C`, then `:q :q :q :q` to cascade-close
  all four leaves. Asserts every filename appears in the
  rendered PTY stream and that the active-leaf reverse-video
  escape (`ESC[7m`) fires.

### Added (M4)
- `src/mode.cyr` — modes `MODE_SEARCH = 3` and
  `MODE_SEARCH_BACK = 4`. Action ids 25-30:
  `ACT_TO_SEARCH` / `ACT_TO_SEARCH_BACK` (mode-changing
  on `/` / `?`), `ACT_SEARCH_EXECUTE` / `_CANCEL` (Enter /
  Esc inside SEARCH), `ACT_SEARCH_REPEAT` / `_REPEAT_BACK`
  (`n` / `N` in NORMAL). Editor state grew 112 → 128 bytes
  for `search_pattern` (cstr) + `search_direction`
  (0=forward, 1=back) so `n`/`N` survive mode transitions.
  Dispatch reuses cmdbuf for SEARCH-mode pattern entry —
  same APPEND/BACKSPACE actions, just different
  EXECUTE/CANCEL ids that route to search instead of `:`.
- `src/search.cyr` — naive byte-wise substring scan with
  one wrap-around. `search_forward` starts at cursor + 1
  (so a repeat doesn't lock onto the current match);
  `search_backward` starts at cursor - 1 with backward
  scan + end-wrap. `search_apply` snapshots the cmdbuf
  pattern as a heap cstr on EXECUTE, dispatches to the
  right scan, sets `ERR_UNKNOWN_CMD` when no match.
- `src/render.cyr` — status row now prefixes `/` for
  MODE_SEARCH and `?` for MODE_SEARCH_BACK; cursor is
  positioned in the cmdline area for both.
- `src/driver.cyr` — `editor_step` chain extended with
  `search_apply` (after `window_apply`).
- `tests/search.tcyr` — grew to 59 assertions: 37 from the
  initial bite (forward/backward scan + `n`/`N` cycle +
  cancel + cmdbuf edits + no-match + `+1` offset + empty
  pattern), 18 added for `*` (next word under cursor) /
  `#` (previous word) including whitespace + single-
  occurrence + word-extraction edge cases, plus 4 new for
  `:set ic`-driven case-fold scans (alpha FOO ↔ foo).
- `src/search.cyr` — `_search_word_under_cursor(s)` walks
  the cursor's CCLASS_WORD run forward + backward and
  returns a NUL-terminated heap copy. `*` saves it as the
  search pattern, sets direction forward, runs the scan;
  `#` does the same in reverse. Whitespace / EOF cursor
  is a no-op. The scan helpers gained a `fold` parameter
  consulted by `search_forward` / `_backward` from
  `editor_cfg_ignorecase`; `:set ic` flips it.
- `src/undo.cyr` — snapshot-based undo / redo per buffer.
  Snapshot record (24 B): `data` heap copy + `len` +
  `cursor`. `Buffer` record grew 24 → 40 B for `undo_stack`
  and `redo_stack` vec slots. `undo_record_pre_op` is the
  single hook driver fires before any mutating action;
  `undo_pop` snapshots-then-restores via the redo stack;
  redo is symmetric. New edit clears the redo stack. M4's
  cost note: O(buf_len) per edit; M5 perf can compress.
- `tests/undo.tcyr` — 24 assertions: empty undo is no-op,
  `iabc<Esc>u` empties + Ctrl-r restores, multi-step
  unwinds insert sessions one at a time, new edit clears
  redo, `x` records its own snapshot, undo on a
  no-edits-yet buffer is no-op, undo stacks are per-buffer.
- `src/visual.cyr` — VISUAL / VISUAL_LINE selection with
  anchor stamping on entry, `y` (capture to register), `d`
  (capture + delete + mark modified), `p` / `P` paste
  from register. Single-register model (no a-z named
  registers; system clipboard deferred to post-v1.0 per
  roadmap). `_visual_delete` recorded under undo so visual
  delete is rollback-safe. Editor state grew 128 → 152 B
  for `visual_anchor` + `yank_register` + `len`.
- `tests/visual.tcyr` — 36 assertions: v / V enter
  modes + stamp anchor; selection lo / hi computed
  correctly char-wise and line-wise (snap to line); y /
  d capture-only / capture-+-delete; p / P paste at
  before / after cursor; empty register is safe; y → p
  duplicates the selection; d is undo-able; v / V
  toggling and swapping; VISUAL swallows insert/command
  transition keys.
- `src/driver.cyr` — `editor_step` chain extended with
  `visual_apply` (after `undo_apply`) and pre-mutation
  undo snapshot now covers `ACT_VISUAL_DELETE`,
  `ACT_PASTE_AFTER`, `ACT_PASTE_BEFORE`. New
  dot-repeat tracking — `_dot_begin` / `_dot_record_byte`
  / `_dot_replay` — captures byte-by-byte during INSERT
  sessions; `.` (ACT_DOT_REPEAT) snapshot-replays through
  recursive `editor_step` calls.
- `tests/dot.tcyr` — 19 assertions: dot_buf records bytes
  typed in `iabc<Esc>`; `.` replays at current cursor;
  multiple `.` accumulate; `a` (entry_key=97) recorded
  separately from `i`; `.` with no prior edit is a no-op;
  new insert overrides dot_buf; empty session (`i<Esc>`)
  replays nothing; dot state survives buffer switches.
- `src/cyimrc.cyr` — config-key parsing: `ignorecase`,
  `line_numbers`, `tabstop`. Parsed values held in
  module globals (`-1` sentinel = "not set"); `main.cyr`
  applies them to editor state right after `cyimrc_load()`
  unless the file left a sentinel.
- `src/command.cyr` — `:set <option>`: `ic` / `noic` for
  ignorecase, `number` / `nonumber` for line_numbers,
  `tabstop=N` for tab width. Unknown option →
  `ERR_UNKNOWN_CMD`. `tests/command.tcyr` extended with
  12 new assertions covering each toggle plus the
  unknown-option path.
- `src/mode.cyr` — editor state grew 152 → 200 bytes:
  `dot_entry_key` / `dot_buf` / `dot_recording` (M4.5)
  and `cfg_ignorecase` / `cfg_line_numbers` /
  `cfg_tabstop` (M4.6). New action ids: 14-15
  (TO_VISUAL / TO_VISUAL_LINE), 25-32 (search infra),
  210-211 (UNDO / REDO), 220-221 (PASTE_AFTER / BEFORE),
  230-231 (VISUAL_YANK / DELETE), 240 (DOT_REPEAT). Two
  new modes (VISUAL = 5, VISUAL_LINE = 6) with their
  own dispatch arms swallowing insert/command keys so
  the selection isn't lost mid-stream.
- `tests/integration_smoke.py` extended with three M4
  scenarios: `/foo<Enter>iX<Esc>u:wq` proves search +
  undo + save round-trip is identity; `iAB<Esc>$aCD<Esc>0.:wq`
  proves `.` replays the last insert at the new cursor;
  `vlldp:wq` proves visual-delete + paste round-trip.

### Added (M5)
- `docs/guides/usage.md` — getting started for the day-1 vim user.
  Modes table, NORMAL bindings cheat-sheet, INSERT semantics, search
  behaviour, visual + register, multi-file + windows, save/quit,
  differences-from-vim section, troubleshooting.
- `docs/guides/keymap.md` — full keybinding reference. Per-mode
  tables (NORMAL motions, edits, mode transitions, search repeat,
  Ctrl-w window navigation; INSERT; COMMAND; SEARCH; VISUAL).
  Action-id column links every binding to the dispatcher's enum. Also
  documents the action-ID space layout (10s = transitions, 100s =
  motions, 200s = edits, 220s = paste, 230s = visual, 400s = window).
- `docs/guides/cyimrc.md` — config schema. File location, format
  rules, palette overrides table (10 token kinds + bundled defaults),
  editor options table (`ignorecase`, `line_numbers`, `tabstop`),
  boot order, forward-compat policy, and an explicit
  "what's not in the config surface" section for vim users hunting
  for `:nmap` / `:autocmd` / `:!cmd`.
- `docs/audit/2026-04-25-security-audit.md` — initial security audit.
  Internal-only pass against CLAUDE.md's security-hardening checklist;
  external CVE corpus survey deferred to M7. Six findings filed:
  - **F-1 [MEDIUM]** Terminal escape injection — buffer content with
    raw ESC bytes echoes to terminal verbatim. Fix: control-byte
    substitution in render. Tracked for M5 polish or M6.
  - **F-2 [LOW]** Unbounded `:e` file load (DoS).
  - **F-3 [LOW]** Unbounded cmdbuf grow (DoS).
  - **F-4 [LOW]** `_dot_replay` silently fails on > 2048-byte
    insert.
  - **F-5 [LOW]** `:e <path>` accepts arbitrary paths (assumed
    trust model — documenting for future restricted-mode).
  - **F-6 [LOW]** `grammar_load` reads from search path
    (supply-chain shape note for future user-grammar overlays).

  No CRITICAL or HIGH findings — the obvious vim/neovim vuln classes
  are absent by design (no embedded scripting, no `:!cmd`, no
  plugins, no modeline parsing).

- `tests/perf.bcyr` — 8 microbenchmarks driven by `cyrius bench`.
  Gap-buffer fill (1 / 10 / 100 MB), cursor moves on 10 MB, search
  scan (best / worst / case-fold worst), `render_build_line` ×
  1000, `highlight_buf` 1 MB. Surfaces the M2-deferred
  tokenization hot-path: 269 ms / MB → ~3.7 fps for per-frame
  retokenize on a 1 MB file. Flagged for M6 hardening (cache
  tokenbuf keyed by version-counter).
- `BENCHMARKS.md` — top-level perf log. M5 baseline tables
  (gap-buffer, cursor moves, search, render, highlight),
  vim/nvim comparison receipts, test-surface receipts, build
  size by milestone.
- `fuzz/buffer.fcyr` — 10 K random gap-buffer ops with cursor /
  buf_len invariants. Deterministic LCG seed.
- `fuzz/tokenizer.fcyr` — 100 random 1 KB buffers through
  `highlight_buf`; walks every emitted token's kind / start /
  len; asserts spans stay inside `buf_len` and kind is in
  TK_IDENT..TK_ERROR.
- `fuzz/driver.fcyr` — 5 K random keystrokes through
  `editor_step` with a 70/30 printable/control bias; mode +
  cursor + `buf_len` invariants.
- `cyrius.cyml` — `bench` added to stdlib deps for the
  `lib/bench.cyr` framework.

### Added (M6)
- `src/buffer.cyr` — gap-buffer header grew 32 → 64 B for the
  tokenbuf cache: `version` (bumped on every content mutation),
  `cached_tb`, `cached_version`, `cached_lang`. Accessors:
  `buf_version` / `buf_bump_version` / `buf_cached_*` /
  `buf_set_cache`. Mutation helpers (`buf_insert_byte`,
  `buf_delete_left`, `buf_delete_right`, `buf_clear`) now bump
  the version. Cursor moves don't.
- `src/highlight.cyr` — `highlight_buf` consults the per-buffer
  cache: hits when (cached_tb != 0, cached_version == version,
  cached_lang ptr == lang). Pointer-equality is robust because
  `lang_name(i)` returns stable string literals. Closes the
  M5-flagged 3.7 MB/s tokenize hot path — read-only render
  frames now hit a 17 ns pointer compare.
- `src/render.cyr` — `render_ctrl_substitute(c)` returns the
  `^X`-encoded second byte for control bytes (< 0x20 except Tab,
  plus 0x7F DEL). Tab is preserved (indent display); LF never
  reaches the path (line iterator stops at line_end). Both
  `render_build_line_naked` and `render_build_line` now substitute
  control bytes before emitting them — closes M5 audit F-1
  (terminal escape injection). Substituted bytes count as 2 visible
  columns.
- `src/command.cyr` — `command_append` caps cmdbuf at
  `COMMAND_MAX_LEN = 4096`; overflow drops the byte and surfaces
  a status message. Closes audit F-3.
- `src/driver.cyr` — `_dot_replay` snapshot cap raised 2048 →
  16384; overflow surfaces a status message instead of silent
  no-op. Closes audit F-4.
- `tests/perf.bcyr` — new bench `highlight_buf_cache_hit_x1000`
  measures the cache-hit path. M6 result: 17 μs total / 1000 calls
  = ~17 ns per call. ~15.5 million× faster than the cold-tokenize
  baseline (265 ms).
- `tests/render.tcyr` — 23 new assertions covering F-1: ESC /
  BEL / DEL all substituted as `^X`; Tab preserved verbatim; the
  `render_ctrl_substitute` unit table.
- `tests/command.tcyr` — 3 new assertions covering F-3: cmdbuf
  caps at `COMMAND_MAX_LEN`, byte past cap dropped, overflow
  status message set.
- `BENCHMARKS.md` — M6 perf delta table at the top: cache-hit
  ~15.5M× win on the read-only render path; +27% raw-fill cost
  from the per-byte version bump (acceptable trade-off given
  the editing workflow has more renders than mutations).
- `src/mode.cyr` — refactor: the byte-identical SEARCH and
  SEARCH_BACK dispatch arms collapsed into one `||`-guarded
  block (zero behavior change).
- `src/render.cyr` — refactor: the three nearly-identical
  cmdline-prefix render arms (COMMAND / SEARCH / SEARCH_BACK)
  collapsed via a new `_render_cmdline(s, prefix_byte, cols)`
  helper; the three cursor-positioning arms in
  `_render_frame_multi` collapsed into a single `||` branch.
  Net: ~50 lines of duplication removed, zero behavior change.
- `cyrius/docs/development/proposals/relax-uninitialized-var-or-improve-error.md`
  — proposal filed upstream against cc5 5.7.x: relax the
  parse-time rejection of `var X;` (uninitialized) or improve the
  diagnostic to point at the missing initializer rather than the
  `;`. Discovered while writing `fuzz/driver.fcyr` — the misleading
  error message cost ~10 minutes of debugging time across two
  hits in M5.

### Added (M7)
- `docs/security/2026-04-25-0day-corpus.md` — external CVE
  corpus survey, organized into 13 attack classes (modeline RCE,
  regex backtracking, terminal escape injection, integer
  overflow, scripting sandbox escapes, plugin supply chain,
  large-input DoS, TOCTOU, format strings, paste-as-command,
  path traversal, memory corruption, Unicode parsing). Each
  class maps to cyim's posture — *refused-by-design*, *closed*,
  *open*, or *documented*. Includes a top-of-doc note: specific
  CVE references are pending external verification (M7.5
  WebFetch pass against NVD / MITRE / vim CHANGELOG); class
  taxonomy and cyim-posture mapping are independent and stand
  on their own.
- `docs/audit/2026-04-25-m7-audit.md` — second-pass audit re-walks
  CLAUDE.md's security-hardening checklist with the corpus's 13
  classes in hand. Triages M5 carryover findings and files five
  new findings (M7-1 through M7-5). All M5 audit findings now
  closed or documented; **0 CRITICAL / 0 HIGH / 0 MEDIUM**
  remaining.
- `docs/adr/0001-trust-model.md` — Architecture Decision Record
  documenting cyim's threat model: interactive editor for a
  single local user; not a privilege boundary. Fixes the
  long-running ambiguity around F-5 / M7-3 / M7-4. Future
  setuid mode, restricted mode, or daimon-driven sandbox would
  need follow-up ADRs to widen / narrow the trust model.
- `src/mode.cyr` — editor state grew 200 → 208 bytes for
  `cfg_max_filesize` (default 100 MB). New error
  `ERR_FILE_TOO_LARGE` (6) for `:e` size-cap rejections.
- `src/command.cyr` — `_cmd_file_size(path)` opens-lseeks-closes
  to get a file's byte size before allocating any buffer.
  `_cmd_e` now pre-checks against `editor_cfg_max_filesize(s)`
  and refuses with `ERR_FILE_TOO_LARGE` if the file exceeds the
  cap. Closes M5 audit F-2 (corpus Class 7).
- `src/command.cyr` — `:set maxfilesize=N` runtime toggle. The
  `_cmd_match_kv(cb, start, len, prefix)` helper consolidates
  the prefix-match logic for both `:set tabstop=N` and
  `:set maxfilesize=N` (refactor: ~20 lines of nested-if
  duplication removed).
- `tests/command.tcyr` — 9 new assertions covering F-2: `:e`
  refuses files larger than the cap with `ERR_FILE_TOO_LARGE`,
  raising the cap allows the same file, `:set maxfilesize=N`
  updates the cap at runtime.
- `docs/guides/usage.md` — troubleshooting note added for the
  M7-5 byte-vs-glyph column-counting distinction (cursor
  positions are byte offsets, not glyph offsets — matches vim's
  `:set encoding=latin1`).

### Status (M7)
- All 4 M7 bites landed (corpus survey, checklist re-walk,
  remaining-findings closure, closeout) plus M7.5 (WebFetch CVE
  verification) queued as a follow-up.
- 847 .tcyr assertions across 18 suites + 14 PTY end-to-end
  checks + 3 fuzz harnesses + 9 perf benches; all green.
- DCE binary: 274,656 B (M6 was 273,912 B; +744 B for F-2 fix).
- **Security audit triage at end of M7:**
  - **0 CRITICAL / 0 HIGH / 0 MEDIUM** findings.
  - 8 LOW findings, all triaged: F-2 fixed in M7; F-3 / F-4 /
    M5 F-1 closed in M6; F-5 / M7-3 / M7-4 documented per ADR
    0001 (interactive-local-user trust model); M7-1 deferred
    (tabstop overflow surfaces only when the consumer exists);
    M7-2 deferred (user-grammar overlay supply chain — feature
    not yet shipped); M7-5 documented in usage.md (byte-vs-glyph
    column counting).
- **v1.0 gate clear:** CLAUDE.md's "CRITICAL/HIGH must close
  before v1.0" rule satisfied.
- M7.5 — CVE verification pass (WebSearch + WebFetch against
  NIST NVD, MITRE, vim/neovim GitHub Security Advisories,
  Red Hat / Ubuntu / SUSE bulletins). The corpus survey now
  carries verified CVE citations with primary-source links per
  class: CVE-2019-12735 / CVE-2016-1248 / CVE-2002-1377
  (modeline RCE), CVE-2017-17087 / CVE-2017-1000382
  (swap files), CVE-2008-2712 (Vimscript injection),
  CVE-2023-4738 (heap overflow in vim_regsub_both),
  CVE-2022-0413 / CVE-2022-0351 / CVE-2021-3778 / CVE-2025-22134
  (memory corruption family), GHSA-q22m-h7m2-9mgm /
  GHSA-6g74-hr6q-pr8g / GHSA-f2m2-v387-gv87 (vim integer
  overflow advisories), GHSA-2gmj-rpqf-pxvh / CVE-2026-34714
  (tabpanel %{expr} format-string-class), CVE-2017-8386 (less
  paste-as-command bypass via git-shell), CVE-2013-1862
  (Apache mod_rewrite — exemplary terminal-escape-injection),
  GHSA-6f9m-hj8h-xjgj (neovim treesitter path traversal). The
  corpus's "verification pending" warning was removed; the
  audit-doc cross-reference updated to match.

### Status (M6)
- All 6 M6 bites landed: tokenbuf cache, F-1 escape-injection
  fix, F-3/F-4 caps, cleanliness gate, refactor pass, closeout.
- 838 .tcyr assertions across 18 suites + 14 PTY end-to-end
  checks + 3 fuzz harnesses + 9 perf benches; all green.
- DCE binary: 273,912 B (M5 was 262,504 B; +11 KB for the
  cache slots + control-byte substitution + cap-and-message
  handling).
- M5 audit findings closed: F-1 fixed (control-byte
  substitution); F-3 fixed (cmdbuf cap + status); F-4 fixed
  (replay cap raised + status). F-2 (file-load DoS) and F-5/F-6
  (path traversal / supply-chain notes) remain documented for
  M7 / post-v1.0 work.
- M6 perf wins: tokenbuf cache → 15.5M× on read-only render
  path. Trade-off: +27% raw-fill cost from version bump.
- `cyrius lint`: 0 correctness warnings; ~30 advisory line-length
  warnings (style only).
- `cyrius fmt --check`: clean across all `src/*.cyr`.

### Status (M5)
- All 4 M5 bites landed: docs pass (usage / keymap / cyimrc /
  initial security audit), perf benchmarks (1/10/100 MB
  fixtures), fuzz harnesses, receipts.
- 812 .tcyr assertions across 18 suites + 14 PTY end-to-end
  checks + 3 fuzz harnesses + 8 performance benchmarks; all
  green.
- DCE binary: 262,504 B (M4 was 256,344 B; +6 KB for `:set`
  cfg fields + `lib/bench.cyr` dep).
- M5 baseline benches recorded in `BENCHMARKS.md`. Hot path
  identified: vyakarana tokenization at ~3.7 MB/s. Flagged for
  M6 hardening with proposed fix (tokenbuf cache by version).
- Initial security audit (`docs/audit/2026-04-25-security-audit.md`)
  filed with 0 CRITICAL / 0 HIGH / 1 MEDIUM (F-1: terminal
  escape injection from buffer content) / 5 LOW. Full M7 audit
  will pair with external CVE corpus survey.

### Status (M4)
- All 6 M4 bites landed: `/?nN` search + n/N repeat,
  `*`/`#` word search, undo/redo, visual + yank/paste,
  `.` dot-repeat, `:set` + `.cyimrc` config.
- 812 .tcyr assertions across 18 suites + 14 PTY
  end-to-end checks (5 M1 + 2 M2 + 4 M3 + 3 M4).
- DCE binary: 256,344 B (M3 was 226,064 B; +30,280 B for
  search + undo stacks + visual + dot recording + config).
- M4 success criterion verified: vim muscle memory survives
  a full editing session — `/`, `?`, `n`, `N`, `*`, `#`,
  `u`, Ctrl-r, `v`, `V`, `y`, `d`, `p`, `P`, `.`, `:set`
  all behave as expected; integration smoke proves
  search + undo + dot + visual all work end-to-end through
  the live PTY.

### Status (M3)

### Status (M3)
- All 6 M3 bites landed: buffer registry + `:bn/:bp/:b N`,
  `:ls` + status channel, window-tree skeleton, `:sp/:vsp`
  splits, Ctrl-w h/j/k/l navigation, `:q` cascade + per-window
  status + integration smoke.
- 659 .tcyr assertions across 14 suites + 11 PTY-driven
  end-to-end checks (5 from M1, 2 from M2, 4 from M3); all green.
- DCE binary: 226,064 B (M2 was 162,184 B; +63,880 B for
  registry, window tree, multi-window render, per-leaf status).
- M3 success criterion verified: three files open in two splits,
  navigate without losing state, `:q` cascades cleanly to exit.

### Status (M2)
- All 6 M2 bites landed: vyakarana dep + grammars, highlight
  module, lang detection, palette + ANSI render, main.cyr wiring
  + integration smoke, `.cyimrc` palette overrides.
- 467 .tcyr assertions across 12 suites + 7 PTY-driven end-to-end
  checks; all green.
- DCE binary: 162,184 B (M1 baseline 101,560 B; +60,624 B for
  vyakarana + 11 grammars + render highlighting + cyimrc).
- M2 success criterion: `cyim src/buffer.cyr` shows Cyrius
  highlighting matching vyakarana's reference output. Verified
  via the integration smoke's `ESC[38;5;141m` keyword-fg check.

### Added
- `src/buffer.cyr` — gap-buffer primitive: `buf_new`, `buf_len`, `buf_cap`,
  `buf_gap`, `buf_cursor`, `buf_get`, `buf_move`, `buf_grow`,
  `buf_insert_byte`, `buf_insert`, `buf_delete_left`, `buf_delete_right`.
  32-byte heap header `{data, gap_start, gap_end, cap}`; doubles on growth;
  preserves cursor and content across realloc.
- `src/buffer.cyr` file I/O: `buf_load_file` (chunked read, auto-grows),
  `buf_save_file` (two-segment write — pre-gap + post-gap — so save does not
  mutate the cursor).
- `tests/buffer.tcyr` — 47 assertions covering empty-state, end/middle inserts,
  backspace + `x`, no-op edge cases at start/end, growth past initial capacity,
  and growth-with-cursor-mid-buffer.
- `tests/roundtrip.tcyr` — 23 assertions: end-cursor round-trip is
  byte-identical, mid-cursor round-trip exercises the two-segment write,
  missing-file returns -1 without touching the buffer, save-then-load
  preserves a 300-byte payload past initial capacity.
- `src/tty.cyr` — raw-mode TTY: `tty_apply_raw_flags` (pure flag-mask
  function on a 60-byte termios buffer), `tty_raw` / `tty_cooked` (TCGETS
  / TCSETS via ioctl, gated to `CYRIUS_TARGET_LINUX`, captures cooked
  state so any exit path can restore), `tty_probe` (live diagnostic),
  ANSI helpers (`tty_alt_enter` / `_leave`, `tty_clear`,
  `tty_cursor_hide` / `_show` / `_home`, `tty_move(row, col)`,
  `tty_itoa`).
- `tests/tty.tcyr` — 37 assertions: 32-bit field load/store little-endian
  round-trip, raw-flag mask clears all five iflag bits + OPOST + ECHO /
  ICANON / IEXTEN / ISIG and forces CS8 while preserving bystander bits,
  VMIN=1 / VTIME=0 are forced, the mask is idempotent (fixed point), and
  `tty_itoa` formats 0 / 7 / 42 / 1024 correctly.
- `src/mode.cyr` — modal dispatch state machine: `editor_new(buf)`,
  `editor_dispatch(s, key)`, `editor_drive(s, keys, n, out_actions)`
  (headless agent-drive entry point). Three modes (NORMAL / INSERT /
  COMMAND); single-byte NORMAL keymap (`h j k l 0 $ w b G x i a A :`)
  via `map_u64`; INSERT and COMMAND fall through to literal-insert /
  cmdline-append by default with hard-coded specials for Esc / Enter /
  Backspace / DEL. Stable action-id enum with numbered groups so future
  actions land without renumbering. Multi-byte sequences (gg, dd, arrow
  escapes) deferred.
- `tests/dispatch.tcyr` — 57 assertions over 16 groups covering each
  motion, mode-default, every transition path, Backspace/DEL/Enter/LF
  equivalences, and an 8-key headless drive (`i H i Esc l : q Enter`)
  that asserts the full action sequence and final mode.
- `src/buffer.cyr` line/column queries: `buf_line_start`, `buf_line_end`,
  `buf_line_of`, `buf_line_count`, `buf_pos_of_line` (clamps past-end
  to last actual line in a single forward pass), `buf_col_of`. Vim
  convention: trailing `\n` is a line terminator, not a new empty line.
- `src/motion.cyr` — vi motions over the gap-buffer: `motion_left`,
  `_right`, `_up`, `_down`, `_line_start`, `_line_end`, `_word_fwd`,
  `_word_back`, `_file_end`, `_file_start`, plus `motion_cclass`
  (whitespace / word / punctuation classifier — vim-style
  iskeyword) and `motion_apply` which dispatches `ACT_MOVE_*` to the
  right handler and updates `buf_move`. j/k preserve column with
  clamp to target-line end. l/h respect line boundaries. w/b honor
  class transitions and skip whitespace runs. G lands on column 0
  of the last line (first-non-blank refinement deferred).
- `tests/motion.tcyr` — 87 assertions over 11 groups: line-count
  edge cases (empty / lone-`\n` / trailing-`\n`), line/col helpers
  on a 26-byte 3-line fixture, h/l line-boundary clamps, 0/$,
  j/k column-preservation with clamp on shorter lines, w across
  newlines, b across whitespace, G/gg, `motion_apply` end-to-end
  via the editor state, and "all motions on an empty buffer are
  safe no-ops".
- `src/insert.cyr` — INSERT-mode handlers: `insert_literal`,
  `insert_delete_left`, `insert_to_after` (vim `a`: cursor +1
  clamped to buf_len), `insert_to_line_end` (vim `A`: cursor →
  line's `\n` or buf_len; empty lines stay put),
  `insert_to_normal` (vim Esc: cursor steps back one within line
  bounds), and `insert_apply(s, action, key)` which silently
  no-ops on non-INSERT actions.
- `src/driver.cyr` — `editor_step(s, key)` (the canonical
  consume-one-byte function: dispatch + insert_apply +
  motion_apply) and `editor_run(s, keys, n)` (the headless
  agent-drive entry point — same code path the TTY consumer
  takes).
- `tests/insert.tcyr` — 39 assertions over 10 groups including
  unit-level handler invariants, `insert_apply` routing, and four
  end-to-end `editor_run` drives covering `iHello<Esc>` (Esc
  step-back lands cursor on 'o'), `iHello<Esc>$a World<Esc>` to
  build "Hello Wor" via mode round-trip, backspace inside INSERT
  (DEL and ^H both work), and motion+insert mix that prepends
  "hello " before "world".
- `src/buffer.cyr` — `buf_clear` (drop logical content; capacity
  preserved).
- `src/mode.cyr` — `EditorState` grew from 24 → 64 bytes:
  `cmdbuf` (gap-buffer for the `:cmd` line, allocated in
  `editor_new`), `modified`, `quit`, `last_error`, `file_path`.
  Accessors `editor_cmdbuf`, `editor_modified`, `editor_quit`,
  `editor_last_error`, `editor_file_path`, plus paired
  `editor_set_*`. Error-code constants `ERR_NONE`, `ERR_DIRTY`,
  `ERR_NO_FILE_NAME`, `ERR_FILE_NOT_FOUND`, `ERR_SAVE_FAILED`,
  `ERR_UNKNOWN_CMD`.
- `src/insert.cyr` — `insert_literal` and `insert_delete_left`
  now mark the buffer modified (delete only marks if a byte was
  actually removed, so a no-op at line 0 col 0 stays clean).
- `src/edit.cyr` — NORMAL-mode mutations: `edit_delete_right`
  (vim `x`) and `edit_apply` dispatch. New file isolates
  NORMAL-mode edits from INSERT-mode handlers; future `dd`,
  `yy`, change-operators land here.
- `src/command.cyr` — full COMMAND-mode surface: cmdbuf
  lifecycle (`command_reset`, `_append`, `_backspace`),
  parser (`command_execute` splits on first space; matches
  `q` / `q!` / `w` / `wq` / `e`), and per-command implementations
  with modified-flag tracking. `:q` refuses dirty (sets
  `ERR_DIRTY`); `:q!` always quits; `:w` saves and clears
  modified; `:w <path>` updates `file_path`; `:wq` chains; `:e`
  refuses dirty and `ERR_FILE_NOT_FOUND` on missing path.
- `src/driver.cyr` — `editor_step` chain extended to call
  `edit_apply` and `command_apply`; handlers remain mutually
  exclusive on action ids, so the chain stays trivial.
- `tests/command.tcyr` — 58 assertions over 16 groups: cmdbuf
  lifecycle, modified-flag invariants, every command's success
  + failure path (dirty, missing path, missing file, unknown),
  and four end-to-end `editor_run` drives including `:q!` from
  INSERT, `:w <path>` byte-checking the on-disk file, mid-cmdline
  backspace, and Esc-cancels-cmdline.
- `tests/dispatch.tcyr` updated to include `src/buffer.cyr`
  (the new `editor_new` allocates a cmdbuf via `buf_new`).
- `src/render.cyr` — TTY rendering: `render_line` (per-line
  scratch-buffered write with CRLF for raw-mode terminals;
  truncates at `cols`), `render_status` (mode tag + filename +
  modified flag, or `:cmdbuf` in COMMAND mode), `render_frame`
  (clear, walk lines, vim-style `~` for past-EOF rows, position
  cursor on bottom row in COMMAND mode and at line/col
  otherwise).
- `src/main.cyr` — full editor entry point. CLI shapes:
  `cyim [<file>]`, `cyim --version`, `cyim --help`,
  `cyim --probe`. Main loop reads one byte at a time, calls
  `editor_step`, exits when `editor_quit() == 1` or stdin EOF.
  Wraps the loop with `tty_alt_enter` / `tty_raw` on the way in
  and `tty_alt_leave` / `tty_cooked` on the way out.
- `tests/integration_smoke.py` — Python PTY harness that spawns
  cyim against a fixture file, drives recorded keystrokes through
  a real pseudo-terminal, and asserts on-disk file content. Five
  end-to-end checks: `:q` clean exit doesn't modify, `iEDIT<Esc>:wq`
  prepends "EDIT", `A!!<Esc>:wq` appends "!!" before `\n`, `xx:wq`
  deletes first two chars, dirty `:q` refused + `:q!` discards.

### Status
- M1 (gap-buffer + raw-mode TTY + modal dispatch) is complete.
  All 8 bites landed.
- 350 .tcyr assertions across 8 suites + 5 PTY-driven end-to-end
  checks; all green.
- DCE binary: 101,560 B (M0 was 57,728 B; +43,832 B for the
  full editor).

## [0.1.0] — 2026-04-25

### Added
- Initial project scaffold via `cyrius init` (Cyrius 5.7.1)
- Identity locked: sovereign VIM-inspired text editor, Cyrius-native, zero attack surface
- M0–M4 roadmap drafted (gap-buffer → vyakarana highlighting → multi-buffer → search/undo/config)
- Stdlib footprint chosen for modal-editor baseline (fs, hashmap, args, vec, string)
