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

Motions never cross newlines (`l` at end-of-line is a no-op; `h` at
column 0 stays put). j/k preserve column, clamping to target-line end.

### Edits

| Key      | Byte | Action                | Action ID              | Vim |
|----------|------|-----------------------|------------------------|-----|
| `x`      | 120  | Delete byte           | `ACT_DELETE_RIGHT`     | =   |
| `i`      | 105  | INSERT at cursor      | `ACT_TO_INSERT`        | =   |
| `a`      | 97   | INSERT after cursor   | `ACT_TO_INSERT_AFTER`  | =   |
| `A`      | 65   | INSERT at line end    | `ACT_TO_INSERT_LINE_END`| =  |
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

Unknown commands → `ERR_UNKNOWN_CMD`.

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
| 10–22   | Mode transitions       |
| 25–32   | Search subsystem       |
| 100–109 | Motions                |
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
