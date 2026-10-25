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
