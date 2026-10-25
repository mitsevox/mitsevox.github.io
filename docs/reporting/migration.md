# Historical migration plan

The shared registration, contract importer, validation, storage and rendering described below are now implemented. New integration follows [the generic project template](onboarding.md) and [platform interface](platform.md). The original planning notes below are retained as context, not instructions to copy a game-specific pipeline.

The NFL consumer adapter, semantic validation, package locking and static assembly are implemented; see [the operational reference](nflstreet2.md). The remaining phases below are acceptance targets, not a claim of deployment. Existing production pages and decomp.dev feeds continue until parity is demonstrated. No source repository CI/settings changes are authorized merely by this design document.

For an executable implementation assignment rather than this phased overview, use the [integration handoff](onboarding.md). It names existing code to extend, working versus required-new commands, and the game/site landing sequence.

## 1. Establish the shared contract locally

Implement semantic validators and payload schemas beside the draft manifest schema. Use sanitized NFL packages plus explicit synthetic edge cases: partial, exact-unlinked, unknown inventory, zero denominator, duplicate ranges, changed boundaries, missing credits, stale runs and corrupt history. Keep fixtures isolated from production ingestion.

Define project configuration independently of report capabilities. Complete module mount/unmount behavior; disabling Contribute must not disable credits; attribution tracking is an independent project policy. Disabling credit display must not silently change an enabled tracking policy.

Acceptance: all agreed metric definitions round-trip; malformed or incompatible reports fail with an actionable error; toggles preserve the approved UI without empty placeholders.

## 2. Adapt NFL Street 2 first

The current implementation consumes NFL’s existing authenticated artifacts and adds no game CI steps. The site now preserves immutable snapshots and its latest lock on its own `report-data` branch before deployment. Game-side `progress-data` branches remain optional future work.

Wrap the existing verified exporter and publication receipts. Preserve matching, map, credit, history and trusted integrated-report reuse checks. Map existing names into the common fields; keep existing decomp.dev generation. Inventory exactness and named-file semantics must retain their evidence requirements.

The site store imports and cross-checks existing publication history before initializing its latest pointer. Keep the current artifact archive and Pages path available through migration.

Acceptance: same revision/target yields equal raw totals, function/file inventories, map coverage, credits and history in the old and new consumers. Verify both a full validation run and a legitimate proof-reuse run. Test a failed export, identical rerun and older run finishing late. Independent review and owner clearance remain separate from these checks.

## 3. Add MVP and Tiger Woods adapters

For each game, record the exact target hash, pinned compiler/linker/report-tool inputs and how objdiff measures map to the common contract. Establish actual code/data fuzzy support separately. Never use synthetic fixtures or estimate unsupported file/function statistics.

Retain each game's build specifics. MVP keeps a separate artifact-consuming publisher; TW separates history writes from its build job and retains stale-object pruning. Both gain strict history/report handling, idempotent publication, input-aware cache keys, immutable tool provenance and the common semantic validator.

Import existing `pages-history` without overwriting it. Keep legacy/reconstructed provenance and full SHAs where recoverable; do not guess missing identities from short hashes. Audit past function credit through surviving commits, original PRs, integration records and source/evidence ledgers. Record unresolved ownership as unresolved internally and keep rankings disabled until the selected credit policy is satisfied. Missing historical evidence may remain unrecoverable; automation cannot manufacture it.

Acceptance per game: compare the same revision against its current build report, verify adapter arithmetic and maps, exercise a genuine partial function, and document unsupported capabilities. Enable each UI module only when its data passes.

## 4. Connect the central site

The hosted site repository exists publicly and Pages is configured for the authorized current-main workflow. Owner merge remains the launch gate. Build static pages from locked report snapshots; replace fixture locations with packaged data. Keep the persistent header/router and individual `/games/<slug>/` routes. Verify direct navigation and refresh on the actual Pages base URL.

Keep shared reporting definitions in the site repo and pin reviewed versions from game repos. Add manual/scheduled refresh before considering dispatch credentials. Verify cache fingerprinting, stale-data behavior, rollback and per-project isolation when one producer fails.

Acceptance: no synthetic measurement package reaches production; only verified, production-enabled routes are included; contribution button appears only for NFL. Existing game Pages can redirect only after live parity and owner-approved cutover. decomp.dev artifact names/feeds remain working independently.

## Decisions at implementation time

- Confirm approved image digests/tool hashes for MVP/TW with the owner; do not modify dependency access or substitute toolchains.
- The site’s `report-data` branch is created by its first successful main publication. Any game-side `progress-data` branch still requires a separate scoped decision.
- The site refreshes every six hours and fails visibly without replacing the live site on refresh errors; decide later whether faster dispatch is worth an extra credential.
- Resolve any attribution policy conflict with existing game rules before enabling rankings.
- Agree the cutover/rollback revision and redirect behavior. No automatic main merge or deployment approval is implied.
