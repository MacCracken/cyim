# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
