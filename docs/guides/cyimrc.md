# `.cyimrc` configuration

cyim is configured through `.cyimrc` (CYML) and runtime `:set` toggles.
Configuration is **data, not code** — by design. There is no embedded
scripting language and never will be. If a setting can't be expressed
as a key=value line, it doesn't ship.

The two surfaces are paired: every key in `.cyimrc` has a matching
`:set` toggle, and vice versa. `.cyimrc` runs at startup; `:set`
overrides at runtime.

---

## Where cyim reads it from

Two files, in order, **later overriding earlier** (v1.9.2 —
[ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md)):

| # | Path | What it's for |
|---|---|---|
| 1 | `$XDG_CONFIG_HOME/cyim/cyimrc`, else `$HOME/.config/cyim/cyimrc` | **Your** config. Follows you between projects |
| 2 | `./.cyimrc` — the current working directory | Per-project overrides |

**Overrides are key by key.** A local file that sets one colour keeps every
other setting from your user config — you never restate a whole palette to
change one entry:

```cyml
# ~/.config/cyim/cyimrc
palette.keyword = 141
palette.string  = 113
palette.number  = 215
```
```cyml
# ./.cyimrc in one project
palette.string = 99      # only this changes; keyword and number stay 141 / 215
```

A missing or empty file at either location is a silent no-op. With neither,
bundled defaults apply. If `$HOME` and `$XDG_CONFIG_HOME` are both unset, the
user-level file is **skipped**, not guessed at — cyim will not read
`/.config/cyim/cyimrc`.

### The local file is the directory's input, not yours

Worth knowing plainly: `./.cyimrc` is read from wherever you happen to be. If
you clone a repository, `cd` into it and open a file, you have applied that
repository's configuration without reading it.

[ADR 0005](../adr/0005-cyimrc-cwd-trust-boundary.md) accepts that on purpose,
and the reason is the size of the surface: the whole of `.cyimrc` is ten
colour indexes and three display integers, so **the worst a hostile directory
achieves is a wrong colour**. There is no path from a config file to code
execution, file access or command dispatch, because cyim has no scripting
language for one to reach for.

That acceptance is conditional on the surface staying small. Every new key
gets classified — local-overridable or user-config-only — when it is added.
Keymaps, if they ever land, are the first serious candidate for the latter: a
colour from a cloned directory is a wrong colour, but a keymap from it decides
what your keystrokes do.

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
- **Embedded scripting** (Vimscript / Lua / Python). The load-bearing
  refusal: every layer of the editor's behaviour is in compiled
  Cyrius; configuration is data only.

Note on plugins: cyim **does** have a plugin system — but plugins
are AOT-compiled Cyrius bundles folded in at build time via the
sandhi pattern, not runtime-loaded scripts. The 1.x ABI is frozen
at v1.3.6 / [ADR 0004](../adr/0004-plugin-abi-freeze.md); the
shipping consumers are
[cyim-lsp](https://github.com/MacCracken/cyim-lsp) (LSP client)
and `src/plugins/trailing_ws.cyr` (inline). The `.cyimrc` /
`:set` surface configures the editor; plugin selection is decided
at build time via `cyrius.cyml`'s `[deps.<plugin>]` blocks. See
[`docs/architecture/001-plugin-system.md`](../architecture/001-plugin-system.md).
