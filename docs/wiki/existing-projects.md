# Existing projects

**Optional appendix. Skip this when starting a repository from scratch.** The main handbook and starter checklist define the new-project path: choose policy, establish verified tools/inputs, build and measure, start a measured timeline, then register the standard public report.

Use this appendix only when adopting the structure in a repository that already has source, CI, review conventions, attribution or historical data. These are generic adoption procedures; they are not extra prerequisites for new projects.

## Map existing responsibilities

Inventory existing tools, source layout, configuration, validation outputs and owner instructions. Preserve working engines and evidence-supported paths where they fulfill the documented responsibilities. Map them to the adapter contract rather than reorganizing source solely to match example names. Identify actual gaps and test them; do not declare the old workflow equivalent without evidence.

## Adopt policy without overriding authority

Record the review/merge model selected for the project. Existing documented owner/task delegation remains authoritative until explicitly changed; a generic default does not silently grant or revoke merge permission. Preserve review independence and the gates selected by that policy.

The starter uses SHIP/FIX/REDO/BLOCKED. A project retaining SHIP/FIX/REDO must represent missing essential evidence as an explicit blocked state with a nonpassing check, or deliberately adopt BLOCKED across its records and verifier. Never convert blocked evidence into a passing verdict. This is a compatibility decision for an existing workflow; new projects can use the coherent starter vocabulary directly.

## Branch and trigger conventions

Keep a documented existing branch convention if appropriate. A branch prefix is not authorization or a reporting-contract field. Inspect the actual triggers: optional branch-push checks may have prefix filters while PR validation covers all contribution branches. Make any trigger change deliberately and verify both event paths. New projects can use the starter's agent-neutral branch examples and PR/main validation model.

## Recovering past credit

Use surviving original PRs, commit authorship, pinned source blobs, integration records and reviewed evidence. A closed PR or deleted branch may still leave useful records; do not assume they are available indefinitely. Distinguish supported attribution, explicit joint work and unresolved ownership.

Keep a bounded recovery record explaining each decision and uncertainty. Do not give every function to the current file author or merger. If a project promises complete exact-function attribution, unresolved gaps block that capability's publication until resolved or the owner explicitly changes the policy.

## Import legacy history

Existing history is useful even when it predates this pipeline. Migrate it before the first accepted report using a reproducible, reviewed conversion; retain the raw input separately. Do not reset an already accepted timeline during a later refresh.

The same [timeline contract](/docs/reporting/platform.md#timeline-semantics) applies to imported rows. Legacy input does not bypass identity, raw-value, timestamp or continuity requirements.

1. **Inventory the old format.** Record its target, metric meanings, denominators, timestamp basis and evidence sources. Count unresolved rows and preserve the original export/hash in a migration record.
2. **Resolve abbreviated commits.** Fetch required history, resolve each prefix to exactly one commit, and verify it belongs to the intended project's history. A missing or ambiguous prefix is unresolved; never select the first matching object. Use the adopting project's branch name in ancestry checks.
3. **Recover values from evidence.** Prefer preserved reports, receipts, versioned target/placement metadata or a reproducible historical replay. A denominator may be carried across rows only with evidence that the target and measured universe were unchanged. Today's total is not automatically every historical total. Rounded percentages generally do not recover an exact byte numerator uniquely.
4. **Classify provenance.** Use `measured` for supported historical measurement, `reconstructed` for values rebuilt from identified historical evidence, and `inherited` when preserving an already accepted compatible record. A new importer does not turn an old measurement into a newly executed build.
5. **Normalize without inventing.** Resolve duplicate revisions and ordering using a documented deterministic rule before initial acceptance. Preserve the timestamp's actual meaning; a commit time is not a historical build time. If the available timestamp is a commit-time proxy, state that in reconstructed provenance and the migration record.
6. **Validate and reconcile.** Check schema, integer arithmetic, evidence-backed denominators, ordering, current-row parity, and continuity against any previously accepted history. Record conversion method, source records/hashes and unresolved/excluded rows in the project.

For a known abbreviated commit, use Git's ambiguity checks rather than matching a log line by eye. Replace these placeholders and the main ref with actual project values:

```sh
git fetch origin main
git rev-parse --verify --end-of-options 'ABBREVIATED_SHA^{commit}'
# Where the timeline policy requires current-main ancestry:
git merge-base --is-ancestor FULL_COMMIT_SHA origin/main
```

Missing original refs or rewritten history need a documented recovery decision; they are not reasons to choose a different commit with a similar prefix.

A full SHA proves identity, not missing totals. `reconstructed` requires evidence for the values: it does not permit zero-filling, interpolation or repeating today's numbers. Keep initially unrepresentable rows in the project's legacy archive with reasons and publish the supported subset, or defer timeline support until sufficient evidence is available. Do not silently omit rows already accepted by the site; those require an explicit compatible migration/correction.

An `inherited` wrapper may include the exact prior accepted row as `provenance.record`. Its revision, time, code and data values must remain identical. It cannot wrap an abbreviated/missing-total raw row and simultaneously claim the normalized fields are unchanged. Reconstructed rows identify their source/method through `provenance.source` instead.

See the [illustrative legacy timeline](/docs/reporting/examples/timeline-legacy.json). Its placeholder commit identities and values are not production evidence. The site retains provenance in accepted data; the current graph does not display separate provenance badges, so the metadata label alone does not create a visible rebuilt/measured distinction.

## Adoption acceptance

- [ ] Existing commands and selected policies map to the standard responsibilities without lost evidence or unauthorized changes.
- [ ] Any retained verdict/branch conventions agree with their actual verifier and CI triggers.
- [ ] Legacy raw history and credit sources are retained with conversion method, unresolved rows and limitations.
- [ ] Historical identity and raw values are supported; reconstruction labels do not replace evidence.
- [ ] Previously accepted history remains unchanged or moves through an explicit compatible transition.
- [ ] Real report import and the next refresh preserve prior accepted state.

These checks apply only to the adoption being performed. They are intentionally absent from the starter's new-project checklist.

## Changing an accepted report format

Stage the next producer policy as `pending` while the current importer stays active.
Authenticate real outputs in both formats and compare raw summaries, map coverage and
metrics, complete function IDs, optional credits and historical values/provenance. A
pending policy cannot itself admit packages or select the active importer.

When changing history representation, let the last current publisher finish, restore the
durable store and freeze its exact snapshot using the registration's `freeze` fields:
`path`, `revision`, `manifestSha256`. Copy the final stored row's revision and built_at
verbatim to the producer; retain its original timestamp spelling. Do not infer the
cutover from a local preview, an earlier parity run or the latest repository commit.

The freeze permits other projects to refresh but blocks this project's newer imports,
added rows and publication changes. Wait for the producer's cutover pin and successful
main package. Then activate the staged policy, remove the freeze, archive the previous
format policy and require every previously accepted row to survive unchanged or through
an exact inherited record. Retire the producer's former website/artifact jobs only after
the shared-site switch succeeds. See the [platform controls](/docs/reporting/platform.md).

## Tracked policy sources

The normal new-project interface is a complete tracked producer policy JSON. An
existing exporter that generates its policy only at runtime must publish a tracked
policy before automatic synchronization can be enabled. Do not execute exporter
code in the site job to recover that configuration.

For an existing tracked template that omits only `workflowBlobs`, the site can
explicitly register `mode: "template"`. The sync job obtains the current workflow's
Git blob at the pinned producer revision and adds it to the previously approved
list. All other schema, identity, successful-package and review checks are the
same. A template must omit that field; a complete policy must declare its own
approved blobs. Template mode is an optional adoption aid, outside the starter
checklist. Prefer a complete tracked policy for a new repository.

## Explicit target adoption

This optional migration is unnecessary for a working single-target report-v1 producer. Agree
on the new consumer contract before renaming directories or emitted identities.

1. Deploy report-v2 consumer support while the existing producer still emits v1.
2. Register the exact old target object (`id`, `console`, executable `sha1`) in the canonical
   target's `legacyTargets`. Keep its old policy in that target's `archives` and preserve every
   original package byte, receipt, checksum and timeline row. The site adopts the pointer only
   through this explicit same-binary alias. It never guesses a revision from a game ID.
3. Migrate producer/private-original paths and generated outputs, approve the pinned environment,
   implement target-specific CI, and pin a reviewed v2 packager. Coordinate required-check names
   with the owner. Preserve existing compiler profiles and measurement methodology when their
   meaning has not changed. Known targets without validated builds remain archived metadata.
4. Review the new policy and workflow blob for each publishing target. Produce and authenticate
   a real main package, compare old/new totals and geometry, and prove history retention with
   zero lost/changed rows. Switch that producer to report-v2 only after these checks pass.
5. Update policy-sync source paths and completion notifier pins/format. Keep single-target
   projects on their existing wire contract. Do not retain duplicate legacy build/report pipelines.

Legacy rows remain records of their original execution. Function identifiers in newly generated
v2 reports use the explicit target ID; never rewrite already accepted v1 packages to update IDs.
