# cyim — Roadmap

A phased plan for building cyim from scaffold to a daily-driver modal
text editor. Each milestone is independently shippable and adds a
coherent layer. The goal is to have something a user can actually edit
text with at the end of every phase past M1.

---

## Guiding Principles

- **Modal grammar is fixed; everything else is up for grabs.** Vim's
  modal grammar (normal/insert/command/visual) is a 50-year proven
  interface — we inherit it. Implementation, configuration surface,
  rendering, and extensibility are designed today, not transliterated.
- **No embedded scripting language. Ever.** Vimscript, Lua, Python —
  the editor's surface is its binary. Configuration is data
  (`.cyimrc`, CYML). Refusal §0.
- **Reference, don't mimic.** Vim is the reference. cyim is what a
  modal editor looks like designed today, in a sovereign language,
  without the carried legacy of `:set compatible` and 30-year `.vimrc`
  shapes.
- **Two consumer classes, designed in parallel.** Humans drive cyim at
  a TTY. AI agents (daimon-orchestrated, Claude-style assistants
  included) drive cyim programmatically. The modal grammar is the
  same; the I/O harness differs. Don't retrofit headless drive — the
  keymap dispatch is the API surface for both.
- **Every milestone is dogfoodable.** From M1 onward, the user should
  be able to open this very file in cyim and edit it. M0 is the only
  exception — it just boots and exits.
- **Defer what you can.** LSP, tree-sitter equivalents, plugin
  systems, terminal emulator embedding, clipboards — all post-v1.0.

---

## Milestone 0 — Scaffold (this release, v0.1.0)

**Goal:** the repo exists, compiles, builds clean.

- Project structure: `src/`, `tests/`, `docs/`, `lib/` (vendored stdlib)
- `cyrius.cyml` with stdlib footprint chosen for the modal-editor arc
  (`fs`, `hashmap`, `args`, `vec`, `string`, `str`, `io`, `fmt`)
- `cyim --version`, `cyim --help` (stub)
- CI builds, tests pass

**Done when:** `cyrius build` succeeds and `./build/cyim` exits 0.

---

## Milestone 1 — Modal core

**Goal:** the editor works end-to-end on one buffer. Proves the runtime shape.

- **Gap-buffer** primitive (`src/buffer.cyr`) — insert/delete/move-cursor
- **Raw-mode TTY** (`src/tty.cyr`) — termios via syscalls, alternate screen, no curses dep
- **Modal dispatch** (`src/mode.cyr`) — normal/insert/command tables in `hashmap`
- Normal-mode motions: `h j k l w b 0 $ gg G`
- Insert-mode: type to insert, `Esc` to exit
- Command-mode: `:q` / `:q!` / `:w` / `:wq` / `:e <file>`
- `cyim <file>` opens; `cyim` opens scratch
- Coverage invariant: round-trip read → buffer → write is byte-identical

**Done when:** you can edit `src/main.cyr` in cyim, save, and the
diff is exactly your edits.

---

## Milestone 2 — Syntax highlighting via vyakarana

**Goal:** color shows up. Proves the consumer relationship with vyakarana.

- Add `[deps.vyakarana]` to `cyrius.cyml`
- `src/highlight.cyr` — call `tokenize_source(buf, lang)`, map kinds to
  ANSI palette
- Detect language from file extension (vyakarana already exposes this)
- Configurable palette via `.cyimrc` (data, not code)
- Repaint on edit — no incremental retokenize yet, full-buffer is fine
  for M2

**Done when:** opening `src/buffer.cyr` shows Cyrius highlighting
matching vyakarana's reference output.

---

## Milestone 3 — Multi-buffer & splits

**Goal:** real editing day, not toy demo.

- Buffer list (`:ls`, `:b <n>`, `:bn`, `:bp`)
- Horizontal split (`:sp`), vertical split (`:vsp`)
- Window navigation (`Ctrl-w h/j/k/l`)
- `:e <file>` opens into current window
- Status line per window (filename, modified flag, line/col)
- Close-on-`:q` cascades correctly when last window closes

**Done when:** you can hold three files open in two splits and
navigate without losing state.

---

## Milestone 4 — Search, undo, config

**Goal:** the editor *feels* like vim under your fingers.

- `/pattern` and `?pattern` search; `n`/`N` repeat; `*`/`#` word search
- Undo tree (gap-buffer snapshots) — `u` undo, `Ctrl-r` redo
- `.cyimrc` (CYML) — keymaps, palette, tab width, line numbers
- Visual mode (`v`, `V`, `Ctrl-v`) + yank/paste registers (one register,
  no system clipboard yet — that's post-v1.0)
- Repeat (`.`)
- `:set` for runtime toggles backed by the `.cyimrc` schema

**Done when:** muscle memory from vim survives the switch for a full
editing session.

---

## Milestone 5 — Polish & v1.0

**Goal:** ship.

- Documentation pass: `docs/usage.md`, `docs/keymap.md`, `docs/cyimrc.md`
- Performance pass: large-file (10MB+) edit benchmarks
- Stability pass: fuzz the tokenizer→highlighter pipeline on random bytes
- `agnoshi` integration verified end-to-end
- `aethersafha` integration verified end-to-end (Wayland)
- Receipts: lines-of-code, binary size, vs. `vim`/`neovim` baselines

**Done when:** the user is editing AGNOS code in cyim daily.

---

## Post-v1.0 — Demand-Gated

| Feature | Trigger | Notes |
|---------|---------|-------|
| **Headless / agent-drive mode** | daimon agent first calls cyim non-interactively | Same keymap dispatch, no TTY harness. The AI-agent edit loop. Possibly earlier than post-v1.0 if daimon needs it sooner. |
| **System clipboard** | Wayland integration via `aethersafha` | Belongs in compositor layer, not editor |
| **LSP client** | Cyrius LSP becomes a real consumer | `cyrius lsp` already exists; wire when it stabilizes |
| **Terminal emulator embed** | Third user asks for `:term` | Until then, `Ctrl-z` + shell is fine |
| **Macros** | Recurring need surfaces | `q<reg>` recording; not v1.0 scope |
| **Plugin system** | Probably never | Refusal §0 — if cyim needs to do X, cyim should do X |

---

## Non-Goals

- **No Vimscript / Lua / Python / any embedded scripting.** This is
  the load-bearing constraint of the project. If a feature requires a
  language to express, the feature gets data syntax or doesn't ship.
- **No `:set compatible`.** We are not a vim clone. We are a modal
  editor in the lineage.
- **No GUI.** cyim is a TTY editor. The compositor (`aethersafha`)
  hosts a terminal; the editor is in the terminal.
- **No "IDE" features.** Project drawer, fuzzy file finder,
  integrated debugger — those compose externally via the AGNOS
  library, not internally via plugin sprawl.

---

## Naming

`cy` (Cyrius) + `im` (the lineage `vi → vim → nvim → cyim`). A name
in the tradition, written in the language of the library.

---

*Last updated: 2026-04-25 (v0.1.0 scaffold)*
