# Pipeline audit

Read-only source/configuration inspection on 2026-10-25. These are observations at pinned revisions, not attestations of passing CI, deployed freshness, branch protection, secret access or artifact availability. No game build was run for this audit.

| Project | Inspected revision | Current target |
| --- | --- | --- |
| NFL Street 2 | `d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211` | GN7E69 |
| MVP Baseball 2005 | `f1e1763bf76b7806ba704868be26935876a6efb1` | GV4E69 |
| Tiger Woods 2004 | `ec5e6077ae41c3de7cebf69eae645c130cafd818` | GW4E69 |

## NFL Street 2

[Baseline workflow](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/.github/workflows/baseline.yml) pins its build environment by digest and Actions by commit. It validates the original relink, source build, comparison reports, inventory, maps, timeline and credits. Its [exporter](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/tools/export_progress.py) derives the website and decomp.dev exports together and deletes stale outputs before generating replacements.

[Publication handoff](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/tools/publication.py) allows verified final-integration reports to be reused after a merge. [Lane selection](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/tools/ci_policy.py) separates build-proof reuse from inventory-cache reuse. Preserve both. History is restored and verified, then archived as `published-history-v1-*` artifacts with 90-day retention; PR handoff artifacts have 14-day retention. A separate Pages job deploys the site.

Changes needed: wrap existing outputs in the common contract; split data production from website rendering; add a durable snapshot store and consumer lockfile. Retain existing history verification and decomp.dev export while adding the new destination. Archive retention is a reason for durable storage, not evidence that history is currently lost.

## MVP Baseball 2005

[Build](https://github.com/mitsevox/mvp2005/blob/f1e1763bf76b7806ba704868be26935876a6efb1/.github/workflows/build.yml) runs configure/Ninja and uploads `GV4E69_report`. Build permissions are read-only. The private container uses a mutable `:main` tag; Actions use version tags. Project compiler downloads are separately configured, so container pinning alone will not describe all build inputs.

[Pages](https://github.com/mitsevox/mvp2005/blob/f1e1763bf76b7806ba704868be26935876a6efb1/.github/workflows/pages.yml) consumes a successful main-push Build through `workflow_run`, or manually selects one. This separation from private build inputs is useful. It maintains `pages-history`, avoids committing unchanged history, and deploys in another job.

A missing report download emits a warning and continues; the [exporter](https://github.com/mitsevox/mvp2005/blob/f1e1763bf76b7806ba704868be26935876a6efb1/tools/dashboard/server.py) can publish a no-report page. The [history helper](https://github.com/mitsevox/mvp2005/blob/f1e1763bf76b7806ba704868be26935876a6efb1/tools/dashboard/pages.py) treats invalid/missing history as empty and invalid numeric input as zero. Some omitted objdiff fields legitimately mean zero; the adapter must use the pinned upstream schema's defaults, not reject every omitted field or silently accept malformed values.

Changes needed: pinned environment/tool provenance, strict report/history failure handling, richer inventory/map adapter and function-credit evidence. Existing report support is not proof of equivalent NFL semantics or complete historical attribution.

## Tiger Woods 2004

[Build](https://github.com/mitsevox/tw2004/blob/ec5e6077ae41c3de7cebf69eae645c130cafd818/.github/workflows/build.yml) runs configure/Ninja, stale-object pruning and the audit-table check, then uploads `GW4E69_report`. Preserve the stale-object cleanup: the workflow documents a real case-insensitive compiler lookup problem. It also uses a mutable container tag and version-tagged Actions.

Main builds append `pages-history`, export the site and upload it. Deployment is separate, but the build job requests `contents: write` for history publication. Move publication writes into a separate job rather than broadening build privileges. The history step commits unconditionally, so an unchanged rerun can fail at commit. Its [history helper](https://github.com/mitsevox/tw2004/blob/ec5e6077ae41c3de7cebf69eae645c130cafd818/tools/dashboard/pages.py) has the same permissive loading/numeric fallback as MVP, plus legacy seed/merge support. Preserve legacy provenance rather than treating every historical point as a verified build.

Changes needed: the common reporting adapter, explicit history integrity and idempotence, isolated publication, complete tool provenance, and evidence-backed contributor mapping.

## Shared improvements

- Bind every published package to target, source revision/tree, methodology, tool versions and authenticated run evidence.
- Keep valid older data when a new report fails. Never reset an established history after a fetch/parse failure.
- Reconcile out-of-order runs using Git ancestry and immutable snapshot identity. Concurrency alone does not establish commit order; [GitHub documents ordering limits](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency).
- Preserve observed drops when inventory or methodology changes; explain them with versioned provenance instead of forcing monotonic percentages.
- Extend complete-range comparison and credit checks from NFL; do not infer credit from merger identity or PR author alone.

The new frontend currently uses frozen NFL reports and synthetic MVP/TW measurements. Real latest-commit metadata is independent of those measurements. No production migration should ship these synthetic packages.
