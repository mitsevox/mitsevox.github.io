# Targets

`config/targets.json`, `config/site.json` and `config/ci-targets.json`, field by field.

A target is one original binary. A game with one disc revision has one target; a second revision, region or platform is a second entry, never a replacement. The three files below are the producer's only inputs to the site apart from the objdiff report. Copies with placeholders are in the [starter kit](/wiki/starter-kit/).

## config/targets.json

```json
{
  "schema": 1,
  "defaultTarget": "GAME01-rev0",
  "targets": [
    {"id": "GAME01-rev0", "platform": "gamecube", "label": "GAME01", "region": "USA", "revision": "0",
     "sha1": "0000000000000000000000000000000000000000", "status": "active"},
    {"id": "GAME01-rev1", "platform": "gamecube", "label": "GAME01", "region": "USA", "revision": "1",
     "sha1": "1111111111111111111111111111111111111111", "status": "planned"}
  ]
}
```

| Field | Meaning | Rule |
| --- | --- | --- |
| `schema` | Format version | Always `1` |
| `defaultTarget` | The target the game page and hub card show first | Must be listed, and must be `active` |
| `id` | The target's identity: directory names, `?target=`, the data directory | `[A-Za-z0-9._-]+`, unique, never changed once published |
| `platform` | Lower-case platform name | `[a-z0-9]+`, for example `gamecube`, `wii`, `ps2` |
| `label` | Display: the game id on disc; the target picker groups by it | Non-empty string |
| `region` | Display | Non-empty string |
| `revision` | Display: the disc revision, unrelated to Git revisions; the picker groups by it under `label` | Non-empty string |
| `sha1` | SHA-1 of the original executable | 40 lower-case hex digits |
| `status` | `active`: built, verified, measured, published. `planned` or `archived`: listed on the page, never built | One of the three |

Two readers validate this file and both must accept it. `tools/targets.py` (starter) rejects any other field, requires exactly `schema`, `defaultTarget` and `targets` at the top level, and requires `defaultTarget` to be active. The publish action's `publish.py` reads the seven fields above, requires the default to be listed and writes the list verbatim into `game.json`. Run `python3 -m unittest discover -s tests -p 'test_*.py'` after every edit: `tests/test_targets.py` loads the file.

Every active target needs a directory `config/<id>/`, an original in the build image at `/orig/<id>/<original path>`, and an entry in `config/ci-targets.json`. A `planned` or `archived` target needs only the `ci-targets.json` entry (the planner requires every listed target to be covered) and may have an empty `config/<id>/`.

To find the SHA-1 of an original:

```sh
sha1sum /path/to/main.dol        # Linux
shasum -a 1 /path/to/main.dol    # macOS
```

## config/site.json

```json
{
  "schema": 1,
  "slug": "game",
  "title": "A Game: Full Title",
  "shortTitle": "A Game",
  "console": "GameCube",
  "year": "2002",
  "contributions": {"accepting": false},
  "artwork": {"cover": "cover.webp", "width": 1112, "height": 1600}
}
```

| Field | Meaning | Rule |
| --- | --- | --- |
| `schema` | Format version | `1` |
| `slug` | The game's name everywhere on the site and in the data repository | `[a-z0-9][a-z0-9-]*`, required |
| `title` | Full title shown on the page | Required, non-empty |
| `shortTitle` | Shorter title for the hub card | Optional; defaults to `title` |
| `console` | Display name of the console; the hub filters by it and it picks the console icon | Required, non-empty |
| `year` | Release year, a string | Optional |
| `contributions` | `{"accepting": true, "guideUrl": "<url>"}` shows a Contribute link to that URL; `accepting: false` hides it | Optional; defaults to `{"accepting": false}` |
| `artwork` | `cover` is a file name relative to `data/<slug>/` in the data repository, `width` and `height` its pixel size | Optional; add it only after committing the cover ([The site](/wiki/site/)) |

The publish action copies this file into `game.json` on every publish, adding `repository` (from the CI run's `GITHUB_REPOSITORY`), `defaultTarget` and `targets`. Changing the presentation is therefore an edit to this file followed by a merge to `main`; the next publish of any active target rewrites `game.json`.

## config/ci-targets.json

```json
{
  "schemaVersion": 1,
  "shared": ["src/**", "include/**", "asm/**", "configure.py", "tools/**", ".github/workflows/validate.yml",
             "config/targets.json", "config/ci-targets.json", "config/site.json"],
  "targets": {
    "GAME01-rev0": ["config/GAME01-rev0/**", "orig/GAME01-rev0/**"],
    "GAME01-rev1": ["config/GAME01-rev1/**", "orig/GAME01-rev1/**"]
  },
  "nonBuild": ["*.md", "docs/**", "references/**", "tests/**", ".github/workflows/review.yml",
               ".github/pull_request_template.md", ".gitignore", ".gitattributes"]
}
```

`tools/ci_targets.py` reads it in the `Plan affected targets` job and decides which active targets a push or pull request must build:

| A changed path that matches | Selects |
| --- | --- |
| a `shared` pattern | every active target |
| a `targets.<id>` pattern | that target, if active |
| a `nonBuild` pattern only | nothing |
| no pattern at all | every active target (unknown paths never skip validation) |

Patterns are `fnmatch` globs matched against the repository-relative path; `*` and `**` both match across `/`. Rules: `schemaVersion` is `1`; the four keys are exactly `schemaVersion`, `shared`, `targets` and `nonBuild`; `targets` must name every target in `targets.json`, including planned and archived ones; no pattern may start with `/` or contain `..`. A manual run (`workflow_dispatch`), a push with no known base (first push, force push) and a changed path that cannot be diffed all select every active target.

A change that selects no target still runs the `Tool tests` job and passes the `Validate targets` check.

## Adding or changing a target

1. Commit the original to the private repository under `orig/<id>/`, add its `COPY` and checksum lines to the Dockerfile and the `image.yml` verification, push, and take the new digest ([Build environment](/wiki/build-environment/)).
2. Add the entry to `config/targets.json` (`status: active`), its patterns to `config/ci-targets.json` and its inputs to `config/<id>/`.
3. Point `validate.yml` at the new digest.
4. Push to `main`. The data directory `data/<slug>/<id>/` appears with the first publish.

Setting a published target to `archived` keeps its data directory and history in the data repository, but the site reads `latest.json` only for `active` targets, so the page lists it without a measurement. Removing a target from the list entirely removes it from `game.json` on the next publish; the data directory is deleted by hand, if at all.
