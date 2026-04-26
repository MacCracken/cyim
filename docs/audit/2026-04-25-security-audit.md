# 2026-04-25 — cyim Security Audit (Initial)

## Scope

Initial audit pass over the cyim codebase as of v0.1.0 + M4 (812 .tcyr
assertions, 14 PTY end-to-end checks, DCE binary 256,344 B). Performed
during M5 polish to seed M7's deep-dive corpus and to catch the
obvious findings before going public.

This is *not* the full M7 security-audit milestone. M7 will pair the
external CVE corpus survey (vim, neovim, terminal-app patterns) with
a second pass on the checklist below.

## Methodology

Internal review against the security-hardening checklist in
[CLAUDE.md](../../CLAUDE.md#security-hardening-before-every-release):

1. Input validation
2. Buffer safety
3. Syscall review
4. Pointer validation
5. No command injection
6. No path traversal
7. Document findings with severity

External CVE corpus review (vim modeline RCEs, escape-sequence
injection, regex catastrophic backtracking, neovim Lua sandbox
escapes, terminal-app DoS patterns) is **deferred to M7**.

## Findings

Severity legend per CLAUDE.md: **CRITICAL** (remote / privilege
escalation), **HIGH** (moderate effort), **MEDIUM** (specific
conditions), **LOW** (defense-in-depth).

### F-1 [MEDIUM] Buffer content echoed verbatim — terminal escape injection

**Where:** `src/render.cyr` — `_render_build_line_body` writes each
byte from the gap-buffer directly to stdout via `syscall(1, 1, ...)`.

**Issue:** if a buffer contains raw ESC (0x1B) or other control bytes
(0x00–0x1F outside Tab/CR/LF), the terminal interprets them as
control sequences. A maliciously-crafted file could:

- Redefine ANSI color palette (annoying)
- Change window title (`ESC]0;TITLE\007`)
- On xterm with `allowWindowOps: true`: report cursor position back
  via `ESC[6n` → terminal answers via stdin, which cyim reads as
  user input → composable into a paste-as-command-style attack on
  the parent shell when cyim exits
- DECRC / DECSC save/restore tricks to garble the rendered frame

**Reference corpus:** vim has had multiple CVEs in this class
(CVE-2008-2712, CVE-2017-17087 family). Most modern terminals
disable the worst sequences by default, but cyim shouldn't rely on
that.

**Recommendation:** in render, replace control bytes (< 0x20 except
Tab=9, LF=10, CR=13) with a visible substitute — `^X` notation
(`^[` for ESC, `^A` for 0x01, etc.) or a reverse-video glyph.
Match vim's `:set list` / `nrformats` style.

**Severity rationale:** MEDIUM rather than HIGH because (a) most
terminals sanitize the worst, (b) the attacker needs cyim to open a
crafted file, (c) damage scope is "redraw weirdness" in the common
case — but the cursor-position-readback path is real and worth
fixing before v1.0.

**Triage:** Fix in M5 polish or early M6. Tracked.

---

### F-2 [LOW] Unbounded `:e` file load — memory exhaustion DoS

**Where:** `src/buffer.cyr` — `buf_load_file` reads in 4 KB chunks
into the gap-buffer with no max-size check. Gap-buffer auto-grows
unboundedly (`buf_grow` doubles capacity on demand).

**Issue:** opening a 100 GB file would attempt to allocate 100 GB+ in
the gap-buffer. The bump allocator (`alloc.cyr`) bumps brk; eventually
ENOMEM, eventually OOM-kill.

**Recommendation:** bound at `:e` to a configurable max (default
maybe 100 MB). Above the limit, refuse with `ERR_FILE_TOO_LARGE`
(new error code). User can override with `:e!` (force) or a `:set
maxfilesize=N` toggle.

**Severity rationale:** LOW — DoS-class only; needs an attacker who
can put a giant file in front of you and convince you to `:e` it.
The user already has shell access; they can choose what to open.
Worth a guard for accidental-mistake protection (e.g., piping output
into a tmpfile and accidentally `:e`-ing it).

**Triage:** Defer to M5 perf bite (where benchmarks will surface the
threshold) or M6.

---

### F-3 [LOW] Unbounded cmdbuf grow — memory exhaustion DoS

**Where:** `src/command.cyr` — `command_append` uses `buf_insert_byte`
on `editor_cmdbuf(s)`. No max-length check.

**Issue:** typing arbitrarily many bytes in COMMAND or SEARCH mode
grows cmdbuf without bound. Same bump-allocator path as F-2 — slower
to exhaust but possible (hold a key down for hours).

**Recommendation:** cap cmdbuf at, say, 4 KB. On overflow, drop the
new byte and beep / status-message.

**Severity rationale:** LOW — purely self-inflicted DoS; no remote
trigger. Fix is a one-liner.

**Triage:** Defer to M6 hardening.

---

### F-4 [LOW] `_dot_replay` silently fails on > 2048-byte insert

**Where:** `src/driver.cyr` — `_dot_replay` snapshots the recorded
insert session into a `var snap[2048]` static buffer and returns 0
if `n > 2048`.

**Issue:** if you typed > 2048 bytes in a single insert session and
then `.`, nothing happens — silently. UX-confusing rather than
exploitable.

**Recommendation:** raise the cap to a sensible limit (8 KB?) and
add an editor_status message on overflow ("dot: edit too large").

**Severity rationale:** LOW — UX issue rather than security. No
data corruption, no crash, just silent no-op.

**Triage:** M6 hardening.

---

### F-5 [LOW] `:e <path>` accepts arbitrary paths (assumed trust model)

**Where:** `src/command.cyr` — `_cmd_e` passes `<path>` straight to
`buf_load_file` → `sys_open`. No path-traversal check, no chroot,
no allowlist.

**Issue:** in cyim's current threat model — a local editor invoked
by an interactive user — this is fine. The user can `cat /etc/shadow`
already; cyim isn't a privilege boundary. Documenting it as a
finding so any future restricted-mode (e.g., daimon-driven sandbox)
inherits the question.

**Recommendation:** when restricted-mode lands (post-v1.0
demand-gated), document its trust model explicitly and validate
paths against the sandbox root. Until then, no change.

**Severity rationale:** LOW — not a vuln in the assumed trust model.

**Triage:** Out of scope for v1.0; revisit if/when restricted-mode
ships.

---

### F-6 [LOW] `grammar_load` reads from search path — supply-chain shape

**Where:** `src/highlight.cyr` — `_hl_resolve_dir` finds
`./grammars/cyrius.cyml` via `/proc/self/exe`-relative search; if a
user grammar overlay path is added later (planned per `cyimrc.md`
deferred features), an attacker who can write to that dir can
substitute a malicious grammar.

**Issue:** vyakarana's `grammar_load` parses CYML — not Turing-
complete, just rule data, so no RCE — but a crafted grammar could
make the tokenizer misbehave (mistokenize keywords as comments etc.,
masking a security-relevant string from the user's eye).

**Recommendation:** when user-grammar overlays land, document the
trust model: user grammars are user-controlled, like `.cyimrc`. No
sandboxing needed (data, not code), but be explicit.

**Severity rationale:** LOW — not exploitable today; documenting
for M4 / M5 successor work.

**Triage:** Tracked for whichever bite adds user-grammar overlays.

---

## Checklist coverage

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Input validation | **PARTIAL** | F-2, F-3 are unbounded inputs; otherwise gap-buffer / cmdbuf bounds-checked at use |
| 2 | Buffer safety | **CLEAN** | Every `var buf[N]` reviewed; sizes match consumer expectations; no overflows found |
| 3 | Syscall review | **CLEAN** | readlink (89), ioctl (16, TCGETS/TCSETS), file_open/read/write all checked: bounds correct, error paths tested |
| 4 | Pointer validation | **CLEAN** | All struct access via load64/store64 + explicit offsets; no untrusted-pointer dereference |
| 5 | No command injection | **CLEAN** | `:!cmd` not shipped; no `sys_system` use anywhere |
| 6 | No path traversal | **DOCUMENTED** | F-5 — assumed trust model is "interactive local user"; OK for v1.0 |
| 7 | Findings filed | **CLEAN** | This document |

## Triage summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0 | — |
| HIGH     | 0 | — |
| MEDIUM   | 1 | F-1 — fix before v1.0 (M5 polish or M6) |
| LOW      | 5 | F-2..F-6 — tracked; F-3, F-4 in M6; F-5, F-6 documented for future work |

No CRITICAL or HIGH findings — the obvious classes are absent (no
embedded scripting → no Vimscript/Lua sandbox escapes; no `:!cmd` →
no command injection; no plugins → no plugin-sandbox escapes; no
modeline parsing → no modeline RCE).

## What this audit does NOT cover

- **External CVE corpus review** — M7. The full vim / neovim CVE
  history needs a dedicated pass; many vim CVEs have been in
  features cyim deliberately doesn't ship (modelines, Vimscript,
  `:!cmd`), but the regex / escape-sequence / large-input patterns
  apply broadly.
- **Fuzzing surface coverage** — M5 bite 3 (separate). Fuzz
  harnesses for tokenizer, gap-buffer, and `editor_step` driver
  are queued.
- **Threat model documentation** — should land as an ADR during M6
  alongside the trust-model notes from F-5 / F-6.
- **Stdlib audit** — `lib/*.cyr` is vendored from the Cyrius
  toolchain. Per CLAUDE.md, "Do not edit anything in lib/". Stdlib
  audit happens upstream in cyrius itself.

## Next pass

**M7 — Security Audit.** Re-walk this checklist alongside the
external corpus survey (`docs/security/0day-corpus-YYYY-MM-DD.md`).
Re-triage findings against any new CVE patterns. Close all
CRITICAL / HIGH before tagging v1.0.
