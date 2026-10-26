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

Configure the stable source path `/assets/covers/<slug>.webp`. A `/releases/<hash>/...` URL belongs to a built site artifact and must never be copied into project registration; the builder versions real asset references itself.

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

## Map parity and geometry

A supported map includes both `sections` and `files`. For each of code and data separately, their leaf address unions must be identical and each view's top-level metrics must sum to the summary. The views can group bytes differently; matching numeric totals at different addresses still fail.

Use positive, end-exclusive intervals without overlaps inside a view. Preserve disjoint ranges through `mapped_extents`, aggregate child metrics into parents, and represent measured bytes without known file ownership as gap/unmapped nodes. Do not invent ownership or drop unassigned bytes. Function fragments must collectively cover the declared complete extent and reconcile any reported function inventory; fragments alone cannot earn full-function exact credit.

The [map specification and paired examples](/docs/reporting/platform.md#map-semantics) list the exact field/aggregation rules. Validate with the shared packager locally; a schema-valid JSON tree can still fail coverage checks.

### Optional node evidence

Use [map-v2](/docs/reporting/schema/map-v2.schema.json) when the public map carries source or
file-boundary evidence. Set `map.json` to `schemaVersion: 2`; the report manifest stays v1.
The shared packager labels that asset `map-v2`. Pin a site tools revision supporting v2
before publishing it: the package validator and browser reject unknown or mismatched
versions. Existing v1 maps remain supported, with unknown fields still rejected.

| Optional field | Allowed node `type` | Valid values and purpose |
| --- | --- | --- |
| `source` | `file`, `group`, `function` | Repository-relative source file holding the code |
| `comparison_source` | `function` | Repository-relative file used for this function's comparison |
| `complete` | `file` | Boolean: whole file extent accounted for versus partial |
| `auto_generated` | `file` | `true` only for an unmapped placeholder; omit otherwise |
| `boundary` | `file` | `exact`, `provisional`, `open`: established, tentative or unresolved original boundary evidence |
| `scope` | `file` | `mapped-ranges` or `candidate-ranges`: mapped versus candidate extent ownership |

Every field is optional, but a node carrying evidence must explicitly declare an allowed
type. V2 introduces `group`; section and gap nodes cannot carry these fields. Translate
untyped internal nodes deliberately rather than guessing ownership or copying file-only
flags onto functions or groups.

Paths preserve case and use ASCII letters, digits, `_`, `.`, `+` and `-` in components
separated by single `/` characters. They must be canonical repository-relative paths:
no `.`/`..` or empty components, absolute paths, backslashes, URLs, percent escapes,
whitespace or controls. A producer's source tree need not be named `src/`.

The compact hover prefixes the source path when absent from the name and marks “partial
file” when source equals name and `complete` is false. Selecting an evidence-bearing node
shows source, comparison source, boundary, scope and supplied file flags in its details.
Raw evidence stays in the public map. These fields never change byte totals, function IDs,
exact credit or aggregation; `complete` alone does not prove matching or exact original
file boundaries.

See the [full field contract](/docs/reporting/contract-v1.md#optional-map-evidence-map-v2)
and [v2 example](/docs/reporting/examples/map-evidence.json), which uses the existing
[example summary](/docs/reporting/examples/map-summary.json).

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

Producer `job`, `requiredSteps`, selected-lane steps and artifact names match GitHub's actual run API **exactly**, including case, spaces and matrix suffixes. For a matrix job displayed as `Build (TARGET_ID)`, register that resolved name, not merely `Build` or the YAML job key. Inspect the actual successful run/attempt; there must be one matching producer job and exactly one successful occurrence of every required step. See [policy inspection commands](/docs/reporting/platform.md#execution-policy-and-reuse).

The [platform contract and commands](/docs/reporting/platform.md) specify the public input files, packager metadata, producer policy, full/reused execution lanes, import CLI and preserved historical policies. These are shared interfaces; the project supplies its own measured inputs and approved execution facts.

```sh
uv run --locked python tools/import_reports.py --project game-slug --run RUN_ID
uv run --locked python tools/build_site.py --output build/new-candidate
```

## Policy updates

After initial registration, keep a complete producer policy in a tracked JSON file,
normally `config/TARGET_ID/producer.json`, and use it for packaging. The site records
that path once in its policy-sync configuration. When the workflow, reporting job,
required steps, artifact or tools change, update the policy in the same producer PR.
Record the actual committed workflow Git blob; never substitute a commit SHA.

The site's enabled policy-sync workflow detects changes and prepares a matching
site PR. It copies the policy verbatim, preserves the previous policy for historical
reports, authenticates a real successful package and validates the site candidate.
You no longer need to pass hashes between agents manually. The PR still needs
review/merge under the site's policy; a successful upstream run cannot approve
itself. Until approval, the live site retains its last successful deployment.

Routine progress needs no policy update when the policy is unchanged. A missing
tracked policy or failed package produces a visible setup/validation result rather
than guessed configuration. The [policy-sync guide](/docs/reporting/policy-sync.md)
covers the source registration, immediate/dry-run checks, site-owned token setup,
manual approval and recovery. Producer repositories need no site-write token.
Existing hash-free policy templates are an optional adoption case in the
[existing-project appendix](/wiki/existing-projects/#tracked-policy-sources).

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

### Prompt updates

After registration, add a separate completion notifier using the site's pinned
reusable workflow. A successful main report run requests a site refresh; the site
reauthenticates the run and imports only changed approved packages. No new policy
is trusted automatically. This avoids waiting for the periodic refresh without
rerunning site source tests for every producer commit.

The site-scoped GitHub App, caller generator, exact event fields, repository
variables/secrets, five-minute fallback and recovery behavior are documented in
[Producer policy sync](/docs/reporting/policy-sync.md#prompt-report-refresh).
These are optional delivery automation; the report contract and manual import
remain the same. Keep the notifier separate from the approved report workflow.
