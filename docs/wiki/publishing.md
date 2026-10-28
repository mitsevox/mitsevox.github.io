# Publishing

The GitHub App credential, the publish action's inputs and what happens on a push to `main`.

Publishing is one step at the end of each `Validate <target id>` job on `main`. The step is the composite action [`mitsevox/mitsevox.github.io/.github/actions/publish`](https://github.com/mitsevox/mitsevox.github.io/tree/main/.github/actions/publish), referenced at `@main`. It converts the objdiff report into the contract files, validates them, and pushes them to the data repository with a short-lived token minted from a GitHub App. The producer holds the App's client id and private key; the site holds nothing.

## The credential

The credential is a GitHub App installed on the data repository only, with **Contents: read and write** as its only repository permission (plus the mandatory **Metadata: read**). It is not installed on the producer. The action mints a one-hour installation token scoped to the data repository at the start of the step; the token is revoked when the job ends.

For the owner's site the App already exists and is installed on `mitsevox/decomp-data`; a new game needs its client id and private key as a variable and a secret in the producer repository. For a new data repository, create the App once:

1. GitHub Settings, Developer settings, GitHub Apps, New GitHub App ([documentation](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)). Any name; no webhook; **Where can this GitHub App be installed?** Only on this account.
2. Repository permissions: **Contents: Read and write**. Leave every other permission at no access. Never add Actions or Workflows.
3. After creating it, note the **Client ID** on the App's page and generate a **private key** (a `.pem` file downloads).
4. Install the App on the account, choosing **Only select repositories** and selecting the data repository alone.

Then, in the producer repository (Settings, Secrets and variables, Actions):

| Kind | Name used in this guide | Value |
| --- | --- | --- |
| Variable | `DATA_APP_CLIENT_ID` | The App's client id |
| Secret | `DATA_APP_PRIVATE_KEY` | The full contents of the `.pem` file |

The names are yours; `validate.yml` passes them to the action as `app-client-id: ${{ vars.DATA_APP_CLIENT_ID }}` and `app-private-key: ${{ secrets.DATA_APP_PRIVATE_KEY }}` (PARAMETER 4). The reference repository uses the names `PORTFOLIO_APP_CLIENT_ID` and `PORTFOLIO_APP_PRIVATE_KEY`.

## The action's inputs

| Input | Required | Default | Meaning |
| --- | --- | --- | --- |
| `target` | yes | | Target id, as listed in `targets.json` |
| `report` | yes | | Path of objdiff's `report.json` for this target |
| `targets` | no | `config/targets.json` | The producer's targets file |
| `site` | no | `config/site.json` | The producer's presentation file |
| `tools` | no | empty | Measured-with tools, one `name=version` per line; shown on the page as provenance |
| `measured-at` | no | now | UTC time of the measurement, `%Y-%m-%dT%H:%M:%SZ` |
| `code-sections` | no | `.init,.text` | Comma-separated code section names; every other section counts as data |
| `unit-prefix` | no | `main/` | Prefix stripped from objdiff unit names for display |
| `data-repository` | no | `mitsevox/decomp-data` | `owner/name` of the data repository |
| `app-client-id` | yes | | Client id of the GitHub App installed on the data repository |
| `app-private-key` | yes | | Private key of that GitHub App |

The starter workflow passes `target`, `report`, `tools`, `measured-at`, `app-client-id` and `app-private-key` and leaves the rest at their defaults. The `tools` lines come from `tools/measuring_tools.py`: `build-environment=<image digest>`, then one line per tag it reads from `configure.py` (`dtk=v1.8.3`, `objdiff=v3.6.1` in the starter).

## What the action does

1. Splits `data-repository` into owner and name.
2. Mints the token with `actions/create-github-app-token` (pinned to its v3.3.0 commit), with `owner`, `repositories: <name>` and `permission-contents: write`.
3. Runs `python3 "$GITHUB_ACTION_PATH/publish.py" publish --target ... --report ... --targets ... --site ... --tools ... --measured-at ... --code-sections ... --unit-prefix ... --data-repository ...` with the token in the environment variable `DATA_TOKEN`. `publish.py` is standard-library Python and runs inside the build image, which is why the image needs `python3` and `git`.

`publish.py publish` then:

1. Reads the report, `targets.json` and `site.json`, and builds `game.json`, `latest.json` and `map.json` in memory. `repository` comes from `GITHUB_REPOSITORY`; the measured revision, its commit time and subject come from `git log -1` on the checkout; `source.url` and `source.runUrl` are built from `GITHUB_SERVER_URL`, `GITHUB_REPOSITORY` and `GITHUB_RUN_ID`.
2. Clones the data repository at depth 1 using the token (sent as an HTTP header through the environment, never on a command line) and configures the committer as `<slug> publisher <publisher@users.noreply.github.com>`.
3. Up to five times: resets to the newest tip of the default branch, writes the target's files, runs the full tree check, commits as `<slug> <target>: <7-char sha>, <n>% code linked` with the run URL as the body, and pushes. A lost race (another target or game pushed in between) is retried from the new tip; the write is idempotent, so a retry re-applies the same measurement.
4. Prints `published <slug>/<target> <sha>`, or `<slug>/<target> <sha> already published` when nothing changed.

Writing the target's files follows two rules that make re-runs and out-of-order runs safe: the first measurement of a revision wins (re-running the workflow for the same commit changes nothing), and `latest.json` and `map.json` only move forward by commit time (a slow run of an older commit never replaces a newer one). The history row for the revision is appended either way. The exact file formats are in [Data contract](/wiki/data-contract/).

Everything written is checked before the push by the same code as `publish.py check`, so a bad conversion fails the job instead of landing in the data repository. The target must be `active` in `targets.json`; publishing a `planned` target stops with `Target <id> is not an active target of <slug>`.

## Verifying a publish

1. In the `Validate <target id>` job log, the `Publish to the site` step prints `published game/GAME01-rev0 <sha>`.
2. The data repository has a new commit by `game publisher`; its `Deploy` workflow runs (about a minute).
3. `https://mitsevox.github.io/decomp-data/data/game/GAME01-rev0/latest.json` shows the new `source.revision`.
4. `https://mitsevox.github.io/games/game/` shows the new numbers. The page fetches the data with `cache: no-cache`, so a reload is enough.

## Running the conversion locally

The action's script runs anywhere with Python 3 and Git. From the producer checkout, after a local build:

```sh
git clone https://github.com/mitsevox/mitsevox.github.io site
python3 site/.github/actions/publish/publish.py publish --target GAME01-rev0 \
  --report build/GAME01-rev0/report.json --repository owner/game \
  --tools "$(python3 tools/measuring_tools.py)" --dry-run --output /tmp/tree
python3 site/.github/actions/publish/publish.py check /tmp/tree
```

`--dry-run` writes the files into `--output` (or a temporary directory) and pushes nothing; `check` validates a whole tree. `--repository` is required outside Actions because `GITHUB_REPOSITORY` is unset; `source.runUrl` is `null` locally. This is the fastest way to find out whether a report converts before the first `main` push, and the only way to inspect the generated files.

## Before the first push to main

- The App is installed on the data repository with Contents read and write.
- The producer has the variable and the secret, and `validate.yml` names them.
- `config/targets.json` and `config/site.json` validate (`python3 -m unittest discover -s tests -p 'test_*.py'` and a dry run).
- A pull request has passed `Validate targets`.

Then merge. The first publish creates `data/<slug>/` and adds the slug to `index.json`; no one edits the data repository for a new game except to add cover art ([The site](/wiki/site/)).
