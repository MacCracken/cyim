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
