# Repository settings

Branch rules, merge method, Actions permissions, credentials, security features and presentation, applied by a script and re-checked monthly.

Settings are part of the standard because they are what makes the rest enforceable: a required check means nothing on a branch that accepts direct pushes, and a read-only default token is what keeps a workflow from approving its own PR. Three kinds of repository are in scope: the public source repository, the private build repository and the site. The data repository receives pushes from the publishing App and has its own settings.

## The standard

| Setting | Source repository | Build repository | Site repository |
| --- | --- | --- | --- |
| Default branch | `main` | `main` | `main` |
| Ruleset `main` | require a pull request; required check `Validate targets`; block force pushes and deletion; no bypass actors | none: rulesets on a private repository need a paid plan, and only the owner can push there | require a pull request; required check `Test`; block force pushes and deletion; no bypass actors |
| Ruleset `merges` | one `update` rule; its only bypass actor is the Repository admin role with bypass mode "pull requests only" | none | none |
| Merge method | squash only | squash only | squash only |
| Auto-delete head branches | on | on | on |
| Allowed actions | GitHub-owned, plus `mitsevox/mitsevox.github.io/.github/actions/*` | GitHub-owned only | GitHub-owned only |
| Default `GITHUB_TOKEN` | read-only; workflows declare their own `permissions` | read-only | read-only |
| Actions may approve pull requests | off | off | off |
| Fork pull request approval | required for all outside collaborators (the fork guard in `validate.yml` is the second line) | not applicable | required for all outside collaborators |
| Artifact and log retention | 30 days | 30 days | 30 days |
| Variable and secret | the repository variable `DATA_APP_CLIENT_ID`; no repository secret | none; `GITHUB_TOKEN` publishes the image | `SETTINGS_READ_TOKEN` for the monthly check |
| Environments | `publish`: deployment branches `main` only (no tag rule), the secret `DATA_APP_PRIVATE_KEY`, nothing else; `validate`: every branch, no secrets | none | none |
| Package | not applicable | private; `Manage Actions access` grants the source repository `Read` | not applicable |
| Secret scanning, push protection, Dependabot alerts, private vulnerability reporting | on | on where the plan allows | on |
| Dependabot version updates | off; pinned actions are bumped by hand twice a year | off | off |
| Issues | on | off | on (the drift issue) |
| Wiki, Projects, Discussions | off | off | off |
| Description, homepage, topics | `<Title> (<console>, <year>) decompilation`; `https://mitsevox.github.io/games/<slug>/`; `decompilation`, `<platform>`, `<slug>` | `Private build environment for <owner>/<game>`; none; none | the repository's own |

Two rulesets protect `main` in a source repository. `main` makes every change a pull request that passed `Validate targets`. `merges` decides who may merge: contributors hold write access, because CI refuses a fork's pull request (a fork's build would reach the private image), and write access alone would let a contributor merge a pull request that passed CI. The `update` rule restricts updates of `main` to the ruleset's bypass actors, and the only one is the Repository admin role in "pull requests only" mode: a writer pushes branches and opens pull requests but cannot merge, the owner merges through a pull request, and nobody, the owner included, pushes to `main` directly. GitHub shows the rule as "Restrict updates" and the bypass as "Repository admin, Pull requests only".

Each ruleset `--check` reads is the one with the standard's name, or else the one of that shape that targets the default branch under another name (`merges` is the ruleset whose only rule is `update`), never the same ruleset for both; `--apply` then renames it rather than adding a second one. An `update` rule inside `main` is drift: with no bypass actor there, nobody could merge. It also compares the pull request rule's merge methods and stale-approval dismissal, and the up-to-date requirement, which stays off: `main` rebuilds and verifies after every merge.

A single setting may differ for one repository (a merge method, say) when its process needs it; that is a row in the per-repository overrides of the configuration file, never a change to the table.

## The script

The standard is data: [`config/repo-standard.json`](https://github.com/mitsevox/mitsevox.github.io/blob/main/config/repo-standard.json) in the site repository holds the table keyed by kind, a `repositories` block that names each repository with the values its description, homepage and topics are built from, and the overrides. [`tools/repo_settings.py`](https://github.com/mitsevox/mitsevox.github.io/blob/main/tools/repo_settings.py) reads it and talks to the GitHub REST API; standard-library Python, idempotent.

```sh
export GH_TOKEN="$(gh auth token)"
python3 tools/repo_settings.py --repo owner/game --check
python3 tools/repo_settings.py --repo owner/game --apply
python3 tools/repo_settings.py --all --check
```

`--check` prints one line per setting that differs (`expected ..., found ...`) and exits 1 when anything does. A setting the token cannot read counts as drift, so a check never passes blind. `--apply` sets, in this order, the repository fields and features, the merge settings, the Actions permissions and allowlist, the default token permissions, fork approval, retention, the `main` and `merges` rulesets (each created or updated by name), the environments with their deployment branch policies, and the security features, then re-reads everything and prints what remains. A repository that is not listed in the configuration is checked against its kind alone (`--kind source` or `--kind build`), and its description, homepage and topics are its own.

What the script cannot set, and prints as hand steps:

- the variable (Settings, Secrets and variables, Actions) and the environment secret (Settings, Environments, `publish`), and deleting any others; a `DATA_APP_PRIVATE_KEY` repository secret goes only at its step of the move order below;
- the private package's `Manage Actions access` grant to the source repository;
- the GitHub App that writes the data repository ([Publishing](/wiki/publishing/));
- removing a `.github/dependabot.yml` if one exists.

The owner runs `--apply` with their own token once per repository after it adopts the standard, and after any deliberate change to the table.

## Keeping it true

Two readers keep the settings from drifting back:

1. **The scaffold check**, in every repository's `Tool tests` job ([CI](/wiki/ci/)), reads what the default `GITHUB_TOKEN` can see without any extra permission: the description, homepage, topics, features, merge settings and the rules that apply to `main` (`GET /repos/{owner}/{repo}/rules/branches/main`, the union of both rulesets, so a missing `update` rule shows there). It warns on each difference next to its other findings. It can read neither Actions permissions nor secrets, and it never writes.
2. **The monthly check** in the site repository, `.github/workflows/settings-check.yml`, runs `--check` for every listed repository with a fine-grained personal access token on those repositories, expiring yearly, stored as the secret `SETTINGS_READ_TOKEN`. The token holds read access, and nothing more, for: Administration (the Actions permissions), Metadata (the rulesets), Actions (the environments and their deployment branch policies), Environments (the environment secrets), Secrets and Variables (the repository's own); a permission missing from the token reads as permanent drift, because unreadable counts as drift. On drift it opens one issue in the site repository, or updates the open one, with the full report. It never applies anything, and no write-capable administration token ever exists in CI.

The monthly workflow is committed with manual dispatch only. Once the token exists, the owner creates the secret and adds the `schedule` block that the file's comment shows; nothing else changes. When the token expires, the check fails loudly at its first step rather than passing silently.

## Owner steps when adopting the standard

1. Merge the repository's scaffold PR, so that `validate.yml` and the `Validate targets` check exist before the ruleset requires them.
2. Run `python3 tools/repo_settings.py --repo owner/game --apply` and `--repo owner/game-build --apply` from a site repository checkout.
3. Do the printed hand steps: create the `DATA_APP_CLIENT_ID` variable and the `DATA_APP_PRIVATE_KEY` environment secret, delete the credentials and variables of any earlier process, confirm the package grant, and remove from the ruleset any required check whose job no longer exists.
4. Once, for the site repository: create the read-only token and the `SETTINGS_READ_TOKEN` secret, then enable the monthly schedule.

A repository that still holds the key as a repository secret moves it in this order. A job that references an environment reads the environment's secret when it has one of that name and otherwise falls back to the repository secret, so while both exist a `published` line proves nothing about the environment secret; the order below deletes the repository secret first and then demands a publish.

1. Create the `publish` environment with its branch policy and the environment secret, and the empty `validate` environment ([Publishing](/wiki/publishing/)); `--apply` creates both environments and the policy, the secret is by hand.
2. Merge the `validate.yml` change that references the environments (the kit sync).
3. Delete the repository secret `DATA_APP_PRIVATE_KEY` (Settings, Secrets and variables, Actions, Secrets).
4. Run the workflow on `main` by hand (Actions, Validate, Run workflow, branch `main`) and require `Publish to the site` to print `published ...`. A failure at `Mint a data-repository token` means the environment secret is wrong: fix it and run again; nothing was published in between, and the next run publishes.
5. Prove the branch policy, with both probes; they are the only evidence that the policy applies with `deployment: false`, which GitHub documents for secrets but not for environments created on the fly. On a throwaway branch change the environment line to `name: publish`, then (a) open a draft pull request: every `Validate <target id>` job must be refused before its first step with an environment protection message; (b) run the workflow by hand on that branch (Actions, Validate, Run workflow, choose the branch): refused the same way. Close the pull request and delete the branch. A probe that runs instead of being refused means the key is reachable from branches: delete the environment secret at once and report it.
6. `python3 tools/repo_settings.py --repo owner/game --check` reports no drift.

## Assumptions to confirm

- The actions-allowlist, retention and fork-approval endpoints behave as documented for personal accounts.
- `Manage Actions access` is still the package-level grant that lets the source repository pull the image.
- Every agent authors under the owner's login. That is what makes a native approval rule pointless and the procedural merge authority of [Contribution workflow](/wiki/contribution-workflow/) the right shape. If agents ever get their own accounts, add one required approving review from the owner with stale approvals dismissed, and nothing else changes.
