# Using cyim — a guide for the day-1 vim user

cyim's modal grammar is vim's. If your fingers know `i`, `Esc`, `:wq`, and
`hjkl`, you can use cyim today. This guide covers the bindings cyim
ships, the parts that match vim exactly, and the parts that don't.

For the full keymap, see [`keymap.md`](keymap.md).
For configuration, see [`cyimrc.md`](cyimrc.md).

---

## Starting cyim

```sh
cyim                # open a scratch buffer
cyim foo.cyr        # open foo.cyr
cyim --version
cyim --help
cyim --probe        # TTY round-trip diagnostic (raw on / sleep / cooked off)
```

`cyim --probe` is the smoke test for "does my terminal cooperate?" — it
flips into raw mode for ~50 ms, prints a banner, restores cooked mode.
If raw mode fails to engage, your terminal isn't a TTY (maybe stdin is
piped) and cyim exits 1.

---

## Modes

| Mode | Enter from | Exit to |
|------|-----------|---------|
| **NORMAL** (default)    | (start) / Esc / `:` `Enter` / `/` `Enter` | — |
| **INSERT**              | `i` `a` `A` from NORMAL                 | Esc → NORMAL |
| **COMMAND**             | `:` from NORMAL                         | Esc / Enter → NORMAL |
| **SEARCH** (forward)    | `/` from NORMAL                         | Esc / Enter → NORMAL |
| **SEARCH_BACK** (back)  | `?` from NORMAL                         | Esc / Enter → NORMAL |
| **VISUAL** (char)       | `v` from NORMAL                         | Esc / `v` / `y` / `d` → NORMAL |
| **VISUAL_LINE**         | `V` from NORMAL                         | Esc / `V` / `y` / `d` → NORMAL |

The status row shows the current mode (`-- NORMAL --`, `-- INSERT --`,
etc.). In COMMAND / SEARCH the status row shows your typed buffer
prefixed with `:` / `/` / `?`.

---

## Editing in NORMAL

```
h j k l       move cursor (line-bounded; doesn't cross newlines)
0             jump to start of line
$             jump to end of line
w b           next / previous word (whitespace + class boundaries)
G             last line
x             delete byte under cursor
i             enter INSERT at cursor
a             enter INSERT one byte right of cursor
A             enter INSERT at end of line
v             enter VISUAL (char-wise selection)
V             enter VISUAL_LINE (line-wise selection)
u             undo
Ctrl-r        redo
.             repeat last edit
p             paste yank register AFTER cursor
P             paste yank register BEFORE cursor
:             enter COMMAND
/             enter SEARCH (forward)
?             enter SEARCH (backward)
n             repeat last search (same direction)
N             repeat last search (opposite direction)
*             search forward for word under cursor
#             search backward for word under cursor
Ctrl-w h/j/k/l    switch focus to neighbor window
```

---

## Inserting

`i` enters INSERT at cursor. Type bytes; they go in. `Esc` returns to
NORMAL and steps the cursor back one byte (vim's "after-typed-byte"
convention). `Backspace` and `DEL` both delete the byte left of cursor.

`a` (append) enters INSERT one byte right of cursor — useful when you
want to add to the end of a word. `A` jumps the cursor to the end of
the line first, then enters INSERT.

`.` repeats the last insert session at the current cursor. So
`iEDIT<Esc>` followed later by `.` will insert "EDIT" again wherever
the cursor is now.

---

## Search

`/foo<Enter>` jumps to the next occurrence of "foo" after the cursor.
`?foo<Enter>` searches backward. The last pattern is remembered: `n`
repeats in the saved direction, `N` reverses.

`*` and `#` search for the word under the cursor (forward / backward).
A "word" is a maximal run of letters / digits / underscore.

Case-insensitive search: `:set ic` (or `:set noic` to revert).

---

## Visual

`v` enters char-wise VISUAL with the anchor at your current cursor.
Move the cursor with `h j k l 0 $ w b G` to grow / shrink the
selection. The status bar shows `-- VISUAL --`.

In VISUAL:

```
y       yank selection into the register, return to NORMAL
d       delete selection (also yanks), return to NORMAL
v       toggle off (back to NORMAL without yanking)
V       swap to VISUAL_LINE (line-wise selection)
Esc     cancel
```

`V` is line-wise: the selection snaps to whole lines. Useful with `d`
to delete entire lines.

The yank register is a single shared slot — there are no a-z named
registers yet (post-v1.0 demand-gated).

---

## Multiple files & windows

Open another file with `:e <path>`. The previous buffer stays in the
registry. List with `:ls`, switch with `:bn` / `:bp` / `:b N`.

```
:ls         list buffers (active marked with *)
:bn         next buffer
:bp         previous buffer
:b 2        switch to buffer 2
```

Splits:

```
:sp         horizontal split (current + sibling, both showing same buffer)
:vsp        vertical split
Ctrl-w h    move focus to the left neighbor
Ctrl-w l    move focus to the right neighbor
Ctrl-w j    move focus down
Ctrl-w k    move focus up
:q          close active window (cascades to exit when the last leaf closes)
:q!         force close (no dirty check)
```

After splitting, each window can show a different buffer — `:bn` in one
window doesn't affect the other. The active window's status row is
shown in reverse video.

---

## Saving and quitting

```
:w               save to current file (ERR_NO_FILE_NAME if buffer is unnamed)
:w foo.txt       save to foo.txt; current file becomes foo.txt
:wq              save then close window
:q               close window (refuses with ERR_DIRTY if unsaved)
:q!              close unconditionally
```

`:e <path>` on a dirty buffer is *not* refused — instead, the previous
buffer is preserved in the registry (you can come back via `:b N`). The
new buffer becomes active.

---

## Differences from vim

- **No `:set compatible`.** cyim is a modal editor in vim's lineage,
  not a vim clone. Some defaults differ.
- **No embedded scripting.** Vimscript / Lua / Python aren't
  available — by design (refusal). Configuration is data
  (`.cyimrc`, see [`cyimrc.md`](cyimrc.md)), not code.
- **No system clipboard.** The yank register is internal-only. System
  clipboard wiring belongs in the compositor (`aethersafha`); not in
  the editor.
- **No `:!cmd`.** Shell-out is deliberately absent. `Ctrl-z` to your
  shell, do the thing, `fg` back.
- **No plugins.** If cyim needs to do X, cyim should do X — refusal §0.

---

## Troubleshooting

**Tab inserts a tab character.** `:set tabstop=N` controls display
width; literal Tab insertion stays. (Auto-indent / spaces-as-Tab is
post-v1.0 if asked.)

**Arrow keys put me in NORMAL.** Terminals send arrow keys as `\x1b[A`
etc.; the leading `\x1b` is Esc, which exits INSERT. Use `h j k l`
instead — they're faster anyway.

**`:q!` quits, but my edits weren't saved.** That's intentional — `:q!`
is "discard and quit". Use `:wq` to save before quitting.

**Highlighting is missing for my file.** cyim ships grammars for c,
cyrius, javascript, json, markdown, python, rust, shell, toml,
typescript, yaml. If your file's extension isn't in the
[lang.cyr table](../../src/lang.cyr), it falls through to `plain` and
no highlighting is applied. Adding a language: contribute a grammar
upstream to [vyakarana](https://github.com/MacCracken/vyakarana).
