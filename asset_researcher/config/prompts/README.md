# Prompts

Every instruction sent to the model lives here as a `.md` file, loaded by
name, never inline in application logic. A prompt change is then a one-file
diff that a non-engineer can read and review without opening any Python.

- `narrative.md`, Call A: the cited descriptive sections.
- `reconciliation.md`, Call B: the reconciliation, thesis, variant views and
  the disconfirming case.
- `mandate_parse.md`, free text describing a mandate to a structured profile.
- `concept_resolution.md`, a filer's XBRL concept names to canonical metrics.
- `_style.md`, the shared register and prohibitions, appended to the two
  writing prompts so the rules live in one place rather than two.

Two rules hold across all of them and are the reason the output can be
trusted. The model may not write a financial figure in prose; the renderer
inserts filed values. And the model may not use knowledge of the company
beyond the supplied documents, because that knowledge is unverifiable here.
