# Design evidence and implementation decisions

Reviewed 2026-11-09. “AI-looking” is a subjective perception, not a measurable origin detector. Community comments are design hypotheses; technical behavior is grounded in official browser guidance and must be measured in this app.

| Source | Observation / recommendation | Applied decision and verification |
| --- | --- | --- |
| [Community discussion: less AI-looking](https://www.reddit.com/r/nocode/comments/1wgfkl2/make_your_site_less_ailooking/) (page shows relative age, exact day unconfirmed) | Comments criticize equal visual weight for every section and generic hierarchy. These are individual opinions, not a representative study. | Replace marketing-style repeated cards with a task-specific catalogue and reading desk. Review the actual full/empty/history states together. |
| [Community discussion: similar AI-built sites](https://www.reddit.com/r/webdevelopment/comments/1wldhiq/anyone_else_notice_every_aibuilt_site_looks_the/) (relative age only) | Discussion emphasizes intentional choices and preserving familiar navigation; novelty alone is not evidence of usability. | Keep recognizable search/import/download controls while making typography, numbering, surfaces and transitions specific to an archive. No invented testimonials or counts. |
| [NN/G: role of animation](https://www.nngroup.com/articles/animation-purpose-ux/) (2020-01-12) | Motion can communicate feedback, state and navigation; irrelevant persistent movement distracts. | Distinct import, selection and completion motion; optional richer ambient mode outside reading content. Check disabled mode preserves every function. |
| [web.dev: high-performance animations](https://web.dev/articles/animations-guide) | Prefer transform/opacity; layout and paint work need scrutiny. | Animate composited properties where possible; bounded Canvas effect rather than many moving DOM particles. Inspect frame pacing, long tasks and idle behavior instead of claiming universal 60fps. |
| [web.dev: prefers-reduced-motion](https://web.dev/articles/prefers-reduced-motion) | Respect the operating system's reduced-motion preference. | System reduction takes precedence over decorative effect settings; verify media-emulation behavior. |
| [MDN: Page Visibility](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API) | Avoid unnecessary background work when a document is hidden. | Stop the effect loop when hidden and resume only when appropriate. Verify lifecycle behavior and avoid accumulating animation loops. |

## What will not count as success

Changing a font or adding a glow alone; beautiful screenshots with broken flows; motion that cannot be disabled; effects obscuring mail; generic copy replacing useful status; tests that merely assert an implementation exists. Final assessment requires working interactions, usable contrast, narrow layouts, restrained resource use and the owner's review.

Artwork remains project-created CSS/SVG/Canvas; no third-party illustration or animation-library code is copied. Hanken Grotesk and Newsreader are locally bundled with their SIL Open Font License notices in `mailcairn/static/fonts/`; typography is therefore not wholly project-created. Application data remains local.

## Background arrival feedback — 2026-11-13

Rechecked [NN/G's role of animation](https://www.nngroup.com/articles/animation-purpose-ux/) and [Material's motion guidance](https://m3.material.io/styles/motion) on 2026-11-13. The former explains feedback and attention; the latter describes spatial continuity. These are design guidance, not evidence that this product's visual treatment satisfies users.

Applied inference: background synchronization should animate newly visible mail, while existing rows should remain still. Deliberate searches and paging retain the bounded eight-row entrance. New-row choreography has its own sequence without gaps inherited from old rows; reduced-motion and disabled-motion settings still take precedence. Behavioral coverage is recorded separately from real-browser and owner visual acceptance.

## Stronger light follow-up

Reviewed 2026-11-09: [MDN Canvas optimization](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas), page updated 2026-08-25. Static paper remains CSS, moving light is bounded Canvas, no per-particle shadowBlur is used, and backing-store pixels are capped. The renderer still creates gradients during frames; measured performance and scheduling limits are reported in test-results.md, not inferred from the implementation alone.
