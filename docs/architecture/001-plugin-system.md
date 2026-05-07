# 001 — Plugin system

> **Non-obvious invariants for cyim's Cyrius-plugin extension surface.**
> Decision rationale lives in [ADR 0003](../adr/0003-cyrius-plugin-system.md);
> this file is the architectural reference future readers reach for
> when they need to know *what's true* about the plugin system, not
> *why we chose it*.

---

## What plugins are

cyim accepts **AOT-compiled Cyrius plugins** folded into the binary
at build time via the sandhi pattern (the same pattern vyakarana
and niyama already use). A plugin is a Cyrius library shipped as a
distfile (`dist/<plugin>.cyr`) that cyim pulls in via explicit
`include` from `src/main.cyr`. The cyrius compiler concatenates
plugin source into cyim's translation unit; DCE strips unused
plugin code at link time.

Plugins are **not**:
- Embedded scripts (Lua / Python / Vimscript) — refused per
  [`CLAUDE.md` Refusal §0](../../CLAUDE.md). The cyim binary has
  no interpreter, no eval, no plugin VM.
- Runtime-loaded modules — there is no `dlopen`. The binary
  shipped to the user contains the plugin set decided at build.
- Sandbox-isolated — plugins are trusted code, treated identically
  to cyim's own source per [ADR 0001's trust model](../adr/0001-trust-model.md).
- Allowed to extend the modal grammar — they extend the
  *dispatch table* (action mappings, ex-commands, hooks). The
  modal grammar (NORMAL / INSERT / COMMAND / VISUAL) is fixed.

## ABI surface

The plugin ABI is defined in [`src/plugin.cyr`](../../src/plugin.cyr).
Six hook types, registered via `plugin_register_*` calls and
invoked by cyim's core via `_plugin_fire_*` / `_plugin_lookup_*` /
`_plugin_collect_*` helpers.

| Hook | fp signature | Use case |
|------|--------------|----------|
| `post_save_hook` | `fn(s, path) -> 0` | LSP `textDocument/didSave` |
| `post_change_hook` | `fn(s) -> 0` | LSP `textDocument/didChange` |
| `status_segment` | `fn(s) -> cstring` | Right-aligned status segment ("E:3 W:1") |
| `normal_key` | `fn(s) -> action_id` | NORMAL-mode key handler (`gd` for go-to-def, etc.) |
| `ex_command` | `fn(s) -> exit_code` | `:lsp-restart`, `:fmt`, ... |
| `diagnostic_provider` | `fn(s, b, out_vec) -> 0` | Append diagnostics for buffer rendering |

**v1.3.4 wires only** `post_save` + `post_change` fire-points into
cyim's core dispatch (after `_cmd_w` save success in
`src/command.cyr`; after `editor_step` if `buf_version` changed
in `src/driver.cyr`). The other four hooks have register / lookup /
collect helpers in place but are not yet called from cyim's
render / mode-dispatch / command paths — those wire-ups land at
v1.3.5+ when a real plugin (cyim-lsp at v1.4.0) surfaces what it
actually needs from each hook.

The full ABI surface freezes at **ADR 0004** (planned for the cyim
1.3.x series, after the LSP forces ABI choices). Until then, the
listed surface is *provisional* and may shift in 1.3.x cuts as
the prototype consumer surfaces edge cases.

## Storage shape

Six vec globals in `src/plugin.cyr`, lazily initialized by
`plugin_init()`:

```text
_plugin_post_save_hooks      vec<fp>             # simple hook
_plugin_post_change_hooks    vec<fp>             # simple hook
_plugin_status_segments      vec<fp>             # producer hook
_plugin_normal_keys          vec<keyed_record>   # keyed hook
_plugin_ex_commands          vec<keyed_record>   # keyed hook
_plugin_diagnostic_provs     vec<fp>             # producer hook
```

Keyed records (`normal_key`, `ex_command`) allocate a 24 B
heap struct: `{ name_or_key_ptr, name_len, fp }`. Simple +
producer hooks store fp directly as i64.

`plugin_init()` is **idempotent** — safe to call twice. Each
registry pointer is checked against 0 before being assigned a
fresh `vec_new()`; subsequent calls leave existing registrations
intact.

## Fire-point semantics

- **Simple hooks (`post_save`, `post_change`):** every registered
  fp is called in registration order; return values are ignored.
  Fire-and-forget.
- **Keyed hooks (`normal_key`, `ex_command`):** lookup walks the
  vec for the first matching key/name and returns its fp (or 0).
  First registration wins on duplicate keys; cyim's built-ins
  always win over plugin registrations (cyim's modal grammar is
  the inheritance — plugins extend, never override).
- **Producer hooks (`status_segment`, `diagnostic_provider`):**
  every registered fp is called; outputs are accumulated into the
  caller-owned aggregate (gap buffer for status, vec for
  diagnostics).

## post_change firing rule

cyim fires `post_change` from `editor_step` only when the active
buffer's version (`buf_version(b)` at offset +32) increments
during the step. Every cyim mutating primitive
(`buf_insert_byte`, `buf_delete_left`, `buf_delete_right`,
`buf_clear`) calls `buf_bump_version`, so every direct mutation
funnels through the version counter; non-mutating steps (motions,
mode toggles, search submission) leave the version unchanged
and don't fire.

This avoids the LSP-flooding failure mode where every keystroke
triggers a `didChange` even on pure-motion presses. It also
avoids over-engineering — no debouncer, no per-action allowlist,
just a single load64 + comparison on each step.

## Trust and audit model

Per [ADR 0001](../adr/0001-trust-model.md), cyim is for an
interactive local user; plugins inherit the trust model. A
malicious Cyrius plugin can do anything cyim can do — there's no
sandbox. Mitigation:

1. **Build-time visibility.** Every plugin's contribution is
   visible at `cyrius lint` / `cyrius build` / CHANGELOG-diff
   time. Reading the CHANGELOG of a cyim release tells you which
   plugins are linked in.
2. **No drive-by install.** Adding a plugin requires editing
   `cyrius.cyml`, running `cyrius deps`, and rebuilding cyim.
   Three explicit steps; not "drop a file in `~/.cyim/plugins/`".
3. **AOT type-checking.** Plugin compile-time errors surface as
   cyrius compile errors against the cyim binary, not runtime
   surprises.
4. **DCE-stripping.** A plugin's code that doesn't get called
   is dead-code-eliminated, so unused plugin features don't
   inflate the attack surface or the binary.

Users (or distro packagers) deciding which plugins to include
should treat `cyrius.cyml [plugins.<name>]` entries with the same
care as any code dependency: prefer signed releases, audit
source, pin tags.

## Manifest convention

Plugins are declared in cyim's `cyrius.cyml`:

```toml
[plugins.cyim-lsp]
git = "https://github.com/MacCracken/cyim-lsp.git"
tag = "1.0.0"
modules = ["dist/cyim-lsp.cyr"]
```

This mirrors the existing `[deps.<name>]` shape exactly. The
`[plugins.<name>]` section name is **documentary, not
mechanical** — at the cyrius build-tool level today, a plugin
is structurally identical to any external Cyrius dep. The
naming makes cyim-side intent visible:

- `grep '\[plugins\]' cyrius.cyml` lists the editor's extension
  surface.
- `grep '\[deps' cyrius.cyml` lists transitive language libraries.

If cyrius adds first-class `[plugins]` parsing in a future
release, cyim picks it up at the next toolchain bump. Until
then, the section name is a convention.

## Hook expansion policy

The initial hook set (the 6 listed above) was chosen against
ADR 0003's design + cyim-lsp's anticipated needs. **Adding a new
hook type requires an ADR.** This is the load-bearing constraint
that keeps plugins composable: two plugins can both register
ex-commands without colliding, but neither can "tap into
`editor_step` byte-by-byte", neither can "intercept `:w`",
neither can "replace the search engine."

A future hook (e.g. `pre_save`, `pre_quit`, `register_text_object`)
gets:

1. An ADR justifying the hook point and its semantics.
2. A reference plugin or cyim-side use case demonstrating the
   need.
3. Implementation in `src/plugin.cyr` mirroring the existing
   shape (registry, register API, fire/lookup/collect helper).
4. Wire-up in cyim's core at the documented call site.
5. Update to this file's hook table.

## Test surface

[`tests/plugin.tcyr`](../../tests/plugin.tcyr) exercises the
register → fire / lookup / collect cycle without any external
plugin. It registers a per-hook-type counter callback, drives
small editor sequences, and asserts the callbacks fired (or not)
at the documented call sites. The eight existing test files that
include `src/driver.cyr` or `src/command.cyr` had
`include "src/plugin.cyr"` added before those includes (Cyrius is
single-pass; plugin.cyr's symbols must be defined before
references in command.cyr / driver.cyr resolve).

`tests/cli_smoke.sh` and `tests/integration_smoke.py` exercise the
plugin scaffold transitively — every cyim CLI invocation runs
through `plugin_init()` at startup, so the lazy-init path stays
covered.

## What's NOT in the plugin system (and won't be)

Per ADR 0003 § Out of scope:

- **Multi-plugin composition stress tests** — until a second
  plugin exists, ABI composition is unverified. v1.4.x picks up
  if a second consumer surfaces.
- **Runtime enable/disable** — plugins are compile-time. To
  "disable" a plugin, rebuild cyim without it. Runtime toggling
  is an explicit non-feature.
- **Plugin-on-plugin dependencies** — plugins are leaf consumers
  of cyim. Shared code goes into a separate Cyrius lib (not a
  plugin); both plugins `[deps]` it from there.

## See also

- [ADR 0003 — Cyrius plugin system](../adr/0003-cyrius-plugin-system.md)
  (decision rationale, alternatives considered, plan)
- [ADR 0001 — Trust model](../adr/0001-trust-model.md) (plugins
  inherit the interactive-local-user trust model)
- [`docs/development/roadmap.md`](../development/roadmap.md) (LSP
  client at v1.4.0; ABI freeze in ADR 0004 at v1.3.5+)
- [`src/plugin.cyr`](../../src/plugin.cyr) (the ABI itself)
- [`tests/plugin.tcyr`](../../tests/plugin.tcyr) (worked example
  of register / fire / lookup)
