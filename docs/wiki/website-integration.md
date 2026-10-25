# Website

One shared renderer, game-owned measurements and modules selected per project.

## Current state

The shared UI is a local prototype with persistent navigation and individual game routes. NFL uses a frozen real report; MVP and Tiger Woods use synthetic layout measurements. The common reporting contract and CI migration are proposals. This chapter explains the integration target and the concrete remaining work; it is not a claim that a new game's CI can already plug in automatically.

## Project identity and artwork

Use the same slug for repository identity, `/games/<slug>/` and asset names. Configure title, console, target ID/hash, repository link, cover dimensions and contribution policy. Keep region/revision explicit. A different target must not overwrite another target's report history.

Store covers as `assets/covers/<slug>.webp` with their original aspect ratio. Use owned or authorized presentation artwork; do not export raw game assets through build reports. Console icons and other reused assets retain their provenance/license notes.

The local prototype's `assets/projects.js` is the current registration point. Adding a fixture there enables a layout preview, not production measurement. Production registration will use the versioned configuration and verified report locations described below.

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

The proposed project configuration independently enables maps, function counts, file counts, timeline and contributor rankings. Core code/data measurements are required by this initial site contract. Producer capabilities describe what actually exists; site preferences select what appears.

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

This is a draft configuration example. It does not modify the live prototype by itself. Enabling Contribute requires a guide URL. Attribution tracking is a separate game-repository policy; rankings require supported verified attribution data.

A disabled module creates no empty space, fetches or event listeners. Unsupported data is not zero. If an already-supported enabled module fails to export, retain the last valid package and fail the refresh rather than silently hiding it.

## Producer adapter checklist

1. Establish target and tool identity; verify build/comparison inputs.
2. Translate raw measurements into the common manifest without changing denominators or losing partial progress.
3. Supply typed map/history/credit payloads for supported modules; attach checksums and provenance.
4. Validate ranges, inventory, arithmetic, target identity, history continuity and the project's attribution policy.
5. Produce website and decomp.dev outputs from the same verified computation where possible.
6. Publish immutable snapshots and advance latest only after success.

The [draft manifest schema](/docs/reporting/schema/report-v1.schema.json), [configuration schema](/docs/reporting/schema/project-v1.schema.json) and [semantic contract](/docs/reporting/contract-v1.md) are available. Full payload schemas, semantic validators and producer adapters remain implementation gates. JSON-schema validation alone does not authenticate CI.

## Consumer and rollout checklist

Fetch packages during the site build, pin exact identities in a lockfile, validate provenance/checksums, reject fixture origins and copy the selected data into the static output. Browser visitors need no GitHub credentials. Load heavy map/history payloads only when their module needs them.

If one game's refresh fails, keep its last verified package; another game's valid update can still publish. Never present newest-commit metadata as a newly measured build. Test direct routes, custom menus, keyboard navigation, disabled modules, cached assets and rollback before deployment.

Migrate NFL first, compare both consumers at the same revision, then add MVP and Tiger Woods. Preserve their current decomp.dev artifact feeds and histories throughout. Redirect existing game Pages only after owner-approved live parity. The [migration plan](/docs/reporting/migration.md) lists the acceptance gates.
