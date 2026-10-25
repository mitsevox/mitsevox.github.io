# Agent assignment: integrate this game

Read this repository's current README, CONTRIBUTING and AGENTS, then:

- https://mitsevox.github.io/wiki/
- `INTEGRATION.md` in this starter archive, or https://mitsevox.github.io/docs/reporting/onboarding.md
- https://mitsevox.github.io/docs/reporting/contract-v1.md
- https://mitsevox.github.io/docs/reporting/nflstreet2.md

Work in separate dedicated branches/worktrees for the game repository and
`mitsevox/mitsevox.github.io`. Inspect before editing and preserve unrelated work.
Both checkouts are required. Identify the owner, target/hash, approved tools,
raw report, history, attribution policy and available artifact evidence.

Implement both halves: a game exporter of supported public measurements and a
website adapter that authenticates, normalizes, validates, stores and renders
them. Read the handoff's shared extension map: current package validation,
execution policy, storage, import CLI and some renderer assumptions are NFL-specific.
Configuration alone cannot integrate another game.

If other game agents are active, coordinate common website changes through one
site integration owner. Keep per-game adapter work separate. Do not independently
replace shared storage, validation or workflow files on competing branches.

Use the handoff's capability matrix. Keep contribution acceptance, attribution
tracking and displayed rankings independent. No contributor feed means unsupported
rankings, not fabricated ownership. Optional payloads must actually be optional.
Use the raw report and one real successful main run for parity; do not substitute
fixture measurements, change denominators, infer full exactness from fragments,
or reset inherited history to get a passing result.

Preserve the existing game build specifics, private dependency access and
working decomp.dev feeds. Pin approved tools and authenticate full/reused proof
as documented. Use existing build evidence when it is adequate; avoid duplicating
full game builds for website/docs changes.

Complete the implementation sequence and acceptance matrix in INTEGRATION.md.
Include positive and failure cases, second-project storage and unchanged NFL
coverage. Deliver coordinated game/site changes with exact revisions, commands,
producing run/attempt/artifact, manifest digest, settings, limitations and results.
Follow the owner's authorization and repository rules for pushes, PRs, publication
and merge; do not change approval controls to accommodate the patch.

Finish by verifying the deployed route and the next scheduled/manual refresh.
A green local test, a configuration entry or a candidate artifact alone is not
completed public integration. Report any missing access/evidence with a concrete
next action instead of inventing it.
