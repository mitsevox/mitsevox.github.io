# Repository starter

Copyable files for a new decompilation repository that follows the guide at
<https://mitsevox.github.io/wiki/>. Every file is ready to use once its parameters are filled in; the
parameters are the only project-specific values and are listed below. Nothing here builds a game: the
toolchain, split configuration and source are the project's own. `scaffold.json` is the spec the
scaffold check enforces against a repository; it lists which of these files must stay byte-identical
to the kit, which are checked by outline, and which are free.

## Where each file goes

| In this kit | Copy to | Purpose |
| --- | --- | --- |
| `README.md.template` | `README.md` | The seven-heading project README |
| `AGENTS.md` | `AGENTS.md` | Agent instructions: a fixed header, then the project's own `## Project` section |
| `CLAUDE.md` | `CLAUDE.md` | A one-line import of `AGENTS.md` |
| `CONTRIBUTING.md` | `CONTRIBUTING.md` | Tiers, the task loop, matching integrity, the hostile checklist, the record format |
| `CREDITS.md` | `CREDITS.md` | Origin, revision and license of imported source and tooling |
| `.gitignore`, `.gitattributes` | same paths | Keeps originals, disc images and generated output out of Git; LF for toolkit files |
| `.github/pull_request_template.md` | same path | Scope with tier, the Targets table, evidence and review sections |
| `.github/workflows/validate.yml.template` | `.github/workflows/validate.yml` | Plan, tool tests and scaffold check, per-target build in the private image, publish on `main` |
| `config/targets.json` | same path | The target list (schema 1) |
| `config/site.json` | same path | The game's presentation on the site |
| `config/ci-targets.json` | same path | Which shared paths affect every target and which affect none |
| `config/README.md` | same path | The evidence record format |
| `include/version.h` | same path | The version-difference rule and the group macros |
| `tools/__init__.py`, `tools/targets.py`, `tools/ci_targets.py`, `tools/versions.py`, `tools/evidence.py`, `tools/new_target.py`, `tools/measuring_tools.py`, `tools/tier.py`, `tools/credits.py` | same paths | Target registry and define, CI planner, version views, evidence check, target scaffolding, tool provenance, the review-tier floor, the credits check |
| `tests/test_targets.py` | same path | The tests the `Tool tests` job runs |
| `build-image/Dockerfile`, `build-image/.github/workflows/image.yml`, `build-image/README.md` | the root of the **private** build repository | The build environment image that holds the originals |
| `scaffold.json` | nowhere | The scaffold spec, read by the scaffold check in the site repository |
| `contract/README.md` | reference only | The data contract the publish action writes |

The kit does not include `configure.py` or `config/<target id>/`: the build files come from your
toolchain (for GameCube and Wii, from dtk-template), and `python3 tools/new_target.py <id>` scaffolds
a target's directory once the registry lists it.

## Parameters

| Placeholder | Meaning | Where it appears |
| --- | --- | --- |
| `owner/game` | The public source repository | CONTRIBUTING.md, build-image/README.md |
| `OWNER_LOGIN` | The owner's GitHub login | CONTRIBUTING.md, README.md.template |
| `game` | The site slug, `[a-z0-9][a-z0-9-]*` | config/site.json, README.md.template |
| `GAME01-rev0`, `GAME01-rev1` | Target ids, `[A-Za-z0-9._-]+` | config/targets.json, .github/pull_request_template.md, README.md.template, build-image/* |
| `GAME01`, `USA`, `0` | A target's `label`, `region` and `revision` display strings | config/targets.json |
| `0000...0000` (40 hex digits) | A target's original SHA-1, lower case | config/targets.json, build-image/Dockerfile |
| `A Game: Full Title`, `A Game`, `GameCube`, `2002` | `title`, `shortTitle`, `console`, `year` | config/site.json, README.md.template |
| `owner/game-build` and its `@sha256:` digest | The private build image | validate.yml.template (PARAMETER 1), build-image/README.md |
| `sys/main.dol` | The original's path under `orig/<target id>/` and `/orig/<target id>/` | validate.yml.template (PARAMETER 2), build-image/*, config.yml |
| configure and build commands | PARAMETER 3 in validate.yml.template | validate.yml.template |
| `DATA_APP_CLIENT_ID`, `DATA_APP_PRIVATE_KEY` | The repository variable and the `publish` environment secret holding the GitHub App credential | validate.yml.template (PARAMETER 4) |
| `TAGS`, `PINS`, `VERIFY` | The `config.<name>` lines of configure.py (or the JSON pin files) reported as tool provenance, and the commands that confirm each image-installed tool's version against the pin | tools/measuring_tools.py |
| `## Project` | The repository's own agent rules | AGENTS.md |

`config/site.json` may also carry `"artwork": {"cover": "cover.webp", "width": 1112, "height": 1600}`
once the cover image has been committed to the data repository (see the Site chapter), and
`"contributions": {"accepting": true, "guideUrl": "https://github.com/owner/game/blob/main/CONTRIBUTING.md"}`
to show a Contribute link.

## Checking the kit locally

From the repository root, after copying the files and renaming the templates:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/targets.py check
python3 tools/versions.py check
python3 tools/evidence.py check
```

The scaffold check runs in CI (`Tool tests`, the `Check the scaffold` step). To run it locally, clone
the site repository and run `python3 <site>/.github/actions/scaffold-check/scaffold_check.py --repo .`.
