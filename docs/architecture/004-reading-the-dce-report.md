# 004 — A DCE report is not a dead-code list

**Added:** 2026-08-23 (v1.8.5, out of hardening-audit residual R-2)

---

## The thing you cannot derive

`CYRIUS_DCE=1 CYRIUS_DCE_VERBOSE=1 cyrius build` prints every function
unreachable from `main`. For cyim that is **~514 symbols, of which 24 are
cyim's own** — and deleting any of those 24 would be wrong.

"Unreachable from `main`" and "dead" are different questions, and for this
project they diverge for three structural reasons:

| Why it is unreachable from `main` | Count | May it be deleted? |
|---|---:|---|
| **Frozen plugin ABI** — `plugin_list_*`, `plugin_register_normal_key`, `plugin_last_diags`, `diag_*` | 9 | **No.** [ADR 0004](../adr/0004-plugin-abi-freeze.md) forbids removal for the whole 1.x line, whether or not cyim itself calls them. They exist *for* out-of-tree callers |
| **Test / fuzz introspection** — `buf_cap`, `buf_gap`, `buf_save_was_atomic`, `editor_last_error`, `editor_run`, `editor_drive`, `editor_set_mode`, `lang_index`, `lang_is_valid`, `marks_count`, `visual_selection_hi`/`_lo`, `window_count_leaves` | 13 | **No.** Reachable from `tests/*.tcyr` and `fuzz/*.fcyr`, which are separate compilation units. The harnesses are not in `main`'s graph and never will be |
| **Documented-deferred config** — `editor_cfg_tabstop`, `editor_cfg_line_numbers` | 2 | **No.** Stored-but-not-yet-rendered, per [`cyimrc.md`](../guides/cyimrc.md) and the roadmap's deferred-notes section |

## How to read it, then

The DCE count is a **size metric**, not a backlog. The question worth asking
of it is not "what is unreachable" but:

> **Does every unreachable cyim-side symbol have a caller somewhere —
> `src/`, `tests/`, or `fuzz/`?**

A symbol with no caller anywhere is either genuinely dead, or a **coverage
hole**. Both are worth acting on; they are not the same action.

At 1.8.5 the answer was 23 of 24, and the exception was instructive:
`diag_msg` had no caller because `diag_line` and `diag_severity` were both
tested and the third accessor of the same record was not. It looked like dead
code and was a missing test. Deleting it would have broken the frozen ABI and
left an incomplete accessor set behind. The fix was the test.

The check, in one shell loop:

```sh
CYRIUS_DCE=1 CYRIUS_DCE_VERBOSE=1 cyrius build src/main.cyr build/cyim 2>&1 \
  | grep -oP '^  dead: \K.*' | sort -u \
  | while read f; do
      grep -qE "^fn ${f}\(" src/*.cyr src/plugins/*.cyr 2>/dev/null || continue
      callers=$( { grep -rhoE "\b${f}\(" tests/*.tcyr tests/*.bcyr fuzz/*.fcyr 2>/dev/null
                   grep -rhnE "\b${f}\(" src/*.cyr src/plugins/*.cyr 2>/dev/null \
                     | grep -vE "^[0-9]+:fn ${f}\("; } | wc -l )
      [ "$callers" = "0" ] && echo "NO CALLERS: $f"
    done
```

## Where real dead code actually turned up

Not in the function report. The 1.8.5 sweep found nothing worth deleting there
and five findings **one level down**, in a class the DCE pass does not model:

**A named constant the code does not use.** `BUFFER_REC_SIZE`,
`RENDER_LINE_BUF`, `KEY_CTRL_R`, `_CYIMRC_PALETTE_SLOTS` and the
`REPLACE_FIRST_UNIQUE` / `REPLACE_ALL` pair were all declared beside the thing
they described while the code carried on using the literal. That is worse than
unused: the declaration and the literal can drift, the constant's name appears
in comments as if it were load-bearing, and grepping for it finds prose. Four
were wired up; one (`_CYIMRC_PALETTE_SLOTS`, a byte size that a `var buf[N]`
declaration can never reference) was replaced by a count that could be.

The scan that finds them — declared globals whose only occurrence *in code,
with comments stripped* is the declaration — is worth re-running each closeout,
because the function-level DCE report will never show it.

## See also

- [2026-08-23 hardening audit](../audit/2026-08-23-1.8x-hardening.md) § R-2
- [ADR 0004 — Plugin ABI freeze](../adr/0004-plugin-abi-freeze.md)
