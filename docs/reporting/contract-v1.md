# Public report contract v1

The shared manifest and project configuration define the integration boundary. Each producer and consumer adapter validates its own payload format against these semantics. Use the [project integration template](onboarding.md) and [website chapter](../../wiki/website-integration/) when applying the contract.

The [platform interface](platform.md) implements this contract for registered owner repositories. It provides common packaging, import, validation, storage and rendering; producer-specific fields are normalized into typed report-v1 assets.

## Package and identity

A manifest declares repository/project, console and target hash, measured source commit/tree, methodology and generation, `measuredAt` and `publishedAt`, tool provenance and run identity. `origin` is `measured` or `fixture`; production rejects `fixture`. The schema's run fields are claims until verified against trusted execution and receipts.

Code/data summaries are small and inline. Larger optional modules are separate JSON assets referenced by safe package-relative path, schema identifier and SHA-256. Fetch them only when needed. Restrict path resolution to the package root and allowlisted formats; verify checksum and size limits before parsing. A checksum binds content, not authorship.

Payload schemas preserve the project's map, inventory, history and provenance without losing evidence. Stable function identity is target + address + measured extent, not display name; a boundary correction needs an explicit identity migration. File grouping carries provisional/exact-boundary evidence and preserves address ordering. Unassigned ranges stay represented.

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

## Map coverage contract

When map support is enabled, section and file views must cover exactly the same leaf address union for each of code and data. Each view independently sums to the summary's total/linked/matched/supported-fuzzy values. Leaves cannot overlap within a view; children sum to parent metrics, and explicit parent geometry equals the child union. Unassigned measured bytes remain represented. Equal totals at different addresses fail.

Use end-exclusive intervals, explicit disjoint extents, full function identity/coverage and declared inventory parity. See the [complete map rules and paired examples](platform.md#map-semantics); JSON Schema alone does not establish these relationships.

## Three independent controls

1. **Producer capabilities:** a module is `supported` with a validated asset, or `unsupported` with a reason. A supported module that failed to generate is a failed report, not a newly unsupported feature.
2. **Presentation:** `modules` in site project configuration chooses whether maps, function/file counts, timeline and contributor rankings appear. Disabled modules must mount no UI, section listeners or empty spacing. Shared assets may still be fetched for an enabled sibling. Summary-only reports and independently optional history/credit payloads must be supported without fabricating sibling data. Core code/data summaries remain required.
3. **Contribution policy:** `contributions.accepting` controls the Contribute button and requires a guide URL when true. It does not control attribution recording or whether past contributors deserve credit.

Enabled UI requires the corresponding supported/valid data. During initial migration, configure unsupported modules off deliberately. For an already-supported module, a refresh failure retains last good data and surfaces CI failure, never silently hides it.

## History and contributors

History entries retain full revision, target, methodology, denominator, commit/measurement timestamps and evidence quality. Preserve measured, inherited legacy and reconstructed entries distinctly; do not turn interpolated/repeated values into verified builds. Timeline transitions across a changed basis need explicit handling.

Legacy rows with short SHAs or missing totals need evidence-backed normalization before initial acceptance. Resolve identity unambiguously, recover actual raw values and record `reconstructed` provenance where appropriate; the label does not excuse invented values. Preserve unresolved raw records in a project archive rather than presenting them as measured points. See the [legacy migration procedure](platform.md#import-legacy-history).

Credits use stable function IDs and evidence-backed author identities. Preserve original contribution provenance through aggregate PRs, squash merges and deleted branches. PR author and merger are supporting clues, not sole attribution. When attribution tracking is enabled by project policy, store provenance in the game repository so disabling its display cannot erase it. Tracking may be disabled independently; rankings then remain unavailable, while measurement and history can still publish. The project's recorded attribution policy remains authoritative until its owner changes it.

For the exact-function leaderboard, preserve explicit joint attribution: each person counts a function once, and personal totals may overlap. Never equate the sum of personal counts with the unique function inventory. Reconcile the set of credited exact function IDs against the measured exact inventory; investigate historical gaps rather than assigning them to the merger. Enable rankings only when the declared attribution evidence can be validated.

Latest repository commit metadata is a separate site input. Its timestamp/title may be newer than the measured revision; it never changes report identity or makes old progress look freshly measured.

## Versioning and validation boundary

Schema v1 rejects unknown fields to catch spelling mistakes. Evolve with an explicit version and consumer compatibility check; pin a shared validator revision. Adapter acceptance requires semantic validation of range bounds/overlaps, aggregation, identities, source naming policy, credits, history consistency, target/tool hashes and provenance. Reused build proof requires the authenticated tree/environment checks in the workflow specification. Production must reject fixtures even when structurally valid.

For Python JSON Schema tooling, install `jsonschema[format]` and enable `FormatChecker`; a bare installation may not enforce the date-time format. Schema validation must reject negative byte counts, malformed target hashes, invalid module shapes, path traversal, unknown fields, invalid timestamps and an enabled contribution button without a guide. Semantic validation additionally establishes measured-data consistency; trusted execution must be authenticated separately.
