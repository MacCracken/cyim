# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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

## [0.1.0] — 2026-04-25

### Added
- Initial project scaffold via `cyrius init` (Cyrius 5.7.1)
- Identity locked: sovereign VIM-inspired text editor, Cyrius-native, zero attack surface
- M0–M4 roadmap drafted (gap-buffer → vyakarana highlighting → multi-buffer → search/undo/config)
- Stdlib footprint chosen for modal-editor baseline (fs, hashmap, args, vec, string)
