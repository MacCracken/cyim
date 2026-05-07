# Contributing to cyim

Thanks for your interest. cyim is part of the
[AGNOS library](https://github.com/MacCracken/agnosticos); the
overall contribution norms live there. This file collects the
cyim-specific bits.

## Before you open a PR

1. **Read [`CLAUDE.md`](CLAUDE.md).** It's the durable rulebook for
   this project — process, hard constraints, Cyrius idioms,
   documentation conventions.
2. **Run the full local check** that CI runs:
   ```sh
   cyrius deps                             # resolve vyakarana + cyim-lsp
   cyrius build src/main.cyr build/cyim    # default build
   CYRIUS_DCE=1 cyrius build ...           # DCE parity
   cyrius test                             # all .tcyr suites (~973 assertions)
   cyrius fuzz                             # fuzz harnesses
   cyrius smoke                            # tests/smcyr/* (LSP protocol harness)
   cyrius bench tests/perf.bcyr            # gap-buffer / search / render perf
   python3 tests/integration_smoke.py      # PTY end-to-end
   cyrius lint src/*.cyr                   # advisory only
   ```
   Everything must be green.
3. **Update the CHANGELOG.** New behavior gets a bullet under
   `[Unreleased]`. Performance claims need numbers from
   `tests/perf.bcyr`. Security-relevant changes reference the
   audit doc.
4. **One change per PR.** A bug fix doesn't need surrounding
   refactors; a refactor PR shouldn't change behavior. Mixing the
   two slows review and obscures intent.

## What cyim refuses

These are load-bearing refusals — please don't propose them as
features without a prior conversation:

- No embedded scripting language (Vimscript / Lua / Python /
  anything). Configuration is data, not code. The cyim binary
  has no interpreter, no eval, no plugin VM.
- No `dlopen` / runtime-loaded plugins. cyim **does** have a
  plugin system (cyim-lsp ships at v1.4.0+, trailing_ws inline
  since 1.3.5) but plugins are AOT-compiled Cyrius bundles
  folded into the binary at build time via the sandhi pattern —
  not runtime-loaded scripts. The refusal is on eval, not on
  bundles.
- No GUI. cyim is a TTY editor.
- No `:!cmd` shell-out. Use Ctrl-z + your shell + `fg`.
- No modeline parsing. The `.cyimrc` config surface is the only
  load path for editor settings.

See [docs/security/2026-04-25-0day-corpus.md](docs/security/2026-04-25-0day-corpus.md)
for the security rationale — these refusals are the bulk of why
the editor's CVE surface stays small.

## Filing an issue

Open against the cyim repo. Useful info to include:

- cyim version (`./build/cyim --version`)
- Cyrius toolchain version (`cyrius --version` or `cc5 --version`)
- Repro steps (`cat keystrokes | script -q -c './build/cyim file' /dev/null`)
- Expected vs. actual

For security issues, see [`SECURITY.md`](SECURITY.md).

## License

By contributing you agree your work ships under cyim's
[GPL-3.0-only](LICENSE) license.
