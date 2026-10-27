# Report-v2: explicit targets

Report-v2 adds explicit target identity and independent target publication. The byte metrics,
module payloads, map geometry rules, execution proof rules and history preservation rules of
[report-v1](contract-v1.md) still apply. A consumer must explicitly support report-v2 before a
producer emits it. Pin an approved site revision whose packager implements report-v2; do not
add fields to report-v1 or relabel an old package in place.

## Identity and registry

A game has one stable `project` slug and repository. Every executable/disc revision has a
separate target object, validated by [target-v2](schema/target-v2.schema.json):

```json
{
  "id": "ABC123-rev0",
  "platform": "gamecube",
  "gameId": "ABC123",
  "region": "USA",
  "discRevision": 0,
  "sha1": "0123456789abcdef0123456789abcdef01234567"
}
```

For GameCube, `gameId` is six uppercase alphanumeric characters and `id` is exactly
`<gameId>-rev<discRevision>`. Disc revisions are integers from 0 to 255. `sha1` identifies the
original executable, not the whole disc. Establish game ID/region/disc revision from original
media evidence; a directory name alone is not evidence. Git `revision` and `tree` remain full
Git SHAs and are unrelated to `discRevision`.

The producer publishes `config/targets.json` using [targets-v1](schema/targets-v1.schema.json).
The site keeps an owner-reviewed copy in `config/<slug>-targets.json`. Discovery is metadata,
not permission to import a new target or execute producer code.

```json
{
  "schemaVersion": 1,
  "project": "game-slug",
  "defaultTarget": "ABC123-rev0",
  "targets": [
    {
      "target": {
        "id": "ABC123-rev0", "platform": "gamecube", "gameId": "ABC123",
        "region": "USA", "discRevision": 0,
        "sha1": "0123456789abcdef0123456789abcdef01234567"
      },
      "status": "active",
      "support": {"build": true, "reportFormats": ["report-v2"]},
      "legacyTargets": []
    },
    {
      "target": {
        "id": "ABC123-rev1", "platform": "gamecube", "gameId": "ABC123",
        "region": "USA", "discRevision": 1,
        "sha1": "89abcdef0123456789abcdef0123456789abcdef"
      },
      "status": "archived",
      "support": {"build": false, "reportFormats": []},
      "legacyTargets": []
    }
  ]
}
```

An archived target without a report is selectable as metadata only. It has no percentages,
map, timeline, invented baseline, or producer policy. Build support and report support must be
verified before activation. Each enabled producer policy must exactly match a catalog target.
The default target must have validated data; the hub shows its metrics, never a sum or average
across revisions.

## Packages and authentication

Use [report-v2](schema/report-v2.schema.json), [execution-v2](schema/execution-v2.schema.json)
and [producer-v2](schema/producer-v2.schema.json). Their `schemaVersion` is 2. Each package
contains exactly one target; module schemas retain their own versions (`map-v1` or `map-v2`,
`timeline-v1`, `contributors-v1`). All identity objects in manifest, receipt and policy must
agree exactly. Unknown fields remain errors. Counts, original-size function identities and
aggregation are unchanged; function identities use the explicit target ID.

Use a unique artifact name per target, such as `report-v2-ABC123-rev0`, and an exact job display
name such as `Validate ABC123-rev0`. Policies retain exact `requiredSteps` and `lanes` and add
`requiredJobs`: successful shared prerequisites such as `Plan affected targets` and `Tool tests`.
The target's build, complete-binary verification, measurements, packaging and artifact upload
belong to that target job. A successful sibling is never a substitute for it.

A completed main workflow may have conclusion `success` or `failure` for v2 import. The selected
target job, every required step, its single validation lane and every required shared job must
all succeed on the exact run attempt/head. Cancelled workflows are ineligible. PR runs remain
evidence only. Retained PR proof reuse still binds exact target, source tree and originating
artifact. Report-v1 imports continue to require whole-workflow success.

The scanner ignores newer runs that did not produce this target or whose target job failed.
It authenticates a selected package normally; an unapproved workflow, bad receipt or history
loss fails that target update and retains its last-good selection. Policy sync proposes changes
for one registered target at a time and never approves new identities automatically.

## Site registration and durable state

A [project-v2](schema/project-v2.schema.json) presentation keeps game-level title, repository,
artwork, contributions and enabled modules. Replace its single `target` string with
`"targetRegistry": "game-slug-targets.json"`. Module availability is intersected with each
target report's actual capabilities.

The producer registry entry is:

```json
{
  "game-slug": {
    "format": "report-v2",
    "catalog": "game-slug-targets.json",
    "targets": {
      "ABC123-rev0": {"format": "report-v2", "policy": "game-slug-ABC123-rev0-producer.json"}
    }
  }
}
```

Policy-sync configuration can use a matching `targets` map, each entry containing `policyPath`
and `mode`, or an explicit `disabled` reason. Catalog changes and new targets require manual
registration. Existing single-target producer and policy-sync entries need no change.

Lock version 2 stores multi-target entries under `projects.<slug>.targets.<targetId>`. Existing
single-target entries stay flat, including in a mixed v2 lock. New immutable snapshots live at
`data/<slug>/targets/<targetId>/snapshots/<commit>-v2-<run>-<attempt>-g<generation>-<methodHash>`.
Every target has independent last-good state, history and source-proof cache. Store publication
is append-only and cannot erase another target. History rows never move between targets by
address, name similarity or a shared Git revision.

The game URL is `/games/<slug>/?target=<targetId>`. Region/game ID and revision selectors change
all target content together and participate in browser history. Omitted `target` selects the
configured default. A URL with an unknown target must not display the default target's data.

## Target-scoped CI and repository layout

```text
config/targets.json                 # explicit supported/archived identities
config/ci-targets.json              # shared and target dependency patterns
config/<targetId>/                  # splits, symbols, evidence, checksum, producer policy
src/                               # shared source; do not duplicate entire source trees
orig/<targetId>/sys/main.dol         # ignored/private originals
build/<targetId>/                   # generated configuration, objects, measurements, package
```

Declare shared inputs and each target's inputs. Plan from an authenticated full Git diff,
including deletions and both sides of renames. Unknown inputs conservatively select all
buildable targets. Changes only to an archived target may run tool tests without a binary build.
Shared source/header/toolchain changes select every actual dependent target. Manual audit runs
can explicitly select all buildable targets. Never assume all shared files affect only a default.

Run a matrix with `fail-fast: false`. Each selected target builds fresh in its own runner and
has distinct outputs/artifacts. A stable aggregate validation check still fails the PR when any
required target fails; publication of a successful main target remains independent. Required-check
renames are coordinated with the repository owner, not silently bypassed. Target-local generated
Ninja/objdiff configurations permit local switching without overwriting another target's files.

Keep caches and proof reuse optional. If introduced, include target ID, original hash, target
configuration, dependent source, tools and measurement methodology in cache/proof identities.
A source tree hash alone never authorizes cross-target reuse.

## Rollout and optional adoption

New projects can start directly with this registry and report-v2, even with one active target.
Existing report-v1 projects remain valid without changes. See the optional
[adoption appendix](../wiki/existing-projects.md#explicit-target-adoption) for identity migration.
