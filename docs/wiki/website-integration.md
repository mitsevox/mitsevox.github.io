# Website

Export a versioned public report and register it with the shared renderer.

## Responsibilities

| Game repository | Shared website |
| --- | --- |
| Defines target/hash, approved tools and validation objective | Owns the shared layout, navigation, styling and interactions |
| Produces source-derived measurements and execution evidence | Authenticates imports and validates the public contract |
| Maintains supported map, inventory, history and credit data | Stores accepted snapshots and selects one exact package per project |
| Documents build/export commands and capability policy | Registers projects, selects modules and publishes the static site |

Use the repository's existing structure and build tools. The integration boundary is the public report contract. A site adapter translates the project's actual export into that contract and the renderer's view model; game code does not need to adopt another project's compiler, source paths or internal ledgers.

## Project identity and presentation

Choose a stable lowercase slug. Use it consistently in report identity, `/games/<slug>/`, project registration and artwork names. Keep display title, console, target ID/hash and repository URL explicit. Different targets must not silently replace each other's histories.

The shared site renders each project using the same header, gutters, code/data bars, metric rows, map controls, tooltips, timeline and contributor style. Register data and capabilities through the shared renderer rather than copying a standalone page per game.

Store cover artwork as `assets/covers/<slug>.webp` with the original aspect ratio. Use authorized artwork and retain required license/provenance notes. The latest commit title/time is independent of measured build progress.

## Required public contract

Use the [manifest schema](/docs/reporting/schema/report-v1.schema.json), [project configuration schema](/docs/reporting/schema/project-v1.schema.json) and [metric definitions](/docs/reporting/contract-v1.md). A producer and its site adapter must agree on schema and methodology versions before registration.

A package contains a manifest, a validated summary, an execution receipt, and JSON assets for each supported module. Paths are package-relative and checksummed. Keep raw public measurement output available for parity checks. A manifest or valid checksum alone does not authenticate a build.

| Manifest group | Required content |
| --- | --- |
| Identity | Project/repository, platform, target/hash, full measured revision and source tree |
| Method | Methodology, generation and pinned tool identities |
| Time | Measurement time and publication time separately |
| Summary | Raw code/data totals, linked/exact bytes, independently supported fuzzy coverage and optional inventories |
| Validation | Full/reused mode, run/attempt, workflow revision and checksummed receipt |
| Modules | Each optional capability declared supported with a typed asset, or unsupported with a reason |

Receipts bind the public files to the producing execution. The consumer verifies repository/workflow/job identity, success, attempt, target/tree, artifact digest and main eligibility against its trusted producer policy. Never execute a report package.

## Measurement rules

| Metric | Meaning |
| --- | --- |
| Linked | Source-produced bytes incorporated into the validated target build |
| Matched | Exact measured bytes, including eligible unlinked comparisons |
| Fuzzy | Target-size-weighted similarity; null when unsupported |
| Functions exact / named | Complete exact extents / names accepted under the naming policy |
| Files exact / named | Exact original boundaries and content / descriptive source groups, including provisional groups |

Derive percentages from raw totals. Keep code and data denominators stable and account for all declared ranges. Linked, matched and fuzzy overlap; never add them. Preserve the actual relationship between linked and matched under the project's promotion policy.

A function fragment cannot earn full-function exactness. A compiled unit marked complete does not establish an original file boundary. Address labels do not count as descriptive names. Support code and data fuzzy independently; never copy one into the other or label a fallback as measured fuzzy progress.

## Choose modules independently

Presentation settings belong in the site's project registration, such as `config/projects.json`:

```json
{
  "schemaVersion": 1,
  "slug": "game-slug",
  "title": "Game title",
  "console": "Console name",
  "artwork": {
    "cover": "/assets/covers/game-slug.webp",
    "width": 640,
    "height": 900
  },
  "repository": "OWNER/REPO",
  "target": "TARGET_ID",
  "modules": {
    "map": true,
    "functionCounts": true,
    "fileCounts": false,
    "timeline": true,
    "contributors": false
  },
  "contributions": { "accepting": false }
}
```

Replace identity placeholders with verified facts. Enable a module only when the producer supplies data validated by its adapter. A disabled module leaves no heading, empty space or section listeners. Shared payloads can still serve another enabled module, but a timeline must not require contributor data and summaries must not require an invented map.

Attribution tracking, contributor rankings and accepting contributions are independent. `contributions.accepting: true` adds the Contribute button and lower contribution section and requires an HTTPS `guideUrl`. It does not enable tracking or rankings.

Unsupported data remains unavailable. Valid zero stays zero. If a supported export unexpectedly fails, retain last-good data and report the failure instead of silently hiding the capability.

## Producer template

1. Run the project's documented validation and comparison commands.
2. Export raw byte measures and supported modules from the same measured inputs.
3. Validate ranges, recursive totals, complete function extents and inventory policy.
4. Restore history and append the measurement without rewriting existing records.
5. Reconcile contributor evidence only when the selected tracking policy requires it.
6. Generate the versioned manifest, payload checksums and execution receipt.
7. Upload only public JSON after all required checks pass.

Do not upload original binaries, object code, complete debug exports, credentials or private experiment files. Retain the existing decomp.dev feed where used; compare fields supported by that format against the same raw measurements.

The downloadable workflow maps its operations onto the canonical report-v1 inputs, not a particular game's old export format. Implement the mapping to `summary.json` and supported `map.json`, `timeline.json`, `contributors.json`; then use the shared packager from an approved pinned tools revision. The starter's `CI.md` lists metadata fields, step policy and full/reused artifact requirements. No separate website importer is needed for a conforming report-v1 producer.

## Consumer template

1. Register a trusted producer policy and an adapter for the export format.
2. Select a successful eligible main execution and authenticate its actual artifact.
3. Parse a bounded, exact allowlist of public files; reject unsafe paths, links and malformed values.
4. Validate schema, target/revision, arithmetic, optional modules and raw-report parity.
5. Check the new package against prior accepted history and Git ancestry.
6. Install immutable files and atomically update only this project's lock entry.
7. Build one coherent static site from the selected locked packages.
8. Preserve accepted snapshots in durable storage before deployment.

Keep project-specific field translation inside the adapter. The website owns shared contract validation, storage and rendering. An import must preserve every other project's lock and snapshots. A report's strings must not select arbitrary executable code.

Consumers may reuse an identical previously authenticated package after temporary upstream artifacts expire. A changed or previously unaccepted package still needs original execution proof. Latest commit metadata never changes the selected measurement identity.

## Register and use the platform

The site owner registers a producer in `config/producers.json` and its presentation in `config/projects.json`. Producer policy and artifact data follow the shared versioned schemas. A conforming producer uses the common importer and renderer; adding a project does not require a separate site implementation. Artwork stays in the website repository.

The [platform contract and commands](/docs/reporting/platform.md) specify the public input files, packager metadata, producer policy, full/reused execution lanes, import CLI and preserved historical policies. These are shared interfaces; the project supplies its own measured inputs and approved execution facts.

```sh
uv run --locked python tools/import_reports.py --project game-slug --run RUN_ID
uv run --locked python tools/build_site.py --output build/new-candidate
```

## Integration acceptance

A workflow change is also a consumer trust change. Approve its actual Git blob after reviewing the code, update full/reused step requirements together, and test deliberate audit-step skips. Preserve archived policies and immutable history. A green upstream run must not automatically expand the receiver's trust.

| Area | Required evidence |
| --- | --- |
| Producer | Successful validated main result with target, source/tree, tool and artifact identities |
| Summary | Raw total/linked/exact parity; correct independent fuzzy support |
| Optional modules | Enabled modules work; absent map/count/history/credits do not create empty sections or fake data |
| History and storage | Existing records survive, identical reruns are no-ops, stale/diverged updates and immutable collisions fail |
| Isolation | Updating or failing one project preserves the other projects' accepted data |
| Build | No fixtures or private files; exact lock selection and fingerprinted assets |
| Browser | Shared styling, direct route/refresh, navigation, hover and map behavior |
| Publication | Public page and manifest agree; the next refresh preserves the same accepted state |

Record commands, revisions, run/attempt, artifact/package hashes, module settings and limitations in the integration PR. The [integration checklist](/docs/reporting/onboarding.md) and [starter files](/wiki/starter-kit/) provide a reusable handoff. Each repository supplies its own implementation details.
