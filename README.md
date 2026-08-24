# cyim

**Sovereign Cyrius-native text editor — VIM-inspired, zero attack surface.**

Modal editing in the lineage of `vi`/`vim`/`neovim`, redesigned from the
ground up in [Cyrius](https://github.com/MacCracken/cyrius). No Lua, no
Vimscript, no plugin sandbox to escape — the editor's surface *is* its
binary, and the binary is auditable end-to-end.

Part of the [AGNOS](https://github.com/MacCracken/agnosticos) library
for humanity. Consumers:

- **`agnoshi`** — the AI shell
- **`aethersafha`** — the Wayland compositor
- **`daimon`-orchestrated agents** — AI assistants (Claude-style and
  AGNOS-native agents alike) editing through cyim. The same modal
  surface humans use, agents drive programmatically. The edit loop
  closes through cyim; nothing in the loop ships from outside the
  library.

## Status

**1.10.0 — released.** The 1.x series shipped:

- **v1.0** (2026-04-25) — M0–M7 landed: gap-buffer + raw-mode TTY,
  modal dispatch, vyakarana syntax highlighting, multi-buffer +
  splits, search / undo / visual / `.` / config, polish, P(-1)
  hardening, security audit.
- **v1.0.x / v1.1.x** — agent-drive CLI surface lit up:
  `--headless` / `--write` / `--replace[-all]` / `--grep`
  (1.0.1–1.1.0); `--batch` (1.1.2); `--grepfiles` / `--context=N` /
  `--replace-files[-all]` (1.1.4).
- **v1.2.x / v1.3.x** — `--regex=<flavor>` modifier on grep/replace
  verbs: `ere` (1.2.0, cyrius stdlib Pike NFA), then
  `bre`/`re2`/`pcre`/`vim`/`fuzzy` via the niyama fold (1.3.0+),
  with `--fuzzy-edits=<n>` precision (1.3.2).
- **v1.3.x** (continued) — plugin ABI scaffold + 6-hook freeze
  (1.3.4–1.3.6 / [ADR 0004](docs/adr/0004-plugin-abi-freeze.md)).
- **v1.4.x** — first non-trivial external plugin folded in:
  [cyim-lsp](https://github.com/MacCracken/cyim-lsp) at 1.4.0.
  Additive ABI extensions (`plugin_register_normal_prefix_key`,
  `plugin_buf_load_file`) at 1.4.2 unlock `gd` / `gr` keymap dispatch
  and cross-file goto-def at 1.4.3.
- **v1.5.x** — `plugin_list_display` ABI (popup-picker subsystem)
  at 1.5.0; cyim-lsp 1.2.0 pickup at 1.5.1 turns `:lsp-find-refs` /
  `gr` into a navigable quickfix list.
- **v1.5.2** — closeout cut for the 1.5.x cycle. 0 CRITICAL / 0 HIGH /
  0 MEDIUM / 4 LOW findings (tracked).
- **v1.5.3** — closes 3 of 4 LOW closeout findings (multi-iter bench,
  prefix-clear hardening, URL-decode for `file://` URIs via cyim-lsp 1.2.1).
- **v1.6.0** — VIM-style marks (`m<letter>` / `'<letter>`; per-buffer
  a-z + global A-Z). First feature minor of the post-1.5.x cycle.
- **v1.7.x** — toolchain + dep-currency cycle: darshana TUI dep pickup
  (cyim is the donor and first consumer) at 1.7.0, then forward-compat
  darshana / cyrius pin refreshes (1.7.1–1.7.5). No editor-surface
  behavior change across the cycle.
- **v1.8.0** — **cyim runs on AGNOS.** Full-screen on the framebuffer
  console (`src/agnos_kbd.cyr` reverse-maps raw Set-1 scancodes from
  `kbscan#42` into the byte stream `editor_feed` already consumes), or an
  ed/ex line editor via `cyim --line`. Verified on the real kernel under
  QEMU and under mirshi. 1.8.1 restored the `--agnos` *build*.
- **v1.8.2** — dependency + toolchain catch-up (cyrius `6.5.35`,
  darshana `1.0.0`, vyakarana `2.4.0`, 46 bundled grammars), and the
  highlighting regression it uncovered: **34 of 45 routed languages had
  no grammar loaded** since 1.6.2 and rendered uncoloured. Fixed, with a
  two-way drift guard.
- **v1.8.3–v1.8.5** — P(-1) hardening and its follow-through. The HIGH
  finding: every write path treated a short `write(2)` as a completed
  one, so `:w` and all six agent verbs could destroy most of a file and
  exit 0. Fixed at 1.8.3 (reported), closed at 1.8.4 (**atomic save** —
  sibling temp + `rename`, per
  [ADR 0006](docs/adr/0006-atomic-save.md)). 1.8.5 swept dead code and
  cleanliness; 1.8.6 closed the last documentation gap.

- **v1.8.7** — closeout for the 1.8.x cycle: all 11 `CLAUDE.md` steps, 2
  code-review findings fixed, and a 94%-duplicated render pair collapsed
  with byte-identical output.
- **v1.9.0** — **`o` / `O`** open a line below / above and enter INSERT.
  Undoable as one unit, dot-repeatable. Fixed alongside: `A` appended
  *before* the character on a one-character line — a bug present since
  `A` landed, surfaced only when `o` copied the same idiom.

- **v1.9.1–v1.9.3** — BUG-002 closed (the LSP client works for the first time
  since the 1.4.0 fold-in, via a cyim-lsp tag bump), `.cyimrc` moved to
  `$XDG_CONFIG_HOME` with project-local override
  ([ADR 0005](docs/adr/0005-cyimrc-cwd-trust-boundary.md)), and the 1.9.x
  closeout.
- **v1.10.0** — **resize-aware rendering.** cyim uses your terminal's real
  size and repaints when you resize it; before this it drew a fixed 24×80 on
  every target but agnos.

Current pins: cyrius `6.5.35`, vyakarana `2.4.0`, cyim-lsp `1.5.2`,
darshana `1.0.0`.

Live state in [`docs/development/state.md`](docs/development/state.md);
sequencing + deferred LSP polish in
[`docs/development/roadmap.md`](docs/development/roadmap.md).

## Why "cyim"

`cy` (Cyrius) + `im` (the editor lineage `vi → vim → nvim → cyim`).
A name in the tradition, written in the language of the library.

## Build

```sh
cyrius deps                              # resolve deps (vyakarana, cyim-lsp, darshana)
cyrius build src/main.cyr build/cyim     # compile
CYRIUS_DCE=1 cyrius build ...            # dead-code-eliminated release build
cyrius tests                             # 21 .tcyr suites (1226 assertions)
cyrius fuzz                              # 4 .fcyr harnesses
sh tests/cli_smoke.sh                    # 128 agent-CLI assertions
cyrius smoke                             # tests/smcyr/lsp_fold.smcyr (real cyrius-lsp)
cyrius bench tests/perf.bcyr             # gap-buffer / search / render / highlight perf
cyrius lint src/*.cyr                    # static checks
cyrius audit                             # full check: self-host, test, fmt, lint
```

## Interactive editor

```sh
cyim                                       # open scratch buffer
cyim <file>                                # open <file>
cyim --version
cyim --help
cyim --probe                               # TTY round-trip diagnostic
```

Daily-driver bindings (full reference: [`docs/guides/keymap.md`](docs/guides/keymap.md)):

- `h j k l` motions; `0` / `$` line bounds; `w` / `b` words; `gg` / `G` file bounds
- `m<letter>` set mark; `'<letter>` jump to mark (per-buffer a-z + global A-Z)
- `i` / `a` / `A` enter INSERT; `Esc` exits; `x` deletes; `u` / `Ctrl-r` undo/redo; `.` repeat
- `v` / `V` visual + `y` / `d` yank/delete
- `/` / `?` search; `n` / `N` repeat; `*` / `#` word-search
- `:e <file>` open; `:ls` / `:bn` / `:bp` / `:b N` switch buffers; `:sp` / `:vsp` split;
  `Ctrl-w h/j/k/l` window navigation
- `:w` / `:wq` / `:q` / `:q!` save and quit
- `gd` / `gr` LSP nav (when cyim-lsp is folded in); `:lsp-status`, `:lsp-restart`,
  `:lsp-goto-def`, `:lsp-find-refs`

## LSP integration

cyim ships [cyim-lsp 1.5.0](https://github.com/MacCracken/cyim-lsp) folded
in via the sandhi pattern. With `cyrius-lsp` on PATH (the cyrius toolchain installs
it at `~/.cyrius/bin/cyrius-lsp`), opening a `.cyr` file lazily spawns the server
and surfaces:

- **Server-pushed diagnostics** — counts in the status segment (`E:N W:M I:K H:L`)
  + inline render via cyim's `diagnostic_provider` plugin hook
- **`gd`** — goto-definition. Same-file: cursor moves; cross-file: file loads + cursor
  jumps in the new buffer
- **`gr`** — find-references. Pops a quickfix picker; `j` / `k` navigate, `Enter` jumps
  to the selected reference, `Esc` / `q` dismiss
- **`:lsp-restart`**, **`:lsp-status`** — server lifecycle
- **`:lsp-goto-def`**, **`:lsp-find-refs`** — same as `gd` / `gr`, ex-command form

## Plugin system

Plugins are **AOT-compiled Cyrius bundles** folded into the binary at build time
via the sandhi pattern (the same pattern vyakarana and niyama use). No `dlopen`,
no eval, no runtime sandbox. Plugins extend cyim's
[6-hook ABI](docs/adr/0004-plugin-abi-freeze.md)
(post_save / post_change / status_segment / diagnostic_provider / normal_key /
ex_command) and three additive 1.4–1.5 extensions (prefix-keymap, buf_load_file,
list_display). Built-ins win on conflict per
[ADR 0003 §3](docs/adr/0003-cyrius-plugin-system.md).

ABI **frozen** at v1.3.6; 1.x-stable. Live consumers:

- [`cyim-lsp`](https://github.com/MacCracken/cyim-lsp) — LSP client
- [`src/plugins/trailing_ws.cyr`](src/plugins/trailing_ws.cyr) — inline plugin (proves the ABI end-to-end)

Architecture: [`docs/architecture/001-plugin-system.md`](docs/architecture/001-plugin-system.md).

## Agent-drive (no TTY required)

Same dispatch chain humans use, but piped from stdin / argv:

```sh
cyim --headless [<file>]                              # keystroke stream over stdin
cyim --write <file>                                   # replace <file> with stdin
cyim --replace <old> <new> <file>                     # substitute first; OLD must be unique
cyim --replace-all <old> <new> <file>                 # substitute every occurrence
cyim --replace-files <old-file> <new-file> <file>     # OLD/NEW from file contents
cyim --replace-files-all <old-file> <new-file> <file> # same, every occurrence
cyim --grep <pattern> <file>                          # FILE:N:LINE per hit
cyim --grepfiles <pattern> <file...>                  # multi-file grep
cyim --batch <file>                                   # NUL-separated OLD/NEW pairs from stdin
```

Modifiers (parsed in any order between the verb and its positional args):

| Modifier | Applies to | Effect |
|---|---|---|
| `--wc[=l\|=long]` | `--write`, `--replace[-all]`, `--batch` | Print `wc(1)` for the resulting file on success |
| `--expect=<pat>` / `--expect-not=<pat>` | `--write`, `--batch` | Post-save shape assertion (exit **6** on mismatch) |
| `--expect-N=<n>` / `--expect-1` | `--replace[-all]` | Pre-substitution count assertion |
| `--all` | `--batch` | Apply each pair via `--replace-all` semantics |
| `--context=<n>` | `--grep`, `--grepfiles` | `grep -C N` shape with overlap-merge + `--` separators |
| `--regex=<flavor>` | `--grep`, `--grepfiles`, `--replace[-all]`, `--replace-files[-all]` | Treat pattern as regex; flavor: `ere` / `bre` / `re2` / `pcre` / `vim` / `fuzzy` |
| `--fuzzy-edits=<n>` | (any verb with `--regex=fuzzy`) | Max edit distance (Levenshtein) |

Exit codes (verb-disambiguated where noted):

| Code | Meaning |
|------|---------|
| 0 | Success (or, for `--grep[files]`, ≥1 match) |
| 1 | Save failed (`--write`/`--replace`) \| no match (`--grep[files]`) |
| 2 | Bad CLI args |
| 3 | File not found |
| 4 | OLD not found in FILE (`--replace[-all]`) |
| 5 | OLD non-unique under `--replace` |
| 6 | Assertion failed (`--expect`/`--expect-not`/`--expect-N`) |

Full guide: [`docs/guides/usage.md`](docs/guides/usage.md).
Keymap reference: [`docs/guides/keymap.md`](docs/guides/keymap.md).
Configuration: [`docs/guides/cyimrc.md`](docs/guides/cyimrc.md).

## Design Principles

- **Modal first.** Normal/insert/command/visual — VIM grammar, learned once, kept forever.
- **Zero attack surface.** No embedded scripting language. Configuration is data, not code.
- **Refusal as architecture.** Inherits AGNOS [§0 Refusal](https://github.com/MacCracken/agnosticos/blob/main/docs/design-patterns.md) — every layer must justify itself with a living reason.
- **Reference, don't mimic.** Vim is the reference. cyim is what a modal editor looks like designed today, in a sovereign language, with no carried legacy shape.
- **Two consumer classes, one grammar.** Humans drive cyim at a TTY. AI agents drive cyim programmatically (`--headless` for full keymap drive; `--write`/`--replace[-all]`/`--grep[files]`/`--batch` for one-shot ops). The modal surface is the API for both.
- **Plugins as bundles, not as scripts.** AOT-compiled Cyrius distfiles fold into the binary at build time via the sandhi pattern. No `dlopen`, no eval. The editor's surface is its binary; the binary is auditable end-to-end.

## License

GPL-3.0-only
