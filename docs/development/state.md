# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-04-26 (v1.1.0 — `--grep`, `--expect`, `--expect-N` agent-drive primitives)*

---

## Version

- **VERSION**: `1.1.0`
- **Cyrius toolchain pin**: `5.7.1` (in `cyrius.cyml [package].cyrius`)
- **Last release**: `1.1.0` — `--grep` + `--expect`/`--expect-not` + `--expect-N`/`--expect-1` agent-drive primitives, 2026-04-26
- **Prior release**: `1.0.2` — `--wc` modifier + BUG-001 fix, 2026-04-26

## Binary

- `build/cyim` — DCE build size: **293,192 B** (v1.1.0 added `run_grep` + `_cli_argprefix` + `_cli_atoi_nn` + `_cli_write_buf_range` to `src/cli.cyr` and the per-verb modifier-consume loop to `src/main.cyr`; v1.0.2 was 283,984 B; v1.0.0 was 274,656 B; M6 was 273,912 B; M5 was 262,504 B; M4 was 256,344 B; M3 was 226,064 B; M2 was 162,184 B; M1 was 101,560 B; M0 stub was 57,728 B).

## Tests

- Test suites: M0 + M1 (8) + M2 (4) + M3 (2) + M4 (4)
- Assertion count: 847 (M1 350; M2 +117 = 467; M3 +192 = 659; M4 +153 = 812; M6 +26 = 838; M7 +9 = 847)
- Integration smoke: `tests/integration_smoke.py` — 45 PASS assertions across PTY-driven + headless-subprocess sections: `--headless`, `--write`, `--replace`, `--replace-all`, `--grep`, `--write --expect[/-not]`, `--replace[-all] --expect-N/--expect-1`, multi-window cascade
- Fuzz harnesses: 3; all pass under `cyrius fuzz`
- Performance benches: 9; M5 baseline + M6 cache-hit win in [`BENCHMARKS.md`](../../BENCHMARKS.md)
- Security audit: initial pass [M5](../audit/2026-04-25-security-audit.md), second pass [M7](../audit/2026-04-25-m7-audit.md), 0day-corpus survey at [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md), trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md). **End-of-M7 triage: 0 CRITICAL / 0 HIGH / 0 MEDIUM**; 8 LOW findings all triaged with rationale.
- Cleanliness: `cyrius lint` 0 correctness warnings; `cyrius fmt --check` clean across all `src/*.cyr`

## Active Milestone

- **M0** — scaffold. *Done.*
- **M1** — gap-buffer + raw-mode TTY + modal dispatch. *Done.*
- **M2** — syntax highlighting via `vyakarana`. *Done.*
- **M3** — multi-buffer + splits + window navigation. *Done.*
- **M4** — search, undo, visual, `.` repeat, `:set` + `.cyimrc`. *Done.*
- **M5** — polish: docs, perf benchmarks, fuzz, receipts. *Done.*
- **M6** — P(-1) hardening: tokenbuf cache, F-1/F-3/F-4 closures, cleanliness gate, refactor pass. *Done.*
- **M7** — Security audit: 0day corpus, checklist re-walk, F-2 fix, trust-model ADR, M7.5 verification pass. *Done.* All CVE references in the corpus survey verified against primary sources.
- **v1.0** — release. *Done — 2026-04-25.*
- **v1.0.1** — agent-drive CLI surface: `--write`, `--replace`, `--replace-all` folded into the binary directly (src/cli.cyr). *Done — 2026-04-25.*
- **v1.0.2** — `--wc` modifier on agent-drive ops + BUG-001 fix (silent argv truncation > 4 KB). *Done — 2026-04-26.*
- **v1.1.0** — `--grep` (read-only line scan), `--expect`/`--expect-not` (post-write shape assertion on `--write`), `--expect-N`/`--expect-1` (pre-substitution count assertion on `--replace[-all]`). Closes the "tool boundary jump" — structural-invariant checks stay in one binary. *Done — 2026-04-26.*

## Post-v1.0

Demand-gated work now continues per [`roadmap.md`](roadmap.md)'s
post-v1.0 table. v1.0.1 closed the agent-drive ergonomics gap
(`--headless` + `--write` + `--replace` + `--replace-all` all
ship in the binary). v1.1.0 closes the structural-invariant
gap — `--grep` + `--expect[-not]` + `--expect-N`/`--expect-1`
let scripts assert "after this rewrite, X must / must not appear"
or "this substitution must hit exactly N times" without leaving
the binary. Remaining: system clipboard (via `aethersafha`),
LSP client (when cyrius-lsp stabilizes), terminal embed,
macros, etc.

## Consumers

| Consumer | Status | Notes |
|----------|--------|-------|
| `agnoshi` | Planned | Wires at M3 (multi-buffer ready) |
| `aethersafha` | Planned | Wires at M3 (Wayland terminal hosts cyim) |
| `daimon`-orchestrated agents | Surface ready (v1.1.0) | `cyim --headless` for full keymap drive; `cyim --write`/`--replace`/`--replace-all`/`--grep` for one-shot ops; `--expect[-not]` and `--expect-N`/`--expect-1` modifiers for in-line shape/count assertions. Daimon integration when that consumer is ready. |

## Dependencies

- **stdlib**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`
- **External Cyrius deps**: none through M1; `vyakarana` added at M2 for syntax highlighting

## Verification Hosts

- x86_64 Linux (primary dev) — verified at scaffold
- aarch64 Pi — pending M1 hardware test
- Apple Silicon Mach-O — pending M1 hardware test
- Windows PE32+ — out of scope (TTY editor; Linux/macOS/BSD targets only)

## Bootstrap Chain

`cyrius` (5.7.1) → vendored stdlib in `lib/` → `src/main.cyr` → `build/cyim`.
Zero external dependencies as of M0.
