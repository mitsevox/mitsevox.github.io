# Start here

How to set up a decompilation repository that builds in a private environment, accepts reviewed contributions and publishes its progress to this site.

This guide is written for someone, or some agent, dropped into an empty repository with a game binary and no other context. Followed in order, it ends with a repository whose every push to `main` builds the target, verifies it byte for byte, measures it with objdiff and publishes the measurement to the progress site. The only things it cannot decide for you are your project's parameters: the platform, the compiler versions and tooling, the split configuration, the target ids and the presentation. Everything else is specified exactly, and every command, file name, field and secret named here matches the shipped code.

## The three repositories

Each game is three repositories. Two are yours; the third is shared by every game on the site.

| Repository | Visibility | Holds |
| --- | --- | --- |
| `owner/game` | public | Source, headers, target configuration, tools and CI. The only place contributors work. |
| `owner/game-build` | private | The original executables and the toolchain, built into a container image on GitHub Container Registry. Also private. |
| [`mitsevox/decomp-data`](https://github.com/mitsevox/decomp-data) | public, shared | The published measurements of every game, served by GitHub Pages at `https://mitsevox.github.io/decomp-data/`. |

The site itself, [`mitsevox/mitsevox.github.io`](https://github.com/mitsevox/mitsevox.github.io), is a static page that reads the data repository at view time. It also hosts the publish action and the data contract that the producer uses. Adding a game changes nothing in the site repository.

```text
owner/game (public)                        owner/game-build (private)
  push to main                               push to main
  validate.yml                               image.yml
    plan: which targets changed                docker build: /orig/<target>/..., toolchain
    tests: tool tests                          push ghcr.io/owner/game-build:main, print digest
    Validate <target>, inside the image  <---  referenced by digest
      copy and verify the original
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
| `ghcr.io/owner/game-build@sha256:...` | the build image, always referenced by digest |
| `DATA_APP_CLIENT_ID`, `DATA_APP_PRIVATE_KEY` | the repository variable and secret that hold the publishing credential (names are yours to choose) |

The examples are for a GameCube target built with decomp-toolkit and dtk-template, because that is what the reference repositories use. Another platform changes the toolchain, the original's path inside the image and the build commands; it changes nothing in CI structure, publishing or the site.

## The setup path

1. [Repository layout](/wiki/repository-layout/): create the public repository with the tracked and ignored paths.
2. [Targets](/wiki/targets/): write `config/targets.json`, `config/site.json` and `config/ci-targets.json`.
3. [Build environment](/wiki/build-environment/): create the private repository, build the image, make the package readable by the public repository, note the digest.
4. [Build, verify, measure](/wiki/build-verify-measure/): get a byte-identical relink locally and an objdiff `report.json`.
5. [Evidence](/wiki/evidence/) and the [contribution workflow](/wiki/contribution-workflow/): adopt `AGENTS.md`, `CONTRIBUTING.md` and the PR template.
6. [Review gate](/wiki/review-gate/): install `review.yml`, set `REVIEW_OWNER`, make the status required.
7. [CI](/wiki/ci/): install `validate.yml` with your image digest and build commands.
8. [Publishing](/wiki/publishing/): create the GitHub App credential, add the variable and secret, push to `main`.
9. [The site](/wiki/site/): check the page, commit cover art to the data repository.

[Data contract](/wiki/data-contract/) describes what the publish action writes; [Troubleshooting](/wiki/troubleshooting/) lists the failure messages; [Starter kit](/wiki/starter-kit/) is the download with every copyable file.

## What done looks like

- A push to `main` runs `Validate` with the jobs `Plan affected targets`, `Tool tests`, `Validate <target id>` for each affected active target and `Validate targets`.
- The `Validate <target id>` job ends with `Publish to the site`, and the data repository gains a commit titled `game GAME01-rev0: <sha>, <n>% code linked`.
- The data repository's `Deploy` workflow runs, and `https://mitsevox.github.io/games/game/` shows the new measurement within a few minutes.
- A pull request runs the same build without the publish step, and cannot merge until `Validate targets` and `Owner review clearance` pass.

## Glossary

| Term | Meaning |
| --- | --- |
| target | One original binary the project matches: a game id plus a disc revision, region or platform. Identified by a stable id. |
| active | A target that is built, verified and measured. `planned` and `archived` targets are listed on the page but never built. |
| original | The unmodified executable, kept in the private image and never in the public repository. |
| build image | The private container image with the originals and the toolchain, referenced by digest. |
| objdiff report | `report.json`, written by `objdiff-cli report generate`; the only measurement input the publish action reads. |
| linked | Bytes of units that compile from source into the byte-identical executable (`Matching` objects). |
| matched | Bytes that match exactly whether linked or not (exact functions in `NonMatching` units count). |
| fuzzy | Size-weighted similarity of every function and data section. |
| publish action | `mitsevox/mitsevox.github.io/.github/actions/publish`, which converts the report into the contract files and pushes them. |
| data repository | `mitsevox/decomp-data`: one directory per game and target, served by Pages. |
| contract | The schema-1 file format (`contract/README.md`); `publish.py check` is its executable form. |
| review record | A PR comment that starts with `Revision:` and an `Accuracy:` or `Hostile:` verdict. |
| owner clearance | The owner's comment that names the head revision and two passing review records. |
| `REVIEW_OWNER` | The login whose clearance comments the review gate trusts. |
| merge gate | Optional: an agent acting under the owner's account to which the owner delegates clearance and merging. |

## Using this guide with an agent

Give the agent the [whole guide as one Markdown file](/wiki/downloads/handbook.md), the [starter archive](/wiki/downloads/repository-starter.zip) and the project parameters. The [starter kit](/wiki/starter-kit/#prompt-for-an-agent) has a prompt. An agent cannot obtain the original, create the private repository, install the GitHub App or set repository settings on its own; the guide marks those steps as the owner's.
