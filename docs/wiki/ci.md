# CI

`validate.yml`: plan the affected targets, run the tool tests and the scaffold check, build each target in the image, publish on `main`.

One workflow does everything. It runs on every push to `main`, every pull request and on manual dispatch. Pull requests get the full build and nothing else; pushes to `main` additionally publish. There is no cache, no artifact and no second workflow to keep in step: the starter `validate.yml.template` is the whole thing, the four parameters marked in it are the only edits, and one optional step is the only addition. The scaffold check compares the file's job and step names with the kit on every run.

## Jobs

```text
Plan affected targets ──┐
                        ├──> Validate <target id>  (one job per affected active target, in the image)
Tool tests ─────────────┘            │
                                     └──> Validate targets  (the aggregate check the ruleset requires)
```

### Plan affected targets

Checks out with `fetch-depth: 0` (the planner diffs two commits) and runs `python3 tools/ci_targets.py`. The planner reads the event: for a pull request it diffs the base SHA against the head, for a push it diffs `before` against the pushed commit, and for `workflow_dispatch`, a push without a usable `before` (first push, force push) or `--force-all` it selects every active target. It applies `config/ci-targets.json` ([Targets](/wiki/targets/)), with each target's `config/<id>/**` and `orig/<id>/**` derived from the registry, and writes two outputs:

- `matrix`: `{"include":[{"target":"GAME01-rev0"}, ...]}`
- `has_targets`: `true` or `false`

On a pull request the job's second step, `Check the declared tier`, runs `python3 tools/tier.py`: it reads the first `Tier A`, `Tier B` or `Tier C` in the PR body and fails when the diff needs more (`config/<id>/splits.txt` or `symbols.txt`, an `inferred` evidence row, or a `cflags`, `ldflags`, `asflags` or `mw_version` line in `configure.py` need A; other source or `configure.py` changes need B). Outside pull requests it passes. Editing the body does not re-run it; the next push does.

The third step, `Check the credits`, runs `python3 tools/credits.py`. It does nothing unless `config/site.json` sets `"contributors": true`; then it checks the PR body's `Credits:` line and every target's `credits.tsv` and confirms each login exists on GitHub ([Publishing](/wiki/publishing/), "Credits").

Nothing finer than selection is attempted. A build-graph planner cannot cover headers without compiler depfiles, so every `include/**` change selects everything anyway; a target job is about a minute and local builds are incremental through ninja.

### Tool tests

Runs on the plain runner, outside the image, on every event, in two steps:

```sh
# Run tool tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/targets.py check
python3 tools/versions.py check
python3 tools/evidence.py check
# Check the scaffold
uses: mitsevox/mitsevox.github.io/.github/actions/scaffold-check@main
```

The first step runs the project's tests (add yours under `tests/test_*.py`) and the three kit checks: the hashes agree per target, the version blocks use known tokens only, the evidence records are well formed. The second is the scaffold check, a composite action in the site repository. GitHub clones the whole site repository to run it, so the check compares the checkout against the starter kit and the scaffold spec at the action's own revision, and the kit, the spec and the check can never disagree. It prints one `::warning::` per finding and exits 0; `with: strict: true` makes it fail instead, which the owner flips once every repository has been clean for a month. With the default token it also reads the repository's description, topics, features, merge settings and the rules on `main` and warns where they differ from the [settings standard](/wiki/repository-settings/). Keep anything that needs the toolchain out of this job.

### Validate `<target id>`

One job per selected target, `fail-fast: false`, so one target's failure does not cancel another's build or publish. It runs inside the private image, named once at the top of the file. GitHub does not make the `env` context available to `container.image`, so the plan job passes the value on as its `image` output:

```yaml
env:
  BUILD_IMAGE: ghcr.io/owner/game-build@sha256:<digest>     # PARAMETER 1
...
  plan:
    outputs:
      image: ${{ env.BUILD_IMAGE }}
...
    permissions:
      contents: read
      packages: read
      pull-requests: read
    environment:
      name: ${{ github.ref == 'refs/heads/main' && (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && 'publish' || 'validate' }}
      deployment: false
    container:
      image: ${{ needs.plan.outputs.image }}
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    env:
      TARGET_ID: ${{ matrix.target }}
```

The job references a deployment environment: `publish` on a push or manual run of `main`, `validate` otherwise. `publish` holds the publishing key as an environment secret and its deployment branch policy allows `main` only, so a run of any other branch that names `publish` is refused by GitHub before its first step; `validate` holds nothing. `deployment: false` uses the environment's secrets without recording a deployment per run; that the branch policy still applies with it is proven per repository by the two refused probe runs of the move order ([Repository settings](/wiki/repository-settings/), [Publishing](/wiki/publishing/)).

| Step | What it does |
| --- | --- |
| `Require a repository contribution branch` | `test "$SOURCE_REPOSITORY" = "$GITHUB_REPOSITORY"`, where `SOURCE_REPOSITORY` is the PR head repository or, outside PRs, the repository itself. A fork's PR fails here, before the original is touched. |
| `actions/checkout` | `persist-credentials: false`; the default depth is enough because the publish step only needs `HEAD`. |
| `Provide target original` | `mkdir -p orig/$TARGET_ID/sys`, `cp /orig/$TARGET_ID/sys/main.dol orig/$TARGET_ID/sys/main.dol`. PARAMETER 2 is the path. The toolkit checks the hash against `config.yml` when it splits; a third check of the same bytes is not needed. |
| `Configure target` | `python3 configure.py --version "$TARGET_ID" --dtk /usr/local/bin/dtk --binutils /binutils --compilers /compilers`. PARAMETER 3. |
| `Build, verify complete executable and measure progress` (`id: measure`) | `ninja -f "build/$TARGET_ID/build.ninja" progress "build/$TARGET_ID/report.json"`, then writes the output `measured-at` as the current UTC time in `%Y-%m-%dT%H:%M:%SZ`. PARAMETER 3. The build fails unless the executable's hash matches. |
| `Check the report` | `uses: mitsevox/mitsevox.github.io/.github/actions/check-report@main` with `target` and `report`, on every event. It converts the report into the contract files with the same code as the publish step, into an empty tree, and checks them, without a credential and without credits. A report the site would refuse fails the pull request here, not the `main` publish. A repository that passes `code-sections` or `unit-prefix` to the publish step passes the same values here. |
| `Project checks`, optional | The one step a repository may add: its own checks that need the build or the toolchain, with a command of its choice. The template shows it commented out; keep the name. |
| `List measuring tools` (`id: tools`) | Runs `python3 tools/measuring_tools.py --verify` on every event. The tool reads `BUILD_IMAGE` from the environment and the tool versions the repository pins (the tags in `configure.py`, or the JSON pin files its `PINS` parameter names); `--verify` runs each command its `VERIFY` parameter names inside the image (`dtk --version` in the kit) and fails the job unless the pinned version appears in the output, so the provenance published on `main` names what measured the report, and a pull request that bumps the image digest without the pin, or the pin without the image, fails here. The lines are captured in the output `lines` with a random heredoc delimiter. |
| `Publish to the site`, `main` only | `uses: mitsevox/mitsevox.github.io/.github/actions/publish@main` with `target`, `report: build/<target>/report.json`, `tools`, `measured-at`, `app-client-id` and `app-private-key`. PARAMETER 4 names the repository variable and the `publish` environment's secret. |

The publish step and the job's environment use the same condition, `github.ref == 'refs/heads/main' && (github.event_name == 'push' || github.event_name == 'workflow_dispatch')`: a push and a manual run on `main` publish, and nothing else does, the events being named rather than excluded so that an event added later never publishes by accident. Secrets are not available to pull requests from forks anyway, but the fork guard runs first in every case.

### Validate targets

Runs always, after the others, and fails unless `plan` and `tests` succeeded and the target jobs either all succeeded (when `has_targets` was `true`) or were skipped (when it was `false`). Its name, `Validate targets`, is the single check the `main` ruleset requires; the per-target job names vary with the matrix and cannot be required one by one.

## Workflow-level settings

```yaml
permissions:
  contents: read
concurrency:
  group: validate-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

A new push to a PR cancels that PR's running validation; pushes to `main` queue instead, so every `main` commit is measured and published. The workflow holds no write permission anywhere; the publish action brings its own credential, read from the `publish` environment on `main` runs only. The image is never referenced by tag, and no bot bumps the digest: changing it is a reviewed, owner-decided edit to `BUILD_IMAGE`.

## Installing it

1. Copy `validate.yml.template` to `.github/workflows/validate.yml`.
2. Fill PARAMETER 1 with the digest from the image workflow ([Build environment](/wiki/build-environment/)).
3. Fill PARAMETERS 2 and 3 with the original's path and the configure and build commands that work locally ([Build, verify, measure](/wiki/build-verify-measure/)). The image's tool paths replace the local ones.
4. Fill PARAMETER 4 with the variable and environment secret names from [Publishing](/wiki/publishing/); the step is harmless until they exist, because it only runs on `main`. The owner creates both environments, `publish` and `validate`, before the first run.
5. Copy the `tools/` and `tests/` starter files and `config/ci-targets.json`.
6. Open a pull request with all of it and watch the four jobs. The first run of `Validate <target id>` proves the image pull (package access), the original (the toolkit's hash check), the toolchain (configure), the match (`build.sha1`) and, in `Check the report`, that the report converts into the site's contract. The `Check the scaffold` step lists what still differs from the kit.
7. Merge. The first `main` run publishes, provided the credential is in place.

## Builds without configure.py

A repository whose build is not dtk-template's (its own scripts, a Makefile) keeps the same workflow; only the parameter slots differ:

- **Entry point.** `build.py` or a `Makefile` at the root (the scaffold accepts either in place of `configure.py`).
- **PARAMETER 2.** The image still holds `/orig/<target id>/sys/main.dol`; the step copies it wherever the build reads it.
- **PARAMETER 3.** `Configure target` runs the build's setup (or `true` when there is none). `Build, verify complete executable and measure progress` runs one command that fails unless the complete executable is byte-identical, prints `build/<target id>/main.dol: OK` (the line every repository's build ends with) and writes an objdiff-shaped `build/<target id>/report.json` that `Check the report` accepts (locally: `publish.py publish --dry-run --no-credits`, [Publishing](/wiki/publishing/)): `measures` with `total_functions` and `matched_functions`, and units whose sections carry real names and `metadata.virtual_address`. The `code-sections` and `unit-prefix` the report needs go to both the report check and the publish step.
- **Measuring tools.** Set `PINS` in `tools/measuring_tools.py` to the JSON files that pin the tools (`{"<name>": {"version": ...}}`), and `VERIFY` to the command that prints each image-installed tool's version, so that `--verify` confirms every pin against the image.
- **Tools.** Every tool the build runs is baked into the build image, as in the kit's Dockerfile; the target job downloads nothing.
- **Tool tests.** The `Tool tests` job runs on the bare runner; a test that needs the toolchain skips there and runs in `Project checks` instead.
- **Build inputs.** `tests/**` is a `nonBuild` pattern in the kit because every test runs in `Tool tests`. A repository whose tests run in `Project checks` moves `tests/**` from `nonBuild` to `shared` in `config/ci-targets.json`, so that a test change rebuilds every target where that test runs ([Targets](/wiki/targets/)).

## What a pull request proves

A green `Validate targets` on a PR means: the tool tests pass, and for every target the change can affect, the complete executable built from the PR's source plus the original bytes for unlinked ranges is byte-identical to the original, objdiff produced a report, and that report converts into the site's contract. It does not mean the reconstruction is right; that is what the review tiers in [Contribution workflow](/wiki/contribution-workflow/) are for. Pull requests publish nothing, so a PR cannot change the site.
