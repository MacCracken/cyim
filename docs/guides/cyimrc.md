# `.cyimrc` configuration

cyim is configured through `.cyimrc` (CYML) and runtime `:set` toggles.
Configuration is **data, not code** — by design. There is no embedded
scripting language and never will be. If a setting can't be expressed
as a key=value line, it doesn't ship.

The two surfaces are paired: every key in `.cyimrc` has a matching
`:set` toggle, and vice versa. `.cyimrc` runs at startup; `:set`
overrides at runtime.

---

## File location

cyim looks for `.cyimrc` in the current working directory at startup.
A missing or empty file is a silent no-op — bundled defaults apply.

(XDG search paths — `$XDG_CONFIG_HOME/cyim/cyimrc`,
`$HOME/.config/cyim/cyimrc` — are deferred to a future bite. For now,
ship a project-local `.cyimrc` next to your code.)

---

## File format

Flat CYML: one `key = value` per line. `#` starts a line comment.
Blank lines and arbitrary whitespace around `=` are tolerated.
Unknown keys are silently ignored (forward-compat). Malformed values
preserve the previous slot value rather than overwriting it.

Example:

```cyml
# Theme overrides — 256-color ANSI indices
palette.keyword     = 141
palette.string      = 113
palette.number      = 215
palette.comment     = 245

# Editor defaults
ignorecase   = 1
line_numbers = 0
tabstop      = 4
```

---

## Palette overrides

Maps each [vyakarana token kind](https://github.com/MacCracken/vyakarana)
to a 256-color ANSI index. Setting `-1` means "no color" (terminal
default). Unmentioned kinds keep cyim's bundled palette.

| Key                       | TK_*                | Bundled |
|---------------------------|---------------------|---------|
| `palette.ident`           | `TK_IDENT` (0)      | -1 (default) |
| `palette.keyword`         | `TK_KEYWORD` (1)    | 141 (purple)  |
| `palette.string`          | `TK_STRING` (2)     | 113 (green)   |
| `palette.number`          | `TK_NUMBER` (3)     | 215 (orange)  |
| `palette.comment`         | `TK_COMMENT` (4)    | 245 (grey)    |
| `palette.operator`        | `TK_OPERATOR` (5)   | 110 (steel)   |
| `palette.punctuation`     | `TK_PUNCTUATION` (6)| -1 (default) |
| `palette.whitespace`      | `TK_WHITESPACE` (7) | -1 (default) |
| `palette.preprocessor`    | `TK_PREPROCESSOR` (8)| 221 (yellow) |
| `palette.error`           | `TK_ERROR` (9)      | 196 (bright red) |

The full color value space is 0..255 (xterm 256-color). See
`man xterm-256color` or any 256-color chart.

---

## Editor options

| Key            | Type    | Default | `:set` form                  | Effect |
|----------------|---------|---------|------------------------------|--------|
| `ignorecase`   | 0 / 1   | 0       | `:set ic` / `:set noic`      | Case-fold byte compare in `/` `?` `*` `#` `n` `N` |
| `line_numbers` | 0 / 1   | 0       | `:set number` / `:set nonumber` | Reserved — render integration deferred to a follow-up bite |
| `tabstop`      | integer | 4       | `:set tabstop=N`             | Display width of a TAB byte (storage only today; render integration deferred) |

`line_numbers` and `tabstop` are stored on the editor state and
visible via the accessors today. Their render-side consumption (gutter
display, tab expansion) is queued for a follow-up; the config slots
exist now so `.cyimrc` and `:set` agree.

---

## Boot order

1. `cyrius_init` (allocator + args)
2. `highlight_init` — resolve `grammars/` via `/proc/self/exe` and
   pre-load every bundled grammar
3. `cyimrc_load` — read `./.cyimrc`, populate the cyimrc-globals
4. `editor_new` (allocate state, set defaults)
5. Apply non-sentinel cyimrc-globals to editor state — `.cyimrc`
   values override defaults; absent keys leave defaults in place
6. `bl_init` + `window_init` — set up registry + initial leaf
7. `tty_raw` + `tty_alt_enter` — switch terminal to raw mode

`:set` runs at any point post-step-7 and overrides state directly.

---

## Forward-compat

The format intentionally tolerates unknown keys. A future cyim that
ships, say, `theme = solarized-dark` as a key can land without
breaking your `.cyimrc` (an older binary just ignores the key). Same
for `:set` — unknown options return `ERR_UNKNOWN_CMD` rather than
crashing.

The reverse is not guaranteed: if a key changes meaning (e.g. a value
type narrows), CHANGELOG flags it. The keys above are stable from
v0.5.0 onward.

---

## What's *not* in the config surface

- **Keymap remapping** (`map`, `nmap`, `inoremap`, etc.). vim's keymap
  surface grew baroque; cyim's keymap is currently fixed in
  [`src/mode.cyr`](../../src/mode.cyr). Remapping is queued for a
  future bite if it earns the room — the plan would be a
  `keymap.<mode>.<key> = <action_name>` form, with `<action_name>`
  pulled from the action-id table in [`keymap.md`](keymap.md).
- **Auto-commands** (`autocmd FileType …`). Vim's cross-cutting
  trigger system is the layer where Vimscript becomes load-bearing;
  cyim refuses by design.
- **Shell-out** (`:!cmd`, `system()`). Use Ctrl-z + your shell + `fg`.
- **Plugins.** Refusal §0 — if cyim needs to do X, cyim should do X.
