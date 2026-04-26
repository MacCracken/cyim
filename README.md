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

**1.1.0 — released.** M0–M7 landed at v1.0.0 (2026-04-25); v1.0.1 added
the agent-drive CLI surface; v1.0.2 added the `--wc` modifier and fixed
BUG-001 (silent argv truncation > 4 KB); v1.1.0 adds `--grep` plus
`--expect` / `--expect-not` / `--expect-N` / `--expect-1` modifiers
that close the structural-invariant gap (post-write shape assertion,
pre-substitution count assertion — no more `cyim … && rg -q …` chains).

Live state in [`docs/development/state.md`](docs/development/state.md);
post-v1.0 demand-gated work in [`docs/development/roadmap.md`](docs/development/roadmap.md).

## Why "cyim"

`cy` (Cyrius) + `im` (the editor lineage `vi → vim → nvim → cyim`).
A name in the tradition, written in the language of the library.

## Build

```sh
cyrius deps                              # resolve stdlib deps
cyrius build src/main.cyr build/cyim     # compile
CYRIUS_DCE=1 cyrius build ...            # dead-code-eliminated release build
cyrius test                              # run tests/*.tcyr + src/test.cyr
cyrius lint src/*.cyr                    # static checks
cyrius audit                             # full check: self-host, test, fmt, lint
```

## CLI surface

Interactive editor:

```sh
cyim                                       # open scratch buffer
cyim <file>                                # open <file>
cyim --version
cyim --help
cyim --probe                               # TTY round-trip diagnostic
```

Agent-drive (no TTY required — same dispatch chain humans use, but
piped from stdin / argv):

```sh
cyim --headless [<file>]                   # keystroke stream over stdin
cyim --write <file>                        # replace <file> with stdin
cyim --replace <old> <new> <file>          # substitute first; OLD must be unique
cyim --replace-all <old> <new> <file>      # substitute every occurrence
cyim --grep <pattern> <file>               # read-only; emit FILE:N:LINE per hit
```

Modifiers (parsed in any order between the verb and its positional args):

| Modifier | Applies to | Effect |
|---|---|---|
| `--wc[=l\|=long]` | `--write`, `--replace[-all]` | Print `wc(1)` output for the resulting file on success |
| `--expect=<pat>` | `--write` | Post-save assertion — exit **6** if `<pat>` is missing from the result |
| `--expect-not=<pat>` | `--write` | Post-save assertion — exit **6** if `<pat>` appears in the result |
| `--expect-N=<n>` | `--replace[-all]` | Pre-substitution assertion — exit **6** if `OLD` doesn't occur exactly `<n>` times |
| `--expect-1` | `--replace[-all]` | Sugar for `--expect-N=1` |

Exit codes (verb-disambiguated where noted):

| Code | Meaning |
|------|---------|
| 0 | Success (or, for `--grep`, ≥1 match) |
| 1 | Save failed (`--write`/`--replace`) \| no match (`--grep`) |
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
- **Two consumer classes, one grammar.** Humans drive cyim at a TTY. AI agents drive cyim programmatically (`--headless` for full keymap drive; `--write`/`--replace[-all]`/`--grep` for one-shot ops). The modal surface is the API for both.

## License

GPL-3.0-only
