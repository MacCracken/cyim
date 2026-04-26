# cyim — State Snapshot

> **Volatile.** This file is the live state of the project — current version, sizes, in-flight slot, consumer build status. Bumped every release (ideally by the release post-hook). Don't put durable rules here — those live in [`CLAUDE.md`](../../CLAUDE.md).

*Last bumped: 2026-04-25 (v0.1.0 scaffold)*

---

## Version

- **VERSION**: `0.1.0`
- **Cyrius toolchain pin**: `5.7.1` (in `cyrius.cyml [package].cyrius`)
- **Last release**: `0.1.0` — initial scaffold, 2026-04-25

## Binary

- `build/cyim` — DCE build size: **101,560 B** (M1 closer; M0 stub was 57,728 B)

## Tests

- Test suites: `src/test.cyr` (scaffold smoke) + `tests/cyim.tcyr` (M0 smoke) + `tests/buffer.tcyr` (M1 bite 1: gap-buffer invariants) + `tests/roundtrip.tcyr` (M1 bite 2: file load/save round-trip) + `tests/tty.tcyr` (M1 bite 3: termios flag-mask + ANSI helpers) + `tests/dispatch.tcyr` (M1 bite 4: modal dispatch + headless drive) + `tests/motion.tcyr` (M1 bite 5: vi motions over the gap-buffer) + `tests/insert.tcyr` (M1 bite 6: INSERT mode + `editor_run` headless drive) + `tests/command.tcyr` (M1 bite 7: COMMAND mode — `:q` `:q!` `:w` `:wq` `:e`)
- Assertion count: 350 (47 buffer + 23 round-trip + 37 tty + 57 dispatch + 87 motion + 39 insert + 58 command + 2 smoke)
- Integration smoke: `tests/integration_smoke.py` — 5 PTY-driven end-to-end checks against the cyim binary
- Fuzz harnesses: planned at M2 (gap-buffer + tokenizer integration)
- Benchmarks: planned at M5 (closeout pass)

## Active Milestone

- **M0** — scaffold. *Done.*
- **M1** — gap-buffer + raw-mode TTY + modal dispatch. *Done.* All 8 bites landed: gap-buffer, file round-trip, raw-mode TTY, modal dispatch, vi motions, INSERT mode, COMMAND mode, integration smoke.
- **M2 (next)** — syntax highlighting via `vyakarana`. See [`roadmap.md`](roadmap.md).

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
