# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-04-25 (v0.1.0 scaffold)*

---

## Version

- **VERSION**: `0.1.0`
- **Cyrius toolchain pin**: `5.7.1` (in `cyrius.cyml [package].cyrius`)
- **Last release**: `0.1.0` — initial scaffold, 2026-04-25

## Binary

- `build/cyim` — DCE build size: **274,656 B** (M7 closer; M6 was 273,912 B; M5 was 262,504 B; M4 was 256,344 B; M3 was 226,064 B; M2 was 162,184 B; M1 was 101,560 B; M0 stub was 57,728 B). Source: ~4 200 LOC editor + ~5 100 LOC tests/fuzz/grammars. ~60 source bytes per binary byte.

## Tests

- Test suites: M0 + M1 (8) + M2 (4) + M3 (2) + M4 (4)
- Assertion count: 847 (M1 350; M2 +117 = 467; M3 +192 = 659; M4 +153 = 812; M6 +26 = 838; M7 +9 = 847)
- Integration smoke: `tests/integration_smoke.py` — 14 PTY-driven end-to-end checks (5 M1 + 2 M2 + 4 M3 + 3 M4)
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
- **M7** — Security audit: 0day corpus, checklist re-walk, F-2 fix, trust-model ADR. *Done.* M7.5 (WebFetch CVE verification) queued as a follow-up — class taxonomy and findings stand independent of specific CVE numbers; not v1.0-blocking.
- **v1.0 (next)** — release. CLAUDE.md's CRITICAL/HIGH-must-close gate satisfied. Closeout pass + version bump + tag.

## Consumers

| Consumer | Status | Notes |
|----------|--------|-------|
| `agnoshi` | Planned | Wires at M3 (multi-buffer ready) |
| `aethersafha` | Planned | Wires at M3 (Wayland terminal hosts cyim) |
| `daimon`-orchestrated agents | Planned | Headless / agent-drive mode is post-v1.0 demand-gated; the keymap dispatch is the API for both human + agent drivers |

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
