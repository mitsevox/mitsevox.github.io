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

Then, in the producer repository:

| Kind | Where | Name used in this guide | Value |
| --- | --- | --- | --- |
| Repository variable | Settings, Secrets and variables, Actions, Variables | `DATA_APP_CLIENT_ID` | The App's client id |
| Environment secret | Settings, Environments, `publish`, Environment secrets | `DATA_APP_PRIVATE_KEY` | The full contents of the `.pem` file |

The names are yours; `validate.yml` passes them to the action as `app-client-id: ${{ vars.DATA_APP_CLIENT_ID }}` and `app-private-key: ${{ secrets.DATA_APP_PRIVATE_KEY }}` (PARAMETER 4).

The private key is an environment secret and never a repository secret, because a repository secret is readable by a workflow run of any branch of the repository, and contributors push branches. The `publish` environment's deployment branch policy allows `main` only. The target job references `publish` on a push or manual run of `main` and the empty environment `validate` on every other run, so a run of any other branch, including one that edits `validate.yml` to name `publish`, is refused by GitHub before its first step ([CI](/wiki/ci/)). The owner creates the environments once:

1. Settings, Environments, New environment, name `publish`, Configure environment.
2. Deployment branches and tags: choose "Selected branches and tags", Add deployment branch or tag rule, ref type Branch, name pattern `main`, Add rule. No tag rule: a tag rule would let any contributor's tag push reach the key.
3. Environment secrets, Add environment secret: name `DATA_APP_PRIVATE_KEY`, value the `.pem` contents.
4. Leave required reviewers and the wait timer off.
5. New environment, name `validate`, Configure environment, change nothing: every branch, no secrets.

Both environments are created by hand (or by `python3 tools/repo_settings.py --apply`), never left to appear on their own: GitHub documents that a referenced environment is created on the fly, but does not say whether this happens for a job with `deployment: false`. The settings standard checks both ([Repository settings](/wiki/repository-settings/)).

A repository secret and an environment secret may share a name. A job that references an environment reads the environment's secret when the environment has one of that name, and otherwise falls back to the repository secret. So the key must not exist as a repository secret at all once the environment holds it, and the move from one to the other follows the order in [Repository settings](/wiki/repository-settings/), which deletes the repository secret before trusting a `published` line and then proves the branch policy with two refused runs.

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
| `credits` | no | `config/<target>/credits.tsv` when it exists | Credit overrides; read only when contributors are on |
| `github-token` | no | the workflow token | Reads the merged PR and the credited people when contributors are on; the target job grants `pull-requests: read` |
| `data-repository` | no | `mitsevox/decomp-data` | `owner/name` of the data repository |
| `app-client-id` | yes | | Client id of the GitHub App installed on the data repository |
| `app-private-key` | yes | | Private key of that GitHub App |

The starter workflow passes `target`, `report`, `tools`, `measured-at`, `app-client-id` and `app-private-key` and leaves the rest at their defaults. The `tools` lines come from `tools/measuring_tools.py --verify`: `build-environment=<image digest>`, then one line per tag it reads from `configure.py` (`dtk=v1.8.3`, `objdiff=v3.6.1` in the starter) or per entry of its pin files; the versions are the repository's pins, and `--verify` has just confirmed each tool its `VERIFY` parameter names against the image ([CI](/wiki/ci/)).

## What the action does

1. Splits `data-repository` into owner and name.
2. Mints the token with `actions/create-github-app-token` (pinned to its v3.3.0 commit), with `owner`, `repositories: <name>` and `permission-contents: write`.
3. Runs `python3 "$GITHUB_ACTION_PATH/publish.py" publish --target ... --report ... --targets ... --site ... --tools ... --measured-at ... --code-sections ... --unit-prefix ... --data-repository ...` with the token in the environment variable `DATA_TOKEN`. `publish.py` is standard-library Python and runs inside the build image, which is why the image needs `python3` and `git`.

`publish.py publish` then:

1. Reads the report, `targets.json` and `site.json`, and builds `game.json`, `latest.json` and `map.json` in memory. `repository` comes from `GITHUB_REPOSITORY`; the measured revision, its commit time and subject come from `git log -1` on the checkout; `source.url` and `source.runUrl` are built from `GITHUB_SERVER_URL`, `GITHUB_REPOSITORY` and `GITHUB_RUN_ID`.
2. Clones the data repository at depth 1 using the token (sent as an HTTP header through the environment, never on a command line) and configures the committer as `<slug> publisher <publisher@users.noreply.github.com>`.
3. Up to five times: resets to the newest tip of the default branch, writes the target's files, runs the full tree check, commits as `<slug> <target>: <7-char sha>, <n>% code linked` with the run URL as the body, and pushes. A lost race (another target or game pushed in between) is retried from the new tip; the write is idempotent, so a retry re-applies the same measurement.
4. Prints `published <slug>/<target> <sha>`, or `<slug>/<target> <sha> already published` when nothing changed.

Writing the target's files follows two rules that make re-runs and out-of-order runs safe: the first measurement of a revision wins (re-running the workflow for the same commit changes nothing), and `latest.json` and `map.json` only move forward by commit time (a slow run of an older commit never replaces a newer one). The history row for the revision is appended either way, and `latest.json`'s `digests` follow the files on every write. The exact file formats are in [Data contract](/wiki/data-contract/).

Because the action runs at `@main` in every producer, a change to it is live for every producer's next `main` run the moment it merges. A change that spans the site, the data repository and a producer merges in that order: the site first (the action and the checker), then the data repository (a correction or a migration of the data), then the producer; the site's CI checks the live data with the new checker before the site change merges ([Data contract](/wiki/data-contract/)).

## Correcting published data

A publish never rewrites a published revision: re-running the workflow for the same commit keeps what was published, and a new commit publishes a new measurement beside it. A published file that is wrong is corrected in the data repository, by hand, and nowhere else:

1. Clone the data repository and make the smallest edit that makes the file right (the two data-fuzzy values of one unit in `map.json`, say). Never change a measurement in `history.json` unless that row itself was wrong, and never remove a row.
2. From the site repository's checkout, `python3 .github/actions/publish/publish.py reseal <clone>`: it rewrites `digests` in each `latest.json` whose files changed and prints them, then runs the whole tree check. Without the reseal, `publish.py check` and the site's live-data check refuse the tree (`map.json: digest differs from latest.json`).
3. Open a pull request against the data repository that states the reason, merge it; the `Deploy` workflow publishes it.

The page fetches `map.json`, `history.json` and `contributors.json` by their digest, so the corrected file has a new URL and no browser shows the old copy; `latest.json` itself is always revalidated. The measurement's revision and time stay what they were: a correction changes a file, not the measurement's identity. (The page also refetches a cached map once past the cache when it fails validation, but a correction must not depend on that.)

## Credits

Credits are optional per repository: `"contributors": true` in `config/site.json` switches them on, and nothing changes while it is `false` or absent. With them on, each `main` build also writes `contributors.json`:

1. **Who.** The PR whose merge made the measured revision (`GET /repos/<repo>/commits/<sha>/pulls`). Its body's `Credits: @login, @login` line names the people; without the line its author is credited. Work an agent did under the owner's login is the owner's merge and is credited to the owner. A revision that no PR merged credits nobody and fails the publish.
2. **What.** A function is credited to the people of the earliest measured `main` build in which it was exact. Newly exact functions take this build's people; functions already credited keep theirs; a function that is no longer exact moves to `retired` with its credit, and gets that credit back when it returns. An older commit whose run finishes late moves a credit earlier when it was exact first, and adds or retires nothing, because `latest.json` decides what is exact now.
3. **Switching on.** The first build with credits on credits every function already exact to the repository owner.
4. **Overrides.** `config/<target>/credits.tsv` (address, comma-separated logins, reason; `#` comments allowed) credits the listed functions to those people whatever the merges say: for batches that carry other people's work, imports and corrections. It is reviewed like any other record.

The pull request side runs before merge: the plan job's `Check the credits` step (`tools/credits.py`) does nothing while credits are off, and otherwise checks the `Credits:` line and every `credits.tsv` and confirms that each login exists, so a bad credit fails the PR and never the publish on `main`.

Everything written is checked before the push by the same code as `publish.py check`, so a bad conversion fails the job instead of landing in the data repository. The target must be `active` in `targets.json`; publishing a `planned` target stops with `Target <id> is not an active target of <slug>`.

## Verifying a publish

1. In the `Validate <target id>` job log, the `Publish to the site` step prints `published game/GAME01-rev0 <sha>`.
2. The data repository has a new commit by `game publisher`; its `Deploy` workflow runs (about a minute).
3. `https://mitsevox.github.io/decomp-data/data/game/GAME01-rev0/latest.json` shows the new `source.revision`.
4. `https://mitsevox.github.io/games/game/` shows the new numbers. The page revalidates `latest.json` on every view and fetches the other files by digest, so a reload is enough.

## Running the conversion locally

The action's script runs anywhere with Python 3 and Git. From the producer checkout, after a local build:

```sh
git clone https://github.com/mitsevox/mitsevox.github.io site
python3 site/.github/actions/publish/publish.py publish --target GAME01-rev0 \
  --report build/GAME01-rev0/report.json --repository owner/game \
  --tools "$(python3 tools/measuring_tools.py)" --dry-run --no-credits --output /tmp/tree
python3 site/.github/actions/publish/publish.py check /tmp/tree
```

`--dry-run` writes the files into `--output` (or a temporary directory) and pushes nothing; `--no-credits` leaves the credits out, which otherwise need the merged pull request on GitHub; `check` validates a whole tree. `--repository` is required outside Actions because `GITHUB_REPOSITORY` is unset; `source.runUrl` is `null` locally. This is the same conversion the `Check the report` step runs on every pull request ([CI](/wiki/ci/)), and the only way to inspect the generated files. Both write into an empty tree: whether the measurement merges with the published history (one row per revision, in order) is checked by the publish itself.

## Before the first push to main

- The App is installed on the data repository with Contents read and write.
- The producer has the variable and the `publish` environment with its branch policy and secret, and `validate.yml` names them.
- `config/targets.json` and `config/site.json` validate (`python3 -m unittest discover -s tests -p 'test_*.py'` and a dry run).
- A pull request has passed `Validate targets`, whose `Check the report` step converted this target's report.

Then merge. The first publish creates `data/<slug>/` and adds the slug to `index.json`; no one edits the data repository for a new game except to add cover art ([The site](/wiki/site/)).
