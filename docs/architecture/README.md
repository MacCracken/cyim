# Architecture notes

*What can't I derive from the code alone?* Non-obvious invariants,
constraints, and quirks — the things that are true of cyim but are not
visible from reading any single file.

An [ADR](../adr/) says *why we chose this*. An architecture note says
*what will bite you if you don't know it*.

**Never renumber.** Numbers are `NNN-kebab-case.md`, allocated in order.

## Items

| # | Note | The thing you can't derive |
|---|---|---|
| [001](001-plugin-system.md) | Plugin system | How the six hooks, the registry, and the frozen ABI fit together across `src/plugin.cyr` and the consumer glue |
| [002](002-routing-and-loading-are-two-tables.md) | Routing and loading are two tables that must agree | `src/lang.cyr` decides which languages are *routed*; `src/highlight.cyr` decides which grammars are *loaded*, and it suppresses vyakarana's fallback while doing so. Their silent divergence cost 34 languages their highlighting for six minor versions |
| [003](003-render-is-byte-oriented.md) | The renderer is byte-oriented, not codepoint-oriented | One buffer byte draws as one column. C1 pass-through, no double-width handling, and no combining-character handling are all the same decision |

## Related

- [`../adr/`](../adr/) — decisions and their trade-offs
- [`../audit/`](../audit/) — audits; notes 002 and 003 were both written
  out of audit findings that turned out to be architectural rather than
  local
