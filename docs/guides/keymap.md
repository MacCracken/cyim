# cyim keymap reference

Every binding cyim ships, by mode. Action-id column links the binding
to the dispatcher's enum (see [`src/mode.cyr`](../../src/mode.cyr)).
Vim-equivalent column flags any binding whose semantics differ from
vim — the rest match.

---

## NORMAL

### Motions

| Key | Byte | Action            | Action ID            | Vim |
|-----|------|-------------------|----------------------|-----|
| `h` | 104  | Left              | `ACT_MOVE_LEFT`      | =   |
| `j` | 106  | Down              | `ACT_MOVE_DOWN`      | =   |
| `k` | 107  | Up                | `ACT_MOVE_UP`        | =   |
| `l` | 108  | Right             | `ACT_MOVE_RIGHT`     | =   |
| `0` | 48   | Line start        | `ACT_MOVE_LINE_START`| =   |
| `$` | 36   | Line end          | `ACT_MOVE_LINE_END`  | =   |
| `w` | 119  | Next word         | `ACT_MOVE_WORD_FWD`  | =   |
| `b` | 98   | Previous word     | `ACT_MOVE_WORD_BACK` | =   |
| `G` | 71   | Last line, col 0  | `ACT_MOVE_FILE_END`  | ≠ vim's "first non-blank" — cyim lands on col 0 |
| `gg` | 103, 103 | First line, col 0 | `ACT_MOVE_FILE_START` (109) | = |

Motions never cross newlines (`l` at end-of-line is a no-op; `h` at
column 0 stays put). j/k preserve column, clamping to target-line end.

`gg` is a two-byte sequence — the first `g` latches the prefix
(`KEY_G` = 103), the next `g` resolves to `ACT_MOVE_FILE_START`. Any
other follow-up byte falls through to the plugin prefix-key lookup
(see "Plugin prefix-keys" below) — built-ins win on conflict per
[ADR 0003 §3](../adr/0003-cyrius-plugin-system.md).

**Arrow keys** also route to the motion actions: terminals send
`ESC [ A/B/C/D` for up/down/right/left; cyim's driver-side
`editor_feed` parses the 3-byte CSI sequence and dispatches the
matching `ACT_MOVE_*` directly. Available in NORMAL, INSERT, and
VISUAL.

### Edits

| Key      | Byte | Action                | Action ID              | Vim |
|----------|------|-----------------------|------------------------|-----|
| `x`      | 120  | Delete byte           | `ACT_DELETE_RIGHT`     | =   |
| `i`      | 105  | INSERT at cursor      | `ACT_TO_INSERT`        | =   |
| `a`      | 97   | INSERT after cursor   | `ACT_TO_INSERT_AFTER`  | =   |
| `A`      | 65   | INSERT at line end    | `ACT_TO_INSERT_LINE_END`| =  |
| `o`      | 111  | Open line below, INSERT | `ACT_OPEN_BELOW`     | =   |
| `O`      | 79   | Open line above, INSERT | `ACT_OPEN_ABOVE`     | =   |
| `u`      | 117  | Undo                  | `ACT_UNDO`             | =   |
| `Ctrl-r` | 18   | Redo                  | `ACT_REDO`             | =   |
| `p`      | 112  | Paste after cursor    | `ACT_PASTE_AFTER`      | =   |
| `P`      | 80   | Paste before cursor   | `ACT_PASTE_BEFORE`     | =   |
| `.`      | 46   | Repeat last edit      | `ACT_DOT_REPEAT`       | = (insert sessions only; x/paste/visual deferred) |

### Mode transitions

| Key | Byte | Action               | Action ID              |
|-----|------|----------------------|------------------------|
| `:` | 58   | Enter COMMAND        | `ACT_TO_COMMAND`       |
| `/` | 47   | Enter SEARCH         | `ACT_TO_SEARCH`        |
| `?` | 63   | Enter SEARCH (back)  | `ACT_TO_SEARCH_BACK`   |
| `v` | 118  | Enter VISUAL         | `ACT_TO_VISUAL`        |
| `V` | 86   | Enter VISUAL_LINE    | `ACT_TO_VISUAL_LINE`   |

### Search repeat

| Key | Byte | Action                            | Action ID                  |
|-----|------|-----------------------------------|----------------------------|
| `n` | 110  | Repeat last search                | `ACT_SEARCH_REPEAT`        |
| `N` | 78   | Repeat last search (opposite dir) | `ACT_SEARCH_REPEAT_BACK`   |
| `*` | 42   | Search forward for word @ cursor  | `ACT_SEARCH_WORD_FWD`      |
| `#` | 35   | Search backward for word @ cursor | `ACT_SEARCH_WORD_BACK`     |

### Window navigation (Ctrl-w prefix)

`Ctrl-w` (byte 23 / 0x17) starts a two-byte sequence. The next byte
selects the navigation direction:

| Sequence | Bytes  | Action               | Action ID         |
|----------|--------|----------------------|-------------------|
| `Ctrl-w h` | 23 104 | Move to left window | `ACT_WIN_LEFT`    |
| `Ctrl-w j` | 23 106 | Move to lower window| `ACT_WIN_DOWN`    |
| `Ctrl-w k` | 23 107 | Move to upper window| `ACT_WIN_UP`      |
| `Ctrl-w l` | 23 108 | Move to right window| `ACT_WIN_RIGHT`   |

`Ctrl-w` followed by anything else clears the prefix and produces no
action.

### Plugin prefix-keys

cyim's NORMAL-mode dispatch generalizes the prefix mechanism (Ctrl-W
above, KEY_G for `gg`) to plugins via
[`plugin_register_normal_prefix_key(prefix, key, fp)`](../adr/0004-plugin-abi-freeze.md#v142-additive-extensions-2026-05-07)
— the additive ABI extension landed at cyim 1.4.2. Plugins register
their two-byte sequences; built-ins (Ctrl-W navigation, `gg`) win
on conflict.

When [cyim-lsp](https://github.com/MacCracken/cyim-lsp) is folded
in (cyim 1.4.0+, default with the `[deps.cyim-lsp]` block in
`cyrius.cyml`), the LSP plugin's `cyim_lsp_init()` registers:

| Sequence | Bytes  | Action |
|----------|--------|--------|
| `gd`     | 103 100 | Go to definition (same-file: cursor moves; cross-file: file loads + cursor jumps) |
| `gr`     | 103 114 | Find references (pops a quickfix picker — see "List mode" below) |

`gd` / `gr` delegate to `:lsp-goto-def` / `:lsp-find-refs`
respectively; the prefix-keymap is the muscle-memory surface, the
ex-commands are the typed-out form.

### Marks (v1.6.0)

Two new prefixes join the family at v1.6.0: `m` (set mark) and
`'` (jump to mark). VIM's mark grammar with one simplification —
cyim's `'<letter>` lands at the exact recorded byte offset
(cyim is byte-oriented; vim's `'<letter>` line vs. `` `<letter> ``
column distinction collapses).

| Sequence | Bytes | Action |
|----------|-------|--------|
| `m<a-z>` | 109, 97-122 | Set per-buffer mark `<a-z>` at cursor |
| `m<A-Z>` | 109, 65-90  | Set global mark `<A-Z>` at cursor (cross-buffer) |
| `'<a-z>` | 39, 97-122  | Jump cursor to per-buffer mark `<a-z>` |
| `'<A-Z>` | 39, 65-90   | Jump to global mark — switches buffer if needed |

`m`/`'` followed by anything else (digits, punctuation, etc.)
is silently swallowed and the prefix clears. Marks not yet set
are no-ops on jump.

**Per-buffer marks** are isolated per buffer — setting `ma` in
buffer A doesn't affect buffer B. Up to 26 per-buffer marks per
buffer.

**Global marks** record both the buffer identity and offset.
Jumping to a global mark switches the active buffer (via
`bl_set_active`) before moving the cursor. Up to 26 global
marks shared across all buffers.

Mark offsets are clamped to `buf_len(b)` on jump — defensive
against post-delete drift (cyim 1.6.0 doesn't yet adjust marks
across edits; if you set a mark at offset 100 and then delete
50 bytes earlier in the buffer, the mark still points at 100,
which now corresponds to a different position. Edit-tracking is
queued for a future 1.6.x patch).

No persistence (vim's `viminfo`) — marks live for the cyim
session.

### LSP ex-commands

Registered by [cyim-lsp](https://github.com/MacCracken/cyim-lsp)'s
consumer-side glue (`src/plugins/lsp_glue.cyr`). Available when
the plugin is folded in.

| Command | Effect | Notes |
|---|---|---|
| `:lsp-restart` | Kill + respawn `cyrius-lsp` subprocess | Useful after upgrading the toolchain or recovering from a server crash |
| `:lsp-status` | Print server pid + describe state | Result lands in the status row |
| `:lsp-goto-def` | textDocument/definition request → jump to result | Same-file or cross-file (1.4.3+) |
| `:lsp-find-refs` | textDocument/references request → pop quickfix picker | List mode opens (1.5.1+) |

---

## INSERT

| Key             | Bytes | Action                   |
|-----------------|-------|--------------------------|
| any printable   | 32–126 | Insert byte at cursor   |
| `Esc`           | 27    | Back to NORMAL (cursor steps back one within line) |
| `Backspace`     | 8     | Delete byte left of cursor |
| `DEL`           | 127   | Same as Backspace          |

cyim's INSERT mode is intentionally narrow — most terminals send
multi-byte escape sequences for arrow keys etc., and the leading `\x1b`
will look like Esc. Use `Esc h j k l` to navigate; faster than the
arrows anyway.

---

## COMMAND

`:` enters COMMAND. Type your command, press `Enter` to execute.

| Key             | Bytes  | Action                      |
|-----------------|--------|-----------------------------|
| any printable   | 32–126 | Append to cmdbuf            |
| `Backspace` / `DEL` | 8 / 127 | Delete byte from cmdbuf |
| `Enter` / `LF`  | 13 / 10 | Execute, return to NORMAL |
| `Esc`           | 27     | Cancel, return to NORMAL  |

### Ex commands

| Command       | Effect | Failure |
|---------------|--------|---------|
| `:q`          | Close active window. Last window → exit. | `ERR_DIRTY` if active buffer modified |
| `:q!`         | Force close (no dirty check)             | — |
| `:w`          | Save active buffer to current file_path  | `ERR_NO_FILE_NAME` if unnamed |
| `:w <path>`   | Save to `<path>`; sets file_path         | `ERR_SAVE_FAILED` on write error |
| `:wq`         | `:w` then `:q`                           | propagates either's failure |
| `:e <path>`   | Open `<path>` as a new buffer in current window; preserves prior buffer in registry | `ERR_FILE_NOT_FOUND` if missing; `ERR_NO_FILE_NAME` if no path; switches to existing slot if `<path>` is already open |
| `:ls`         | Show buffer list in status row           | — |
| `:bn`         | Switch active buffer to next             | no-op if 1 buffer |
| `:bp`         | Switch active buffer to previous         | no-op if 1 buffer |
| `:b N`        | Switch active buffer to slot N           | `ERR_UNKNOWN_CMD` on bad index |
| `:sp`         | Horizontal split                         | — |
| `:vsp`        | Vertical split                           | — |
| `:set <opt>`  | Runtime config toggle (see `cyimrc.md`)  | `ERR_UNKNOWN_CMD` if unknown |

Plugin-registered ex-commands extend this table. Built-ins win on
conflict per [ADR 0003 §3](../adr/0003-cyrius-plugin-system.md);
plugin lookup is reached only after every built-in misses. With
[cyim-lsp](https://github.com/MacCracken/cyim-lsp) folded in,
`:lsp-restart`, `:lsp-status`, `:lsp-goto-def`, `:lsp-find-refs`
are all registered (see "LSP ex-commands" above).

Unknown commands (built-in **and** plugin miss) → `ERR_UNKNOWN_CMD`.

---

## SEARCH / SEARCH_BACK

`/` and `?` enter SEARCH and SEARCH_BACK respectively. Both reuse the
cmdbuf and behave like COMMAND mode for byte entry. On `Enter`, the
pattern is saved and a forward / backward scan runs from the cursor.

| Key             | Bytes  | Action                      |
|-----------------|--------|-----------------------------|
| any printable   | 32–126 | Append to cmdbuf            |
| `Backspace` / `DEL` | 8 / 127 | Delete byte from cmdbuf |
| `Enter` / `LF`  | 13 / 10 | Execute search; return to NORMAL |
| `Esc`           | 27     | Cancel; return to NORMAL  |

### Search behavior

- Forward (`/`): scans from `cursor + 1`; wraps to start of buffer if
  no match in the tail.
- Backward (`?`): scans from `cursor - 1`; wraps to end if no match in
  the head.
- The `+1` / `-1` start offset prevents `n` from locking onto the
  current match.
- No match → cursor unchanged + `ERR_UNKNOWN_CMD` set.
- Pattern is saved per-editor; `n` / `N` repeat it; subsequent `/` /
  `?` replaces it.
- Empty pattern with no prior search is a no-op. (Empty pattern with
  a prior search re-runs the prior pattern — vim convention.)
- Case-sensitive by default. `:set ic` toggles case-fold.

---

## List mode (popup picker)

When a plugin calls
[`plugin_list_display(s, items, count, on_select)`](../adr/0004-plugin-abi-freeze.md#v150-additive-extension-2026-05-07)
(cyim 1.5.0+ ABI), a bottom-anchored popup picker captures input.
Today's only consumer is
[cyim-lsp](https://github.com/MacCracken/cyim-lsp)'s
`:lsp-find-refs` / `gr` quickfix list.

While list mode is active, every keystroke routes through the
list-dispatch interception at the top of `editor_dispatch` — the
buffer is **not** mutated, mode-specific dispatch is skipped, and
all keys return `ACT_NONE` so motion / edit pipelines stay no-ops.

| Key | Bytes | Action |
|-----|-------|--------|
| `j` | 106   | Next item (clamped at `count - 1`) |
| `k` | 107   | Previous item (clamped at 0) |
| `Enter` / `LF` | 13 / 10 | Fire `on_select(s, current_index)`; dismiss |
| `Esc` | 27 | Dismiss without firing |
| `q`   | 113 | Dismiss without firing |
| any other | — | Swallowed (no-op) |

**Arrow keys are NOT bound** in list mode as of v1.6.0 — they
route to motion actions via `editor_feed`'s CSI parser, bypassing
the list-mode interception. Future hardening per the
[deferred LSP polish items](../development/roadmap.md). Use j/k.

`on_select` runs **after** dismiss so the callback can call
`plugin_list_display` again for chained pickers without leaking
active state.

---

## VISUAL / VISUAL_LINE

`v` enters char-wise VISUAL with the anchor at current cursor. `V`
enters line-wise VISUAL_LINE. Motions move the cursor; the selection
spans `[min(anchor, cursor), max(anchor, cursor)]` (snapped to whole
lines for VISUAL_LINE).

| Key | Bytes | Action                    | Action ID            |
|-----|-------|---------------------------|----------------------|
| any motion | (NORMAL motion bytes) | Extend selection | (NORMAL motions) |
| `y` | 121   | Yank selection            | `ACT_VISUAL_YANK`    |
| `d` | 100   | Yank + delete selection   | `ACT_VISUAL_DELETE`  |
| `v` | 118   | Toggle off (NORMAL)       | `ACT_TO_NORMAL` (in VISUAL); swap to VISUAL (in VISUAL_LINE) |
| `V` | 86    | Swap to VISUAL_LINE       | (or toggle off in VISUAL_LINE) |
| `Esc` | 27  | Cancel; return to NORMAL  | `ACT_TO_NORMAL`      |

Insert / command transition keys (`i`, `a`, `:`, `/`) are deliberately
swallowed in VISUAL — you can't accidentally lose your selection by
mistyping.

---

## Action ID space

Action IDs cluster by category to leave room for new actions without
renumbering:

| Range   | Category               |
|---------|------------------------|
| 0       | `ACT_NONE` (no-op)     |
| 1–4     | Mode-default actions (literal-insert, cmdline-append, backspace) |
| 10–22   | Mode transitions (incl. `ACT_OPEN_BELOW` = 16 / `ACT_OPEN_ABOVE` = 17, added v1.9.0) |
| 25–32   | Search subsystem       |
| 100–109 | Motions (incl. `ACT_MOVE_FILE_START` = 109, added v1.4.2) |
| 200     | NORMAL-mode edit (`x`) |
| 210–211 | Undo / redo            |
| 220–221 | Paste                  |
| 230–231 | Visual yank / delete   |
| 240     | Dot-repeat             |
| 400–403 | Window navigation      |

The dispatcher emits an action; the per-mode `*_apply` handlers
(`insert_apply`, `motion_apply`, `edit_apply`, `command_apply`,
`window_apply`, `search_apply`, `undo_apply`, `visual_apply`) each
inspect the action and either consume or pass through. Handlers are
mutually exclusive on action IDs, so the chain in
[`src/driver.cyr`](../../src/driver.cyr)'s `editor_step` calls them
all unconditionally and the right one fires.
