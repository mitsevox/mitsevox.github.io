# Website

One shared renderer, game-owned measurements and modules selected per project.

## Current state

The shared renderer now consumes authenticated NFL Street 2 report packages. The importer verifies NFL’s existing main CI artifacts; it adds no game build steps. The production builder includes only verified configured projects. MVP and Tiger Woods remain layout previews until their own adapters are validated. A successful current-main site workflow preserves verified reports and deploys Pages.

## Refresh and build NFL

In the website repository, with Python 3.11+, uv and an authenticated GitHub CLI:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python tools/import_nfl.py
uv run --locked python tools/build_site.py --output build/site
python3 -m http.server 54872 --bind 127.0.0.1 --directory build/site
```

Use a new output directory for each retained candidate. The [NFL integration reference](/docs/reporting/nflstreet2.md) documents authentication, immutable packages, failure handling and the remaining production-promotion step.

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

Data and code fuzzy measurements need separate support. NFL's decomp.dev scalar is code-only; data similarity is in sections while its current data bar exposes linked/exact progress. Never copy a code score into a data metric to fill a missing field.

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

## Producer adapter checklist

1. Establish target and tool identity; verify build/comparison inputs.
2. Translate raw measurements into the common manifest without changing denominators or losing partial progress.
3. Supply typed map/history/credit payloads for supported modules; attach checksums and provenance.
4. Validate ranges, inventory, arithmetic, target identity, history continuity and the project's attribution policy.
5. Produce website and decomp.dev outputs from the same verified computation where possible.
6. Publish immutable snapshots and advance latest only after success.

The [manifest schema](/docs/reporting/schema/report-v1.schema.json), [configuration schema](/docs/reporting/schema/project-v1.schema.json) and [semantic contract](/docs/reporting/contract-v1.md) are available. NFL has payload schemas, semantic checks and a working consumer adapter. New games still need their own producer authentication and mapping. JSON-schema validation alone does not authenticate CI.

## Consumer and rollout checklist

The NFL importer authenticates and locks packages before static assembly. The builder verifies checksums and semantics, rejects fixture origins and copies selected data into the static output. Browser visitors need no GitHub credentials. Load heavy map/history payloads only when their module needs them.

If one game's refresh fails, keep its last verified package; another game's valid update can still publish. Never present newest-commit metadata as a newly measured build. Test direct routes, custom menus, keyboard navigation, disabled modules, cached assets and rollback before deployment.

Migrate NFL first, compare both consumers at the same revision, then add MVP and Tiger Woods. Preserve their current decomp.dev artifact feeds and histories throughout. Redirect existing game Pages only after owner-approved live parity. The [migration plan](/docs/reporting/migration.md) lists the acceptance gates.

## Current publication boundary

Site CI validates PRs and produces candidates. Push/manual/scheduled refreshes restore the durable last-good package and use read-only access to NFL. A failed refresh fails CI and leaves the live site unchanged. Only current-main publication jobs can append verified snapshots to this site repository’s `report-data` branch and deploy the validated Pages artifact. Historical snapshots remain in Git when candidate artifacts expire after 90 days. No workflow writes game source branches or changes NFL’s existing publication.
