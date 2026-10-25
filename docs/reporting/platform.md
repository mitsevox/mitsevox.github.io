# Personal reporting platform

The site accepts versioned reports from the owner's registered repositories. It is a curated portfolio: identity, artwork, producer policies and enabled features are maintained in this repository. There are no visitor accounts, submissions or automatic repository discovery.

## Registration

Three configuration files separate authority, measurement and presentation:

- `config/site.json`: this site's repository and owner. Registered producer repositories must belong to that owner.
- `config/producers.json`: project slug → fixed supported format and a checked-in producer policy filename. Optional `archives` retain approved older policies/formats for existing snapshots.
- `config/projects.json`: displayed title, console, target, cover path/dimensions, module settings and contribution policy. A registered producer can stay archived without being displayed.

A new producer using `report-v1` needs configuration, artwork and a conforming artifact. No project-specific Python importer, JavaScript project entry or hand-written game route is required. Unknown slugs/formats fail. Report strings cannot load arbitrary executable adapters.

The first source feed retains a legacy format adapter so it can continue unchanged during its CI transition. That adapter translates an older export at the boundary; common installation, locks, storage, registration, rendering and deployment serve all projects.

The [producer configuration example](examples/producer.json) and [presentation example](examples/project.json) are unregistered templates with explicit example identities. Replace their target/tool/workflow facts before use; structural validity alone is not execution proof.

## report-v1 input

The producer supplies `summary.json`, plus any supported `map.json`, `timeline.json` and `contributors.json`. All are JSON files, with no symlinks, extra files or nested archive paths.

`summary.json` is the manifest's `summary` object: raw code/data `totalBytes`, `linkedBytes`, `matchedBytes` and nullable `fuzzyEquivalentBytes`, plus nullable function/file inventories. Linked source can exceed exact coverage; the site preserves that relationship. Unsupported fuzzy is omitted from its UI, not displayed as a copied exact score.

Payload schemas:

- [Map](schema/map-v1.schema.json): code/data nodes with addresses or explicit extents, nested groups, exact/linked/optional fuzzy bytes, and optional full function identities.
- [Timeline](schema/timeline-v1.schema.json): ordered unique measured revisions, raw linked totals and declared provenance. No contributor field is required.
- [Contributors](schema/contributors-v1.schema.json): distinct user identities, counts, and a function-to-authors ledger. Joint authors can each count a function; the union must equal the exact inventory. When function map extents are present, their exact identities must agree with the credit ledger.
- [Execution receipt](schema/execution-v1.schema.json): immutable input/output and execution bindings.
- [Producer policy](schema/producer-v1.schema.json): approved source identity and execution rules.

Counts keep their declared basis. Partial and provisional map groups are supported. The validator checks coverage, overlap, child sums, complete extents and current-history parity. The upstream validated producer remains responsible for original source fidelity and its evidence/naming policy; website JSON validation does not rebuild the game.

## Map semantics

A supported `map.json` contains **both** `sections` and `files`. These are two partitions of the same declared address universe, not independently chosen samples. Code and data are checked separately. Different grouping and different leaf boundaries are allowed.

| Rule | Required result |
| --- | --- |
| Summary parity | In each view and kind, top-level `size`, `linked`, `matched` and supported `fuzzy` sum to the corresponding summary values |
| Address parity | The union of leaf intervals in `sections` equals the union in `files` for each kind; equal byte totals alone are insufficient |
| Intervals | End-exclusive `[start,end)`; positive extent; address strings use `0x` and uppercase hexadecimal digits, 8–16 digits; bounds fit the supported address space |
| Geometry | Within a view/kind, leaves do not overlap; adjacent intervals may merge; separated ranges stay explicit rather than filling holes |
| Node size | `size` equals the sum of its own extents; use `mapped_extents` for disjoint ranges instead of one bounding box |
| Nesting | Children keep the parent's kind; child byte metrics sum to parent metrics; an explicitly declared parent extent equals its children's address union |
| Fuzzy | If summary fuzzy is supported, both views provide it throughout aggregation; fractions use the validator's numeric tolerance, not rounded display percentages |
| Function identity | A `type: function` leaf in the file view supplies `function_address` and `original_size`; its mapped ranges lie inside that complete extent |
| Function coverage | All fragments of a function together cover its full declared extent; a fragment cannot count as a full exact function |
| Inventory parity | When function identities are present, distinct full extents and eligible full-leaf exact matches agree with declared function inventory counts |

Keep unassigned bytes represented as honest gap/unmapped nodes with their actual metrics. Do not invent file ownership, split original units, or shrink summary denominators to hide bytes missing from the file view. A gap between two actual measured ranges is not automatically part of the measured universe; represent only the bytes the summary declares.

The [map example](examples/map.json) and [matching summary](examples/map-summary.json) show one code section split into a descriptive file group and an unassigned range, plus data. The values are illustrative. Rename the selected summary to `summary.json` when preparing a canonical input directory; do not copy every examples file into the package.

For example, two views of 100 bytes at different addresses fail even when every numeric total agrees. A tree can also pass JSON Schema but fail semantic validation because children overlap or parent totals do not reconcile. Run the shared packager/validator locally before uploading.

## Import legacy history

Existing history is useful even when it predates this pipeline. Migrate it before the first accepted report using a reproducible, reviewed conversion; retain the raw input separately. Do not reset an already accepted timeline during a later refresh.

Every published row requires a full 40-character commit SHA, valid `built_at` timestamp, positive integer code/data `total`, integer `linked` between zero and total, and provenance `kind` plus a nonempty `source`. Rows have unique revisions and nondecreasing timestamps. The current report revision must have a row whose code/data totals and linked values exactly equal its summary.

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

See the [illustrative legacy timeline](examples/timeline-legacy.json). Its placeholder commit identities and values are not production evidence. The site retains provenance in accepted data; the current graph does not display separate provenance badges, so the metadata label alone does not create a visible rebuilt/measured distinction.

## Package a producer report

Run the shared tool from a checkout pinned to an approved site revision. It reads public outputs and does not compile the game:

```sh
uv sync --locked
uv run --locked python tools/package_report.py \
  --input /path/to/public-input \
  --metadata /path/to/execution-metadata.json \
  --policy /path/to/approved-producer.json \
  --output /path/to/new-public-report
```

Metadata supplies `project`, `repository`, `target`, full `revision`/`tree`, `methodology`, `generation`, `measuredAt`, `publishedAt`, `tools`, `runId`, `attempt` and `workflowBlob`. Default mode is `full`, with `source: null`. These values come from the actual measured execution, not a copied example. The tool creates the manifest, receipt and checksums and validates the package before exposing it. Output must be a new directory.

Upload the resulting files as the policy's exact artifact name after the policy's required job and validation steps succeed. Keep original binaries, restricted tools and private research out of this artifact. The report revision/tree must be the actual source tested by the producing workflow.

## Execution policy and reuse

A policy declares repository/target, workflow path, branch, approved workflow Git blobs, artifact name, job name, common required steps, tool identities and validation `lanes`. `lanes.full` names successful full-validation steps; optional `lanes.reused` names successful proof-authentication steps. Exactly one lane must have succeeded. Standard main reports originate from `push` or `workflow_dispatch`; producers adapt their job layout to this execution boundary.

Job, step and artifact names are **case-sensitive exact strings** from GitHub's run API, including spaces and punctuation. A matrix job is matched by its resolved display name (for example `Build (TARGET_ID)`), not its YAML job key or the unsuffixed `Build`. Exactly one job must match. Each required/selected-lane step name must occur successfully exactly once. A missing, renamed or skipped required step fails; selection steps intentionally skipped by a lane do not belong in its common requirements.

Inspect a real successful run/attempt before registering policy:

```sh
gh api repos/OWNER/REPO/actions/runs/RUN_ID/attempts/ATTEMPT/jobs \
  --jq '.jobs[] | {name, steps: [.steps[] | {name, conclusion}]}'
```

With a matrix, publish each target under its own registration/artifact policy and exact resolved job name, or use one explicitly named aggregation job that authenticates all contributing target results. Do not use wildcards, trim suffixes, or pick the first successful job. Renaming adopted steps/jobs requires a reviewed matching producer-policy update.

For reuse, metadata sets `mode: reused` and `source` as defined in the execution schema: original revision/tree, run/attempt, artifact ID/digest and original measurement time. The original artifact is a full report-v1 package. The consumer checks its same-repository execution, approved workflow, successful full lane, artifact digest, complete tree, target, tools, methodology, generation, summary, map and credits. A timeline can append the new publication without changing the source measurements. Original proof cannot be replaced by a set of constituent reports.

A newly imported package requires accessible proof. An identical package already authenticated into owner-controlled site main or `report-data` can outlive upstream artifact retention; the consumer rechecks integrity and current run/main eligibility. Local checksums or a real run ID alone do not establish that cache exemption.

## Import and preview

```sh
uv run --locked python tools/import_reports.py --project game-slug --run RUN_ID
uv run --locked python tools/import_reports.py --all
uv run --locked python -m unittest discover -s tests -v
uv run --locked python tools/build_site.py --output build/new-candidate
python3 -m http.server 54876 --bind 127.0.0.1 --directory build/new-candidate
```

`--project` modifies only that project's lock. `--run` cannot bypass provenance, roll back main ancestry or rewrite history. `--all` attempts every registered producer and exits nonzero if any fails, retaining each failure's last-good pointer. Successful imports remain in the candidate. Current site CI blocks deployment on any refresh failure, so the live site stays unchanged until a complete refresh succeeds.

## Storage and cutover

The shared installer validates before taking the publication lock, then rereads state, checks ancestry/history, installs immutable files and atomically replaces only that lock entry. The static builder takes a shared lock while reading and copying.

The `report-data` branch keeps every accepted package and its latest lock. Multi-project restore/publish rejects an older candidate that would erase a stored project. Unknown stored registrations block an outdated publisher instead of being dropped. Ordinary non-force Git pushes reject competing writers, identical publications are no-ops, and current site main is checked before storage and deployment.

A corrected measurement should come from a reviewed new source/tool revision and declare the updated methodology/generation; the same source revision cannot silently acquire conflicting summaries.

When a producer changes format or policy, retain the approved previous `{format, policy}` registration in its `archives`. Historical policies validate historical packages; only the active policy admits new imports. Preserve existing timeline rows unchanged. If a new timeline representation is needed, an `inherited` provenance entry may embed the exact prior row as `record`, with identical revision/time/code/data fields; history validation checks that original record rather than silently rewriting it.

Keep archived policies and payload schemas as long as retained reports need them. Do not reset the store or relax checks to get a format transition through.

## Presentation and completion

The builder generates all `/games/<slug>/` routes from the shared shell and binds validated manifest summaries. Optional assets load only when their enabled modules need them. Summary-only, timeline-only and rankings-only projects do not require fake sibling payloads. Contribution links remain independent of rankings.

Cover files live in the site repository. The site uses the common layout, code/data colors, hover behavior, map, counts and activity sections. Console identity is configured; unknown consoles get a neutral icon rather than another console's mark.

A completed registration has real raw-metric parity, tested failure/ordering behavior, a correct direct public route and a successful subsequent refresh. Synthetic contract fixtures stay isolated in tests and are never registered in production.
