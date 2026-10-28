# Repository settings

Branch rules, merge method, Actions permissions, credentials, security features and presentation, applied by a script and re-checked monthly.

Settings are part of the standard because they are what makes the rest enforceable: a required check means nothing on a branch that accepts direct pushes, and a read-only default token is what keeps a workflow from approving its own PR. Two kinds of repository are in scope, the public source repository and the private build repository. The data repository and the site are the publishing side and have their own settings.

## The standard

| Setting | Source repository | Build repository |
| --- | --- | --- |
| Default branch | `main` | `main` |
| Ruleset on `main` | require a pull request; required check `Validate targets`; block force pushes and deletion; no bypass actors | require a pull request; required check `Build environment image`; block force pushes and deletion |
| Merge method | squash only | squash only |
| Auto-delete head branches | on | on |
| Allowed actions | GitHub-owned, plus `mitsevox/mitsevox.github.io/.github/actions/*` | GitHub-owned only |
| Default `GITHUB_TOKEN` | read-only; workflows declare their own `permissions` | read-only |
| Actions may approve pull requests | off | off |
| Fork pull request approval | required for all outside collaborators (the fork guard in `validate.yml` is the second line) | not applicable |
| Artifact and log retention | 30 days | 30 days |
| Variable and secret | `DATA_APP_CLIENT_ID`, `DATA_APP_PRIVATE_KEY`; nothing else | none; `GITHUB_TOKEN` publishes the image |
| Package | not applicable | private; `Manage Actions access` grants the source repository `Read` |
| Secret scanning, push protection, Dependabot alerts, private vulnerability reporting | on | on where the plan allows |
| Dependabot version updates | off; pinned actions are bumped by hand twice a year | off |
| Issues | on | off |
| Wiki, Projects, Discussions | off | off |
| Description, homepage, topics | `<Title> (<console>, <year>) decompilation`; `https://mitsevox.github.io/games/<slug>/`; `decompilation`, `<platform>`, `<slug>` | `Private build environment for <owner>/<game>`; none; none |

A single setting may differ for one repository (a merge method, say) when its process needs it; that is a row in the per-repository overrides of the configuration file, never a change to the table.

## The script

The standard is data: [`config/repo-standard.json`](https://github.com/mitsevox/mitsevox.github.io/blob/main/config/repo-standard.json) in the site repository holds the table keyed by kind, a `repositories` block that names each repository with the values its description, homepage and topics are built from, and the overrides. [`tools/repo_settings.py`](https://github.com/mitsevox/mitsevox.github.io/blob/main/tools/repo_settings.py) reads it and talks to the GitHub REST API; standard-library Python, about 250 lines, idempotent.

```sh
export GH_TOKEN="$(gh auth token)"
python3 tools/repo_settings.py --repo owner/game --check
python3 tools/repo_settings.py --repo owner/game --apply
python3 tools/repo_settings.py --all --check
```

`--check` prints one line per setting that differs (`expected ..., found ...`) and exits 1 when anything does. A setting the token cannot read counts as drift, so a check never passes blind. `--apply` sets, in this order, the repository fields and features, the merge settings, the Actions permissions and allowlist, the default token permissions, fork approval, retention, the `main` ruleset (created or updated by name) and the security features, then re-reads everything and prints what remains. A repository that is not listed in the configuration is checked against its kind alone (`--kind source` or `--kind build`), and its description, homepage and topics are its own.

What the script cannot set, and prints as hand steps:

- the variable and secret (set them in Settings, Secrets and variables, Actions, and delete any others);
- the private package's `Manage Actions access` grant to the source repository;
- the GitHub App that writes the data repository ([Publishing](/wiki/publishing/));
- removing a `.github/dependabot.yml` if one exists.

The owner runs `--apply` with their own token once per repository after it adopts the standard, and after any deliberate change to the table.

## Keeping it true

Two readers keep the settings from drifting back:

1. **The scaffold check**, in every repository's `Tool tests` job ([CI](/wiki/ci/)), reads what the default `GITHUB_TOKEN` can see without any extra permission: the description, homepage, topics, features, merge settings and the rules that apply to `main` (`GET /repos/{owner}/{repo}/rules/branches/main`). It warns on each difference next to its other findings. It can read neither Actions permissions nor secrets, and it never writes.
2. **The monthly check** in the site repository, `.github/workflows/settings-check.yml`, runs `--check` for every listed repository with a fine-grained personal access token limited to `Administration: read` and `Metadata: read` on those repositories, expiring yearly, stored as the secret `SETTINGS_READ_TOKEN`. On drift it opens one issue in the site repository, or updates the open one, with the full report. It never applies anything, and no write-capable administration token ever exists in CI.

The monthly workflow is committed with manual dispatch only. Once the token exists, the owner creates the secret and adds the `schedule` block that the file's comment shows; nothing else changes. When the token expires, the check fails loudly at its first step rather than passing silently.

## Owner steps when adopting the standard

1. Merge the repository's scaffold PR, so that `validate.yml` and the `Validate targets` check exist before the ruleset requires them.
2. Run `python3 tools/repo_settings.py --repo owner/game --apply` and `--repo owner/game-build --apply` from a site repository checkout.
3. Do the printed hand steps: rename or create `DATA_APP_CLIENT_ID` and `DATA_APP_PRIVATE_KEY`, delete the credentials and variables of any earlier process, confirm the package grant, and remove from the ruleset any required check whose job no longer exists.
4. Once, for the site repository: create the read-only token and the `SETTINGS_READ_TOKEN` secret, then enable the monthly schedule.

## Assumptions to confirm

- Rulesets on a private repository need a paid plan; on a free plan they exist for public repositories only, so the build repository's ruleset may be unavailable and `--check` will keep reporting it.
- The actions-allowlist, retention and fork-approval endpoints behave as documented for personal accounts.
- `Manage Actions access` is still the package-level grant that lets the source repository pull the image.
- Every agent authors under the owner's login. That is what makes a native approval rule pointless and the procedural merge authority of [Contribution workflow](/wiki/contribution-workflow/) the right shape. If agents ever get their own accounts, add one required approving review from the owner with stale approvals dismissed, and nothing else changes.
