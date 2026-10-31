# cyim — State Snapshot

> **Volatile.** This file is the **live state** of the project — current version, sizes, test counts, in-flight slot, consumer build status. Refreshed every release. Don't put durable rules here (those live in [`CLAUDE.md`](../../CLAUDE.md)); don't put release history here (that lives in [`CHANGELOG.md`](../../CHANGELOG.md)); don't put sequencing here (that lives in [`roadmap.md`](roadmap.md)).

*Last bumped: 2026-10-31 (v1.11.2 — **closeout for the 1.11.x line**, the first since 1.9.3. The code review found six LOW defects: five are fixed with tests (arrows ignored the mode and a pending prefix, the picker overlay broke on short terminals, the status row was not width-bounded, a per-frame buffer leak, a possible `epoll_wait` spin), and rxvt's `$`-final keys are filed as BUG-008. The `--agnos` / `--aarch64` builds and the qemu-aarch64 suite are now CI gates.)*

---

## Version

- **VERSION**: `1.11.2`
- **Cyrius toolchain pin**: `6.7.18`
- **Last release**: `1.11.2` — **Patch; the 1.11.x closeout.** 2026-10-31. Full entry in CHANGELOG; audit at [`docs/audit/2026-10-31-1.11x-closeout.md`](../audit/2026-10-31-1.11x-closeout.md).

## Binary

- **`build/cyim`** (CYRIUS_DCE=1): **1,061,696 B**
  - Last delta: **+4,136 B** vs 1.11.1 (1,057,560 B). aarch64 grew only 40 B, so the x86_64 image appears to have crossed a 4 KiB boundary.
  - **`build/cyim_agnos`**: 1,037,616 B — static x86-64 ELF64 (1.11.1: 1,033,480 B). Runs full-screen on the real agnos kernel under QEMU (`scripts/agnos-fullscreen-test.py` PASS at 1.11.2). The `--agnos` build is a CI gate since 1.11.2.
  - **`build/cyim_aarch64`**: 1,483,480 B — ARM aarch64 ELF64 (1.11.1: 1,483,440 B). The whole suite runs under qemu-aarch64 (`cyrius test --aarch64`, 1363 / 0), a CI gate since 1.11.2.
  - Per-release size history is in CHANGELOG's per-version Binary sections.

## Tests

- **`cyrius test`**: **23 suites, 1363 assertions** PASS, 0 failures, **0 warnings** *(measured at 1.11.2. +25: `tests/feed.tcyr` 52 → 66 for arrow dispatch, `tests/render.tcyr` 84 → 95 for the picker height, the status-row width and a `/dev/null`-based winsize fallback. The run also counts `src/test.cyr`, the `[build] test` entry, as a 24th unit; it asserts nothing)*
- **`cyrius test --aarch64`** (qemu-aarch64): the same 23 suites / 1363 / 0. A CI step (`cross-targets`) since 1.11.2.
- **`cyrius fuzz`**: **5 harnesses**, all PASS — `fuzz/{buffer,driver,tokenizer,feed}.fcyr` + `tests/cyim.fcyr`. New at 1.11.0: `fuzz/feed.fcyr`, the key-sequence decoder's **split-independence** property (300 random 64-byte streams; random 1–9-byte chunks must decode exactly as the whole stream does). The 1.10.1 decoder fails it.
- **CLI smoke** (`tests/cli_smoke.sh`): **128 PASS** (unchanged since 1.9.x).
- **Integration smoke** (`tests/integration_smoke.py`): all PASS, **58 PASS lines** (+9 at 1.11.0: file-name escape, C1 in content, Delete in INSERT, ESC timeout ×2, language server dying mid-session, stdout to a dead pipe, two `--headless` split-read inputs). ⚠ Its new cases reset SIGPIPE to SIG_DFL in the child — Python starts with SIGPIPE ignored and an exec'd child inherits that, which hides exactly the SIGPIPE deaths those cases look for. The older `drive()` cases still run with it ignored. DCE parity build re-runs it green.
- **LSP smoke** (`tests/smcyr/lsp_fold.smcyr`): **13 passed, 0 failed**. A CI gate since 1.9.1.
- **agnos full-screen** (`scripts/agnos-fullscreen-test.py`, out-of-band, needs agnos / gnoboot / agnoshi builds): PASS at 1.11.2 — `ZED` typed through kbscan#42 and saved; the framebuffer screendump shows the full-screen render.
- **`cyrius audit`**: fmt / lint / tests / bench stages clean; exits 1 on its docs stage — **48 undocumented public fns, all in `tests/` and `fuzz/`** (test helpers and `main`s), the same 48 as 1.11.0. Since cyrius 6.7.12 its fmt stage takes `cyrfmt --check`'s verdict, so the two no longer disagree.
- **Performance benches** (`tests/perf.bcyr`): run clean; **not re-baselined at 1.11.2 either** — the host was shared (load average ≈ 20 on 16 cores; every workload about 2× its 1.9.3 time). Three alternating rounds against 1.10.1 under the same load: highlighting −10 % (vyakarana 2.10.0), worst-case search +5.5 % (unchanged cyim code — the toolchain), the rest within noise. See CHANGELOG 1.11.2 § Benchmarks. A quiet-host baseline is a roadmap maintenance item; the last absolute baseline is [`BENCHMARKS.md`](../../BENCHMARKS.md)'s 1.8.6 table.
- **Documentation**: `cyrius doc --check` reports **0 undocumented public fns** across `src/` + `src/plugins/`.
- **Cleanliness**: `cyrius lint` 0 warnings and **0 untracked deferrals** across `src/`, `src/plugins/`, `tests/` and `fuzz/`. `cyrfmt --check` clean. Dead-code floor 27, every symbol with a caller; 0 unused globals.
- **Security**: most recent pass is the [1.11.x closeout](../audit/2026-10-31-1.11x-closeout.md) — six LOW defects, five fixed in the cut, one filed (BUG-008); none memory-unsafe. Residuals carried from the [1.11.0 release audit](../audit/2026-10-12-1.11.0-audit.md): the LSP child inherits blocked SIGWINCH / SIGPIPE (upstream fix), and the [1.8.x hardening](../audit/2026-08-23-1.8x-hardening.md)'s R-1a (xattrs / ACLs across the atomic save). 0day-corpus survey in [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md); trust-model ADR at [`docs/adr/0001-trust-model.md`](../adr/0001-trust-model.md).

## CI / Release

- **Toolchain install**: both `.github/workflows/{ci,release}.yml` delegate to the upstream `scripts/install.sh`, fetched from the **tag** named by `[package].cyrius` (immutable ref; the script carries the release signing pubkey for that version), and assert `~/.cyrius/versions/<pin>/lib` exists right after.
  - ⚠ Do **not** reintroduce a hand-rolled `curl -sLO` of the release tarball. Beyond the layout, install.sh is what verifies the `.sha256` and the signature.
- **CI gates** (`build-and-test` job): install → verify layout → deps → fmt → build → ELF → lint (`src/` + `src/plugins/`) → test → fuzz → bench → CLI smoke → LSP smoke → PTY integration smoke → DCE parity. Plus independent `cross-targets` (new at 1.11.2: `--agnos` and `--aarch64` DCE builds, then `cyrius test --aarch64` under qemu-user — about 15 s locally), `security` and `docs` jobs. New suites and harnesses are auto-discovered (`tests/*.tcyr`, `fuzz/*.fcyr`).
  - The fmt gate is a **per-file loop on purpose**: `cyrfmt` reads only `argv[1]` and silently ignores the rest.
- **Not gated**: `cyrius audit` (its docs step counts test helpers) and the agnos full-screen run (it needs agnos, gnoboot and agnoshi builds).

## Cycle in flight

**Current cycle: 1.11.x — closed at 1.11.2.** Next: 1.12.x (agent verbs), per [`roadmap.md`](roadmap.md), which lists every open item by version line through 2.x.x.

**Open bugs: two**, both planned for 1.13.0 and both a decision before code. BUG-007: SS3 keys (`ESC O P`..: F1–F4 on xterm-style terminals) arrive as Esc, `O` (open line above) and a letter. BUG-008: rxvt's `$`-final keys (`ESC [ 3 $`) leave the CSI open and swallow the next key.

⚠ ADR 0005's **live obligation** stands: every new `.cyimrc` key must be classified local-overridable or home-only when it is added. Every open or deferred item is in [`roadmap.md`](roadmap.md), organized by version line.

**Save semantics** are [ADR 0006](../adr/0006-atomic-save.md): atomic by default, in-place for six enumerated file shapes. `buf_save_was_atomic()` reports which path the last save took.

## Consumers

| Consumer | Status | Notes |
|---|---|---|
| `agnoshi` | Planned | Wires when the AI shell embeds cyim |
| `aethersafha` | Planned | Wires when the Wayland compositor hosts cyim |
| `daimon`-orchestrated agents | Surface ready (since v1.2.0) | Drive cyim via `--headless` (full keymap) or one-shot CLI verbs (`--write`, `--replace[-all]`, `--replace-files[-all]`, `--grep[files]`, `--batch`) with composable modifiers (`--expect[/-not/-N/-1]`, `--all`, `--context=`, `--regex=`, `--wc[=l]`, `--fuzzy-edits=`). `daimon` integrates when ready. |

## Dependencies

- **stdlib (auto-prepended)**: `syscalls`, `alloc`, `fmt`, `io`, `fs`, `str`, `string`, `vec`, `args`, `hashmap`, `assert`, `bench`, `regex`, `unicode/{_decode,categories,_categories_data,casefold,_casefold_data,normalize,_normalize_data}`.
- **stdlib (sandhi-pattern, explicit-include)**: `lib/niyama.cyr` (folded at cyrius 5.9.0 per the opt-in pattern; provides `niyama_{bre,re2,pcre,fuzzy,vim}_*`). Since 1.11.0 not vendored — resolved from the pinned snapshot, so it is always the pin's own.
- **External Cyrius deps**:
  - `vyakarana` **2.10.0** — token-level grammar/tokenizer; **49** bundled grammars, all routed by `src/lang.cyr` (extension + basename probes) except `asm_aarch64`. `grammars/*.cyml` is a copy of the tag's `grammars/`, re-synced at every bump: the editor loads grammars from disk by absolute path, never from the bundle's embedded copies, so a stale file ships silently (`tests/lang.tcyr` loads each through that path, but cannot tell a stale file from a current one). ⚠ Routing a language is only half of it: `src/highlight.cyr`'s `hl_grammar_name` table must also name the grammar, because `highlight_init()` suppresses vyakarana's own `bootstrap_grammars()`; `tests/lang.tcyr` asserts both directions. `.asm` stays on `asm_x86_64` although vyakarana's `nasm` also claims it.
  - `cyim-lsp` **1.5.4** — LSP client plugin; consumed via `lib/cyim-lsp.cyr` distfile, glue in `src/plugins/lsp_glue.cyr`. Self-contained bundle, own pin 6.6.2; 1.5.4 is a toolchain-pin release. Under `--agnos` the spawn half is compiled out and cyim registers no LSP hooks. ⚠ Two upstream asks recorded in [`roadmap.md` § Dependency notes](roadmap.md): its spawn (`lsp_proc_spawn`) does raw `fork` / `execve` without resetting the child's signal mask, so the server inherits cyim's blocked SIGWINCH and SIGPIPE; and `lsp_doc_lazy_start` retries the spawn on EVERY edit while the server is missing or dying (10 edits → 10 spawns, measured).
  - `darshana` **1.7.0** — TTY / raw-mode primitives extracted from cyim's `src/tty.cyr` donor source; cyim is primary donor and first consumer. API frozen since 1.0.0 (darshana ADR 0003), additive since; its Linux floor is cyrius ≥ 6.7.2, its AGNOS arm's ≥ 6.7.11. cyim uses: termios (`tty_raw`, `tty_cooked`), screen (`tty_alt_enter` / `_leave`, `tty_clear`, `tty_cursor_home`, `tty_move`), `tty_winsize`, the signalfd pair plus `tty_read_signal` (resize watch) and `TTY_SIGMASK_PIPE` (SIGPIPE guard), `tty_sanitize_buf` (untrusted text outside the buffer), and the SGR composers `tty_fg_256_buf` / `tty_sgr_buf` / `tty_sgr_reset_buf` / `tty_sgr` / `tty_sgr_reset`, plus `tty_dec_buf`. Teardown follows darshana ADR 0002 as amended at 1.1.4 (cooked first, signalfds last). What cyim deliberately does not adopt, and why, is in [`roadmap.md` § Dependency notes](roadmap.md).

## Verification Hosts

- **x86_64 Linux** — primary dev host; verified continuously.
- **aarch64 Linux** — the full suite runs under qemu-aarch64 in CI since 1.11.2 (`cyrius test --aarch64`, 1363 / 0). Not run on real hardware (Pi) this cut.
- **Apple Silicon Mach-O** — out-of-band; not blocking.
- **Windows PE32+** — out of scope (TTY editor; Linux/macOS/BSD targets only).

## Bootstrap Chain

`cyrius 6.7.18` → `lib/`, **generated** by `rm -rf lib/ && cyrius deps` from `[deps].stdlib` plus the three `[deps.*]` bundles and their sidecars (46 files; `cyrius deps --locked` verifies it against `cyrius.lock`). `lib/niyama.cyr` is not vendored — `src/main.cyr`'s explicit `include "lib/niyama.cyr"` resolves to the pinned snapshot (`~/.cyrius/versions/6.7.18/lib`) → `src/main.cyr` → `build/cyim`.
