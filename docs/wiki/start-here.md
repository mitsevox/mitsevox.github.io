# Start here

How to set up a decompilation repository that builds in a private environment, accepts reviewed contributions and publishes its progress to this site.

Every page of this wiki carries its text in its HTML for readers that do not run JavaScript, and the whole guide is one Markdown file at [`/wiki/downloads/handbook.md`](/wiki/downloads/handbook.md).

This guide is written for someone, or some agent, dropped into an empty repository with a game binary and no other context. Followed in order, it ends with a repository whose every push to `main` builds each target, verifies it byte for byte, measures it with objdiff and publishes the measurement to the progress site. The only things it cannot decide for you are your project's parameters: the platform, the compiler versions and tooling, the split configuration, the target ids and the presentation. Everything else is specified exactly, every command, file name, field and secret named here matches the shipped code, and a scaffold check in CI keeps the repository matching the guide afterwards.

## The three repositories

Each game is three repositories. Two are yours; the third is shared by every game on the site.

| Repository | Visibility | Holds |
| --- | --- | --- |
| `owner/game` | public | Source, headers, target configuration, tools and CI. The only place contributors work. |
| `owner/game-build` | private | The original executables and the toolchain, built into a container image on GitHub Container Registry. Also private. |
| [`mitsevox/decomp-data`](https://github.com/mitsevox/decomp-data) | public, shared | The published measurements of every game, served by GitHub Pages at `https://mitsevox.github.io/decomp-data/`. |

The site itself, [`mitsevox/mitsevox.github.io`](https://github.com/mitsevox/mitsevox.github.io), is a static page that reads the data repository at view time. It also hosts the publish action, the scaffold check, the starter kit, the scaffold spec, the repository settings standard and the data contract. Adding a game changes nothing in the site repository.

```text
owner/game (public)                        owner/game-build (private)
  push to main                               push to main
  validate.yml                               image.yml
    plan: which targets changed                docker build: /orig/<target>/..., toolchain
    tests: tool tests, scaffold check          push ghcr.io/owner/game-build:main, print digest
    Validate <target>, inside the image  <---  referenced by digest
      copy the original
      configure, build, check the executable hash
      objdiff report -> build/<target>/report.json
      publish action (main only) -----------> mitsevox/decomp-data (public)
                                                data/game/<target>/latest.json, history.json, map.json
                                                data/game/game.json, index.json
                                                deploy.yml -> GitHub Pages
                                                       ^
mitsevox.github.io/games/game/  reads  /decomp-data/ at view time
```

## Placeholders used throughout

| Placeholder | Stands for |
| --- | --- |
| `owner/game` | your public source repository |
| `owner/game-build` | your private build-image repository |
| `OWNER_LOGIN` | the owner's GitHub login |
| `game` | the game's slug on the site, `[a-z0-9][a-z0-9-]*` |
| `GAME01-rev0` | a target id, `[A-Za-z0-9._-]+`; `GAME01` is its label, `0` its revision |
| `VERSION_GAME01_REV0` | that target's preprocessor define, derived from the id |
| `ghcr.io/owner/game-build@sha256:...` | the build image, always referenced by digest |
| `DATA_APP_CLIENT_ID`, `DATA_APP_PRIVATE_KEY` | the repository variable and the `publish` environment secret that hold the publishing credential |

The examples are for a GameCube target built with decomp-toolkit and dtk-template, because that is what the reference repositories use. Another platform changes the toolchain, the original's path inside the image and the build commands; it changes nothing in the layout, the CI structure, publishing or the site.

## The setup path

1. [Repository layout](/wiki/repository-layout/): create the public repository with the tracked and ignored paths and the root allowlist.
2. [Targets](/wiki/targets/): write `config/targets.json`, `config/site.json` and `config/ci-targets.json`; scaffold `config/<id>/` with `tools/new_target.py`.
3. [Build environment](/wiki/build-environment/): create the private repository, build the image, make the package readable by the public repository, note the digest.
4. [Build, verify, measure](/wiki/build-verify-measure/): get a byte-identical relink locally and an objdiff `report.json`; learn how version differences are written and read.
5. [Evidence](/wiki/evidence/) and the [contribution workflow](/wiki/contribution-workflow/): adopt `AGENTS.md`, `CONTRIBUTING.md` and the PR template.
6. [CI](/wiki/ci/): install `validate.yml` with your image digest and build commands; the scaffold check runs in it.
7. [Publishing](/wiki/publishing/): create the GitHub App credential, add the variable and the `publish` environment with its secret, push to `main`.
8. [Repository settings](/wiki/repository-settings/): apply the settings standard to both repositories.
9. [The site](/wiki/site/): check the page, commit cover art to the data repository.

[Multiple targets](/wiki/multi-target/) is the procedure for a second original, once the first is published. [Data contract](/wiki/data-contract/) describes what the publish action writes; [Troubleshooting](/wiki/troubleshooting/) lists the failure messages; [Starter kit](/wiki/starter-kit/) is the download with every copyable file and the scaffold spec.

## What done looks like

- A push to `main` runs `Validate` with the jobs `Plan affected targets`, `Tool tests`, `Validate <target id>` for each affected active target and `Validate targets`.
- The `Tool tests` job's `Check the scaffold` step reports no warnings.
- The `Validate <target id>` job ends with `Publish to the site`, and the data repository gains a commit titled `game GAME01-rev0: <sha>, <n>% code linked`.
- The data repository's `Deploy` workflow runs, and `https://mitsevox.github.io/games/game/` shows the new measurement within a few minutes.
- A pull request runs the same build, checks that the report converts and skips the publish step; it cannot merge until `Validate targets` passes and the owner merges it.
- `python3 tools/repo_settings.py --repo owner/game --check` reports no drift.

## Glossary

| Term | Meaning |
| --- | --- |
| target | One original binary the project matches: a game id plus a disc revision, region or platform. Identified by a stable id. |
| active | A target that is built, verified and measured. `planned` and `archived` targets are listed on the page but never built. |
| define | `VERSION_<ID>`: the id upper-cased with `-` and `.` replaced by `_`. The preprocessor symbol under which a target's differences live. |
| group | A macro in `include/version.h` naming two or more targets that share a difference, such as a region. |
| original | The unmodified executable, kept in the private image and never in the public repository. |
| build image | The private container image with the originals and the toolchain, referenced by digest. |
| objdiff report | `report.json`, written by `objdiff-cli report generate`; the only measurement input the publish action reads. |
| linked | Bytes of units that compile from source into the byte-identical executable (`Matching` objects). |
| matched | Bytes that match exactly whether linked or not (exact functions in `NonMatching` units count). |
| fuzzy | Size-weighted similarity of every function and data section. |
| tier | A, B or C: what a PR touches decides which review records it needs. |
| review record | A PR comment that starts with `Revision:`, `Targets:` and an `Accuracy:` or `Hostile:` verdict. |
| scaffold check | The composite action in the site repository that compares a checkout with the kit and the spec, in warn mode. |
| publish action | `mitsevox/mitsevox.github.io/.github/actions/publish`, which converts the report into the contract files and pushes them. |
| data repository | `mitsevox/decomp-data`: one directory per game and target, served by Pages. |
| contract | The schema-1 file format (`contract/README.md`); `publish.py check` is its executable form. |

## Using this guide with an agent

Give the agent the [whole guide as one Markdown file](/wiki/downloads/handbook.md), the [starter archive](/wiki/downloads/repository-starter.zip) and the project parameters. The [starter kit](/wiki/starter-kit/#prompt-for-an-agent) has a prompt. An agent cannot obtain the original, create the private repository, install the GitHub App or set repository settings on its own; the guide marks those steps as the owner's.
