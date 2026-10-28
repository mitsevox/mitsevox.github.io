# Starter kit

The downloadable files, their parameters, the acceptance checklist and an agent prompt.

Download the [repository starter archive](/wiki/downloads/repository-starter.zip). It unpacks to `repository-starter/` and contains every copyable file this guide refers to, the data contract, and nothing that pretends to be a build system. The same files are browsable in the site repository under [`docs/wiki/starter/`](https://github.com/mitsevox/mitsevox.github.io/tree/main/docs/wiki/starter).

## Contents

| File | Copy to | Chapter |
| --- | --- | --- |
| `README.md` | nowhere; it lists the parameters | this one |
| `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`, `.github/pull_request_template.md` | the repository root and `.github/` | [Contribution workflow](/wiki/contribution-workflow/) |
| `.github/workflows/validate.yml.template` | `.github/workflows/validate.yml` | [CI](/wiki/ci/) |
| `.github/workflows/review.yml.template` | `.github/workflows/review.yml` | [Review gate](/wiki/review-gate/) |
| `config/targets.json`, `config/site.json`, `config/ci-targets.json`, `config/README.md` | `config/` | [Targets](/wiki/targets/), [Evidence](/wiki/evidence/) |
| `tools/__init__.py`, `tools/targets.py`, `tools/ci_targets.py`, `tools/verify_target.py`, `tools/measuring_tools.py` | `tools/` | [Targets](/wiki/targets/), [CI](/wiki/ci/) |
| `tests/test_targets.py`, `tests/review_gate.mjs` | `tests/` | [CI](/wiki/ci/), [Review gate](/wiki/review-gate/) |
| `build-image/Dockerfile`, `build-image/.github/workflows/image.yml`, `build-image/README.md` | the root of the private repository | [Build environment](/wiki/build-environment/) |
| `contract/README.md` | reference only | [Data contract](/wiki/data-contract/) |

Not included, because they are the project's own: `README.md`, `configure.py` and the rest of dtk-template, `config/<target id>/`, `src/` and `include/`.

## Parameters

Every project-specific value, and where it goes:

| Parameter | Value | Files |
| --- | --- | --- |
| Public repository | `owner/game` | `CONTRIBUTING.md`, `tests/review_gate.mjs`, `build-image/README.md` |
| Owner login | `OWNER_LOGIN`; also the `REVIEW_OWNER` variable | `AGENTS.md`, `CONTRIBUTING.md`, `tests/review_gate.mjs` |
| Slug | `game` | `config/site.json` |
| Target ids | `GAME01-rev0`, `GAME01-rev1` | `config/targets.json`, `config/ci-targets.json`, `AGENTS.md`, `CONTRIBUTING.md`, `build-image/*` |
| Target display strings | `label`, `region`, `revision` | `config/targets.json` |
| Original SHA-1 | 40 lower-case hex digits | `config/targets.json`, `build-image/Dockerfile` |
| Presentation | `title`, `shortTitle`, `console`, `year`, `contributions`, `artwork` | `config/site.json` |
| Build image | `owner/game-build` and its digest | `validate.yml.template` PARAMETER 1, `build-image/README.md` |
| Original path | `sys/main.dol` | `validate.yml.template` PARAMETER 2, `tools/verify_target.py`, `build-image/*` |
| Configure and build commands | your toolchain's | `validate.yml.template` PARAMETER 3 |
| Credential names | `DATA_APP_CLIENT_ID`, `DATA_APP_PRIVATE_KEY` | `validate.yml.template` PARAMETER 4 |
| Reported tool versions | `dtk_tag`, `objdiff_tag` | `tools/measuring_tools.py` |
| Toolchain archives, toolkit tag and commit | | `build-image/Dockerfile`, `build-image/.github/workflows/image.yml` |

## Acceptance checklist

The repository is set up when each line is true and can be shown with a run, a commit or a URL.

- The public repository has the layout in [Repository layout](/wiki/repository-layout/); `git status` after a local build shows no original or generated file.
- `python3 -m unittest discover -s tests -p 'test_*.py'` and `node --test tests/review_gate.mjs` pass locally.
- `python3 tools/verify_target.py --target <id>` reports the SHA-1 verified, and `ninja -f build/<id>/build.ninja` produces the byte-identical executable.
- `ninja -f build/<id>/build.ninja progress build/<id>/report.json` writes a report that `publish.py publish --dry-run` converts and `publish.py check` accepts.
- The private repository's image workflow is green on `main`, the package is private, the public repository has Read access, and `validate.yml` names the digest.
- A pull request runs `Plan affected targets`, `Tool tests`, `Validate <id>` and `Validate targets`, all green, and shows `Owner review clearance` pending.
- `review.yml` is on `main`; a test clearance turns the status green; a new commit turns it pending. Branch protection requires both checks.
- The GitHub App is installed on the data repository; the producer holds the variable and the secret.
- The first `main` run's `Publish to the site` step printed `published <slug>/<id> <sha>`; the data repository has the commit; `https://mitsevox.github.io/games/<slug>/` shows it.
- Cover art is committed to the data repository and `artwork` is in `config/site.json`, or the owner has decided to go without.

## Prompt for an agent

```text
Set up a decompilation repository by following the guide in handbook.md exactly, using the files
in repository-starter/. The project parameters are: <platform>, <toolchain and versions>, <target
ids with labels, regions, revisions and SHA-1s>, <slug and presentation>, <owner login>,
<public repository>, <private build repository>. Do not invent any other value.

Work through the chapters in the order Start here gives. Copy each starter file to its destination
and fill only the marked parameters. Where the guide names a command, run it and report its output;
where a step needs the owner (creating the private repository, committing the original, installing
the GitHub App, setting repository variables, secrets, package access or branch protection), stop
and list exactly what the owner must do.

Finish with the acceptance checklist from the Starter kit chapter: for each line, the evidence
(command output, commit, run or URL) or the reason it is not yet true. Never substitute a
placeholder for a real value to make a check pass, never commit an original, and never change the
build image, the review workflow or branch protection on your own.
```
