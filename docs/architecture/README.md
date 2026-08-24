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
| [004](004-reading-the-dce-report.md) | A DCE report is not a dead-code list | ~514 symbols are unreachable from `main`, 24 of them cyim's own, and deleting any would be wrong: frozen ABI, test-only introspection, documented-deferred config. The question worth asking is whether each has a caller *somewhere* — and where real dead code turns up instead |

## Related

- [`../adr/`](../adr/) — decisions and their trade-offs
- [`../audit/`](../audit/) — audits; notes 002 and 003 were both written
  out of audit findings that turned out to be architectural rather than
  local
