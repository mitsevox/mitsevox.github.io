# Public report contract v1

The manifest/configuration schemas and NFL legacy payload schemas are implemented with semantic checks and authenticated ingestion. See [NFL integration](nflstreet2.md) for the exact trust boundary and commands. Use the [integration handoff](onboarding.md) to implement another producer and its website adapter. Current NFL validators, storage and renderer assumptions must be extended explicitly; the schema describes the shared contract, not already working support for every combination.

`manifest.summary` uses `totalBytes`, `linkedBytes`, `matchedBytes` and nullable `fuzzyEquivalentBytes`. The current browser receives NFL legacy fields (`total`, `linked`, `matched`, optional `fuzzy`) through packaged view models. An adapter must validate that translation; publishing the manifest alone will not populate the existing UI.

## Package and identity

A manifest declares repository/project, console and target hash, measured source commit/tree, methodology and generation, `measuredAt` and `publishedAt`, tool provenance and run identity. `origin` is `measured` or `fixture`; production rejects `fixture`. The schema's run fields are claims until verified against trusted execution and receipts.

Code/data summaries are small and inline. Larger optional modules are separate JSON assets referenced by safe package-relative path, schema identifier and SHA-256. Fetch them only when needed. Restrict path resolution to the package root and allowlisted formats; verify checksum and size limits before parsing. A checksum binds content, not authorship.

The NFL payload schemas preserve its existing map and activity representations without losing evidence. Stable function identity is target + address + measured extent, not display name; a boundary correction needs an explicit identity migration. File grouping carries provisional/exact-boundary evidence and preserves address ordering. Unassigned ranges stay represented.

## Measurement semantics

| Field | Meaning |
| --- | --- |
| `totalBytes` | Declared measured byte universe for code or data, excluding no ranges silently |
| `linkedBytes` | Source-produced bytes incorporated in the verified target build under that project's promotion rules |
| `matchedBytes` | Exact byte matches from validated source comparisons, including eligible exact-unlinked source |
| `fuzzyEquivalentBytes` | Size-weighted similarity coverage; fractional, never exact-match credit; null when unsupported |
| `functions.exact` | Full measured function extents that match exactly; fragments do not count |
| `functions.named` | Descriptive names accepted by the documented naming/evidence policy; not automatically recovered original names |
| `files.exact` | Exact mapped file groups with validated original boundaries under the declared policy; all constituent comparisons exact |
| `files.named` | Descriptively named source groups, including provisional boundaries; excludes boilerplate/address names |

Exact/named share their own declared inventory total. They overlap and must not be added. File totals need not equal map rectangles: code/data slices can belong to one source group, and unmapped regions are separate. Persist the inventory basis and version. A completed linked objdiff unit is not automatically an exact original source file.

All byte metrics use the same denominator within a code/data summary. Percentages are derived, not independently authoritative. Values must be finite and within total; zero denominator displays unavailable, not completion. Fuzzy includes exact coverage once, without duplicate ranges; it must not be less than matched under this contract. Linked and matched are independently validated: do not force equality or assume nesting for a new game's policy. The UI layers are overlapping cumulative coverage, never a sum. If a producer cannot support their intended relationship, resolve the adapter/policy instead of changing values for appearance.

Missing or unsupported measurements use null or an explicit unsupported module. Valid zero remains zero. Apply only defaults explicitly defined by the pinned upstream format. Malformed numbers and missing entire reports are errors. Comparison algorithms and weighting rules belong to the methodology version; do not compare historical percentages blindly across changes.

## Three independent controls

1. **Producer capabilities:** a module is `supported` with a validated asset, or `unsupported` with a reason. A supported module that failed to generate is a failed report, not a newly unsupported feature.
2. **Presentation:** `modules` in site project configuration chooses whether maps, function/file counts, timeline and contributor rankings appear. Disabled modules must mount no UI, section listeners or empty spacing. Shared assets may still be fetched for an enabled sibling. The current NFL progress reader requires map data, and its activity reader validates both credits and history; the onboarding task must remove those dependencies for summary-only and independently optional payloads. Core code/data summaries remain required.
3. **Contribution policy:** `contributions.accepting` controls the Contribute button and requires a guide URL when true. NFL is enabled; MVP/TW initially false. It does not control attribution recording or whether past contributors deserve credit.

Enabled UI requires the corresponding supported/valid data. During initial migration, configure unsupported modules off deliberately. For an already-supported module, a refresh failure retains last good data and surfaces CI failure, never silently hides it.

## History and contributors

History entries retain full revision, target, methodology, denominator, commit/measurement timestamps and evidence quality. Preserve measured, inherited legacy and reconstructed entries distinctly; do not turn interpolated/repeated values into verified builds. Timeline transitions across a changed basis need explicit handling.

Credits use stable function IDs and evidence-backed author identities. Preserve original contribution provenance through aggregate PRs, squash merges and deleted branches. PR author and merger are supporting clues, not sole attribution. When attribution tracking is enabled by project policy, store provenance in the game repository so disabling its display cannot erase it. Tracking may be disabled independently; rankings then remain unavailable, while measurement and history can still publish. NFL retains its existing attribution requirement unless its owner changes that policy.

For the exact-function leaderboard, preserve explicit joint attribution: each person counts a function once, and personal totals may overlap. Never equate the sum of personal counts with the unique function inventory. Reconcile the set of credited exact function IDs against the measured exact inventory; investigate historical gaps rather than assigning them to the merger. The existing NFL evidence/credit rules take precedence while adapting its output. MVP/TW credits remain disabled until equivalent evidence is established.

Latest repository commit metadata is a separate site input. Its timestamp/title may be newer than the measured revision; it never changes report identity or makes old progress look freshly measured.

## Versioning and validation boundary

Schema v1 rejects unknown fields to catch spelling mistakes. Evolve with an explicit version and consumer compatibility check; pin a shared validator revision. Adapter acceptance requires semantic validation of range bounds/overlaps, aggregation, identities, source naming policy, credits, history consistency, target/tool hashes and provenance. Reused build proof requires the authenticated tree/environment checks in the workflow specification. Production must reject fixtures even when structurally valid.

For Python JSON Schema tooling, install `jsonschema[format]` and enable `FormatChecker`; a bare installation may not enforce the date-time format. Structural checks performed for this draft accepted both examples and rejected negative byte counts, malformed target hashes, invalid module shapes, path traversal, unknown fields, invalid timestamps and an enabled contribution button without a guide. Local documentation links were also checked. These checks do not establish measured-data correctness or trusted CI execution.
