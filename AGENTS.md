# Agent working agreement

These principles apply to work in this repository. Follow the user's current
instructions when they refine the scope. Do not treat ordinary implementation
decisions as permission gates.

## Start from evidence and a real user task

- Before proposing a new product direction or major feature, find the actual
  user pain. Prefer original discussions, user reviews and support reports from
  the last 3–6 months; retain source URLs, publication dates and access dates.
- Distinguish observed facts, vendor claims, user reports and our inferences.
  Label uncertain dates, self-promotion, small samples and contradictory evidence.
- Validate across independent sources. A popular post, one complaint or a lack
  of search results does not establish demand or the absence of competitors.
- Investigate existing solutions fairly, including successful user experiences
  and whether old complaints have already been fixed. Prefer a clear underserved
  workflow. If entering an existing market, explain the meaningful improvement
  grounded in repeated feedback instead of copying or accumulating features.
- Consider discovery/acquisition, repeated use and a plausible revenue model.
  Do not represent hypotheses as validated willingness to pay or product-market fit.
- Do not assume an industry or add AI unless it demonstrably helps the task.

## Act autonomously and finish the job

- Move from research to selection, implementation, running software, testing and
  release preparation. Share a brief evidence-based decision, then proceed.
- Make ordinary, reversible decisions independently. Install necessary,
  appropriate dependencies when authorized by the task. Ask only when a genuine
  blocker, missing essential input or consequential unauthorized action remains.
- Deliver a complete, focused core workflow, not just a proposal, landing page,
  screenshot or hard-coded-data demonstration. Never claim work or tests were
  completed without executing and checking them.
- Continue the active task after answering status questions or accepting new
  constraints unless the user explicitly stops or replaces it.

## Parallel work and efficient tools

- Use concurrent sub-agents for independent research, implementation, testing,
  review and documentation when useful. Use the available concurrency; do not
  spawn redundant agents merely to inflate the count.
- Assign bounded responsibilities and non-overlapping file ownership. Agree
  interface contracts first. The lead agent integrates, resolves contradictions,
  runs end-to-end checks and remains accountable for the final result.
- If local tooling is repeatedly blocked or inefficient, identify the bottleneck
  and recommend a concrete online tool, service or workflow with its expected
  benefit, cost and data implications. Prefer available integrations. Do not
  upload private source data to an external service without authorization.
- Communicate meaningful findings and blockers concisely while work continues.

## Quality and verification

- UI work should avoid repeated promotional microcopy and decorative labels.
  Give typography distinct readable roles, make motion explain real interaction,
  and preserve keyboard focus when replacing generic input outlines. Treat the
  user's visual feedback as stronger evidence than a passing automated check.

- Actually launch the product and exercise the primary workflow, error cases,
  persistence and recovery. Inspect the interface in a real browser, including a
  narrow viewport, when the product has a browser interface.
- Use representative, explicitly synthetic fixtures and meaningful behavioral
  tests. Check exported artifacts by reopening them. Measure performance before
  claiming support for large files; state the tested scale and environment.
- Preserve original user data. For this product, never fetch email resources,
  execute email HTML, silently discard failed imports, or equate a hash check
  with proof that an email provider exported every message.
- Report limitations and unresolved risks plainly. Do not let delivery claims
  exceed the evidence or verified behavior.

## Release and rights

- Prepare clean source, concise startup instructions, architecture notes,
  research sources, configuration examples, screenshots and test results for
  GitHub publication. Exclude secrets, private mail, databases and local state.
- This project is source-available, not OSI open source. Unauthorized commercial
  use is not permitted under the project's license. Preserve the original
  licensor's ability to earn revenue and grant separate commercial licenses.
- Keep LICENSE, NOTICE, COMMERCIAL.md and README consistent. Audit direct,
  transitive, bundled asset and runtime licenses before adding dependencies.
  Do not replace the license with MIT/Apache/GPL or promise commercial rights.
- Do not merge outside code without addressing the contribution policy and the
  rights needed for future commercial licensing. Never imply that a public
  repository grants rights beyond its actual license.
- Do not publish to a user's external account unless the task authorizes it.
  Preparing a GitHub-ready release and publishing it are distinct actions.

## Usage threshold and detailed handoff

- The owner requests a stop when the **remaining five-hour Codex allowance is
  10% or less**. Before a new stage, before a substantial parallel batch and at
  stage completion, read `codex_app.get_usage_limits` when available. Select the
  300-minute window from `rateLimitsByLimitId` (legacy `rateLimits` only as a
  fallback). Remaining is `max(0, min(100, 100 - usedPercent))`. The percentage
  consumed, weekly allowance and goal token accounting are different measures.
- When a reliable reading reaches that threshold, start no new development,
  browser task, build or agent batch. Stop owned tests safely where possible,
  save a detailed `HANDOFF.md`, report the observed allowance and pause the
  active goal under this explicit conditional instruction. Do not use reset
  credits, buy credits or resume on your own. A later explicit user resume
  controls continuation; recheck the current allowance first.
- Missing/null readings mean unavailable. Say so; do not infer a percentage
  from token counts, elapsed time or an approval/credit error. Checks happen
  during active work, not as a claim of continuous background monitoring.
- Keep `HANDOFF.md` usable without chat context: product background and scope,
  workflow, code map and invariants, exact current source/build/launcher state,
  completed work with build-scoped evidence, pending work in execution order,
  known limits, reproduction commands, owned processes/browser state, user
  decisions and restrictions. Update it at each material milestone, before
  exhausting the remaining allowance. Exclude credentials, account IDs, mail
  content, tokens and quota-reset identifiers from publishable documents.
