# Legacy producer compatibility

This document describes the preserved legacy-format adapter. Shared registration, installation, storage and rendering are documented in the [platform interface](platform.md). New producers export report-v1 through the common path; they do not copy this adapter.

The first adapter consumes NFL's existing verified publication artifacts. It does not change NFL's build workflow, compiler, comparison rules, contributor policy, decomp.dev feed or existing Pages site. The extra validation runs in the website repository.

## Commands

From the website checkout, with Python 3.11+, uv and an authenticated GitHub CLI:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python tools/import_nfl.py
uv run --locked python tools/build_site.py --output build/site
python3 -m http.server 54872 --bind 127.0.0.1 --directory build/site
```

The build output must be a new directory. Use another output path when retaining earlier candidates. No game executable or private compiler access is needed. Authentication is used only by the importer; the built website contains no token and makes no GitHub API calls. The read-only Actions token is used in site CI.

`--run RUN_ID` selects a specific successful NFL main run for investigation. It cannot move the lock behind the last accepted source revision or rewrite recorded history. Use an isolated checkout to inspect older snapshots; do not delete an established lock to bypass that rule.

## What is authenticated

`config/nflstreet2-producer.json` pins the repository, target, approved producer workflow Git blob and build environment digest. A producer workflow change requires an explicit policy review; the importer never automatically expands this allowlist.

The importer checks GitHub-held run identity, same-repository origin, main ancestry, attempt, baseline job, required successful steps and artifact timestamps. It verifies GitHub's archive digest before parsing only the expected public JSON reports. It never extracts or executes scripts from the archive.

The three main artifacts are:

- `github-pages`: progress map, inventory and activity feed.
- `published-history-v1-ATTEMPT`: independently checks the same activity feed and published run/target identity.
- `GN7E69_report`: compares linked/exact code and data totals and code fuzzy coverage with decomp.dev's supported fields.

For reused measurements, the importer also verifies the original PR handoff artifact's digest and its report/tree bindings, compares its measurement payload with the main publication, and retains its original measurement timestamp. NFL's trusted main job remains responsible for authenticating final PR execution and the complete tested tree, source/comparison evidence and original attribution. The consumer does not claim that JSON checks reproduce that game validation.

Offline package checks validate structure, coverage, arithmetic, checksums and recorded policy/receipt consistency. They do not independently authenticate GitHub. Their trust anchor is the previously authenticated snapshot accepted into the site repository or current CI run.

## Package and state

Each import produces `data/nflstreet2/snapshots/REVISION-v1-RUN-ATTEMPT/` with:

- `manifest.json`: normalized summaries, capabilities, target, source tree, measurement/publication timestamps and checksums.
- `progress.json`: unchanged NFL report; complete file/function maps and evidence distinctions survive.
- `activity.json`: unchanged history and contributor rankings.
- `receipt.json`: bounded GitHub execution/artifact evidence and original measurement provenance.
- `summary.json`: the small presentation summary, checked against the report at build time.

`data/reports.lock.json` selects the package by path, full revision and manifest SHA-256. It also holds latest repository commit metadata, independently of the measured revision. The importer downloads and validates before taking a local publication lock, then rereads last-good state and checks ancestry/history before an atomic pointer replacement. Static assembly takes a shared lock for its full read so data cannot change between validation and copying. Newer slow-finishing imports cannot be replaced by older ones. Identical imports do not rewrite immutable snapshots; conflicting contents fail.

A package already accepted into the owner-controlled site `main` or published `report-data` branch can be reused after its downloadable artifacts expire. The importer reads the accepted lock from GitHub, requires its manifest digest/path/revision to match the local package, then rechecks current GitHub execution state, main ancestry and local integrity. A local branch’s self-consistent checksums or a genuine run ID alone are insufficient; unaccepted or changed snapshots require original artifact proof. A new run without accessible proof fails. Fetch, schema, parity, attribution-count, history-continuity or immutable-identity failures leave the old selected package intact.

## Rendering and modules

`assets/projects.js` retains artwork and project identity. `config/projects.json` is the production registration and presentation policy. NFL is the only production-enabled project until the other adapters are verified. All three games remain available in the source-layout preview; synthetic MVP/TW files are never copied into the assembled site.

Each configuration independently selects map, function counts, file counts, timeline and rankings. `contributions.accepting` controls the header/footer contribution links separately from rankings and the game's attribution requirements. Disabled sections mount no UI or section listeners. The legacy NFL adapter shares one map/count payload and one timeline/ranking payload; disabling one member does not suppress a fetch required by its enabled sibling.

The builder rejects unsupported enabled modules, fixture origins, mismatched configuration and corrupted locks. One content-addressed asset directory binds JS, CSS and templates to the same build. Game/wiki routes retain static entry files for direct navigation. Build into a fresh directory; a failed build must not replace a previously deployed artifact.

## Automation and rollout boundary

`.github/workflows/site.yml` validates PRs without publication privileges. Pushes, manual runs and the six-hour schedule restore the last-good package, refresh authenticated NFL reports and assemble a candidate. Failed refreshes fail CI and do not deploy; the live site remains unchanged. Candidate artifacts are retained for 90 days.

A separate successful **current-main** job preserves all verified package files and the latest lock on this site's data-only `report-data` branch, then deploys the same validated artifact to GitHub Pages. The first publication creates the branch from the reviewed bootstrap package. Restore reads bounded blobs without checking out or executing branch contents. It keeps a newer reviewed local package only if ancestry and recorded-history continuity pass. A missing store branch is treated as initial bootstrap; protect this branch from deletion after launch and recover its Git history before running refreshes if it is lost.

Snapshots are immutable, earlier data commits remain accessible, identical reruns are idempotent, and ordinary fast-forward pushes reject concurrent writers. Site main freshness is checked before storage and again immediately before deployment. Only the main publishing job has site-repository contents-write, Pages and deployment-identity permissions. Work branches and PRs cannot publish. No job merges main or writes a game repository.

Already-authenticated snapshots can outlive upstream Actions artifacts because the owner-controlled store lock is an additional cache trust anchor. A new measurement still requires original upstream proof; expiration never permits invented provenance. The site store is an implemented consumer-side archive, not a change to NFL's existing producer/history system or the proposed per-game `progress-data` branches.

Pages is configured for Actions publication. The owner merges the reviewed source PR; its main workflow performs launch. Verify the live hub, NFL route, wiki deep links and report manifest after deployment. MVP and Tiger Woods stay unpublished until their adapters are verified. Existing game sites and decomp.dev feeds remain unchanged. For a UI rollback, merge a reviewed source revert and rebuild with current verified data; do not rerun an obsolete source workflow or reset measurement history.

## New producers

Use the common report-v1 packager, producer policy and importer described in [the platform interface](platform.md). Register metadata and artwork through configuration. Keep this compatibility reader and its approved policy in the registry archives when the existing source moves to the standard format, so accepted reports and history remain readable.

## Standard-report migration

Phase A stages `nflstreet2-report-v1-producer.json` as the pending policy while the active
registration stays `nfl-legacy-v1`. Workflow `98a97409baceb8d8d9f9bf5706507b91331e8e4d` is
approved for both policies. The report-v1 policy derives from the producer-owned template;
its artifact is `report-v1`, job `Toolchain baseline`, with map-v2 evidence.

A real-run parity check at run `40253689256`, revision `caec9316e808e72ccbaf79c5ec108d1ac9fa08d0`,
authenticated both formats and found equal summaries, geometry/metrics/evidence, 14,157
functions, 12,119 exact IDs/unique credits, three contributors and 160 history values.
With the cutover unset, the standard package currently labels those rows measured; it
must not replace the accepted legacy rows yet.

After phase A merges, freeze the legacy selection and copy the **last durable stored**
legacy row's revision and built_at verbatim to the game owner. The producer pins that
cutover and publishes a new main report. Only then may phase C activate the pending
standard policy, archive the compatibility reader and validate that every frozen row
survives through an exact inherited record. Retire game Pages/artifacts after that switch.

Phase B freezes the durable legacy package selected from report-data commit
`399e3417058026523fc675625d8a110b757a5240`, after phase A's main publication succeeded.
The selected package is run `40253689256`, with 160 rows. Its final stored row is:

```json
{
  "revision": "caec9316e808e72ccbaf79c5ec108d1ac9fa08d0",
  "built_at": "2026-10-26T01:23:04.825014+00:00"
}
```

Both import entry points, the common installer and data-store publisher enforce the
checkpoint. Standard import remains pending. Do not remove the freeze or activate it
until the game lands this exact inheritedThrough pin and produces a successful main
package. Phase C must authenticate that package and accept all 160 frozen rows.
