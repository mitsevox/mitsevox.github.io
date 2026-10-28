# CI

`validate.yml`: plan the affected targets, run the tool tests, build each target in the image, publish on `main`.

One workflow does everything. It runs on every push to `main`, every pull request and on manual dispatch. Pull requests get the full build and nothing else; pushes to `main` additionally publish. There is no cache, no artifact and no second workflow to keep in step: the starter `validate.yml.template` is the whole thing, and the four parameters marked in it are the only edits.

## Jobs

```text
Plan affected targets ──┐
                        ├──> Validate <target id>  (one job per affected active target, in the image)
Tool tests ─────────────┘            │
                                     └──> Validate targets  (the aggregate check branch protection requires)
```

### Plan affected targets

Checks out with `fetch-depth: 0` (the planner diffs two commits) and runs `python3 tools/ci_targets.py`. The planner reads the event: for a pull request it diffs the base SHA against the head, for a push it diffs `before` against the pushed commit, and for `workflow_dispatch`, a push without a usable `before` (first push, force push) or `--force-all` it selects every active target. It applies `config/ci-targets.json` ([Targets](/wiki/targets/)) and writes two outputs:

- `matrix`: `{"include":[{"target":"GAME01-rev0"}, ...]}`
- `has_targets`: `true` or `false`

### Tool tests

Runs on the plain runner, outside the image, on every event:

```sh
node --test tests/review_gate.mjs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Add the project's own tests under `tests/test_*.py`; they run here. Keep anything that needs the toolchain out of this job.

### Validate `<target id>`

One job per selected target, `fail-fast: false`, so one target's failure does not cancel another's build or publish. It runs inside the private image:

```yaml
    permissions:
      contents: read
      packages: read
    container:
      image: ghcr.io/owner/game-build@sha256:<digest>     # PARAMETER 1
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
| `Provide and verify target original` | `mkdir -p orig/$TARGET_ID/sys`, `cp /orig/$TARGET_ID/sys/main.dol orig/$TARGET_ID/sys/main.dol`, `python3 tools/verify_target.py --target "$TARGET_ID"`. PARAMETER 2 is the path. |
| `Configure target` | `python3 configure.py --version "$TARGET_ID" --dtk /usr/local/bin/dtk --binutils /binutils --compilers /compilers`. PARAMETER 3. |
| `Build, verify complete executable and measure progress` (`id: measure`) | `ninja -f "build/$TARGET_ID/build.ninja" progress "build/$TARGET_ID/report.json"`, then writes the output `measured-at` as the current UTC time in `%Y-%m-%dT%H:%M:%SZ`. PARAMETER 3. The build fails unless the executable's hash matches. |
| `List measuring tools` (`id: tools`), `main` only | Runs `python3 tools/measuring_tools.py` and captures its lines in the output `lines` with a random heredoc delimiter. |
| `Publish to the site`, `main` only | `uses: mitsevox/mitsevox.github.io/.github/actions/publish@main` with `target`, `report: build/<target>/report.json`, `tools`, `measured-at`, `app-client-id` and `app-private-key`. PARAMETER 4 names the variable and secret. |

The two `main`-only steps use the condition `github.ref == 'refs/heads/main' && github.event_name != 'pull_request'`, so a push and a manual run on `main` both publish, and nothing else does. Secrets are not available to pull requests from forks anyway, but the fork guard runs first in every case.

### Validate targets

Runs always, after the others, and fails unless `plan` and `tests` succeeded and the target jobs either all succeeded (when `has_targets` was `true`) or were skipped (when it was `false`). Its name, `Validate targets`, is the single check to require in branch protection; the per-target job names vary with the matrix and cannot be required one by one.

## Workflow-level settings

```yaml
permissions:
  contents: read
concurrency:
  group: validate-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

A new push to a PR cancels that PR's running validation; pushes to `main` queue instead, so every `main` commit is measured and published. The workflow holds no write permission anywhere; the publish action brings its own credential.

## Installing it

1. Copy `validate.yml.template` to `.github/workflows/validate.yml`.
2. Fill PARAMETER 1 with the digest from the image workflow ([Build environment](/wiki/build-environment/)).
3. Fill PARAMETERS 2 and 3 with the original's path and the configure and build commands that work locally ([Build, verify, measure](/wiki/build-verify-measure/)). The image's tool paths replace the local ones.
4. Fill PARAMETER 4 with the variable and secret names from [Publishing](/wiki/publishing/); the step is harmless until they exist, because it only runs on `main`.
5. Copy the `tools/` and `tests/` starter files and `config/ci-targets.json`.
6. Open a pull request with all of it and watch the four jobs. The first run of `Validate <target id>` proves the image pull (package access), the original (SHA-1), the toolchain (configure) and the match (`build.sha1`).
7. Merge. The first `main` run publishes, provided the credential is in place.

## What a pull request proves

A green `Validate targets` on a PR means: the tool tests pass, and for every target the change can affect, the complete executable built from the PR's source plus the original bytes for unlinked ranges is byte-identical to the original, and objdiff produced a report. It does not mean the reconstruction is right; that is what the [review gate](/wiki/review-gate/) is for. Pull requests publish nothing, so a PR cannot change the site.
