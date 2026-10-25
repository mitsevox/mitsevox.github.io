# CI & publication

Validate once, preserve the evidence and publish only a coherent verified result.

## Jobs and authority

| Job | Inputs and purpose | Authority |
| --- | --- | --- |
| Build/measure | Approved references and pinned tools; baseline, source and comparisons | Read source/packages; no source-branch writes |
| Review clearance | Trusted workflow code and PR discussion records | Read PR records; write the named status |
| Data publication | Authenticated successful measurements and prior history | Narrowly scoped report-store writes |
| Website build | Public verified report packages and site source | Read packages; produce static artifact |
| Pages deployment | Successful site artifact | Pages and deployment identity permissions |

Pin reviewed Actions and shared tools to commits, build images to approved digests, and downloaded compilers/linkers by version and hash. Do not copy mutable image tags into the new archetype. Cache keys include target, environment and relevant configuration/source inputs; caches are acceleration, not validation evidence.

## PR path

Validate the candidate revision and emit a receipt binding target, tested tree, environment, methodology, inputs and artifact checksums. Produce candidate reports for review without advancing public latest. Keep failures actionable and prevent stale output from an earlier successful run being uploaded after a failed export.

CI must fail if required inputs or enabled measurements are unavailable. Scope cheap validation separately from expensive reconstruction builds. The owner should enable required statuses only after observing real passing and failing behavior.

## Main path and proof reuse

NFL can reuse the final integrated PR's verified reports when trusted execution, artifact integrity, pinned environment and complete tested tree match the landed tree. Validate contributor provenance against actual landed/squashed history when that policy is enabled. Missing or incompatible proof falls back to full validation; invalid required attribution or history blocks publication.

An inventory-cache miss does not invalidate otherwise valid source-build proof. Regenerate the affected inventory separately. Do not repeat complete builds solely because review comments changed or an unchanged artifact can be authenticated.

Keep these guarantees when extracting reusable steps. Do not replace NFL's mature handoff checks with “download the latest artifact.”

## History and ordering

Restore prior verified history before appending. Fetch or parse failure must not reset an established timeline. Make identical reruns idempotent. Distinguish commit time, measurement time and publication time.

The implemented website store is its data-only `report-data` branch, currently accepting NFL packages. It preserves immutable snapshots and a latest-good pointer. A separate data-only branch per game is an optional future producer store, not an onboarding requirement. Preserve existing game archives during migration and extend the site store for multiple projects as specified in the [integration handoff](/docs/reporting/onboarding.md). Git ancestry, immutable identity and an atomic pointer update prevent an older slow run from replacing newer progress; concurrency settings alone are insufficient.

A timeline records available verified measurements, not a guaranteed build for every commit. Preserve gaps and legacy evidence quality. Do not manufacture measurements by repeating a previous value and labeling it a fresh build.

## Privileged workflows

Treat PR text and report payloads as data. Never execute scripts from downloaded artifacts or untrusted PR code in a privileged publication/clearance job. Keep private references and build credentials out of the website job. The NFL clearance workflow evaluates trusted logic without checking out a contribution branch.

[GitHub's security guidance](https://docs.github.com/en/actions/reference/security/secure-use) covers pinned Actions and untrusted code. [workflow_run guidance](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run) explains why an upstream result must be authenticated before privileged follow-up work.

## Website deployment

Use a separate build artifact and deployment job. GitHub Pages deployment needs `pages: write`, `id-token: write`, the appropriate environment and a dependency on the artifact-producing job. See [custom Pages workflows](https://docs.github.com/en/enterprise-cloud%40latest/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Build fingerprinted assets and publish one coherent site artifact, so a browser cannot mix old CSS with new markup. Verify home, direct game/wiki URLs, refresh and back/forward behavior at the deployed base path. To roll back UI, have the owner merge a source revert and let the current-main workflow rebuild with the latest verified reports. Old workflow reruns are rejected; measurement history is never rewound.

The [NFL consumer implementation](/docs/reporting/nflstreet2.md) verifies existing artifacts and builds a locked static candidate without adding game CI work. Validation uses read-only permissions. A separate current-main job has site-repository write access for the data-only `report-data` branch, plus Pages and deployment-identity permissions. It preserves snapshots before deployment, rejects stale site revisions and never writes a game repository or merges main.

The [pipeline audit](/docs/reporting/pipeline-audit.md) records the three current producers. The [shared workflow proposal](/docs/reporting/workflow.md) describes the remaining cross-game migration; distinguish it from the implemented site-only workflow.
