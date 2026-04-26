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

## [0.1.0] — 2026-04-25

### Added
- Initial project scaffold via `cyrius init` (Cyrius 5.7.1)
- Identity locked: sovereign VIM-inspired text editor, Cyrius-native, zero attack surface
- M0–M4 roadmap drafted (gap-buffer → vyakarana highlighting → multi-buffer → search/undo/config)
- Stdlib footprint chosen for modal-editor baseline (fs, hashmap, args, vec, string)
