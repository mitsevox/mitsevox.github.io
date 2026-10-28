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
    container:
      image: ${{ needs.plan.outputs.image }}
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    env:
      TARGET_ID: ${{ matrix.target }}
```

| Step | What it does |
| --- | --- |
| `Require a repository contribution branch` | `test "$SOURCE_REPOSITORY" = "$GITHUB_REPOSITORY"`, where `SOURCE_REPOSITORY` is the PR head repository or, outside PRs, the repository itself. A fork's PR fails here, before the original is touched. |
| `actions/checkout` | `persist-credentials: false`; the default depth is enough because the publish step only needs `HEAD`. |
| `Provide target original` | `mkdir -p orig/$TARGET_ID/sys`, `cp /orig/$TARGET_ID/sys/main.dol orig/$TARGET_ID/sys/main.dol`. PARAMETER 2 is the path. The toolkit checks the hash against `config.yml` when it splits; a third check of the same bytes is not needed. |
| `Configure target` | `python3 configure.py --version "$TARGET_ID" --dtk /usr/local/bin/dtk --binutils /binutils --compilers /compilers`. PARAMETER 3. |
| `Build, verify complete executable and measure progress` (`id: measure`) | `ninja -f "build/$TARGET_ID/build.ninja" progress "build/$TARGET_ID/report.json"`, then writes the output `measured-at` as the current UTC time in `%Y-%m-%dT%H:%M:%SZ`. PARAMETER 3. The build fails unless the executable's hash matches. |
| `Project checks`, optional | The one step a repository may add: its own checks that need the build or the toolchain, with a command of its choice. The template shows it commented out; keep the name. |
| `List measuring tools` (`id: tools`), `main` only | Runs `python3 tools/measuring_tools.py`, which reads `BUILD_IMAGE` from the environment and the tool tags from `configure.py`, and captures its lines in the output `lines` with a random heredoc delimiter. |
| `Publish to the site`, `main` only | `uses: mitsevox/mitsevox.github.io/.github/actions/publish@main` with `target`, `report: build/<target>/report.json`, `tools`, `measured-at`, `app-client-id` and `app-private-key`. PARAMETER 4 names the variable and secret. |

The two `main`-only steps use the condition `github.ref == 'refs/heads/main' && github.event_name != 'pull_request'`, so a push and a manual run on `main` both publish, and nothing else does. Secrets are not available to pull requests from forks anyway, but the fork guard runs first in every case.

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

A new push to a PR cancels that PR's running validation; pushes to `main` queue instead, so every `main` commit is measured and published. The workflow holds no write permission anywhere; the publish action brings its own credential. The image is never referenced by tag, and no bot bumps the digest: changing it is a reviewed, owner-decided edit to `BUILD_IMAGE`.

## Installing it

1. Copy `validate.yml.template` to `.github/workflows/validate.yml`.
2. Fill PARAMETER 1 with the digest from the image workflow ([Build environment](/wiki/build-environment/)).
3. Fill PARAMETERS 2 and 3 with the original's path and the configure and build commands that work locally ([Build, verify, measure](/wiki/build-verify-measure/)). The image's tool paths replace the local ones.
4. Fill PARAMETER 4 with the variable and secret names from [Publishing](/wiki/publishing/); the step is harmless until they exist, because it only runs on `main`.
5. Copy the `tools/` and `tests/` starter files and `config/ci-targets.json`.
6. Open a pull request with all of it and watch the four jobs. The first run of `Validate <target id>` proves the image pull (package access), the original (the toolkit's hash check), the toolchain (configure) and the match (`build.sha1`). The `Check the scaffold` step lists what still differs from the kit.
7. Merge. The first `main` run publishes, provided the credential is in place.

## What a pull request proves

A green `Validate targets` on a PR means: the tool tests pass, and for every target the change can affect, the complete executable built from the PR's source plus the original bytes for unlinked ranges is byte-identical to the original, and objdiff produced a report. It does not mean the reconstruction is right; that is what the review tiers in [Contribution workflow](/wiki/contribution-workflow/) are for. Pull requests publish nothing, so a PR cannot change the site.
