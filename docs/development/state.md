# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-04-25 (v0.1.0 scaffold)*

---

## Version

- **VERSION**: `0.1.0`
- **Cyrius toolchain pin**: `5.7.1` (in `cyrius.cyml [package].cyrius`)
- **Last release**: `0.1.0` — initial scaffold, 2026-04-25

## Binary

- `build/cyim` — DCE build size: **162,184 B** (M2 closer; M1 was 101,560 B; M0 stub was 57,728 B)

## Tests

- Test suites: M0 + M1 (8 suites) + M2 (`tests/highlight.tcyr` + `tests/lang.tcyr` + `tests/render.tcyr` + `tests/cyimrc.tcyr`)
- Assertion count: 467 (M1: 350; M2: +31 highlight + 37 lang + 27 render + 22 cyimrc = 117)
- Integration smoke: `tests/integration_smoke.py` — 7 PTY-driven end-to-end checks (5 from M1 bite 8 + 2 M2 ANSI-output checks)
- Fuzz harnesses: planned (gap-buffer + tokenizer integration)
- Benchmarks: planned at M5 (closeout pass)

## Active Milestone

- **M0** — scaffold. *Done.*
- **M1** — gap-buffer + raw-mode TTY + modal dispatch. *Done.* All 8 bites landed.
- **M2** — syntax highlighting via `vyakarana`. *Done.* All 6 bites landed: vyakarana dep + grammars, highlight module, lang detection, palette + ANSI render integration, main.cyr wiring + integration smoke, `.cyimrc` palette overrides.
- **M3 (next)** — multi-buffer + splits + file I/O baseline. See [`roadmap.md`](roadmap.md).

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
