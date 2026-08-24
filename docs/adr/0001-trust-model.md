# ADR 0001 — Trust model: interactive local user

**Status:** Accepted (scope clarified 2026-08-23 — see the note below)
**Date:** 2026-04-25
**Tags:** security, trust-model, v1.0

> **2026-08-23 (v1.8.3) — this ADR does not cover cwd-relative config.**
> Decision § 1 below groups `.cyimrc` with stdin and typed paths as things
> "the user" supplies. `cyimrc_load()` reads **`./.cyimrc`**, so the file
> arrives with whatever directory the user happens to be in — it is the
> *directory's* input, not theirs. The 1.8.x hardening audit surfaced this
> while fixing an out-of-bounds write driven by an unvalidated value in
> that file. The memory-safety half is fixed and was never a trust
> question; the policy half — whether a cwd-relative config should be
> loaded at all, and with what restrictions — is
> [ADR 0005](0005-cyimrc-cwd-trust-boundary.md), status Proposed.
> Read clause 1 as scoped to input the user actually supplies.

---

## Context

The M7 security audit
([`docs/audit/2026-04-25-m7-audit.md`](../audit/2026-04-25-m7-audit.md))
flagged three findings (F-5, M7-3, M7-4) as "documented; trust
model assumed" rather than open vulnerabilities:

- **F-5 / M7-4**: `:e <path>` accepts arbitrary paths (no `../`
  blocking, no chroot, no allowlist).
- **M7-3**: `:w` re-opens the path string at save time; symlink
  swap between `:e` and `:w` follows the new target.
- **F-2** (now closed): unbounded `:e` file load was a DoS only
  if you trusted yourself enough to type `:e /path/to/100GB.log`.

These aren't *defects* — they're *consequences of cyim's threat
model*. This ADR makes the threat model explicit so any future
work that wants to weaken or strengthen it has a referent.

---

## Decision

**cyim is an interactive editor for a single local user. It is
not a privilege boundary.**

In particular:

1. **The user is trusted.** Every byte cyim reads from stdin, every
   path the user types, every `.cyimrc` it loads is trusted to the
   degree the invoking shell trusts the user. cyim doesn't validate
   paths, doesn't sandbox config files, doesn't restrict what `:w`
   writes where.

2. **The filesystem is trusted to the user's own permissions.**
   `:e /etc/shadow` will succeed if the user has read on
   `/etc/shadow`, fail with `ERR_FILE_NOT_FOUND` otherwise. cyim
   makes no decisions about what the user *should* be allowed to
   open — the kernel already does that.

3. **TOCTOU on save is accepted.** `:w` opens the same path string
   it was given; if a symlink moved between `:e` and `:w`, the
   write follows. This matches vim's default behavior. Tools that
   need atomic-write semantics (config-file editors, package
   managers) should use a different tool.

4. **File content from disk is treated as untrusted *for display*
   but trusted to be data.** Per the M5/M6 audit response: control
   bytes are ^X-substituted in render (closing terminal-escape
   injection), but the buffer's bytes are *not* parsed for
   commands, modelines, scripts, or anything else.

5. **The binary is not setuid / setgid / setcap-wrapped.** Running
   cyim under sudo gives cyim root's privileges, just like vim or
   any other editor. That's the user's choice; cyim doesn't try
   to drop privileges.

## Consequences

### What this enables

- The 5 findings above stay LOW and don't gate v1.0.
- cyim can ship without a path-validation layer, without a
  setuid-aware file-open path, without restricted-mode plumbing.
- The audit posture is honest: classes 5 (scripting), 6
  (plugins), 9 (format string), and 11 (path traversal in
  privileged contexts) are refused-by-design or
  documented-by-trust-model — not open vulnerabilities papered
  over.

### What this forbids (without a follow-up ADR)

- **No setuid mode.** The threat model assumes
  cyim's-privilege == user's-privilege. A setuid binary needs a
  *different* threat model — F-5/M7-3/M7-4 all become real
  CRITICAL/HIGH issues there.
- **No "untrusted file" mode.** cyim doesn't currently distinguish
  "I'm opening my own code" from "I'm opening a file someone
  emailed me." If that distinction ever matters, it lands as a
  new mode (`cyim --restricted <file>`) with its own ADR
  defining the new boundary.
- **No daimon-orchestrated sandbox.** The roadmap mentions
  "daimon-orchestrated agents" as a consumer. When that lands,
  it'll need a *different* trust model — agents drive cyim
  programmatically, can write malicious paths into `:e` arguments,
  and presumably should be sandboxed. That work files its own
  ADR (number TBD) defining the agent-trust boundary.

### Ongoing implications

- Any future work that wants to *narrow* the trust model
  (introduce a sandbox, a restricted mode, a privilege drop)
  needs a follow-up ADR explaining which findings get re-opened
  and how they'll be closed.
- Any future work that wants to *widen* the trust model (e.g.,
  load `.cyimrc` from network paths, accept buffer content as
  config, ship a plugin system) needs a follow-up ADR explaining
  why the new attack surface is acceptable.

## Alternatives considered

### A1 — Follow vim's setuid pattern

Vim has had setuid-aware code paths for decades — `:set
secure`, modeline restrictions in setuid mode, etc.

**Rejected.** cyim's no-modeline / no-scripting / no-plugin
posture means the setuid attack surface is much smaller than
vim's, but it's also a complexity floor cyim hasn't paid for
yet. If a real setuid use case surfaces, file an ADR then.

### A2 — Restricted mode by default

Some editors (sandboxed text editors in container UIs) restrict
filesystem access to a project root by default, expanding only
on user opt-in.

**Rejected.** Doesn't fit cyim's roadmap target — a daily-driver
editor for AGNOS code. The user opens cyim *because* they want
to edit files outside one project root.

### A3 — Per-buffer trust labels

Track which buffers came from "trusted" vs. "untrusted"
sources, refuse some operations on untrusted buffers (e.g., `:w`
without a prompt).

**Rejected.** No clear definition of "trusted" without
context cyim doesn't have. Defer to a future restricted-mode
ADR if needed.

## References

- [`docs/security/2026-04-25-0day-corpus.md`](../security/2026-04-25-0day-corpus.md) — class taxonomy
- [`docs/audit/2026-04-25-m7-audit.md`](../audit/2026-04-25-m7-audit.md) — findings + triage
- CLAUDE.md → "Security Hardening" — checklist + severity definitions
- AGNOS design-patterns §0 (Refusal) — the broader "what cyim
  doesn't do" stance that this ADR specializes
