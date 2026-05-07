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
**Frozen at v1.3.6 per [ADR 0004](../adr/0004-plugin-abi-freeze.md);
1.x-stable.** Six hook types + three additive operations / extensions
(per the ADR's "additions allowed" envelope).

### Registration surface (6 hooks, frozen v1.3.6)

| Hook | fp signature | Use case | Wired in cyim core |
|------|--------------|----------|--------------------|
| `post_save_hook` | `fn(s, path) -> 0` | LSP `textDocument/didSave` | `_cmd_w` save success path (`src/command.cyr`) |
| `post_change_hook` | `fn(s) -> 0` | LSP `textDocument/didChange` | `editor_step` after `buf_version` increments (`src/driver.cyr`) |
| `status_segment` | `fn(s) -> cstring` | Right-aligned status segment ("E:3 W:1") | `render_status` (`src/render.cyr`) |
| `normal_key` | `fn(s) -> action_id` | NORMAL-mode key handler | `editor_dispatch` after built-in keymap miss (`src/mode.cyr`) |
| `ex_command` | `fn(s) -> exit_code` | `:lsp-restart`, `:fmt`, ... | `command_execute` after every built-in `:cmd` miss (`src/command.cyr`) |
| `diagnostic_provider` | `fn(s, b, out_vec) -> 0` | Append diagnostics for buffer rendering | `render_frame` once per frame (`src/render.cyr`) |

All six fire-points active from v1.3.5. Built-ins win on conflict
for keyed hooks (`normal_key`, `ex_command`) per ADR 0003 §3 —
plugin lookup is consulted only after every built-in misses.

### Additive extensions (1.4.x / 1.5.x)

Three additions landed under ADR 0004's "additions allowed"
envelope. None broke the 1.x freeze:

| Symbol | Version | Purpose |
|---|---|---|
| `plugin_register_normal_prefix_key(prefix, key, fp)` | 1.4.2 | Two-byte NORMAL-mode prefix sequence (e.g. `(KEY_G, 'd')` for cyim-lsp's `gd`); built-ins win on conflict |
| `plugin_buf_load_file(s, path)` | 1.4.2 | Load file into a new buffer + switch active. Wraps the same `:e <file>` machinery; returns buf or 0 with `editor_last_error` set |
| `plugin_list_display(s, items, count, on_select)` | 1.5.0 | Display a bottom-anchored popup picker (j/k/Enter/Esc/q surface). `on_select(s, idx)` fires on Enter then dismisses |

The first is registration-shaped; the latter two are operations
plugins call to drive cyim state. ADR 0004's amendments document
each in detail.

## Storage shape

Globals in `src/plugin.cyr`, lazily initialized by
`plugin_init()`:

```text
_plugin_post_save_hooks      vec<fp>             # simple hook
_plugin_post_change_hooks    vec<fp>             # simple hook
_plugin_status_segments      vec<fp>             # producer hook
_plugin_normal_keys          vec<keyed_record>   # keyed hook
_plugin_normal_prefix_keys   vec<prefix_record>  # keyed hook (v1.4.2)
_plugin_ex_commands          vec<keyed_record>   # keyed hook
_plugin_diagnostic_provs     vec<fp>             # producer hook
_plugin_last_diags           vec<diag>           # per-frame collected output
_plugin_list_active          i64 (0/1)           # list-display state (v1.5.0)
_plugin_list_items           vec<cstring>        # active picker labels
_plugin_list_count           i64                 # items count
_plugin_list_index           i64                 # current selection
_plugin_list_on_select       fp                  # Enter callback
```

Keyed records (`normal_key`, `ex_command`) allocate a 24 B heap
struct: `{ name_or_key_ptr, name_len, fp }`. Prefix records
(`normal_prefix_keys`, v1.4.2) also 24 B:
`{ prefix, key, fp }`. Simple + producer hooks store fp directly
as i64. List-display is a singleton (one active picker at a time;
calling `plugin_list_display` while another is up replaces).

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

Plugins are declared in cyim's `cyrius.cyml` as `[deps.<name>]`
blocks (cyrius's standard external-dep shape):

```toml
[deps.cyim-lsp]
git = "https://github.com/MacCracken/cyim-lsp.git"
tag = "1.2.0"
modules = ["dist/cyim-lsp.cyr"]
```

`cyrius deps` resolves the entry, vendors the distfile under
`~/.cyrius/deps/cyim-lsp/<tag>/`, and symlinks the tagged
`dist/cyim-lsp.cyr` into cyim's `lib/`. cyim's `src/main.cyr`
brings the bundle into the TU via `include "lib/cyim-lsp.cyr"`.

The earlier draft of this doc proposed a documentary
`[plugins.<name>]` section name to distinguish editor-extending
deps from language-library deps; experience showed the
`[deps.<name>]` shape works fine in practice (vyakarana, niyama,
cyim-lsp are all `[deps]`). The intent is communicated by the
`<name>` itself + a top-level comment in `cyrius.cyml`.

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
plugin. It registers per-hook-type counter callbacks, drives
small editor sequences, and asserts the callbacks fired (or not)
at the documented call sites. **88 assertions across 22+ test
groups** as of v1.6.0 — covers all six hooks plus the v1.4.2 /
v1.5.0 additive extensions (prefix-keymap registration + dispatch
+ built-in-wins-on-conflict; buf-load-file + dedup + missing-file
+ null-path; list-display + j/k navigation + clamping +
Enter/LF/Esc/q lifecycle + buffer-untouched-during-list +
prefix-clear on display per F-CO-3).

Every test file that includes `src/mode.cyr`, `src/driver.cyr`,
or `src/command.cyr` also includes `src/plugin.cyr` (Cyrius is
single-pass; module-scope `var` references must resolve to a
declaration earlier in the TU, and mode.cyr references plugin.cyr
globals like `_plugin_list_active`).

`tests/cli_smoke.sh` and `tests/integration_smoke.py` exercise the
plugin scaffold transitively — every cyim CLI invocation runs
through `plugin_init()` at startup, so the lazy-init path stays
covered.

`tests/smcyr/lsp_fold.smcyr` (the first cyim `.smcyr` smoke
harness, landed v1.4.1) exercises cyim-lsp's protocol bundle
end-to-end against a real `cyrius-lsp` subprocess: spawn →
initialize handshake → describe → clean stop → idempotent
restart. Runs under `cyrius smoke`.

## Live consumers

Two plugins are folded in by default as of v1.6.0:

- **`cyim-lsp`** — LSP client; external repo
  [`MacCracken/cyim-lsp`](https://github.com/MacCracken/cyim-lsp)
  at tag 1.2.0. Activates `gd` / `gr` / `:lsp-*` ex-commands,
  diagnostics surfaces, refs quickfix list. Consumer-side glue
  lives at [`src/plugins/lsp_glue.cyr`](../../src/plugins/lsp_glue.cyr)
  (~520 lines, mirrors cyim-lsp's
  `docs/examples/cyim_glue.cyr` reference).
- **`trailing_ws`** — inline plugin at
  [`src/plugins/trailing_ws.cyr`](../../src/plugins/trailing_ws.cyr).
  Trailing-whitespace highlighter; uses `post_change_hook` +
  `diagnostic_provider` + `status_segment` (3 of 6 hook types).
  Stays inline since the simple line-set bookkeeping doesn't
  justify external repo overhead.

Both register their hooks from `<plugin>_init()` functions called
from cyim's `main()` after `plugin_init()`:

```cyrius
fn main() {
    alloc_init();
    args_init();
    plugin_init();
    trailing_ws_init();
    cyim_lsp_init();
    // ...
}
```

## What's NOT in the plugin system (and won't be)

Per ADR 0003 § Out of scope:

- **Runtime enable/disable** — plugins are compile-time. To
  "disable" a plugin, rebuild cyim without it. Runtime toggling
  is an explicit non-feature.
- **Plugin-on-plugin dependencies** — plugins are leaf consumers
  of cyim. Shared code goes into a separate Cyrius lib (not a
  plugin); both plugins `[deps]` it from there.
- **Stacked / nested pickers in list mode** — `plugin_list_display`
  is a singleton (1.5.0 design choice). Chained pickers work
  (on_select can call `plugin_list_display` again after dismiss),
  but two pickers can't be stacked on screen.
- **Plugin-driven mode transitions via prefix-keys** — by design.
  v1.4.2's `plugin_register_normal_prefix_key` returns `ACT_NONE`
  past the dispatch interception. Plugins that need mode changes
  use `ex_command`.

## See also

- [ADR 0003 — Cyrius plugin system](../adr/0003-cyrius-plugin-system.md)
  (decision rationale, alternatives considered, plan)
- [ADR 0004 — Plugin ABI freeze (v1.3.6)](../adr/0004-plugin-abi-freeze.md)
  (the freeze + v1.4.2 / v1.5.0 amendments documenting the
  additive extensions)
- [ADR 0001 — Trust model](../adr/0001-trust-model.md) (plugins
  inherit the interactive-local-user trust model)
- [`docs/development/roadmap.md`](../development/roadmap.md)
  (closed milestones + carry-over LSP polish + demand-gated
  features)
- [`src/plugin.cyr`](../../src/plugin.cyr) (the ABI itself)
- [`tests/plugin.tcyr`](../../tests/plugin.tcyr) (88 assertions
  across 22+ test groups as of v1.6.0 — registration / dispatch /
  conflict resolution / list-mode lifecycle / prefix-clear
  defense)
