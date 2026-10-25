# Website

Implement the game export and website adapter, validate one real package, then publish it through the shared renderer.

## Current state

NFL Street 2 is integrated and publicly deployed. Its importer authenticates existing main CI artifacts without adding game build steps. The website preserves accepted reports on `report-data` before publishing Pages. MVP and Tiger Woods remain previews until their producer and website adapters pass the onboarding checks.

The instructions below are an implementation assignment for a new agent. Configuration alone does not integrate a game: the current importer, validator and durable store explicitly support NFL. The [complete integration handoff](/docs/reporting/onboarding.md) names every shared-code extension, payload requirement, command and acceptance result. Read it before starting either repository.

## Refresh and build NFL

In the website repository, with Python 3.11+, uv and an authenticated GitHub CLI:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python tools/import_nfl.py
uv run --locked python tools/build_site.py --output build/site
python3 -m http.server 54872 --bind 127.0.0.1 --directory build/site
```

Use a new output directory for each retained candidate. The [NFL integration reference](/docs/reporting/nflstreet2.md) documents authentication, immutable packages, failure handling and the deployed publication flow.

## Project identity and artwork

Use the same slug for repository identity, `/games/<slug>/` and asset names. Configure title, console, target ID/hash, repository link, cover dimensions and contribution policy. Keep region/revision explicit. A different target must not overwrite another target's report history.

Store covers as `assets/covers/<slug>.webp` with their original aspect ratio. Use owned or authorized presentation artwork; do not export raw game assets through build reports. Console icons and other reused assets retain their provenance/license notes.

The local prototype's `assets/projects.js` is the current registration point. Adding a fixture there enables a layout preview, not production measurement. Production registration uses `config/projects.json`; `data/reports.lock.json` selects authenticated snapshots.

## Report semantics

| Metric | Meaning |
| --- | --- |
| Linked | Source incorporated into the verified target build |
| Matched | Exact measured source bytes, including eligible unlinked functions |
| Fuzzy | Target-size-weighted similarity; never exact-function credit |
| Functions exact / named | Complete exact extents / supported descriptive names within the declared inventory |
| Files exact / named | Exact evidenced file boundaries and contents / descriptive file identities, including provisional ones |

Overlapping progress layers are not additive percentages. A neutral name does not earn naming credit. A complete file claim requires its own boundary evidence. Map groups can be provisional without earning source progress. Preserve unmapped ranges.

Data and code fuzzy measurements need separate support. NFL's decomp.dev scalar is code-only; the website's packaged report carries separately measured code and data fuzzy coverage. Never copy a code score into a data metric to fill a missing field.

## Modular configuration

The project configuration independently enables maps, function counts, file counts, timeline and contributor rankings. Core code/data measurements are required by this initial site contract. Producer capabilities describe what actually exists; site preferences select what appears.

```json
{
  "schemaVersion": 1,
  "slug": "game-slug",
  "title": "Game title",
  "repository": "owner/game-slug",
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

Add a project to `config/projects.json` only after its adapter and first package are validated. This example shows the configuration shape; it does not make an unsupported game ready by itself. Enabling Contribute requires a guide URL. Attribution tracking is a separate game-repository policy; rankings require supported verified attribution data.

A disabled module creates no empty section or section listeners. NFL shares payloads between map/counts and timeline/rankings; an enabled sibling can still require that shared file. Unsupported data is not zero. If an already-supported enabled module fails to export, retain the last valid package and fail the refresh rather than silently hiding it.

## Hand a game to an agent

Give the agent the game checkout and `mitsevox/mitsevox.github.io`, each on its own work branch. The game owns builds, comparisons and source-derived reports. The website owns authentication, normalization, durable storage, project registration and rendering. An agent working only in the game repository cannot finish both halves.

Use this prompt together with the project's current repository instructions:

```text
Integrate this game with https://mitsevox.github.io/.
Read the wiki and https://mitsevox.github.io/docs/reporting/onboarding.md.
Work in separate game and website branches/worktrees; preserve unrelated work.

Inspect the real target, approved tools, build/report workflows and history.
Record supported measurements and optional modules. Do not infer credits from
merger identity or populate unsupported metrics from the layout fixtures.

Implement both the game report export and its website adapter. Account for
all NFL-specific assumptions listed in the handoff, including authentication,
package validation, multi-project storage, renderer inputs and CI refresh.
Keep contribution acceptance, attribution tracking and rankings independent.

Use a real successful main report for parity. Test absent optional data,
failed refreshes, unchanged reruns, stale runs, immutable collisions and
NFL-plus-this-game storage. Preserve previous history and decomp.dev output.

Deliver the two coordinated changes with exact revisions, commands, run and
artifact evidence, capability settings and the onboarding acceptance results.
Follow existing task authorization for pushes, PRs, publication and merges.
Do not call integration complete until the public page and its next refresh
have been verified against the accepted package.
```

The [starter archive](/wiki/downloads/repository-starter.zip) includes this prompt and the complete technical handoff. Agents should read the linked schemas and actual source rather than treat the starter files as a working compiler or generic CI pipeline.

If separate game agents work concurrently, assign one website integration owner for shared validation, storage, renderer and workflow changes. Implement that common extension once. Each game then supplies its own producer policy, adapter, tests and registration through it.

## Implementation sequence

| Step | Game repository | Website repository | Evidence before moving on |
| --- | --- | --- | --- |
| Inventory | Identify target/hash, build tools, raw report and history | Read the current NFL path and shared extension map | Verified facts and a capability matrix |
| Common foundation | Preserve the current build | Add trusted adapter dispatch, per-project storage and optional renderer inputs | NFL plus a second-project test; existing NFL data intact |
| Producer | Export supported public JSON and execution evidence from the existing measured build | Keep the new project disabled | Successful main artifact under a reviewed workflow/tool policy |
| Adapter | Retain original report, history and supported decomp.dev output | Authenticate the run; normalize, validate and lock the real package | Same-revision raw metric and module parity |
| Registration | Document the new export | Configure modules, contribution policy and production route | Build and browser checks with no fixtures |
| Publication | Keep the old feed until cutover is approved | Preserve the package, deploy and exercise the next refresh | Public manifest/route and durable lock agree |

The technical handoff gives MVP and TW's current target/report identities and build commands. It also explains their specific migration work: preserve MVP's separate publisher; preserve TW's stale-object pruning and audit checks while separating history writes from build permissions. Verify current revisions before implementation.

## Required public data

Use the [manifest](/docs/reporting/schema/report-v1.schema.json), [project configuration](/docs/reporting/schema/project-v1.schema.json) and [semantic contract](/docs/reporting/contract-v1.md). Each adapter adds payload schemas and a trusted producer policy for its actual workflow. Copying NFL's receipt type, job names or step names does not authenticate another game.

A package binds full source revision/tree, target/hash, methodology/generation, tool identities, measurement/publication times and file checksums to GitHub-verified run/artifact evidence. Raw byte totals remain authoritative; percentages are derived. Code/data fuzzy support is independent. Larger map/history/credit payloads are optional and referenced by checksum. The original public report remains available for parity checks.

A game with no contributor feed declares contributors unsupported and disables its rankings. A timeline must work without a contributor field. A summary-only game must display bars without inventing maps or inventory. The existing NFL readers still require common-code changes for these combinations; the [renderer compatibility checklist](/docs/reporting/onboarding.md#renderer-compatibility-work) names them explicitly.

A newly failed supported report is an error, not a new unsupported capability. Keep last-good data and report the failure. Preserve history evidence quality; do not manufacture historical measurements or contributor ownership to fill gaps.

## Website changes an agent must implement

| Area | Existing implementation to extend |
| --- | --- |
| Artifact selection and execution proof | `tools/import_nfl.py`, `tools/reporting/github.py` |
| Trusted adapter selection and payload validation | `tools/reporting/validation.py`, per-game producer policy and payload schemas |
| Multiple projects in the permanent archive | `tools/report_store.py` |
| Verified data bindings and static routes | `tools/build_site.py`, `assets/projects.js`, `assets/report-projects.js` |
| Optional map/count/history/credit data and fuzzy layers | `assets/progress.js`, `assets/activity.js`, `assets/reports.js`, homepage bars |
| Refresh all registered games | `.github/workflows/site.yml` |
| Regression and isolation coverage | Existing reporting/store tests plus the new adapter's tests |

The handoff specifies a project-selecting `tools/import_reports.py` interface for agents to implement. It does **not** exist yet. Keep the current NFL CLI working during that extension. The current Pages workflow blocks deployment if any refresh fails; independently preserving a successful project's import does not change that deployment policy.

## Acceptance and completion

Use the [full acceptance matrix](/docs/reporting/onboarding.md#6-commands-and-acceptance-evidence). It requires authentic execution, raw metric parity, optional-module behavior, honest maps/inventories, history continuity, multi-project storage, failure isolation and browser/live checks.

Website validation needs no game compiler:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python tools/build_wiki.py
uv run --locked python tools/build_site.py --output build/onboarding-candidate
python3 -m http.server 54876 --bind 127.0.0.1 --directory build/onboarding-candidate
```

Use a new build output directory. Offline validation cannot authenticate a new upstream package; separately run the implemented adapter against a real successful main run. Test corruption and races in isolated fixtures/remotes, not by damaging public history. Reuse adequate existing coverage and required game build evidence instead of repeating unrelated full builds.

The final handoff supplies both PRs/revisions, target/tools, producing run/attempt/artifact, import/build commands, manifest digest/lock, capability/policy matrix, parity/failure results and live refresh verification. A second game is integrated when its public route and the next scheduled/manual refresh preserve the accepted data alongside NFL. Any blocker gets a concrete next action; it is not checked off as complete.

## Current publication boundary

Site CI validates PRs and produces candidates. Push/manual/scheduled refreshes restore the durable last-good package and use read-only access to NFL. A failed refresh fails CI and leaves the live site unchanged. Only current-main publication jobs can append verified snapshots to this site repository’s `report-data` branch and deploy the validated Pages artifact. Historical snapshots remain in Git when candidate artifacts expire after 90 days. No workflow writes game source branches or changes NFL’s existing publication.
