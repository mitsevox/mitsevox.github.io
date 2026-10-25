# Agent workflow

A repeatable assignment, reconstruction and delivery process, with project policy made explicit.

## Adopt the project policy first

The default is an isolated author branch, independent blind accuracy review, a fresh hostile reviewer, final-revision CI and owner-only merge authority. These are defaults for a new project, not assumptions an agent may silently impose on an existing one. The owner records any alternative in CONTRIBUTING.md before work begins. The site contract does not enforce a reconstruction review model.

Record who can assign work, push, open PRs, review, clear and merge. Permission to implement does not automatically authorize publishing or changing repository settings. Attribution tracking, rankings and accepting contributions remain separate decisions.

## Intake and scope

1. Read README.md, CONTRIBUTING.md, AGENTS.md and configuration documentation. Inspect the actual checkout, current main, open PRs and active reservations.
2. Inventory authorized executables, symbols, debug information, maps, source references and tool access. Record what exists and what is missing; distinguish a searched location from a complete absence claim.
3. Identify one bounded question and scope: functions, data ranges, declarations, original units or tooling. Include affected shared files and dependent branches.
4. Reserve active work using the project's chosen mechanism. Establish a dedicated branch/worktree; preserve unrelated dirty work and prior useful partials.
5. Record the base revision, target/hash, evidence locators, applicable compiler profiles, deliverables, exclusions and task authorization in the issue or PR. Keep detailed experiments private.

For an integration task, additionally inventory current CI triggers, job permissions, build stages, cache trust, public outputs, history storage and site registration. Map existing tools onto the contracts in the [starter kit](/wiki/starter-kit/); do not replace working tools just to obtain the example filenames.

## Evidence before reconstruction

Establish behavior, boundaries, references, calling convention and accessed layouts. Distinguish recovered original names from descriptive inferred names and neutral unknown labels. Do not let a desired name or a high matching score decide the interpretation.

Escalate according to the unresolved question: static analysis for behavior/ownership, compiler intermediate output for code-generation questions, bounded runtime tracing for an execution hypothesis. State the question, inputs, tool settings, result and remaining uncertainty. An unavailable essential reference is a named gap, not permission to invent an answer.

Implement useful partial source in its normal location. Keep original bytes in the verified linked build until promotion. Register complete comparison extents, dependencies and the supported profile. Do not move unfinished functions into a separate source tree merely to distinguish their reporting status.

## Iteration and attribution

Run the smallest relevant build/comparison and self-check evidence, names, declarations, comments, boundaries and ranges. Preserve mismatches honestly. Matching-only flags, patched output, invented padding, unsupported assembly and excluded failing bytes are not a valid repair.

When tracking is enabled, register original contributors and source provenance. A source edit can invalidate a pinned blob even if the function's bytes still match: re-pin and check the actual final source. Run ledger-only checks before an expensive build; reconcile coverage against the measured exact inventory after comparisons. Fuzzy source retains provenance without full exact-function credit.

Keep pushes coherent. A new PR push normally cancels that PR's older CI. Tooling/profile changes have wider invalidation than ordinary source changes and deserve their own bounded change where practical.

## Independent review

For the default policy, supply the full revision, scoped source/headers, target evidence, extents, profiles, comparisons and existing validation artifacts. The accuracy reviewer first interprets target behavior without the author's proposed names/comments; then reconciles the interpretation. The hostile reviewer checks the evidence and integrity checklist independently.

Reviewer independence is about authorship and prior reasoning, not a different display name. Creating another agent does not automatically make its work independent. Do not fabricate a review record when no reviewer or evidence was available. Use the project's accepted reviewer arrangement and document limitations.

Report findings with a location, evidence and required correction. Measured incompleteness alone is not a failed fidelity review. A useful partial may pass while its original bytes remain linked.

After a fix, the reviewer checks the finding and affected dependencies, carrying forward adequate earlier coverage. A new reviewer may use that record; replacement alone is not grounds to restart everything. Follow the [review record and clearance specification](/wiki/review-and-approval/).

## Refresh, batches and final revision

Fetch current main before final integration. Inspect the changed inputs, conflict resolutions and shared declarations; record the resulting head. Review the delta and affected dependencies, then issue final-head review records that cite carried-forward coverage. A prior verdict does not by itself cover a new head.

A batch preserves each original PR, author revision and review evidence. Reconcile shared metadata by stable identity, resolve overlaps, and validate the combined tree once. Independently passing component builds do not establish the combined build. Close originals as incorporated only after the combined change lands.

Distinguish these identities: the PR head is reviewed and cleared; the synthetic merge tree is usually what PR CI builds; the landed commit is what main publishes. Receipts bind the tested tree and both relevant revisions. Tree equality allows authenticated reuse across a squash; identical commit messages or file counts do not.

## Delivery and owner decision

Post concise separate review records for the actual final revision, resolve findings, and link successful final CI and measured artifacts. The owner then follows the selected clearance/merge policy. A reviewer returning SHIP has not authorized a merge.

After merge, verify the eligible main publication, report identity, prior history and subsequent site refresh. A green PR, a local preview and a deployed page are different evidence. End with changes, tested revision/commands, measured results, unresolved gaps and the precise review/publication state. Never add a running public diary of agent activity.

## Implementing this template with an agent

An agent setting up CI must deliver a command mapping, adopted policy, pinned environment, stage receipts, meaningful invalidation tests, report-v1 packaging and real successful/failing execution evidence. Start with fresh validation. Add caches and proof reuse only after that path works and the owner selects them. The [setup checklist](/wiki/starter-kit/#acceptance-checklist) is the handoff boundary; unchecked items must stay visible.
