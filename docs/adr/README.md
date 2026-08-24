# Architecture Decision Records

*Why did we choose X over Y?* Each ADR records a decision, the context
that forced it, and what it costs — so a future cut can weigh the
trade-off again instead of rediscovering it.

**Never renumber.** A superseded ADR stays in place with its status
changed and a pointer to what replaced it.

New records use [`template.md`](template.md).

## Index

| # | Title | Status | Decides |
|---|---|---|---|
| [0001](0001-trust-model.md) | Trust model: interactive local user | Accepted *(scope clarified 2026-08-23)* | cyim is not a privilege boundary: no path validation, no config sandbox, no setuid mode. Scoped to input the user actually supplies — see 0005 |
| [0002](0002-regex-extensibility-shape.md) | Regex extensibility shape | Accepted | How additional regex flavours attach to the search surface without a plugin sandbox |
| [0003](0003-cyrius-plugin-system.md) | The Cyrius plugin system | Accepted | Plugins compose through the AGNOS library at build time, not through an in-binary sandbox; ABI to be prototyped by the LSP client rather than designed in vacuum |
| [0004](0004-plugin-abi-freeze.md) | Plugin ABI freeze (v1.3.6) | Accepted *(additive extensions v1.4.2, v1.5.0)* | The 1.x plugin ABI is frozen; additions allowed, removals and shape changes are not |
| [0005](0005-cyimrc-cwd-trust-boundary.md) | `.cyimrc` is loaded from the cwd, and that is a trust boundary 0001 does not cover | Accepted *(decided 2026-08-23)* | Config lives in `$XDG_CONFIG_HOME/cyim/cyimrc`; a project-local `./.cyimrc` overrides it, key by key. Every new key must be classified local-overridable or home-only |
| [0006](0006-atomic-save.md) | Saving is atomic by default, with an enumerated in-place fallback | Accepted | Sibling temp + `rename` so a failed write cannot destroy the file; six named conditions where in-place is correct instead. Amends 0001 § 3 |

## Status values

- **Proposed** — the decision is written down but not made. Options and
  their costs are recorded; nothing in the tree depends on the outcome yet.
- **Accepted** — in force. Code and docs may cite it as the authority.
- **Superseded** — replaced; the record stays, with a pointer forward.

## Related

- [`../architecture/`](../architecture/) — non-obvious invariants and
  quirks. An ADR says *why we chose this*; an architecture note says
  *what you cannot derive from the code alone*.
- [`../audit/`](../audit/) — security and closeout audits. Audits
  routinely surface ADR gaps; ADR 0005 came out of the 1.8.x pass.
