# ADR 0003 — Cyrius plugin system: AOT-compiled, sandhi-pattern, LSP-first

**Status:** Accepted (Proposed, Pending v1.4.0 prototype)
**Date:** 2026-05-06
**Tags:** plugins, extensibility, sandhi, lsp, refusal-zero

---

## Context

cyim's `CLAUDE.md` and `docs/design-patterns.md` Refusal §0 forbid
**embedded scripting languages** (Vimscript, Lua, Python, JS).
This is load-bearing: configuration is data
(`.cyimrc`, CYML), not code; the editor's surface is its binary;
"if a feature requires a language to express, it gets data syntax
or doesn't ship."

Three things have surfaced that motivate revisiting whether a
*Cyrius* plugin system — distinct from embedded scripting — fits
within Refusal §0 or stands outside it:

1. **The sandhi pattern is already in production.** vyakarana
   (M2, syntax highlighting via `lib/vyakarana.cyr`) and niyama
   (v1.3.0+, additional regex engines via `lib/niyama.cyr`) are
   external Cyrius libraries folded byte-identical into cyim's
   `lib/` and pulled in via explicit `include`. Both are
   compile-time additions to the cyim binary, not runtime-loaded
   modules. The infrastructure for "third-party Cyrius code that
   ships as part of cyim" already exists.

2. **The LSP client (v1.4.0) is the third consumer-shaped
   feature** — after vyakarana and niyama — that has *editor-
   adjacent* concerns and could justifiably sit outside the
   editor core. cyrius-lsp itself is upstream-stable
   (`programs/cyrius-lsp.cyr`); cyim's role is to spawn it as a
   subprocess, frame JSON-RPC over pipes, render diagnostics in
   the buffer, and route `gd`/`gr` to LSP queries. That's a
   well-bounded subsystem with its own state and protocol. It's
   editor-dependent (needs buffer + status-line + keymap hooks)
   but not editor-fundamental (modal grammar doesn't change).

3. **CLAUDE.md's third-instance refactoring threshold has been
   reached.** "Refactor when the code tells you to — duplication,
   unclear boundaries, measured bottlenecks. Wait for the third
   instance." vyakarana + niyama + (planned) lsp = the third
   instance of "third-party Cyrius code that extends cyim
   functionally without becoming part of its core grammar." The
   pattern wants to be formalized.

The question this ADR answers: **does Refusal §0 forbid a Cyrius
plugin system, or only embedded scripting? And if a Cyrius plugin
system is admissible, what does it need to look like?**

---

## Decision

A Cyrius plugin system **is admissible** and is structurally
distinct from the Refusal §0 prohibition. Refusal §0 stays
unchanged — no Vimscript / Lua / Python / JS / any embedded
scripting language. A Cyrius plugin is a compile-time addition
to the cyim binary, not a runtime extension surface.

We commit to **prototyping the system via the v1.4.0 LSP client
as the first plugin** rather than designing the ABI in vacuum.
The plugin system is "Accepted" as a direction; the concrete ABI
crystallises against the LSP client's actual needs.

Five load-bearing choices follow.

### 1. AOT-compiled via the sandhi pattern, not runtime-loaded

Plugins are Cyrius modules vendored into cyim's `lib/<plugin>.cyr`
(or pulled via `[deps.<plugin>]` git-resolution like
vyakarana/niyama do today) and pulled in via explicit `include`
in `src/main.cyr`. The cyrius compiler concatenates plugin source
into the cyim translation unit before lowering to native code.
DCE strips unused plugin code at link time, just as it strips
unused stdlib functions. The plugin's contribution to the binary
is visible in CHANGELOG, `cyrius lint`-able pre-ship, and
diff-able commit-by-commit.

Crucially: **no plugin loader, no `dlopen`, no plugin VM, no
sandbox, no eval.** The cyrius compiler is the only mechanism
that admits code into the cyim binary. A user who installs cyim
gets exactly the plugins that were `cyrius build`-ed in at ship
time. There is no runtime extension surface for a malicious
plugin to exploit at user-install time. This is what makes the
Cyrius plugin system *not* an embedded scripting language under
Refusal §0: the plugin author's code is treated identically to
cyim's own code at compile time, and treated identically to any
other native code at runtime.

This also matches ADR 0001's trust model: cyim is for an
interactive local user; plugins are treated as trusted code, the
same as cyim itself. The user (or distro packager) controls which
plugins are linked in. If they don't trust a plugin author, they
don't include the plugin.

### 2. Plugin ABI surface (provisional — finalised against LSP)

cyim exposes a stable extension API on top of which plugins
interact with the editor. The provisional surface, to be tightened
during the v1.4.0 LSP build:

```
# Buffer / view (read mostly)
buf_len(b), buf_get(b, i)              # byte-level reads
buf_line_at(b, line_no)                # line span lookup
buf_lines(b)                           # line count
editor_active_buf(s)                   # current buffer
editor_cursor(s)                       # cursor offset
editor_set_cursor(s, off)              # programmatic cursor move
editor_active_window(s)                # window pointer
editor_set_status(s, msg, msg_len)    # status-line write

# Mode dispatch (read mostly)
editor_mode(s)                         # current mode
ACT_*                                  # action enum (existing)

# Plugin-side hooks (write — narrow)
plugin_register_normal_key(k, cb)      # NORMAL-mode key → callback
plugin_register_ex_command(name, cb)   # `:lsp-restart` → callback
plugin_register_status_segment(cb)     # render right-aligned status
plugin_register_post_save_hook(cb)     # didSave LSP notify, etc.
plugin_register_post_change_hook(cb)   # didChange LSP notify
```

The hook callbacks are Cyrius `fn` values registered at plugin
init time (called once during `editor_new` setup, walked through
each plugin's `register_*` calls). Each hook is bounded: a
NORMAL-mode key callback returns an action constant for the
core dispatch loop to apply; it can't directly mutate buffer
state outside the action set. This preserves the modal grammar
("Modal grammar is fixed; everything else is up for grabs") —
plugins can't extend the *grammar*, only the *dispatch table*.

The full ABI lands in a follow-up ADR (0004 or higher) once the
LSP client surfaces what it actually needs. Anything not in the
listed surface is internal to cyim and may break across releases.

### 3. Hook points are first-class, not conventions

Plugin hooks are explicitly enumerated at the cyim level. A
plugin can't subscribe to "any cyim event" — it picks from a
fixed set of hook points. This is the load-bearing constraint
that keeps plugins composable: two plugins can both register
ex-commands without colliding, but neither can tap into
`editor_step` byte-by-byte, neither can intercept `:w`, neither
can replace the search engine. The hook surface is reviewed and
expanded by ADR.

Initial hook points (provisional):

- **NORMAL-mode keymap registration.** Plugin reserves a key
  prefix or specific key sequence; cyim dispatches matching
  input to the callback, which returns an action.
- **Ex-command registration.** Plugin reserves `:foo`, `:foo-bar`
  command names; cyim's command-mode parser routes to the
  callback. Conflict with built-in commands is a compile-time
  error (the plugin's `cyrius build` fails).
- **Post-save hook.** Called after `:w` succeeds, with the buffer
  + new file path. LSP uses this for `textDocument/didSave`.
- **Post-change hook.** Called after edits (debounced). LSP uses
  this for `textDocument/didChange`.
- **Status-line segment provider.** Right-aligned segment renderer
  called once per repaint. LSP uses this for diagnostic count
  ("E: 3 W: 1") or LSP server status.
- **Diagnostic provider.** A side-channel where plugins can
  attach (line, severity, message) records to a buffer; cyim's
  render layer paints them as inline highlighting. LSP uses this
  for `textDocument/publishDiagnostics`.

Initial hook points are intentionally narrow. New hook points
require an ADR.

### 4. Manifest shape: `[plugins]` block in `cyrius.cyml`

Plugins are declared in cyim's `cyrius.cyml` `[plugins]` block,
mirroring the shape of `[deps.vyakarana]` today. Each plugin
entry specifies a git source + tag + module list, exactly as
external Cyrius deps do:

```toml
[plugins.cyim-lsp]
git = "https://github.com/MacCracken/cyim-lsp.git"
tag = "1.0.0"
modules = ["dist/cyim-lsp.cyr"]
```

`cyrius deps` resolves and vendors the plugin into cyim's `lib/`;
`src/main.cyr` pulls it via `include "lib/cyim-lsp.cyr"`. This
is the *exact* sandhi pattern vyakarana and niyama already use.
The only delta is the section name: `[plugins.<name>]` rather
than `[deps.<name>]`. The naming makes the intent visible
(`grep '\[plugins\]' cyrius.cyml` lists the extension surface;
`grep '\[deps' cyrius.cyml` lists transitive language libraries).

`[plugins]` entries are otherwise interchangeable with
`[deps.<name>]` at the build-tool level. The distinction is
documentary, not mechanical.

### 5. First consumer: cyim-lsp at v1.4.0

The LSP client (v1.4.0) is the first plugin and the design
forcing-function for the ABI surface. Concrete deliverables in
the v1.4.0 cut:

1. A new repo `MacCracken/cyim-lsp` shipping a `dist/cyim-lsp.cyr`
   distfile per the sandhi pattern (mirrors vyakarana/niyama
   layout: `src/`, `tests/`, `dist/`).
2. cyim's `cyrius.cyml` gains the first `[plugins.cyim-lsp]`
   entry pointing at `cyim-lsp@1.0.0`.
3. cyim's `src/main.cyr` gains `include "lib/cyim-lsp.cyr"`
   alongside the existing vyakarana / niyama includes.
4. The plugin ABI listed in §2 is realised exactly as needed by
   cyim-lsp — not more, not less. A follow-up ADR (likely 0004)
   freezes the ABI surface against what shipped.
5. The `[plugins]` cyrius.cyml extension is documented in
   `docs/architecture/` (whichever next NNN-kebab-case slot is
   open).

A plugin-author guide (`docs/guides/writing-a-cyim-plugin.md`)
lands in the v1.4.0 cut or v1.4.1 follow-up, referencing the
cyim-lsp source as the worked example.

---

## Consequences

### Positive

- **Refusal §0 stays intact.** No embedded scripting language is
  added. Cyrius plugins compile to native code at cyim build
  time, identical to cyim's own source. There is no runtime
  load step, no sandbox to audit, no plugin VM.
- **Sandhi pattern formalised.** vyakarana + niyama pioneered
  the structure ad-hoc; ADR 0003 now records it as the canonical
  way to compose Cyrius code into cyim. Future libraries (e.g.
  a `cyim-tree-sitter` consumer, a `cyim-snippets` engine) slot
  in mechanically.
- **Auditable ship surface.** Every plugin's contribution is
  visible at `cyrius lint` / `cyrius build` / CHANGELOG-diff
  time. No drive-by-install attack surface. ADR 0001 trust
  model unchanged.
- **Modal grammar protected.** Plugins extend the *dispatch
  table*, not the grammar. The Refusal §0 prohibition's
  underlying concern — "30 years of `:set compatible` shape" —
  doesn't apply to a sandhi-style extension where the grammar
  rules are still defined exclusively by cyim's core.
- **Bounded plugin failure modes.** A buggy plugin produces
  build-time errors (cyrius lint / type-check), not runtime
  surprises. A panicking plugin crashes cyim cleanly; it can't
  partially corrupt buffer state because all writes go through
  the action enum.
- **Forces good ABI design.** Building cyim-lsp as the first
  plugin will surface every implicit assumption in cyim's
  internals; the `editor_*`/`buf_*` API gets formalized as a
  consequence.

### Negative

- **Binary-size growth per plugin.** Folding plugins increases
  cyim's binary linearly in plugin size. niyama added ~6.6 KLOC
  (~520 KB). cyim-lsp will likely add comparable. This is the
  same trade-off CLAUDE.md flagged for the niyama fold and
  accepts: DCE recovers most of it; the audit story is worth
  the bytes.
- **Refusal §0's optical clarity weakens.** Saying "no plugins"
  was a clean line; saying "no embedded-scripting plugins, but
  Cyrius plugins are fine" requires explaining the distinction
  to every new reader. ADR 0003 itself is the explainer; the
  Refusal §0 line in `design-patterns.md` will need a forward
  reference here.
- **Plugin authors must use Cyrius.** The barrier-to-write
  is higher than a Lua plugin would be. This is a feature, not
  a bug: it's the same constraint that gates contributions to
  cyim itself, which is why we accept it. But it means the
  plugin ecosystem stays small by design.
- **ABI freeze obligation.** Once cyim-lsp ships against an
  ABI, that ABI becomes a compatibility contract. Breaking it
  requires a major version bump (per first-party-standards) or
  a coordinated bump across all plugins. This is the standard
  cost of any extension surface; the sandhi pattern doesn't
  change it.
- **No sandboxing for adversarial plugin authors.** The trust
  model assumes the user trusts every plugin they install. A
  malicious Cyrius plugin can do anything cyim can do. ADR 0001
  already establishes that cyim isn't a privilege boundary, so
  this matches the existing model — but it means plugins from
  untrusted sources should not be added to `cyrius.cyml`.

### Neutral

- **The `cyrius-plugins` repo at `MacCracken/cyrius-plugins`
  remains for Claude Code wiring**, not cyim plugins. cyim
  plugins live in their own per-plugin repos (cyim-lsp,
  hypothetical cyim-tree-sitter, etc.) under the sandhi pattern.
  The two plugin systems address different consumers.

---

## Alternatives considered

### A. Reject all plugins; keep Refusal §0 absolute

The simplest path. Every editor-adjacent feature gets folded into
cyim's own source as core code. LSP becomes part of cyim proper,
not a plugin.

Rejected because: cyim's binary stays cleanly auditable, but the
core code grows unboundedly as the editor accretes integrations.
LSP, clipboard, terminal embed, macros — each becomes part of the
core codebase, growing the surface all auditors must walk.
vyakarana and niyama are evidence the sandhi pattern works at
scale; LSP is large enough to benefit from the same isolation.
Refusing all plugins is also tonally inconsistent with the
already-shipped sandhi precedent.

### B. Lua / scripting plugins (the vim/neovim path)

Embed an interpreter; let users write plugins in a scripting
language for low barrier-to-write. Massive ecosystem, fast
iteration.

Rejected because: this is *exactly* what Refusal §0 forbids, and
for the reasons listed in `docs/design-patterns.md`: turing-
complete plugin sprawl, drive-by malicious plugins (the Lua
sandbox escape CVE corpus is its own vim/neovim audit chapter),
incompatible plugin combinations, "plugin-init slowness" as a
cyim performance bug. The cyim project's identity is the
refusal of this path.

### C. Runtime `dlopen` of compiled Cyrius plugins

Plugins ship as `.so` files dropped in `~/.cyim/plugins/`, loaded
at startup via `dlopen`. Faster iteration than rebuild-from-source;
preserves the "compiled native code, no interpreter" property.

Rejected because: introduces a runtime extension surface (anyone
who can drop a file in the plugin dir extends cyim), defeats the
auditable-ship-surface property (the running binary is no longer
the binary that was lint-tested), and adds a new failure mode
(plugin-vs-cyim ABI skew at version mismatch). The AOT-compile
choice in §1 is specifically motivated by avoiding all three.

### D. Wait for a fourth plugin-shaped use case before formalising

CLAUDE.md says "Don't refactor speculatively. Wait for the third
instance." vyakarana + niyama + LSP = three. Could wait for a
fourth (clipboard provider? snippet engine?) to confirm the
pattern.

Rejected because: the third instance has clear "third instance"
energy — LSP is large, well-bounded, structurally identical to
the first two, and naming the pattern *now* shapes how LSP itself
gets implemented. Waiting risks LSP getting written as core code,
collapsing the third-instance threshold past the point we can
extract a clean pattern. ADR 0003 records the decision; ADR 0004
(or 0005) freezes the ABI surface that ships with the actual
prototype.

---

## Plan / Needed items

For v1.4.0 to ship the first plugin (cyim-lsp), the following
must land — roughly in order:

**In cyim:**
1. Define the plugin ABI in `src/plugin.cyr` (new file): the
   `plugin_register_*` accessor set listed in §2. Functions can
   be stubs initially; cyim-lsp drives concrete signatures.
2. Wire hook-point invocation in `src/driver.cyr`,
   `src/render.cyr`, `src/command.cyr`, `src/buffer.cyr` (the
   "where do hooks fire from" plumbing, narrow set).
3. Add `[plugins]` block parsing to `cyrius.cyml` (likely lands
   in cyrius itself — verify with cyrius maintainer; falls back
   to `[deps.<name>]` syntactic equivalence if the cyml parser
   doesn't gain the new section).
4. Add `include "lib/cyim-lsp.cyr"` to `src/main.cyr` once the
   plugin ships.
5. Document plugin-author surface in
   `docs/architecture/NNN-plugin-system.md` (architectural
   invariants) and `docs/guides/writing-a-cyim-plugin.md`
   (task-oriented how-to).

**In a new `MacCracken/cyim-lsp` repo:**
6. Scaffold via `cyrius init cyim-lsp` (matches niyama / vyakarana
   layout).
7. Implement the LSP client: subprocess spawn of cyrius-lsp,
   JSON-RPC framing on pipes, response routing.
8. Wire to cyim's plugin ABI via `plugin_register_post_save_hook`,
   `plugin_register_post_change_hook`,
   `plugin_register_status_segment`, `plugin_register_ex_command`
   (`:lsp-restart`, `:lsp-status`).
9. Diagnostic rendering — populate cyim's diagnostic-provider
   side-channel from `textDocument/publishDiagnostics` payloads.
10. `gd` / `gr` keymaps via `plugin_register_normal_key`.
11. Tests + dist file generation via `cyrius distlib`.

**ABI freeze (after #11):**
12. ADR 0004 (or next free slot): records the cyim-plugin ABI as
    shipped at v1.4.0. Subsequent plugins develop against that
    contract. Breaking changes need an ADR + major version bump.

**Out of scope for v1.4.0** (and explicitly so):
- **Multi-plugin composition stress tests.** Until a second plugin
  exists, ABI composition is unverified. v1.4.x picks up if a
  second consumer surfaces; v1.5.0 might be the formalisation
  cut.
- **Plugin enable/disable at runtime.** Plugins are compile-time
  by §1. To "disable" a plugin, rebuild cyim without it. Runtime
  toggling is an explicit non-feature.
- **Plugin-on-plugin dependencies.** Plugins are leaf consumers
  of cyim. A plugin that depends on another plugin is a smell;
  if two plugins want shared code, that code goes into a
  separate Cyrius lib (not a plugin) and both `[deps]` it.

---

## References

- [`CLAUDE.md`](../../CLAUDE.md) — Refusal §0 (no embedded
  scripting), sandhi pattern, third-instance refactoring rule.
- [`docs/design-patterns.md`](https://github.com/MacCracken/agnosticos/blob/main/docs/design-patterns.md)
  Refusal §0 (genesis-repo source).
- [ADR 0001](0001-trust-model.md) — Trust model: interactive local
  user. Plugins inherit this trust model; users are responsible
  for which plugins they include.
- [ADR 0002](0002-regex-extensibility-shape.md) — `--regex=`
  extensibility shape. The `[plugins]` block follows the same
  "named-flavor" pattern at the manifest level: each plugin is a
  named extension, dispatched through a stable hook surface.
- [`docs/development/roadmap.md`](../development/roadmap.md) —
  Post-v1.0 demand-gated table; LSP client now promoted to v1.4.0.
- niyama 1.0.1's ADR 0011 (fold trigger) — precedent for
  Cyrius-library fold readiness criteria. cyim-lsp will follow a
  similar fold model if it earns multiple consumers; until then
  it stays a per-cyim plugin.
