# NFL Street 2 standard reporting

NFL Street 2 now uses the same report-v1 importer and renderer as the other registered
projects. Its active policy is `config/nflstreet2-report-v1-producer.json`, workflow
`.github/workflows/baseline.yml`, job `Toolchain baseline`, artifact `report-v1`.
Map-v2 preserves source/comparison paths and file evidence. No current import reads the
game's Pages, published-history or decomp.dev artifacts.

```sh
uv run --locked python tools/import_reports.py --project nflstreet2
uv run --locked python tools/build_site.py --output build/new-candidate
```

## History cutover

Phase A staged the standard policy and authenticated PR tested-merge proofs. Phase B froze
the durable legacy package at 160 rows. The game's cutover pin landed in PR #1133.
Phase C imported successful main run `40258381140`, source
`855854d83f47dd1a6a9cf3afe07c68a7dbf07877`: 161 rows, including all 160 frozen rows as
exact inherited records, zero rejected. The active registration has no freeze or pending
policy.

`config/archives/nflstreet2-legacy-checkpoint.json` retains the exact legacy entry, cutover
row and first standard entry. Historical payloads remain immutable in Git and the durable
store. The legacy producer policy is retained under registration archives solely to read
those packages.

## Archived compatibility

- `tools/archives/import_nfl.py`: retired network adapter; its CLI is disabled and its
  refresh function rejects the current standard registration.
- `tools/reporting/archives/legacy_nfl.py`: read-only validation of retained legacy data.
- `tools/reporting/archives/github.py`: retired Pages parsing and recorded workflow checks.

The active importer accepts standard report-v1 only. Archived code does not select or
refresh production reports. The [historical reference](archive/nflstreet2-legacy.md)
documents the retired path; it is not a setup guide.

## Automation and rollout boundary

Site CI restores accepted report-data, imports each registered producer through the common
standard path, validates/assembles the site, preserves snapshots and deploys only current
main. A failed refresh retains the live release. Source repositories are never written.
See the [platform](platform.md) for the shared execution and storage contracts.

The site supplies `/nflstreet2/` as a redirect to `/games/nflstreet2/`, preserving query/hash
in browsers with JavaScript. Retiring the game's own Pages deployment/settings lets the
shared site's alias serve that path. The game can now remove its old Pages job and legacy
artifacts; approve the next workflow blob on the site before merging that workflow change.
