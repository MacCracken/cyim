# 003 — The renderer is byte-oriented, not codepoint-oriented

**Added:** 2026-08-23 (v1.8.3, out of hardening-audit finding F-7)

---

## The invariant

`render_build_line` walks the gap buffer **one byte at a time** and
treats each byte as one terminal column:

```cyrius
var c = buf_get(b, i);
var kind = highlight_kind_at(tb, i);
...
col = col + 1;
```

There is no UTF-8 decode step anywhere in the render path. `cols` counts
bytes emitted, not characters displayed.

## What follows from it

These are not four separate gaps. They are one decision, and they move
together:

- **Multi-byte characters count as several columns.** A line of CJK or
  accented text truncates earlier than its visual width suggests.
- **Double-width characters are not accounted for.** A CJK glyph occupies
  two terminal cells and one buffer byte per UTF-8 byte; cyim's column
  arithmetic knows neither number.
- **Combining characters count as columns of their own**, though they
  render as zero-width.
- **C1 control bytes (`0x80`–`0x9F`) pass through unsubstituted.**
  `render_ctrl_substitute` handles C0 (`0x00`–`0x1F`, Tab excepted) and
  DEL, which closes the escape-injection finding from the M6 audit. It
  cannot extend to C1 **because `0x80`–`0x9F` overlaps the UTF-8
  continuation-byte range `0x80`–`0xBF`**: substituting them blind would
  mangle every non-ASCII character in every file. Telling a continuation
  byte from a lone C1 byte requires decoding, which is the thing this
  note is about.

## Why this is the right trade today, and where it stops being one

The gap buffer stores bytes; cursor motion, undo, marks, search offsets
and the tokenizer's spans are all byte offsets. A codepoint-aware
renderer is not a change to `render_build_line` — it is a second
coordinate system threaded through every one of those, plus a width
table (`wcwidth`-equivalent) cyim does not have and would need to vendor
or derive from `unicode/`.

The exposure it buys back is small and getting smaller. Terminals are
overwhelmingly UTF-8; a lone `0x9B` renders as a replacement glyph, not
as CSI. Honouring 8-bit C1 controls requires a terminal explicitly in
that mode, which is legacy configuration rather than a default anywhere
current.

**What would change the calculus:** a consumer editing CJK or RTL text
in earnest. `aethersafha` hosting cyim in a compositor terminal is the
likeliest trigger — that is the point where "one byte, one column" stops
being an implementation detail and starts being a visible defect.

## What NOT to do

Do not "fix" C1 pass-through by adding `0x80`–`0x9F` to
`render_ctrl_substitute`. It looks like a two-line hardening patch and it
breaks every non-ASCII file cyim can open. The audit considered exactly
this and rejected it; if you are reading this note because you had the
same idea, that is what it is here for.

## See also

- [2026-08-23 hardening audit](../audit/2026-08-23-1.8x-hardening.md) § F-7
- [2026-04-25 M6 audit](../audit/2026-04-25-m7-audit.md) — F-1, the C0
  substitution this note bounds
- `src/render.cyr` — `render_ctrl_substitute`
