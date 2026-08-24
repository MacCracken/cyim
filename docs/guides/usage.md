# Using cyim — a guide for the day-1 vim user

cyim's modal grammar is vim's. If your fingers know `i`, `Esc`, `:wq`, and
`hjkl`, you can use cyim today. This guide covers the bindings cyim
ships, the parts that match vim exactly, and the parts that don't.

For the full keymap, see [`keymap.md`](keymap.md).
For configuration, see [`cyimrc.md`](cyimrc.md).

---

## Starting cyim

```sh
cyim                                                  # open a scratch buffer
cyim foo.cyr                                          # open foo.cyr
cyim --version
cyim --help
cyim --probe                                          # TTY round-trip diagnostic
cyim --headless [<file>]                              # read keystrokes from stdin; no TTY
cyim --write <file>                                   # replace <file> with stdin
cyim --replace <old> <new> <file>                     # substitute first occurrence; OLD must be unique
cyim --replace-all <old> <new> <file>                 # substitute every occurrence
cyim --replace-files <old-file> <new-file> <file>     # OLD/NEW from file contents
cyim --replace-files-all <old-file> <new-file> <file> # same, every occurrence
cyim --grep <pattern> <file>                          # read-only; FILE:N:LINE per hit
cyim --grepfiles <pattern> <file...>                  # multi-file grep
cyim --batch <file>                                   # NUL-separated OLD/NEW pairs from stdin (atomic)
```

`cyim --probe` is the smoke test for "does my terminal cooperate?" — it
flips into raw mode for ~50 ms, prints a banner, restores cooked mode.
If raw mode fails to engage, your terminal isn't a TTY (maybe stdin is
piped) and cyim exits 1.

### Headless / agent-drive

`cyim --headless [<file>]` runs the editor without touching the TTY:
no raw mode, no alt-screen, no per-frame render. Keystroke bytes are
read from stdin and pushed through the same dispatch + apply chain
the interactive path uses, until stdin closes or `:q`/`:q!` fires.

Recipe — make a one-line edit and save from a shell script:

```sh
printf 'iEDIT\x1b:wq\r' | cyim --headless file.cyr
```

Encoding notes:

- `\x1b` is Esc, `\r` is Enter. Bash's `$''` form (e.g. `$'\x1b'`) and
  `printf` both emit raw bytes; plain double-quoted strings won't.
- `:w` is what persists changes to disk. Without `:wq` (or some `:w`),
  edits stay only in the (now exited) process.
- Exit code: 0 on graceful exit (either `:q`/`:q!` fired or stdin
  closed cleanly); non-zero only on file-load failure.

Same dispatch chain as the TTY path — search / undo / dot / visual /
multi-window / multi-buffer all available. This is the low-level
surface for shell scripts, CI checks, and `daimon`-orchestrated
agents per the roadmap.

For higher-level operations the binary ships four more flags that
skip the dispatch chain entirely (no edit-history / mode-state to
model — they're tools, not user edits):

### `cyim --write <file>` — bulk content replace

```sh
printf 'new file content\n' | cyim --write foo.txt
```

Reads stdin, replaces `<file>` contents. Trailing newlines preserved
exactly (no `$(cat)`-style stripping). Equivalent of "Write" in
agent tool vocabularies.

### `cyim --replace <old> <new> <file>` — unique find/replace

```sh
cyim --replace 'fn old_name(' 'fn new_name(' src/foo.cyr
```

Substitutes the **first** occurrence of `<old>` with `<new>`.
**`<old>` must be unique in the file.** If it occurs more than once,
the command refuses with exit 5 — pick a more specific OLD or use
`--replace-all`. Matches the Claude Code `Edit` tool's invariant.

`cyim --replace-all <old> <new> <file>` does the same without the
uniqueness check; substitutes every occurrence.

### `cyim --grep <pattern> <file>` — read-only line scan

```sh
cyim --grep 'TS_LEX_JSX_SKIP' src/frontend/ts/lex.cyr
# src/frontend/ts/lex.cyr:142:    TS_LEX_JSX_SKIP,
# src/frontend/ts/lex.cyr:418:    case TS_LEX_JSX_SKIP:
```

Scans `<file>` line by line and emits `FILE:N:LINE` (matching `grep -n`
exactly: no spaces around the second colon) for every line containing
`<pattern>` as a literal substring — same matching semantics as
`--replace`'s `OLD` (no regex by default, byte-wise compare).

Why ship grep when `rg`/`grep` exist on every box: it keeps
agent-driven flows inside one binary. No `rg` in `PATH`, no shell
escaping for special characters in `<pattern>`, no tool-boundary
jump between an edit and the check that follows it.

`cyim --grepfiles <pattern> <file...>` extends the same shape over
a list of files (multi-file grep, `FILE:N:LINE` per match). Useful
for "find every reference to X across these N files" without
shell-globbing inside argv.

Exit codes follow `grep(1)`: **0** if any line matched, **1** if
none, **2** on usage error, **3** if `<file>` is missing.

`--context=<n>` modifier (matches `grep -C N`): emit the N lines
before and after each match, with `--` separators between
non-adjacent groups and between files. Overlap-merging keeps the
output clean when matches are close together.

```sh
cyim --grep --context=2 'TODO' src/main.cyr
# Emits 2 lines of context above + below each TODO match.
```

### `cyim --batch <file>` — multi-pair atomic find/replace

```sh
printf 'OLD1\0NEW1\0OLD2\0NEW2\0' | cyim --batch foo.cyr
```

Reads NUL-separated alternating `OLD\0NEW\0OLD\0NEW\0…` pairs from
stdin and applies them to `<file>` in memory, then writes once at
the end. Atomic: if any pair fails (OLD non-unique, OLD missing),
the file on disk stays untouched.

Per-pair semantics default to `--replace` (OLD must be unique). Add
`--all` to switch every pair to `--replace-all` semantics.

### `cyim --replace-files OLD_FILE NEW_FILE FILE` — file-sourced patterns

When OLD or NEW are large, multi-line, or contain shell-special
characters, argv encoding gets fragile. `--replace-files` reads OLD
and NEW from the named files instead:

```sh
cyim --replace-files patches/old-block.txt patches/new-block.txt src/foo.cyr
```

Same uniqueness invariant as `--replace`. Sister verb
`--replace-files-all` drops the uniqueness check.

### `--regex=<flavor>` — regex matching on grep/replace verbs

By default cyim's grep and replace verbs match patterns as literal
substrings. `--regex=<flavor>` switches to regex matching across
all six pattern verbs (`--grep`, `--grepfiles`,
`--replace[-all]`, `--replace-files[-all]`):

```sh
cyim --grep --regex=ere '\bTODO\b' src/main.cyr   # word-boundary anchored
cyim --replace-all --regex=re2 'fn (\w+)' 'pub fn \1' src/lib.cyr
cyim --grep --regex=fuzzy --fuzzy-edits=2 'TS_LEX_JSXSKIP' src/lex.cyr
```

Six flavors ship:

| Flavor   | Engine | Notes |
|----------|--------|-------|
| `ere`    | cyrius stdlib Pike NFA | POSIX-ERE-ish; default for casual regex |
| `bre`    | niyama BRE | POSIX-BRE; archaic but stable for vim users |
| `re2`    | niyama RE2 | RE2-ish; linear-time, no backreferences |
| `pcre`   | niyama PCRE | PCRE-ish; richer but step-limited (no catastrophic backtracking) |
| `vim`    | niyama vim | vim's regex flavor; for vim users porting `:s` patterns |
| `fuzzy`  | niyama fuzzy | Levenshtein edit-distance match; pair with `--fuzzy-edits=<n>` |

Backreferences (`\1`-style) are deferred per niyama's long-term
security-against-misuse plan. Surface in `cyim --help` for the
flavor list. ADR 0002 documents the extensibility shape.

### Modifiers — `--wc`, `--expect`, `--expect-N`

Modifiers sit between the verb and its positional args, in any order
(pre-1.1 callers that placed `--wc` immediately after the verb still
work — the new behavior is a strict superset).

**`--wc[=l|=long]`** — print `wc(1)` output for the resulting file on
successful `--write`/`--replace[-all]`:

```sh
cyim --write --wc      foo.txt < new.txt   # 3 12 84 foo.txt
cyim --write --wc=l    foo.txt < new.txt   # 3 foo.txt
cyim --write --wc=long foo.txt < new.txt   # alias for --wc=l
cyim --replace --wc 'old' 'new' foo.txt
```

**`--expect=<pat>` / `--expect-not=<pat>`** (`--write` only) — after the
file is saved, the resulting buffer is scanned for `<pat>`. Mismatch
returns **exit 6** with a message on stderr; the file is saved either
way (the assertion is a contract on the *result*, not a save gate):

```sh
# "After this rewrite, TS_LEX_JSX_SKIP MUST NOT appear":
cyim --write --expect-not='TS_LEX_JSX_SKIP' src/lex.cyr < new.txt
echo $?    # 0 if clean, 6 if the dead symbol came back

# "After this rewrite, the new ROUTE_TABLE marker MUST appear":
cyim --write --expect='ROUTE_TABLE' src/router.cyr < new.txt
```

Composes with `--wc`:

```sh
cyim --write --wc=l --expect='ROUTE_TABLE' src/router.cyr < new.txt
```

**`--expect-N=<n>` / `--expect-1`** (`--replace`/`--replace-all` only) —
asserts `OLD` occurs *exactly* `<n>` times in the file *before*
substitution. Mismatch returns **exit 6** without writing.
`--expect-1` is sugar for `--expect-N=1`.

```sh
# "Replace the unique occurrence of OLD; fail loudly if there isn't one":
cyim --replace --expect-1 'fn old_name(' 'fn new_name(' src/foo.cyr

# "Substitute every OLD; fail if the count surprises us":
cyim --replace-all --expect-N=3 'TODO_v1' 'TODO_v2' src/foo.cyr

# "Defensive no-op: assert OLD is absent (--expect-N=0)":
cyim --replace --expect-N=0 'DEAD_SYMBOL' '' src/foo.cyr
echo $?    # 0 if absent (clean no-op), 6 if it crept back in
```

Closes the silent-no-op gap: `--replace OLD NEW FILE` exits 4 when
`OLD` is missing, but exit 4 is easy to miss in scripts. Pair with
`--expect-1` and the assertion is explicit.

Exit codes (verb-disambiguated where noted):

| Code | Meaning |
|------|---------|
| 0    | Success (or, for `--grep`, ≥1 match) |
| 1    | Save failed (`--write`/`--replace[-all]`) \| no match (`--grep`) |
| 2    | Bad CLI args (missing positional, empty pattern, malformed `--expect-N`) |
| 3    | File not found |
| 4    | OLD not found in FILE (`--replace[-all]`; suppressed when `--expect-N=0`) |
| 5    | OLD occurs more than once and `--replace-all` not used |
| 6    | Assertion failed (`--expect`/`--expect-not`/`--expect-N` mismatch) |

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
gg            first line, col 0  (two-byte sequence — g latches the prefix)
G             last line, col 0
m<a-z>        set per-buffer mark
m<A-Z>        set global mark (cross-buffer)
'<a-z>        jump to per-buffer mark
'<A-Z>        jump to global mark (switches buffer if needed)
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

Arrow keys also move the cursor (terminal CSI sequences are parsed
at the driver layer). They work in NORMAL, INSERT, and VISUAL.

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
registers yet. (Note: vim's `"a-"z` *registers* are distinct from
its `'a-'z` *marks* — cyim ships marks at v1.6.0 but not registers.
Named registers are demand-gated.)

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

## Marks

VIM-style marks landed at v1.6.0. Two namespaces:

```
m<a-z>    set per-buffer mark <a-z> at cursor
m<A-Z>    set global mark <A-Z> at cursor (cross-buffer)
'<a-z>    jump cursor to per-buffer mark <a-z>
'<A-Z>    jump to global mark <A-Z> (switches buffer if needed)
```

**Per-buffer marks** stay with their buffer. `ma` in `foo.cyr`
and `ma` in `bar.cyr` are independent slots; switching between
the buffers preserves both.

**Global marks** record both the buffer + offset. `'A` from any
buffer jumps to wherever `mA` was last set (and switches buffer
if the mark lives elsewhere).

```
ma                 # in foo.cyr at line 42
:e bar.cyr         # switch buffers
mA                 # in bar.cyr at line 7 — global mark A
'a                 # no-op in bar.cyr — buffer-local 'a' isn't set here
:e foo.cyr         # back to foo
'a                 # jumps to line 42
'A                 # jumps to bar.cyr line 7 (switches buffer)
```

`m` / `'` followed by anything other than a letter (digits,
punctuation) is silently swallowed. Unset marks are no-ops on
jump. `:marks` listing not in 1.6.0; see
[`docs/development/roadmap.md`](../development/roadmap.md) for
deferred mark items.

---

## LSP integration

cyim folds in [cyim-lsp](https://github.com/MacCracken/cyim-lsp)
via the sandhi pattern (since v1.4.0; current dep tag 1.2.1 as
of v1.6.0). With `cyrius-lsp` on PATH (the cyrius
toolchain installs it at `~/.cyrius/bin/cyrius-lsp`), opening a
`.cyr` file lazily spawns the server and surfaces:

- **Diagnostics** — counts in the status segment (`E:N W:M I:K H:L`)
  next to the file path; inline render via the `diagnostic_provider`
  plugin hook (gutter glyphs / underline marks per cyim's render
  layer).
- **`gd`** — go-to-definition. Same-file: cursor moves. Cross-file:
  the destination file loads (dedup-aware against the active
  buflist) and the cursor jumps in the new buffer.
- **`gr`** — find-references. Pops a quickfix picker showing every
  reference site as `filename:line:col`. j/k navigates, Enter
  jumps, Esc/q dismisses.
- **`:lsp-restart`** — kill + respawn the server. Useful after
  upgrading the cyrius toolchain.
- **`:lsp-status`** — print server pid + describe state.
- **`:lsp-goto-def`** / **`:lsp-find-refs`** — same as `gd` / `gr`,
  ex-command form. The keymap surface is muscle-memory; the
  ex-commands are the typed-out form.

Built-in `gg` (first line) wins on conflict against any plugin
attempt to bind `(KEY_G, 'g')` per
[ADR 0003 §3](../adr/0003-cyrius-plugin-system.md). `gd` and `gr`
are unclaimed by built-ins, so cyim-lsp owns them.

Without `cyrius-lsp` on PATH, the LSP plugin lazily-fails on first
post_change: the spawn returns -1, the editor stays clean, and
the LSP-driven hooks become no-ops. No errors propagate to the
edit path.

### Quickfix-style picker (list mode)

When `:lsp-find-refs` / `gr` opens the picker (or any future plugin
that calls `plugin_list_display`), the editor enters **list mode**:

```
j         next item
k         previous item
Enter     select (load file + jump cursor); dismiss
Esc / q   dismiss without selecting
```

Every other keystroke is swallowed while the picker is up — the
buffer stays untouched. Arrow keys are NOT bound in list mode as
of v1.6.0 (they route to motion actions via the driver-level CSI
parser); use j/k.

The picker is bottom-anchored, full-width, and shows up to 10
items at a time. The current item is reverse-highlighted; if the
list is longer than 10 the window auto-scrolls to keep the
selection in view.

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
- **Plugins exist, but as bundles, not scripts.** AOT-compiled
  Cyrius distfiles fold into the binary at build time via the
  sandhi pattern (vyakarana, niyama, cyim-lsp, trailing_ws all
  live this way). No `dlopen`, no eval, no runtime sandbox. The
  refusal is on **embedded scripting** (Vimscript / Lua /
  Python) — not on plugins-as-bundles. See
  [`docs/architecture/001-plugin-system.md`](../architecture/001-plugin-system.md).

---

## Troubleshooting

**Tab inserts a tab character.** `:set tabstop=N` **stores** the display
width on the editor state but does not yet change rendering — a TAB still
draws as one column. Render integration is deferred, as
[`cyimrc.md`](cyimrc.md) records; this page claimed `tabstop` "controls
display" through 1.8.2, which it never has. Literal Tab insertion stays.
(Auto-indent / spaces-as-Tab is post-v1.0 if asked.)

**Arrow keys put me in NORMAL.** Terminals send arrow keys as `\x1b[A`
etc.; the leading `\x1b` is Esc, which exits INSERT. Use `h j k l`
instead — they're faster anyway.

**`:q!` quits, but my edits weren't saved.** That's intentional — `:q!`
is "discard and quit". Use `:wq` to save before quitting.

**Cursor positions don't line up with multi-byte glyphs.** cyim is
byte-oriented — a line with a 3-byte UTF-8 character has column 3
at byte 3, even though the user sees one glyph. This matches vim
with `:set encoding=latin1`. Proper Unicode-aware column counting
is post-v1.0 demand-gated. For ASCII / single-byte content (most
code), the distinction is invisible.

**Highlighting is missing for my file.** cyim ships grammars for c,
cyrius, javascript, json, markdown, python, rust, shell, toml,
typescript, yaml. If your file's extension isn't in the
[lang.cyr table](../../src/lang.cyr), it falls through to `plain` and
no highlighting is applied. Adding a language: contribute a grammar
upstream to [vyakarana](https://github.com/MacCracken/vyakarana).
