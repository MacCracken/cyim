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

**0.1.0 — scaffold.** Boots, prints, exits. M0–M3 roadmap below.

## Roadmap

| Milestone | Scope |
|-----------|-------|
| **M0** | Project scaffold — *current* |
| **M1** | Gap-buffer + raw-mode TTY + modal dispatch (normal/insert/command) |
| **M2** | Syntax highlighting via [`vyakarana`](https://github.com/MacCracken/vyakarana) tokenizer |
| **M3** | Multi-buffer, splits, file I/O, `:w`/`:q`/`:e` baseline |
| **M4** | Search (`/`), undo tree, `.cyimrc` config |

## Why "cyim"

`cy` (Cyrius) + `im` (the editor lineage `vi → vim → nvim → cyim`).
A name in the tradition, written in the language of the library.

## Build

```sh
cyrius deps                            # resolve stdlib deps
cyrius build src/main.cyr build/cyim   # compile
cyrius test                            # run tests/*.tcyr
```

## Design Principles

- **Modal first.** Normal/insert/command/visual — VIM grammar, learned once, kept forever.
- **Zero attack surface.** No embedded scripting language. Configuration is data, not code.
- **Refusal as architecture.** Inherits AGNOS [§0 Refusal](https://github.com/MacCracken/agnosticos/blob/main/docs/design-patterns.md) — every layer must justify itself with a living reason.
- **Reference, don't mimic.** Vim is the reference. cyim is what a modal editor looks like designed today, in a sovereign language, with no carried legacy shape.

## License

GPL-3.0-only
