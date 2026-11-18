# MailCairn interface

Updated 2026-11-09 from the user's review of the previous candidate.
This is an implementation direction, **not user acceptance** of the new effect.

## Product and use

MailCairn is a personal, local MBOX/EML archive. The main surfaces are task-focused
(import, search, read, recover attachments, back up); introductory paper artwork
may be expressive. Actual mail remains plain text. Decorative scenes never
replace working mail or introduce fabricated collection data.

## Typography and copy

- Hanken Grotesk is the local variable UI/body face; Newsreader is the local
  variable display face. Fonts remain separately OFL licensed.
- Use size, weight and spacing for hierarchy. Remove ornamental uppercase
  eyebrows, invented catalogue identifiers and repeated privacy slogans.
- Controls name actions. Keep format restrictions, import outcomes, storage
  limits and recovery instructions where the user needs them.
- Interface and documentation support English and Simplified Chinese. Language
  buttons are direct EN/中文 choices; switching never translates private mail.

## Current interaction direction

- No standalone replay, light-scene or effect-preview controls. Natural first-entry
  envelope motion remains; useful navigation, import and reading own the feedback.
- Successful import must replace the empty state with real saved counts, results
  and readable mail. Review errors and duplicates honestly; offer a useful next action.
- Import changes layout by phase: choice → live progress → compact receipt/review.
- Pointer focus has no enclosing ring. Keyboard focus stays visible through
  underlines/edge marks, with system outlines in forced-colors mode.

## Materials and behavior

- Paper, ink and folded correspondence retain the motif the user liked.
  Rebuild its paper layering and movement rather than adding generic glows.
- Rounded tactile controls use the established accent palettes. Search focus
  uses a visible bottom-line treatment; keyboard focus must remain discernible.
- First entry opens an envelope and lifts four sheets through depth in 2.4 seconds. Pointer movement changes physical depth.
  Message selection opens the real reading surface, without cloning mail text.
- Navigation and search acknowledge state changes promptly. No animation delays
  access to a button or to readable mail. Rapid actions cancel obsolete motion.
- Respect reduced motion, the app's motion preference, hidden pages and narrow
  layouts. Canvas effects keep their existing finite duration and pixel budgets.

## Review

Review desktop and narrow layouts, loaded/fallback fonts, pointer and keyboard
focus, dark theme, real synthetic import/search/read and motion interruption.
Automated checks do not establish that the subjective visual effect meets the
user's expectations. Record observed results in HANDOFF and test-results.

Research: [current primary sources](docs/design-research-current.md).
