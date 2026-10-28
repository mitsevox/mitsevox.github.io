# Repository starter

Copyable files for a new decompilation repository that follows the guide at
<https://mitsevox.github.io/wiki/>. Every file is ready to use once its parameters are filled in; the
parameters are the only project-specific values and are listed below. Nothing here builds a game: the
toolchain, split configuration and source are the project's own.

## Where each file goes

| In this kit | Copy to | Purpose |
| --- | --- | --- |
| `AGENTS.md` | `AGENTS.md` | Agent instructions; points at CONTRIBUTING.md |
| `CONTRIBUTING.md` | `CONTRIBUTING.md` | Contribution, review and merge policy |
| `.gitignore` | `.gitignore` | Keeps originals, disc images and generated output out of Git |
| `.github/pull_request_template.md` | same path | Scope, evidence and review sections of every PR |
| `.github/workflows/validate.yml.template` | `.github/workflows/validate.yml` | Plan, tool tests, per-target build in the private image, publish on `main` |
| `.github/workflows/review.yml.template` | `.github/workflows/review.yml` | The `Owner review clearance` status check |
| `config/targets.json` | same path | The target list (schema 1) |
| `config/site.json` | same path | The game's presentation on the site |
| `config/ci-targets.json` | same path | Which changed paths affect which target |
| `config/README.md` | same path | The evidence record format |
| `tools/__init__.py`, `tools/targets.py`, `tools/ci_targets.py`, `tools/verify_target.py`, `tools/measuring_tools.py` | same paths | Target registry, CI planner, original verification and tool provenance |
| `tests/test_targets.py`, `tests/review_gate.mjs` | same paths | The tests the `Tool tests` job runs |
| `build-image/Dockerfile`, `build-image/.github/workflows/image.yml`, `build-image/README.md` | the root of the **private** build repository | The build environment image that holds the originals |
| `contract/README.md` | reference only | The data contract the publish action writes |

The kit does not include `README.md`, `configure.py` or `config/<target id>/`: the README describes
your target and commands, and the build files come from your toolchain (for GameCube and Wii, from
dtk-template).

## Parameters

| Placeholder | Meaning | Where it appears |
| --- | --- | --- |
| `owner/game` | The public source repository | CONTRIBUTING.md, tests/review_gate.mjs, build-image/README.md |
| `OWNER_LOGIN` | The owner's GitHub login, also the `REVIEW_OWNER` value | AGENTS.md, CONTRIBUTING.md, tests/review_gate.mjs |
| `game` | The site slug, `[a-z0-9][a-z0-9-]*` | config/site.json |
| `GAME01-rev0`, `GAME01-rev1` | Target ids, `[A-Za-z0-9._-]+` | config/targets.json, config/ci-targets.json, AGENTS.md, CONTRIBUTING.md, build-image/* |
| `GAME01`, `USA`, `0` | A target's `label`, `region` and `revision` display strings | config/targets.json |
| `0000...0000` (40 hex digits) | A target's original SHA-1, lower case | config/targets.json, build-image/Dockerfile |
| `A Game: Full Title`, `A Game`, `GameCube`, `2002` | `title`, `shortTitle`, `console`, `year` | config/site.json |
| `owner/game-build` and its `@sha256:` digest | The private build image | validate.yml.template (PARAMETER 1), build-image/README.md |
| `sys/main.dol` | The original's path under `orig/<target id>/` and `/orig/<target id>/` | validate.yml.template (PARAMETER 2), tools/verify_target.py, build-image/* |
| configure and build commands | PARAMETER 3 in validate.yml.template | validate.yml.template |
| `DATA_APP_CLIENT_ID`, `DATA_APP_PRIVATE_KEY` | The repository variable and secret holding the GitHub App credential | validate.yml.template (PARAMETER 4) |
| `dtk_tag`, `objdiff_tag` | The `config.<name>` lines of configure.py reported as tool provenance | tools/measuring_tools.py |

`config/site.json` may also carry `"artwork": {"cover": "cover.webp", "width": 1112, "height": 1600}`
once the cover image has been committed to the data repository (see the Site chapter), and
`"contributions": {"accepting": true, "guideUrl": "https://github.com/owner/game/blob/main/CONTRIBUTING.md"}`
to show a Contribute link.

## Checking the kit locally

From the repository root, after copying the files and renaming the workflow templates:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/review_gate.mjs
```
