# Skills ledger

Every skill invoked on this project, in order, with what it changed. Written
because a skill that was installed and available (impeccable) sat unused
through weeks of UI work, and the only way that is visible from the outside
is if each invocation is recorded.

Rules for this file:

- An entry is written when the skill is invoked, not when it succeeds.
- If a skill cannot be invoked, that goes in "Needs the owner to run" below,
  with the exact command, rather than being quietly skipped.
- "Not used" is a legitimate entry. Silence is not.

## Invoked

| When | Skill | Surface / target | Outcome |
|---|---|---|---|
| 2026-11-20 | `superpowers:brainstorming` | Tonight's three tracks | Ordering decided; three forks put to the owner; this spec |
| 2026-11-20 | `claude plugin marketplace add/install` | `intent`, `perception-first-design` | Installed, user scope |

## Available and scheduled tonight

| Order | Skill | Why it, specifically |
|---|---|---|
| 1 | `superpowers:test-driven-development` | Stale-tag guard. Fixture first, then the fix |
| 2 | `perception-first-design:evaluate` | Diagnose the current screens before any pixel moves |
| 3 | `intent:wireframe` | Structure of home / gate / workspace / samples before CSS |
| 4 | `intent:articulate` | The words: Get Started steps, labels, errors |
| 5 | `impeccable:impeccable` | Surface briefs per screen, then the build against them |
| 6 | `superpowers:systematic-debugging` | Back/history navigation. Reproduce before fixing |
| 7 | `intent:vigil` (agent) | Heuristic + accessibility review of the finished screens |
| 8 | `perception-first-design:evaluate` | Second pass: did the fix hold |
| 9 | `code-review` | Correctness of the diff |
| 10 | `security-review` | Pending changes, before the link is shared |
| 11 | `superpowers:verification-before-completion` | Evidence before any "done" is claimed |

## Not used, and why

| Skill | Why not |
|---|---|
| `intent:investigate` | Needs real users to research. There is one known reader |
| `intent:localize`, `intent:transpose` | Single market, single platform |
| `intent:measure` | No analytics on a private demo, by design |
| `intent:present` | The deliverable is the live link, not a deck |

## Needs the owner to run

Commands the assistant cannot launch itself. Exact text to paste:

- Deep multi-agent cloud review (billed, user-triggered only):

      /code-review ultra

- Streamlit Cloud secrets cannot be read or written from here. The gate
  passphrase and API keys are set only in the app's own Settings -> Secrets.

## Verification standard

A UI claim is backed by a rendered screenshot, not by a grep. Two of this
project's regex "proofs" were wrong: `<th[^>]*>` also matched `<thead>`,
inflating every header count by one, and a dry run reported four clean
companies as broken because it read `.metrics` on an object whose field is
`.series`. Counting is not looking.
