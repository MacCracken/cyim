# Security policy — cyim

## Reporting a vulnerability

Email **yeoman.maccracken@gmail.com** with subject prefix
`[cyim security]`. Or open a private security advisory through
GitHub's Security tab.

Please don't open public issues for vulnerabilities until a fix
ships and a CVE (if applicable) is assigned.

A response acknowledging receipt typically lands within a few
days. cyim is a single-maintainer project; we'll work with you
on disclosure timing.

## Threat model

cyim is documented in [ADR 0001](docs/adr/0001-trust-model.md)
as **an interactive editor for a single local user. It is not a
privilege boundary.** That ADR is the load-bearing reference
for what counts as a vulnerability vs. an accepted trade-off.

In particular:

- The user is trusted. Every byte cyim reads from stdin, every
  path the user types, every `.cyimrc` it loads is trusted to
  the degree the invoking shell trusts the user.
- File content from disk is treated as untrusted *for display*
  but trusted to be data — control bytes are `^X`-substituted
  in render (closes M5 audit F-1), but the buffer's bytes are
  *not* parsed for commands, modelines, scripts, or anything
  else.
- The binary is not setuid / setgid / setcap-wrapped. Running
  cyim under sudo gives cyim root's privileges; that's the
  user's choice.

If you find a vulnerability that breaks the threat model — for
example, an attacker-controlled file that escapes the
buffer-as-data invariant — that's a real finding and we want
to hear about it.

If you find a behavior that's accepted under the trust model
(e.g., `:e <path>` accepts `../`; `:w` follows symlinks;
opening a 200 MB file uses 200 MB of memory) and would change
the trust model to fix, please open a discussion or PR rather
than a security report — those decisions belong in
[`docs/adr/`](docs/adr/), not in CVE filings.

## What's in scope

- Buffer / parser / dispatch correctness (memory safety,
  integer overflow, out-of-bounds reads/writes)
- Terminal escape injection from buffer content
- `.cyimrc` parser correctness (data, not code, but malformed
  input shouldn't crash)
- Vyakarana grammar parser correctness when fed adversarial
  `.cyml` files (see also: vyakarana's own SECURITY.md)
- Any deviation from the [ADR 0001](docs/adr/0001-trust-model.md)
  trust model

## What's out of scope (for security reports — file as feature
requests instead)

- Refusal §0 features cyim explicitly doesn't ship
  ([CONTRIBUTING.md](CONTRIBUTING.md) lists them)
- Threat-model expansions (setuid mode, sandbox, restricted
  mode) — file an ADR proposal, not a CVE
- Performance issues without a security angle — file a perf
  issue and reference [`BENCHMARKS.md`](BENCHMARKS.md)

## Past audits

- [2026-04-25 — Initial security audit (M5)](docs/audit/2026-04-25-security-audit.md)
- [2026-04-25 — M7 pre-v1.0 audit](docs/audit/2026-04-25-m7-audit.md)
- [2026-04-25 — 0day / CVE corpus survey](docs/security/2026-04-25-0day-corpus.md)

State at v1.0: 0 CRITICAL / 0 HIGH / 0 MEDIUM; 8 LOW findings
all triaged with rationale.
