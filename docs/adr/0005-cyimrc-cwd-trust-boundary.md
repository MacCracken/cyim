# ADR 0005 — `.cyimrc` is loaded from the current directory, and that is a trust boundary ADR 0001 does not cover

**Status:** Proposed
**Date:** 2026-08-23
**Tags:** security, trust-model, config, v1.8.3

---

## Context

[ADR 0001](0001-trust-model.md) fixes cyim's threat model as
**"an interactive editor for a single local user; not a privilege
boundary."** Its first clause reads:

> **The user is trusted.** Every byte cyim reads from stdin, every path
> the user types, every `.cyimrc` it loads is trusted to the degree the
> invoking shell trusts the user.

That clause groups `.cyimrc` with stdin and typed paths — things the user
supplies. But `cyimrc_load()` resolves **`./.cyimrc`**, relative to the
current working directory:

```cyrius
fn cyimrc_load() {
    return cyimrc_load_path(".cyimrc");
}
```

So the config is not necessarily the user's. It arrives with whatever
directory they happen to be in. Clone a repository, `cd` into it, open a
file, and cyim has applied that repository's configuration. The user
typed a filename; they did not author — or read — the config that took
effect.

The [1.8.3 hardening audit](../audit/2026-08-23-1.8x-hardening.md)
surfaced this while fixing **F-2**, where an unvalidated `.cyimrc` palette
value reached a buffer index and produced an out-of-bounds write. The
memory-safety half of that is fixed and is *not* a trust question — a
trust model may say "any colour the config names is allowed"; it cannot
say "an out-of-range integer may corrupt the render buffer." What remains
is the policy question this ADR exists to settle.

**This is a well-worn problem.** vim's `.exrc` / `set exrc` is the same
mechanism, and vim's answer is instructive: cwd-relative config is **off
by default**, and when enabled, `set secure` still forbids the dangerous
subset (`:autocmd`, `:write`, `:!`) in any file not owned by the user.
Two of vim's CVE-adjacent embarrassments live in this neighbourhood.

## Decision

**Undecided — this ADR is Proposed, and records the options rather than
picking one.** What *is* decided:

1. **ADR 0001 does not extend to cwd-relative config.** Its "the user is
   trusted" clause is scoped to input the user actually supplies. A file
   found in the working directory is the directory's input. ADR 0001
   should carry a pointer to this ADR rather than continuing to imply
   coverage it does not have.
2. **Memory safety is not in scope for the trust model.** Any value
   `.cyimrc` can express must be range-checked before it reaches an index,
   a length, or a loop bound — regardless of how the policy question below
   is answered. Implemented at 1.8.3 (`_cyimrc_palette_valid`,
   `_cyimrc_parse_int`'s digit cap, `_render_u16_ascii`'s clamp).

## Options considered

| Option | What it costs | What it buys |
|---|---|---|
| **A. Status quo** — keep loading `./.cyimrc` unconditionally | Nothing | Nothing. Correct *today* only because the surface is ten colour indexes |
| **B. Drop cwd; load only from `$XDG_CONFIG_HOME/cyim/cyimrc`** | Breaks per-project config, which is a real use for an editor | Removes the boundary entirely; simplest to reason about |
| **C. Load both; cwd requires an opt-in** (env var or a key in the user-level config) | One flag to document; a surprise for anyone relying on cwd config today | vim's `exrc` shape, with vim's track record behind it |
| **D. Load both; restrict what the cwd copy may set** | Two config grammars to keep in step — the failure mode is forgetting to restrict a newly added key | Per-project colours keep working; the widening surface stays safe |

**C and D are not exclusive**, and vim ships both (`exrc` + `secure`).

## Why this is not urgent, and why it should not be left open either

**Not urgent:** today's entire `.cyimrc` surface is ten palette indexes
and three integers that are stored but not yet rendered. The worst a
hostile config achieves is *the wrong colour*. There is no path from
`.cyimrc` to code execution, file access, or command dispatch, because
cyim has no scripting language to reach for — the
[no-embedded-scripting constraint](../../CLAUDE.md) is doing real work
here.

**Not to be left open:** the surface is scheduled to widen.
[`docs/guides/cyimrc.md`](../guides/cyimrc.md) names keymaps as an M4
candidate, and `line_numbers` / `tabstop` are already parsed against a
future render integration. **A keymap accepted from a directory you just
cloned is a different proposition from a colour** — it decides what your
keystrokes do. The decision should be made while the answer is cheap,
not in the cut that adds keymaps.

## Consequences

### If this stays Proposed

`.cyimrc` keeps loading from the cwd. Every key added to it inherits the
boundary silently. The 1.8.3 audit's F-2 fix means new keys are at least
range-checked, but nothing forces the *policy* question to be asked
again — which is exactly how this went unexamined from M2 to 1.8.3.

### Whichever option is chosen

- ADR 0001 gets an amendment note pointing here, so its "the user is
  trusted" clause stops implying coverage it lacks.
- `docs/guides/cyimrc.md` gains a "where this file is read from, and what
  that means" section — currently it documents the *keys* but never says
  the file is cwd-relative.
- Any future config key gets a documented answer to "is this safe to
  accept from an untrusted directory?" before it ships.

## References

- [ADR 0001 — Trust model: interactive local user](0001-trust-model.md)
- [2026-08-23 — 1.8.x P(-1) hardening audit](../audit/2026-08-23-1.8x-hardening.md), F-2 and § 6
- vim `:help 'exrc'` and `:help 'secure'` — the same mechanism, and the
  reasoning behind its default-off posture
