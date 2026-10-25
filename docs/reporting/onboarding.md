# Integrate another game

This is the implementation handoff for an agent integrating a game with `mitsevox/mitsevox.github.io`. Read it together with the [report contract](contract-v1.md), [NFL operational reference](nflstreet2.md), [pipeline audit](pipeline-audit.md) and both repositories' current instructions. The NFL path has passed real ingestion and public deployment. A new game still needs its own implemented and tested adapter; this document specifies that work rather than assuming it already exists.

## Assignment and ownership

The deliverable is two coordinated changes: verified public reports from the game, and a site adapter that imports, stores and renders them. A game-only PR does not complete integration. Use separate branches/worktrees in the game and website repositories. Keep normal reconstruction work separate from reporting changes.

| Game repository owns | Website repository owns |
| --- | --- |
| Target/hash, authorized references and private build access | Project identity, artwork, routes and presentation settings |
| Pinned build/compiler/linker/comparison tools | Public artifact authentication and safe parsing |
| Original-byte baseline, accepted source and partial comparisons | Normalization, package validation and exact lock selection |
| Source-derived measurements, inventory and supported modules | Durable `report-data` archive and atomic Pages deployment |
| Measurement history and attribution evidence when enabled by policy | Shared renderer, feature controls and consumer tests |

Give the agent read/write working access to both checkouts. Public GitHub read access is enough for the site importer; game build credentials stay with the approved game environment. Do not create cross-repository write tokens for polling. Push, merge, branch controls and publication follow the owner's task authorization and each repository's rules.

If MVP and TW agents work concurrently, assign **one website integration owner** for shared validation, storage, renderer and workflow files. Game agents supply their own adapters/tests and producer PRs; do not let two branches independently replace the same shared infrastructure. Integrate the common extension once, then add each game through it. This is coordination guidance, not permission to message another agent or open a new task.

## 1. Establish facts before editing

Read README, CONTRIBUTING, AGENTS and target configuration in the game checkout. Record its current full revision and tree, verified executable hash, approved build environment, compiler/linker/report tool identities, exact build commands, existing report artifacts and history location. Identify unsupported statistics explicitly.

Existing projects do not need to rename their source tree to match NFL. Follow the [layout and naming chapter](../../wiki/layout-and-naming/) for new files while preserving established paths and evidence. A fresh project first completes the [setup checklist](../wiki/starter/SETUP.md); an adapter cannot establish a missing original-byte baseline.

These read-only commands are usable now; substitute the selected repository:

```sh
gh api repos/mitsevox/mvp2005/commits/main --jq '{revision:.sha,tree:.commit.tree.sha}'
gh run list --repo mitsevox/mvp2005 --workflow build.yml --branch main --status success --limit 5
gh api repos/mitsevox/mvp2005/contents/.github/workflows/build.yml --jq .sha
```

A workflow file's `.sha` is its Git blob identity, not a run result. Pin the reviewed workflow blob and actual environment/tool hashes in the producer policy. Refresh these facts when the implementation starts; a successful run alone does not prove its measurements meet this contract.

### Existing producer starting points

Rechecked against both repositories' main branches on October 25, 2026:

| Game | Source revision | Target | Existing public report |
| --- | --- | --- | --- |
| MVP Baseball 2005 | `f1e1763bf76b7806ba704868be26935876a6efb1` | `GV4E69` | `GV4E69_report`, containing `report.json` |
| Tiger Woods 2004 | `ec5e6077ae41c3de7cebf69eae645c130cafd818` | `GW4E69` | `GW4E69_report`, containing `report.json` |

In their approved prepared build environment, the current workflow build commands are:

```sh
# MVP Baseball 2005
python configure.py --map --version GV4E69
ninja all_source progress build/GV4E69/report.json

# Tiger Woods 2004
python configure.py --map --version GW4E69
python tools/build/prune_stale.py
ninja all_source progress build/GW4E69/report.json
python tools/quality/audit.py --check
```

These commands assume authorized originals and the documented tool setup; they do not install or grant access to either. Do not run a second full game build solely to test website code if a suitable authenticated report already exists.

For MVP, preserve the separate artifact-consuming Pages publisher while making missing report/history failures explicit. For TW, retain stale-object pruning and audit checks; separate history writes from build permissions and make identical history appends a no-op. Both current images use mutable tags and independently downloaded tools: obtain the approved digest/version/hash evidence before pinning, without rebuilding or changing dependency access. See the [pinned audit](pipeline-audit.md) for source links and limitations.

## 2. Choose capabilities and policy

Record this matrix in the integration PR before enabling modules. The adapter implements the supported rows and explains each unsupported row.

| Capability | Required evidence | Site treatment |
| --- | --- | --- |
| Code/data summaries | Raw total, linked and exact byte counts from the same validated build | Required; never substitute a layout fixture |
| Code/data fuzzy | Method and size-weighted equivalent bytes for each kind independently | Null when unsupported; no fabricated third layer |
| Function counts | Stable full extents, complete exactness and descriptive-name policy | Enable only with a validated inventory |
| File counts | Declared group inventory, boundary-exactness and naming policy | Provisional named files may count as named, not exact |
| Map | Covered executable ranges, honest grouping and per-leaf measures | Disable if unavailable; preserve unknown ranges |
| Timeline | Validated historical linked measurements with provenance | Retain inherited/legacy evidence quality and gaps |
| Contributor rankings | Stable identities and evidence-backed exact-function attribution | Disable when unsupported; not inferred from merger or PR author alone |
| Accepting contributions | Owner policy and a public contribution guide | Separate `contributions.accepting` setting |

Attribution tracking is a game policy. It is not universally required to join the site. Keep NFL's existing policy intact. For MVP/TW, initially set contributor rankings and accepting contributions off unless the owner selects and the adapter supports them. Historical uncertainty is not a reason to fabricate names or block unrelated progress modules.

If a supported export unexpectedly fails, fail the refresh and retain last-good data. Do not change its capability to unsupported to conceal that failure. A repository that genuinely supplies no credits should have an unsupported contributors module and `modules.contributors: false`.

## 3. Export public measurements in the game

Prefer extending the existing report generation instead of adding another compile. Generate website and decomp.dev views from one measured input. Preserve the original raw report unchanged for parity/provenance checks. Clear stale output before export and upload only after validation succeeds.

A public artifact contains JSON measurements, map/inventory data for supported features, history when supported, and an execution receipt. Exclude binaries, original objects, complete debug exports, credentials and experiment dumps. Set explicit file/size limits and artifact retention. The site archive must retain accepted reports beyond that retention.

The game receipt must bind repository, full revision and tree, target/hash, methodology/generation, measured time, tool/environment identities, and every public payload checksum. Record the producing run ID/attempt and workflow/job identities. A site adapter authenticates these claims against GitHub-held metadata; self-written JSON is not execution proof.

Use a full validation lane initially. Implement reuse only when trusted main execution verifies complete landed-tree equivalence, target, environment, methodology and original artifact integrity. Keep original measurement time separate from main publication time. Do not mark a build `reused` merely because an objdiff report was downloaded.

Do not prescribe a universal artifact name or reuse NFL's job/step names. Declare the actual names in the game's reviewed producer policy, including the relation between build and publisher runs if separate. Candidate PR artifacts never advance public latest. Keep existing Pages and decomp.dev outputs available until live parity is verified.

## 4. Build the site adapter

The following are **implementation requirements for this onboarding task**, not commands or extension points already supplied for every game. The current code explicitly supports NFL. Implement and test the common extension before registering the second production project.

### Shared extension map

| Current file | Required extension |
| --- | --- |
| `tools/import_nfl.py` | Keep its working CLI as a compatibility wrapper; extract package installation, locking and history/ancestry checks from NFL-specific artifact interpretation. Add a project-selecting importer. |
| `tools/reporting/github.py` | Reuse bounded API/archive utilities. `authenticate_run`, required steps and Pages archive names are NFL-specific; use a reviewed per-adapter execution policy for other workflows. |
| `tools/reporting/validation.py` | Dispatch trusted adapters by registered project/methodology. Keep strict NFL checks. Replace the global five-file allowlist with each adapter's exact declared allowlist; validate all package files and references. |
| `tools/report_store.py` | Replace the exact `{'nflstreet2'}` contract and fixed paths/API with configured-project iteration, preserving the entire durable lock and all prior snapshots. Restore must also preserve a stored project not present in an older source lock. |
| `tools/build_site.py` | Bind only validated registered projects and supported assets. It currently assumes `progress.json`, `activity.json` and a legacy `summary.json`; add explicit bindings or verified normalization for the new adapter. |
| `assets/progress.js`, `activity.js`, `reports.js` | Consume the adapter's validated view model; check only the payload parts needed by enabled modules. Handle missing fuzzy/map/inventory/credits as documented below. |
| `assets/projects.js`, `report-projects.js` | Keep game identity separate from generated report bindings. Existing MVP/TW artwork is already present. |
| `.github/workflows/site.yml` | Refresh every registered adapter, preserve per-project last-good state, then build/store/deploy. It currently invokes NFL only. |
| `tests/test_reporting.py`, `test_report_store.py` | Retain NFL coverage and add real second-game parity plus multi-project ordering, optional-module and storage cases. |

Use a checked-in registry of trusted adapter implementations. A report's strings must never select arbitrary Python imports, paths or executable commands. Choose module layout in the implementation PR; the names in the table are existing files that must be accounted for, not instructions to duplicate an entire NFL importer.

### Required importer interface

Implement `tools/import_reports.py` with this CLI, then document the tested implementation revision:

```sh
# Required new interface; implement it before using these commands.
uv run --locked python tools/import_reports.py --project mvp2005 --run RUN_ID
uv run --locked python tools/import_reports.py --project tw2004 --run RUN_ID
uv run --locked python tools/import_reports.py --all
```

`--project` refreshes only that registered project. `--run` selects one eligible successful execution, never bypasses authenticity or ancestry. `--all` attempts every project, retaining a failed project's last-good pointer without preventing another valid import from being preserved in the candidate lock/artifact. It exits nonzero and names failures. The current deployment workflow blocks deployment on any refresh failure; keep that behavior initially and document it. Allowing partial-success deployment is a separate tested policy change, not something already implemented.

Each adapter must implement these responsibilities:

1. Load a checked-in producer policy such as `config/mvp2005-producer.json`, with repository, target/hash, reviewed workflow blobs, tools/environment, job/lane rules, artifact names and supported capabilities.
2. Select/authenticate eligible main execution, current attempt, job completion and exact artifact digests. Authenticate both runs for a separate publisher. Check the measured revision is still eligible in game main ancestry.
3. Parse a bounded allowlist of public files as data, validate raw metrics, and normalize supported UI fields without losing evidence or changing denominators.
4. Build and validate the manifest, summary, module assets and receipt; enforce raw-report parity before exposing the package.
5. Under the existing publication lock, reread last-good state, verify history continuity and ancestry, install an immutable package, and atomically update only that project's lock entry. Unrelated projects must survive byte-for-byte.
6. Reuse expired upstream proof only for an identical package identity previously authenticated into owner-controlled site main or `report-data`, then recheck integrity and current execution/main eligibility. An unknown checksum still needs original proof.

### Package contract

Use [manifest v1](schema/report-v1.schema.json) and [project configuration v1](schema/project-v1.schema.json). Their field names are the contract; the synthetic examples are not accepted measurements. Add typed payload/receipt schemas and semantic validation for the new methodology. Do not relabel an MVP/TW receipt `nfl-execution-v1` to pass NFL's validator.

Install beneath `data/<slug>/snapshots/<immutable-identity>/`. Bind identity to source revision, methodology, generation and run/attempt; preserve existing NFL identities. If the implementation adds a new naming version, retain a reader for old locks and snapshots. Different targets must not share an ambiguous pointer. The initial configuration supports one selected target per project slug; supporting another target requires explicit registration/routing design.

The lock entry has this shape; values come from the authenticated import:

```json
{
  "path": "data/game-slug/snapshots/IMMUTABLE_IDENTITY",
  "manifestSha256": "SHA256_OF_MANIFEST_BYTES",
  "revision": "FULL_MEASURED_REVISION",
  "latestCommit": {
    "revision": "FULL_LATEST_REPOSITORY_REVISION",
    "title": "Public commit subject",
    "description": "Public commit body",
    "date": "2026-10-25T12:00:00Z",
    "url": "https://github.com/OWNER/REPO/commit/FULL_LATEST_REPOSITORY_REVISION"
  }
}
```

This is a shape illustration with visible placeholders, not a schema-valid fixture. Latest commit metadata never replaces measured revision/time. The durable branch contains data only; do not check it out or execute its contents. All adapters retain safe path checks, no symlinks, duplicate-key/nonfinite rejection, archive expansion limits, atomic pointer replacement and non-force Git updates.

### Renderer compatibility work

The existing site is modular in presentation, but its legacy NFL readers have additional assumptions. Explicitly address them:

- `mountProgress` currently fetches/validates section and file maps even when the map module is disabled. A summary-only game must be able to display its bars without those payloads.
- Both bar renderers fall back from absent fuzzy to matched. Unsupported fuzzy should omit its strip and tooltip rather than claim that fallback is measured fuzzy progress.
- `activity.js` currently requires both `snapshots` and `contributors`, even if only one section is enabled. Timeline-only and rankings-only packages must validate/load independently, including a timeline with no contributor field at all.
- Count rendering has NFL-specific inventory-basis strings. Accept a registered adapter's declared basis after semantic validation; do not falsely assign NFL evidence quality to another inventory.
- The existing bar/metric reader assumes `linked <= matched <= fuzzy`. Verify the game's actual promotion policy. If its linked source can be incomplete, extend validation and strip rendering to preserve real values; do not clamp, sort, relabel or change metrics to fit the nesting assumption.
- Map coordinates, coverage, recursive sums and full function extents remain meaningful. Preserve unmapped ranges, provisional groups and source order. A fragment is not a complete exact function.

For an initial bar-only integration, export raw code/data totals and exact/linked coverage, disable unsupported features, and implement that module path. Adding fabricated map leaves or empty contributor arrays to satisfy NFL's schema is not an acceptable shortcut. An empty real contributor list and an unsupported contributor feed are different states.

## 5. Register and coordinate the cutover

After implementing the adapter and validating its first real package, add its project to `config/projects.json` with supported UI modules selected. Set `contributions.accepting` independently. The adapter policy must be accepted at the producer's landed workflow revision before scheduled imports begin.

Recommended landing order:

1. Merge the site common extension with the new project still disabled; prove NFL import, history, store and rendering remain valid.
2. Merge the game's producer/exporter changes, then obtain one successful authenticated main artifact under the reviewed workflow/tools.
3. Add/approve that exact producer policy, import the real package, compare its raw totals and enabled modules, then register the project in the site PR.
4. Merge/deploy the site registration. Verify the public route and an unchanged subsequent refresh. Keep the old game site/feed until the owner approves any redirect.

No step is complete merely because a workflow is green. Record the measured revision, run/attempt, artifact digest and package identity that were actually checked. Producer and site PR descriptions cross-reference each other. Common code changes are coordinated through the site integration owner.

## 6. Commands and acceptance evidence

These website commands already exist and must continue to work:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
node --check assets/app.js
node --check assets/progress.js
node --check assets/activity.js
uv run --locked python tools/build_wiki.py
uv run --locked python tools/build_site.py --output build/onboarding-candidate
python3 -m http.server 54876 --bind 127.0.0.1 --directory build/onboarding-candidate
```

The output directory must be new. Offline tests/build do not authenticate an unseen upstream report. Run the new importer CLI against a **real** producer main run separately, then build and compare that exact package. Do not execute the main-only `report_store.py publish` locally to bypass deployment guards; use isolated bare Git remotes in tests and the authorized main workflow for real writes.

Acceptance evidence is required for each row:

| Check | Pass condition |
| --- | --- |
| Authenticity | Correct repository/workflow/blob, target, source/tree, successful run/attempt, job and artifact digest; wrong origin, changed workflow or failed execution rejected |
| Metric parity | Raw integer totals/linked/exact equal upstream at one revision; fuzzy independently supported and weighted; decomp.dev compared only on supported fields |
| Optional features | Bar-only, timeline with no credits payload, counts/map disabled, contributions off, and supported-data failure behave as specified |
| Map/inventory | No overlaps or lost ranges, recursive sums agree, full exact extents only, naming/file-boundary policy respected |
| History | Existing archive imported without reset; same revision no-op; history deletion/rewrite and stale/diverged main rejected; legacy provenance retained |
| Store | NFL plus a second game survive restore/publish; stale source lock cannot erase a project; immutable collision fails; a concurrent normal push fails safely |
| Isolation | A failed new-game refresh cannot change NFL's lock/payload; successful independent imports can be preserved; documented CI failure/deployment policy holds |
| Cache | Accepted identical cached report survives artifact expiration; changed/unaccepted package cannot claim that exemption |
| Production output | No fixtures/private files; only enabled verified routes/assets; one coherent fingerprinted release |
| Browser | Home and direct game/wiki URLs, refresh/back/forward, game picker, per-strip hover, map interaction and disabled-module spacing verified |
| Live publication | Main job preserved the durable package before Pages succeeded; public manifest/route match the accepted package; next refresh is idempotent |

Use isolated fixtures and temporary remotes for deliberate corrupt/stale/race tests. Reuse adequate NFL regression coverage and review only the changed dependencies; do not repeat full game builds for documentation or UI edits. Local measurements and GitHub/live evidence must be labeled separately.

## Completion handoff

Supply the game and site PRs/revisions; target and tool identities; producing run/attempt/artifact; exact import/build commands; resulting manifest digest/lock; capability/policy matrix; parity and failure-test results; inherited history limitations; browser/live verification; and unresolved blockers with a next action.

The integration is finished when a second verified game survives both a real deployment and the following scheduled/manual refresh without replacing or losing NFL data. The handbook is the assignment; that game-specific acceptance record is the proof it was completed.
