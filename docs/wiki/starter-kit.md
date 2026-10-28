# Starter kit

The downloadable files, their parameters, the scaffold spec, the acceptance checklist and an agent prompt.

Download the [repository starter archive](/wiki/downloads/repository-starter.zip). It unpacks to `repository-starter/` and contains every copyable file this guide refers to, the scaffold spec, the data contract, and nothing that pretends to be a build system. The same files are browsable in the site repository under [`docs/wiki/starter/`](https://github.com/mitsevox/mitsevox.github.io/tree/main/docs/wiki/starter).

## Contents

| File | Copy to | Chapter |
| --- | --- | --- |
| `README.md` | nowhere; it lists the parameters | this one |
| `README.md.template` | `README.md` | [Contribution workflow](/wiki/contribution-workflow/) |
| `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `CREDITS.md`, `.gitignore`, `.gitattributes`, `.github/pull_request_template.md` | the repository root and `.github/` | [Contribution workflow](/wiki/contribution-workflow/), [Repository layout](/wiki/repository-layout/) |
| `.github/workflows/validate.yml.template` | `.github/workflows/validate.yml` | [CI](/wiki/ci/) |
| `config/targets.json`, `config/site.json`, `config/ci-targets.json`, `config/README.md` | `config/` | [Targets](/wiki/targets/), [Evidence](/wiki/evidence/) |
| `include/version.h` | `include/` | [Build, verify, measure](/wiki/build-verify-measure/) |
| `tools/__init__.py`, `tools/targets.py`, `tools/ci_targets.py`, `tools/versions.py`, `tools/evidence.py`, `tools/new_target.py`, `tools/matching_scope.py`, `tools/measuring_tools.py`, `tools/tier.py`, `tools/credits.py` | `tools/` | [Targets](/wiki/targets/), [Build, verify, measure](/wiki/build-verify-measure/), [CI](/wiki/ci/), [Contribution workflow](/wiki/contribution-workflow/), [Publishing](/wiki/publishing/) |
| `tests/test_targets.py` | `tests/` | [CI](/wiki/ci/) |
| `build-image/Dockerfile`, `build-image/.github/workflows/image.yml`, `build-image/README.md` | the root of the private repository | [Build environment](/wiki/build-environment/) |
| `scaffold.json` | nowhere; the scaffold check reads it | this one |
| `contract/README.md` | reference only | [Data contract](/wiki/data-contract/) |

Not included, because they are the project's own: `configure.py` and the rest of dtk-template, `config/<target id>/` (scaffolded by `tools/new_target.py`), `src/` and `include/` beyond `version.h`.

## Parameters

Every project-specific value, and where it goes:

| Parameter | Value | Files |
| --- | --- | --- |
| Public repository | `owner/game` | `CONTRIBUTING.md`, `build-image/README.md` |
| Owner login | `OWNER_LOGIN` | `CONTRIBUTING.md`, `README.md.template` |
| Slug | `game` | `config/site.json`, `README.md.template` |
| Target ids | `GAME01-rev0`, `GAME01-rev1` | `config/targets.json`, `.github/pull_request_template.md`, `README.md.template`, `build-image/*` |
| Target display strings | `label`, `region`, `revision` | `config/targets.json` |
| Original SHA-1 | 40 lower-case hex digits | `config/targets.json`, `build-image/Dockerfile` |
| Presentation | `title`, `shortTitle`, `console`, `year`, `contributions`, `contributors`, `artwork` | `config/site.json` |
| Build image | `owner/game-build` and its digest | `validate.yml.template` PARAMETER 1 (`BUILD_IMAGE`), `build-image/README.md` |
| Original path | `sys/main.dol` | `validate.yml.template` PARAMETER 2, `build-image/*`, `config/<id>/config.yml` |
| Configure and build commands | your toolchain's | `validate.yml.template` PARAMETER 3 |
| Project checks | optional step and its command | `validate.yml.template` |
| Credential names | `DATA_APP_CLIENT_ID` (repository variable), `DATA_APP_PRIVATE_KEY` (secret of the `publish` environment) | `validate.yml.template` PARAMETER 4 |
| Reported and verified tool versions | `TAGS` (the `configure.py` lines) or `PINS` (JSON pin files), and `VERIFY` (the command that prints each image-installed tool's version) | `tools/measuring_tools.py` |
| Project agent rules | the `## Project` section | `AGENTS.md` |
| Toolchain archives, toolkit tag and commit | | `build-image/Dockerfile`, `build-image/.github/workflows/image.yml` |

## The scaffold spec

`scaffold.json` says which of these files must stay byte-identical to the kit, which are checked by outline, and which are free, and the scaffold check in CI enforces it ([CI](/wiki/ci/)).

| Class | Files | Checked |
| --- | --- | --- |
| Byte-identical | `tools/targets.py`, `tools/ci_targets.py`, `tools/versions.py`, `tools/evidence.py`, `tools/new_target.py`, `tools/matching_scope.py`, `tools/tier.py`, `tools/credits.py`, `tests/test_targets.py`, `config/README.md` | Equal to the kit at the action's revision |
| Outline | `README.md` (the seven headings in order), `CONTRIBUTING.md` (the section headings), `AGENTS.md` (the kit header verbatim, then `## Project`), `.github/pull_request_template.md` (contains `## Targets`), `validate.yml` (job names, step names, the publish, report-check and scaffold-check actions, `BUILD_IMAGE` by digest, the target job's environment line) | Headings or the fixed part; the body is free |
| Free | Everything else | Nothing |

The other checks: every required path present, a build entry point present, the root allowlist, the per-target files for each status, the three hashes agreeing per target, every `MatchingFor` argument and `VERSION_` token known, `ci-targets.json` without a `targets` key, `evidence.tsv` well formed, no `docs/dtk/` or `config.example.yml`, no file in `references/` over 4 MB, `.gitignore` covering `orig/*/*`, `build/`, `*.dol` and `*.elf`, no second workflow, and the readable half of the [settings standard](/wiki/repository-settings/). There is no exception file: a process that needs one is a process the allowlist was wrong about, and project material goes under `docs/`, `tools/` or `references/`.

## Acceptance checklist

The repository is set up when each line is true and can be shown with a run, a commit or a URL.

- The public repository has the layout in [Repository layout](/wiki/repository-layout/); `git status` after a local build shows no original or generated file.
- `python3 -m unittest discover -s tests -p 'test_*.py'`, `python3 tools/targets.py check`, `python3 tools/versions.py check` and `python3 tools/evidence.py check` pass locally.
- `ninja -f build/<id>/build.ninja` produces the byte-identical executable for every active target.
- The measurement command of the README writes `build/<id>/report.json`, and `publish.py publish --dry-run --no-credits` converts it ([Publishing](/wiki/publishing/)).
- The private repository's image workflow is green on `main`, the package is private, the public repository has Read access, and `validate.yml` names the digest in `BUILD_IMAGE`.
- A pull request runs `Plan affected targets`, `Tool tests`, `Validate <id>` and `Validate targets`, all green, and the `Check the scaffold` step prints no warning.
- The `main` ruleset requires a pull request and `Validate targets`, and the `merges` ruleset restricts merging to the Repository admin role; `python3 tools/repo_settings.py --repo owner/game --check` reports no drift for either repository.
- The GitHub App is installed on the data repository; the producer holds the variable and the `publish` environment with the secret.
- The first `main` run's `Publish to the site` step printed `published <slug>/<id> <sha>`; the data repository has the commit; `https://mitsevox.github.io/games/<slug>/` shows it.
- Cover art is committed to the data repository and `artwork` is in `config/site.json`, or the owner has decided to go without.

## Prompt for an agent

```text
Set up a decompilation repository by following the guide in handbook.md exactly, using the files
in repository-starter/. The project parameters are: <platform>, <toolchain and versions>, <target
ids with labels, regions, revisions and SHA-1s>, <slug and presentation>, <owner login>,
<public repository>, <private build repository>. Do not invent any other value.

Work through the chapters in the order Start here gives. Copy each starter file to its destination
and fill only the marked parameters; put the project's own rules under the Project section of
AGENTS.md and nowhere else. Where the guide names a command, run it and report its output; where a
step needs the owner (creating the private repository, committing the original, installing the
GitHub App, setting repository variables, secrets, package access or repository settings), stop
and list exactly what the owner must do.

Finish with the acceptance checklist from the Starter kit chapter: for each line, the evidence
(command output, commit, run or URL) or the reason it is not yet true. Never substitute a
placeholder for a real value to make a check pass, never commit an original, and never change the
build image, the workflow skeleton or the repository settings on your own.
```
