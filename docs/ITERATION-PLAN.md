# Quality iteration — active, not a release

Started 2026-11-09. Owner approval is required before final delivery or GitHub upload. The previous v1 package is a baseline, not the result of this new request.

## Current envelope and transfer revision

User requested stronger motion again. Four-sheet envelope choreography and real
message-selection paper transfer are implemented; 28 frontend checks pass.
Actual runtime, fixed-viewport phase bounds and independent screenshot review
are recorded in spectacle-evidence.json. Owner acceptance remains pending; no
publication authorization.

## Previous typography and interaction revision — 2026-11-09

The owner rejected the preceding generic typography, repeated microcopy,
rigid controls and disconnected effects. The current revision replaces these
with local Hanken Grotesk / Newsreader fonts, concise copy, rounded controls,
underline input focus, paper unfolding and a cancellable real-reader hinge.
76 Python tests and 25 frontend behavior checks pass. Actual browser import,
duplicate/error/search, sampled theme/contrast, narrow selection/back navigation
and motion controls were verified. See `editorial-evidence.json` and the first
section of `test-results.md`. User visual acceptance is still pending; no upload
is authorized. The sections below retain prior requirements and historical work.

## Previous stronger-light iteration — 2026-11-09

Owner chose stronger animation and lighting after seeing the previous candidate. Implementation and local verification are complete for this round; owner visual acceptance remains pending. See cinematic-evidence.json and the stronger-light section of test-results.md. Earlier passed results below describe the prior candidate only. New requirements: visibly stronger layered lighting and depth; a scene entry available with populated archives; coherent interaction motion; preserved readable mail, reduced-motion and visibility cancellation; fresh browser and regression evidence. No publication authorization was given.

## Acceptance requirements

| Requirement | Implementation / proof required | Current status |
| --- | --- | --- |
| Distinctive frontend | Coherent archive-specific hierarchy, reading workspace, original details, light/dark/narrow screenshots inspected | Implemented; screenshots inspected; owner style acceptance pending |
| Motion and interaction | Working state transitions, keyboard commands/navigation, clear loading/cancel/error/focus behavior | Verified locally; keyboard and narrow focus flows passed |
| Particle/light rendering | Real Canvas effects with useful activation/preview, bounded particles/DPR, visibility pause, no perpetual work when disabled | Real Canvas pixels and bounded completion, OS reduction and background-tab stop verified |
| Personalization | Persistent theme/accent/density/type size/motion choices; system preference and corrupt-storage fallback | Reload, corrupted/unavailable storage and system-theme behavior verified |
| Accessibility and resilience | Reduced-motion honored; keyboard and touch operation; contrast and overflow checked; no remote mail resources | Tested axe scenarios passed; 320/390px reflow passed; no screen-reader/physical-touch certification |
| Backend quality | Bounded batch ingestion without weakening durability, atomic receipts, failure-safe restore, bounded HTTP resources | Implemented; current 76 Python tests passed, including new exact font-serving boundary checks |
| Performance | Repeat the same 10,000-message workload; compare import/search/memory and retained correctness | Same-input 10k comparison completed: 131.031 → 15.607 seconds |
| Browser acceptance | Real upload/search/read/export/restore plus customization/reload/keyboard/narrow/failure cases | Core flows, downloads, CLI restore, errors and preferences verified |
| Research applied | Sources and reasoned mapping, not an objective claim that a visual style can be proven human-made | Current revision in design-research-current.md; historical work in design-research.md |
| Release readiness | Updated bilingual documentation, license audit, no private data, complete known-limit report | Local docs/screenshots/license/source checks prepared; remote CI unrun |
| User review | Show actual result, disclose boundaries/defects, collect explicit acceptance, iterate if needed | Candidate screenshots and limitations shown; iteration-direction feedback requested; explicit acceptance pending |
| Publication | Only after user's explicit confirmation of result and upload | Not authorized yet |

## Work ownership

- GPT-6 Astra / high frontend agent: static/.
- GPT-6 Astra / high backend agent: Python application modules.
- GPT-6 Astra / high QA agent: tests/ and benchmark tooling.
- Lead: integration, research evidence, real browser verification, progress/handoff and approval boundary.

Before-iteration baseline: 50 tests passed on Windows in 4.629 seconds. Historical benchmark: 10,000 text-only messages / 103,084,670 bytes, 131.031 seconds ingestion, 29.05 MiB peak working set. Do not reuse old screenshots or old green results as evidence for changed code.
