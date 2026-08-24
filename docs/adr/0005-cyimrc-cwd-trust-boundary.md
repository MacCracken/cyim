# ADR 0005 — `.cyimrc` is loaded from the current directory, and that is a trust boundary ADR 0001 does not cover

**Status:** Accepted (decided 2026-08-23, implemented v1.9.2)
**Date:** 2026-08-23
**Tags:** security, trust-model, config, v1.9.2

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

**The user's config lives in their home directory. A project-local
`.cyimrc` may override it, and that is accepted.**

Concretely — **option C's search path, with the opt-in inverted to on**:

1. **`$XDG_CONFIG_HOME/cyim/cyimrc`** is the primary config, falling back to
   **`$HOME/.config/cyim/cyimrc`** when `XDG_CONFIG_HOME` is unset. This is
   where a user's actual preferences belong: it follows them between
   directories, it is unambiguously theirs, and it is the file they will edit.
2. **`./.cyimrc` is then loaded on top**, overriding any key it sets. No flag,
   no prompt. Per-project colour choices are a real use for an editor and
   making people opt in per project would be friction for no proportional gain.
3. **Later wins, key by key.** The loader stores into per-key slots, so a
   local file overrides only the keys it names and inherits the rest.

And the two things that were already settled, restated because they are what
make (2) defensible:

4. **ADR 0001 does not extend to cwd-relative config.** Its "the user is
   trusted" clause is scoped to input the user actually supplies. A file found
   in the working directory is the *directory's* input. ADR 0001 carries a
   pointer here.
5. **Memory safety is not in scope for the trust model.** Any value `.cyimrc`
   can express is range-checked before it reaches an index, a length, or a
   loop bound — regardless of which file it came from. Implemented at 1.8.3
   (`_cyimrc_palette_valid`, `_cyimrc_parse_int`'s digit cap,
   `_render_u16_ascii`'s clamp).

### The rule that keeps this honest

Accepting local override is a judgement about **what `.cyimrc` can currently
express**: ten colour indexes and three display integers. The worst a hostile
directory achieves is a wrong colour. That is a fine trade.

It stops being a fine trade the moment a key can do something else. So:

> **Every new `.cyimrc` key must be classified as local-overridable or
> home-only when it is added, and the classification recorded here.**

Not machinery — a line in a table and a check in `_cyimrc_apply` if the answer
is ever "home-only". Today the table is trivial:

| Key group | Local override | Why |
|---|---|---|
| `palette.*` (10 keys) | **yes** | A colour. Per-project palettes are the obvious use |
| `ignorecase`, `line_numbers`, `tabstop` | **yes** | Display and search preferences, scoped to the file you are looking at |
| *(none yet)* | **no** | — |

**Keymaps, when they land, are the first serious candidate for home-only.** A
colour accepted from a directory you just cloned is a wrong colour; a *keymap*
accepted from it decides what your keystrokes do. That is a different
proposition, and this ADR exists so the question gets asked then rather than
discovered afterwards.

## Options considered

| Option | What it costs | What it buys | Verdict |
|---|---|---|---|
| **A. Status quo** — keep loading `./.cyimrc` unconditionally, no home config | Nothing | Nothing. Correct *today* only because the surface is ten colour indexes — and leaves users with no config that follows them between projects | Rejected |
| **B. Drop cwd; load only from `$XDG_CONFIG_HOME/cyim/cyimrc`** | Breaks per-project config, which is a real use for an editor | Removes the boundary entirely; simplest to reason about | Rejected — throws out a legitimate use to close a hole whose blast radius is a colour |
| **C. Load both; cwd requires an opt-in** (env var or a key in the user-level config) | One flag to document; friction on every project for a risk that is currently a wrong colour | vim's `exrc` shape, with vim's track record behind it | **Chosen, opt-in inverted to on** — the search path is right, the gate is premature |
| **D. Load both; restrict what the cwd copy may set** | Two config grammars to keep in step — the failure mode is forgetting to restrict a newly added key | Per-project colours keep working; the widening surface stays safe | **Adopted as a rule, not machinery** — see the classification table above. The restriction becomes code the first time a key needs it |

**C and D are not exclusive**, and vim ships both (`exrc` + `secure`). cyim
takes C's *shape* with the gate open, and holds D in reserve as a written rule
rather than unwritten code — because the thing that would justify D (a key
that does more than choose a colour) does not exist yet, and building the
restriction before the thing it restricts is how you get machinery nobody
remembers the reason for.

## Why the risk is acceptable today, and what would change that

Today's entire `.cyimrc` surface is ten palette indexes and three integers.
The worst a hostile directory achieves is **the wrong colour**. There is no
path from `.cyimrc` to code execution, file access, or command dispatch,
because cyim has no scripting language to reach for — the
[no-embedded-scripting constraint](../../CLAUDE.md) is doing real work here,
and it is what makes "local override, no questions asked" a reasonable default
rather than a shrug.

What would change it: the surface widening.
[`docs/guides/cyimrc.md`](../guides/cyimrc.md) names keymaps as an M4
candidate, and `line_numbers` / `tabstop` are already parsed against a future
render integration. **A keymap accepted from a directory you just cloned is a
different proposition from a colour.** The classification rule above is the
mechanism that forces that question to be asked in the cut that adds it,
rather than discovered afterwards.

## Consequences

### What this enables

- **Config that follows the user.** Preferences live in one place and apply
  everywhere, which is what people expect and what cyim did not have.
- **Per-project overrides keep working**, unchanged, including every existing
  `./.cyimrc` in the wild — cwd is still consulted and still wins.
- **The precedence is stated**, so "why is my colour different in this repo"
  has an answer a user can look up.

### What this forbids (without a follow-up ADR)

- **Adding a `.cyimrc` key without classifying it.** The table above is the
  deliverable of this decision, not decoration; a key that lands without a row
  has not been thought about.
- **Executing anything named in a config file**, from either location. That is
  the no-embedded-scripting constraint, and it is the reason this decision can
  be as permissive as it is.

### Residuals

- **No `secure`-style ownership check.** vim additionally refuses the
  dangerous subset in a file not owned by the invoking user. cyim has no
  dangerous subset to refuse, so the check would guard nothing. Revisit
  alongside the first home-only key.
- **Symlinked or shared home directories** are trusted the same as any other
  path under `$HOME` — ADR 0001's model, unchanged.
- Any future config key gets a documented answer to "is this safe to
  accept from an untrusted directory?" before it ships.

## References

- [ADR 0001 — Trust model: interactive local user](0001-trust-model.md)
- [2026-08-23 — 1.8.x P(-1) hardening audit](../audit/2026-08-23-1.8x-hardening.md), F-2 and § 6
- vim `:help 'exrc'` and `:help 'secure'` — the same mechanism, and the
  reasoning behind its default-off posture
