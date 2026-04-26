# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-04-25 (v0.1.0 scaffold)*

---

## Version

- **VERSION**: `0.1.0`
- **Cyrius toolchain pin**: `5.7.1` (in `cyrius.cyml [package].cyrius`)
- **Last release**: `0.1.0` — initial scaffold, 2026-04-25

## Binary

- `build/cyim` — DCE build size: **273,912 B** (M6 closer; M5 was 262,504 B; M4 was 256,344 B; M3 was 226,064 B; M2 was 162,184 B; M1 was 101,560 B; M0 stub was 57,728 B). Source: ~4 100 LOC editor + ~5 000 LOC tests/fuzz/grammars. ~60 source bytes per binary byte.

## Tests

- Test suites: M0 + M1 (8) + M2 (4) + M3 (2) + M4 (4)
- Assertion count: 838 (M1 350; M2 +117 = 467; M3 +192 = 659; M4 +153 = 812; M6 +26 = 838)
- Integration smoke: `tests/integration_smoke.py` — 14 PTY-driven end-to-end checks (5 M1 + 2 M2 + 4 M3 + 3 M4)
- Fuzz harnesses: 3 (`fuzz/buffer.fcyr` + `fuzz/tokenizer.fcyr` + `fuzz/driver.fcyr`); all pass under `cyrius fuzz`
- Performance benches: 9 (`tests/perf.bcyr`); baseline + M6 cache-hit bench in [`BENCHMARKS.md`](../../BENCHMARKS.md)
- Security audit: initial pass at [`docs/audit/2026-04-25-security-audit.md`](../audit/2026-04-25-security-audit.md) — F-1 / F-3 / F-4 closed in M6; F-2 / F-5 / F-6 remain documented for M7 / post-v1.0
- Cleanliness: `cyrius lint` 0 correctness warnings (~30 advisory line-length only); `cyrius fmt --check` clean across all `src/*.cyr`

## Active Milestone

- **M0** — scaffold. *Done.*
- **M1** — gap-buffer + raw-mode TTY + modal dispatch. *Done.*
- **M2** — syntax highlighting via `vyakarana`. *Done.*
- **M3** — multi-buffer + splits + window navigation. *Done.*
- **M4** — search, undo, visual, `.` repeat, `:set` + `.cyimrc`. *Done.*
- **M5** — polish: docs, perf benchmarks, fuzz, receipts. *Done.*
- **M6** — P(-1) hardening: tokenbuf cache, audit-finding fixes (F-1/F-3/F-4), cleanliness gate, refactor pass. *Done.* All 6 bites landed.
- **M7 (next)** — Security audit: external 0-day / CVE corpus review (vim, neovim, terminal apps), full security-hardening checklist re-walk, audit report; remaining CRITICAL / HIGH closed before v1.0. F-2 / F-5 / F-6 triaged here.
- **v1.0** — release; downstream consumers take over.

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
