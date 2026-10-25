# Common validation and publication workflow

The shared platform implements registered producer authentication, package validation, per-project installation, multi-project storage and static rendering. See [the platform interface](platform.md) for the implemented schemas and commands. Each game retains its own build tools and contribution policy. The current site blocks deployment on any refresh failure while preserving every last-good package.

## Pull request

1. Resolve the exact target, source tree, pinned build environment, compiler/linker/comparison tools and reporting revision.
2. Run the game's required baseline/source validation. Preserve useful partial reconstruction in normal source; measure it without promoting original-byte replacements prematurely.
3. Generate measurements, inventory and map from the same candidate revision, plus attribution evidence when project policy enables tracking. Validate complete function extents, coverage and the shared package semantics.
4. Produce a candidate artifact with a receipt identifying the tested tree and execution. Candidate reports are review evidence, not public latest data.
5. Complete the reviews, final-revision delta rechecks and clearance required by the project's adopted policy. Independent accuracy/hostile review and owner-only merging are starter defaults. An explicit project instruction or owner delegation governs who may merge, including an agent authorized to merge its own PRs; this generic template does not revoke that authority.

## Main or manual recovery

1. Select an eligible main revision. Authenticate any final-integrated PR artifact before reuse: trusted workflow execution, artifact digest, complete tested tree equal to the landed tree, matching target/environment/methodology, and valid attribution after squash/integration when the project requires tracking. Do not stitch together constituent PR reports as build proof.
2. If proof is absent or incompatible, run the full required build/comparison path. If only inventory inputs changed, regenerate inventory without discarding valid build proof. A build cache is never evidence by itself.
3. Restore and validate previous history. An established history that cannot be fetched or parsed blocks publication. Bootstrap an empty history only through an explicit initial setup operation.
4. Generate one coherent package and both consumers' exports from the verified measurements. Check decomp.dev parity on metrics its format supports; do not invent data-fuzzy support by copying a code score.
5. Publish immutable public-safe snapshot files, then update the latest-good pointer atomically. The publishing job has write permissions; build/measurement jobs do not need repository writes. Never include original binaries, object code, assembly dumps, credentials or complete debug exports.
6. Rerunning an identical snapshot is a no-op. A different payload for the same immutable identity fails; a corrected measurement requires an explicit new methodology/generation and provenance. Retain earlier records.

Snapshots use target + source revision + methodology + generation identity. Store each validated measurement even if it finishes late; move latest only forward by eligible main ancestry. Handle same-revision corrections explicitly. Under a publication lock, re-read the current pointer and use a compare-and-swap Git update; retry conflicts by re-reading, never force-push. A history rewrite or unrelated ancestry requires owner reconciliation.

The timeline preserves evidence-qualified progress records, including explicitly reconstructed legacy points; it does not promise a successful measured build for every commit. Discover and reconcile eligible unprocessed successful runs; record failures/gaps without fabricating points. Document the timestamp basis used for historical chart context; Git ancestry controls promotion. Measurement time and publication time remain separate.

## Site ingestion and deployment

The site build reads each project's latest manifest once, resolves immutable paths, verifies checksums, schema, semantics and authenticated provenance, and records a lockfile of exact package identities. All files served for one project come from that package. No browser-time GitHub token or game compiler is needed.

A failed refresh retains that project's last validated package and reports the failure in CI. Other games may update independently. A project with no valid initial package cannot be published as real data. Display measurement freshness separately from the repository's latest commit; do not imply the newest commit has passed measurement.

Run module/route smoke checks, including direct deep links, back/forward navigation, unavailable data and disabled modules. Build fingerprinted assets and publish one atomic Pages artifact to prevent HTML/CSS/JS version mixing. The implemented site workflow rolls back UI through an authorized source revert and a new current-main build; stale workflow reruns cannot deploy and game history is retained.

Start ingestion on manual runs and a schedule with best-effort latency. An optional future notification can ask the site to refresh; it must never substitute for verifying the referenced package. Keep credentials scoped to the task, with no site write access to game source branches.

## CI improvements to carry across games

- Pin shared validators and Actions to reviewed commits; pin the approved build image by digest and record separately downloaded tool versions/digests. Do not rebuild or change private environments during this documentation pass.
- Split cheap schema/evidence checks from expensive build/comparison jobs. Use input-aware caching and authenticated complete-tree report reuse.
- Scope cache keys to target, compiler/linker, configuration and relevant source/evidence inputs. Prune stale objects and comparison output before regenerating affected results.
- Validate missing reports, corrupted history, duplicate reruns, stale runs, wrong targets, changed denominators and partial/exact-unlinked examples explicitly.
- Keep adopted independent reviews/clearance, CI evidence, merge and publication separate. Carry forward adequate review of unchanged code.

GitHub supports [reusable workflows pinned by SHA](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows). Reuse validators/publication steps first; keep game build commands in local adapters. A privileged `workflow_run` consumer must authenticate its upstream event/run and treat downloaded contents as data: [GitHub warns about untrusted code in this event](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run). The publishing job must not execute downloaded report payloads or scripts from an untrusted PR.
