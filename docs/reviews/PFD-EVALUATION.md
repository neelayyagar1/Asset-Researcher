# Perception-First Design: evaluation of the application shell

Artifact: Asset Researcher, home screen and Generate-a-report form.
Measured in-browser at 1440x900 against the live DOM, not estimated.
Framework: Perception-First Design (Kovalik), 5-layer diagnostic.

Scope note: this evaluates the **application shell**. The research note
itself is a separate surface and scores far higher; the gap between the
two is the finding that matters.

## Scores

| Layer | Score | Verdict |
|---|---|---|
| L0 Foundation (cognitive load) | 72 | Good. Few elements, clear task, no overload |
| L1 First impression (50ms) | 41 | **Poor.** Reads as an unfinished internal tool |
| L2 Processing fluency | 34 | **Poor.** Measured grid and alignment incoherence |
| L3 Perception bias | 55 | Mediocre. Claims are strong; presentation undercuts them |
| L4 Decision architecture | 61 | Mediocre. Path is clear but weighting is arbitrary |

L2 is the binding constraint. Fix it first; L1 rises with it.

## L2 findings, measured

**L2-GR-001 Grid Consistency — FLAGGED (medium).**
Rule: flag when distinct container max-widths exceed 3.
Form screen: `394.017px`, `512px`, `544px`, `704px` = 4 values.
Home screen: `528.62px`, `630.59px`, `704px` = 3 values.
Fractional values (`.017`, `.62`, `.59`) are `ch`-derived measures
resolving against a proportional font, so no two blocks share an edge.

**Three competing centre axes on one screen (home).**

| Element | Left | Right | Centre |
|---|---|---|---|
| Structural grid (`.ar-claims`) | 392 | 1048 | **720** |
| `h1` "Asset Researcher" | 392 | 1023 | **707** |
| Intro paragraph | 392 | 921 | **656** |

Mechanism: `text-align: center` applied to elements carrying a
`max-width` but no `margin-inline: auto`. The box stays left-anchored at
the column edge, so the text centres within the box rather than the
page. Three boxes of different widths produce three centre lines.
Wertheimer's alignment grouping (1923) treats shared edges as one unit;
here nothing shares an edge, so the eye re-locates the content boundary
on every block. Practitioner observation attached to L2-GR-001 records
users describing exactly this as "messy" or "unfinished" without being
able to name the cause. That matches the owner's report verbatim.

**The form repeats it.** `h1` left edge 448; every label, field and
helper paragraph beneath it 464. A 16px discrepancy, large enough to
perceive and too small to read as intentional. The heading is centred
while everything under it is left-aligned: two axes, one screen.

**L2-BT-001 Button Style Consistency — FLAGGED (high).**
Home buttons measure 166px and 155px wide, separated by a 167px gap,
because each is centred inside its own host-framework column rather
than placed in a shared row. The gap is as wide as the buttons. On the
form, the pair measures 476px against 148px.

**Host columns escape the content column.** The button row spans
392-1048 while the form's content column spans 464-976: 56px past the
left edge and 72px past the right. The row is not aligned to the page
because it is not in the page's grid.

**L2-TY-001 Font Family Count — borderline.**
Three families render: Faustina (display), Public Sans (body) and
Source Sans. The third is the host framework's default leaking through
unstyled elements. The intended system is two plus a monospace for
figures.

## L1 findings

The 50ms judgment currently returns "unfinished academic page." At
1440x900 the lower 40% of the viewport is empty while the content sits
in a narrow band, so the first fixation lands on a horizontal rule
above a title rather than on a proposition. There is no evidence of the
product's actual output anywhere above the fold - the strongest trust
signal available is a research note, and the opening screen shows none
of it. Fogg's Prominence-Interpretation Theory (2003): a trust signal
that is not prominent is not interpreted, because it is never noticed.

## L3 finding: experiential self-contradiction

The three claims read "Every figure is filed", "Every claim is located",
"The counter-case is mandatory" - an argument about rigour and
precision, set in a layout with four container widths, three centre
axes and two button sizes. The lived experience of the page
disconfirms its own thesis before the thesis is read. For a reader
evaluating the builder as much as the tool, this is the costliest
finding on the page.

Separately, "counter-case" is vocabulary this project's own
VOCABULARY.md condemned as having no professional usage, replaced by
"bear case" everywhere except here.

## Fix order

1. **One measure, one axis.** A single container width and one centre
   line that every block shares, headings included. This alone resolves
   the grid, alignment and the perception of unfinishedness.
2. **Take the button row out of host columns** and into the page's own
   markup, equal weights on a shared baseline.
3. **Put the product above the fold.** The note is the proof; show it.
4. **Vocabulary**: "counter-case" to "bear case".
5. Typography: eliminate the third family.

L1 is not fixed by decoration. It is fixed by the page becoming
coherent, which is an L2 operation.
