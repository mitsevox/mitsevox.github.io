# Targets

`config/targets.json`, `config/site.json` and `config/ci-targets.json`, field by field, and what adding a target takes.

A target is one original binary. A game with one disc revision has one target; a second revision, region or platform is a second entry, never a replacement.

**Lay out every project as multi-target from the first commit, even with one disc.** The target id always carries its revision (`GAME01-rev0`, never a bare `GAME01`), every per-target path is keyed by that id, and `targets.json` is a list with one entry. Adding a revision or region later is then a new folder and a new list entry; nothing is renamed or moved. A target id is permanent once published, because it names the target's directory in the data repository and the `?target=` value in its URLs. The three files below are the producer's only inputs to the site apart from the objdiff report. Copies with placeholders are in the [starter kit](/wiki/starter-kit/).

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
| `id` | The target's identity: directory names, `?target=`, the data directory, the define | `[A-Za-z0-9._-]+`, unique, never changed once published; no two ids may give the same define |
| `platform` | Lower-case platform name | `[a-z0-9]+`, for example `gamecube`, `wii`, `ps2` |
| `label` | Display: the game id on disc; the target picker groups by it | Non-empty string |
| `region` | Display | Non-empty string |
| `revision` | Display: the disc revision, unrelated to Git revisions; the picker groups by it under `label` | Non-empty string |
| `sha1` | SHA-1 of the original executable | 40 lower-case hex digits |
| `status` | `active`: built, verified, measured, published. `planned` or `archived`: listed on the page, never built | One of the three |

Two readers validate this file and both must accept it. `tools/targets.py` (starter) rejects any other field, requires exactly `schema`, `defaultTarget` and `targets` at the top level, and requires `defaultTarget` to be active. The publish action's `publish.py` reads the seven fields above, requires the default to be listed and writes the list verbatim into `game.json`. Run `python3 -m unittest discover -s tests -p 'test_*.py'` after every edit: `tests/test_targets.py` loads the file.

`tools/targets.py` is the one reader of this file in the repository: `configure.py` takes its version list from it, the CI planner derives each target's paths from it, and `python3 tools/targets.py check` confirms that the three places a hash lives agree per target (`targets.json`, `config/<id>/config.yml` and `config/<id>/build.sha1`) and that every target has its files. The `Tool tests` job runs it.

## What `active` requires

An active target has an entry here with the original's SHA-1; `config/<id>/` with the toolkit inputs (`config.yml`, `splits.txt`, `symbols.txt` for decomp-toolkit), `build.sha1`, `evidence.tsv` and `README.md`; `orig/<id>/.gitkeep`; the original in the private image at `/orig/<id>/<original path>`; and a byte-identical relink proven by CI. Progress is not a condition: a target at a true 0 percent, every unit `NonMatching`, is active. A `planned` or `archived` target needs `config/<id>/README.md` and `orig/<id>/.gitkeep` only.

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
  "contributors": false,
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
| `contributors` | `true` publishes who made each exact function exact and shows the rankings ([Publishing](/wiki/publishing/), "Credits") | Optional; defaults to `false` |
| `artwork` | `cover` is a file name relative to `data/<slug>/` in the data repository, `width` and `height` its pixel size | Optional; add it only after committing the cover ([The site](/wiki/site/)) |

The publish action copies this file into `game.json` on every publish, adding `repository` (from the CI run's `GITHUB_REPOSITORY`), `defaultTarget` and `targets`. Changing the presentation is therefore an edit to this file followed by a merge to `main`; the next publish of any active target rewrites `game.json`.

## config/ci-targets.json

```json
{
  "schemaVersion": 1,
  "shared": ["src/**", "include/**", "asm/**", "configure.py", "tools/**", ".github/workflows/validate.yml",
             "config/targets.json", "config/ci-targets.json", "config/site.json"],
  "nonBuild": ["*.md", "docs/**", "references/**", "tests/**",
               ".github/pull_request_template.md", ".gitignore", ".gitattributes"]
}
```

`tools/ci_targets.py` reads it in the `Plan affected targets` job and decides which active targets a push or pull request must build:

| A changed path that matches | Selects |
| --- | --- |
| a `shared` pattern | every active target |
| `config/<id>/**` or `orig/<id>/**` | that target, if active |
| a `nonBuild` pattern only | nothing |
| no pattern at all | every active target (unknown paths never skip validation) |

The per-target patterns are not written down: every target owns `config/<id>/**` and `orig/<id>/**`, and the planner derives them from `targets.json`, so adding a target never touches this file. Patterns are `fnmatch` globs matched against the repository-relative path; `*` and `**` both match across `/`. Rules: `schemaVersion` is `1`; the keys are exactly `schemaVersion`, `shared` and `nonBuild` (a `targets` key is a scaffold-check warning); no pattern may start with `/` or contain `..`. A manual run (`workflow_dispatch`), a push with no known base (first push, force push) and a changed path that cannot be diffed all select every active target.

A change that selects no target still runs the `Tool tests` job and passes the `Validate targets` check.

## Adding a target

1. Hash the executable and add a `planned` entry to `config/targets.json`. Commit the original to the private repository under `orig/<id>/`, add its `COPY` and checksum lines to the Dockerfile and the `image.yml` verification, push, and take the new digest ([Build environment](/wiki/build-environment/)). By hand; minutes.
2. `python3 tools/new_target.py <id>` writes `config/<id>/config.yml` with the original's path and hash from the registry, an empty `evidence.tsv` with its header row, a `README.md` stub and `orig/<id>/.gitkeep`. It refuses an id the registry does not list and never overwrites a file.
3. Run the toolkit's analysis on the new original for a first `symbols.txt` and `splits.txt`, build, and confirm that the relink is byte-identical with every unit `NonMatching`. Write `config/<id>/build.sha1`, set `status: active`, and point `validate.yml` at the new digest. Hand-driven; hours.
4. Push to `main`. The planner builds the new target because `config/<id>/` changed, and the first `main` run publishes it: `data/<slug>/<id>/` appears in the data repository.
5. Then widen the shared work: a function already decompiled for a sibling counts on the new target as soon as the new target's `splits.txt` names the same unit, `configure.py` says `Matching` or `MatchingFor` for it there, and its `symbols.txt` gives the function the same name. Nothing is copied between targets; each target's own objdiff report scores it. Seeding `symbols.txt` and `splits.txt` from the sibling is the real cost of a new revision; a symbol-porting tool belongs here once a second original has passed step 3.

Setting a published target to `archived` keeps its data directory and history in the data repository, but the site reads `latest.json` only for `active` targets, so the page lists it without a measurement. Removing a target from the list entirely removes it from `game.json` on the next publish; the data directory is deleted by hand, if at all.
