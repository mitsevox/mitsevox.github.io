# Producer policy sync

The site proposes changes to registered producer policies; it never approves them,
merges them, writes to producer repositories, or changes import trust during an
ordinary report refresh. Initial project registration/artwork and target changes
remain explicit site changes.

## Producer interface

Maintain a tracked, data-only producer policy JSON matching
`producer-v1.schema.json`. Keep it at a stable repo-relative path, normally
`config/TARGET_ID/producer.json`. Use the same policy when packaging reports.
When workflow code, required jobs/steps, artifacts or tool identities change,
update this file in the producer PR. Include the actual committed workflow Git
blob in `workflowBlobs`; a source commit SHA is not a workflow blob.

The site registers the source once in `config/policy-sync.json`:

```json
{
  "schemaVersion": 1,
  "projects": {
    "game-slug": {
      "policyPath": "config/TARGET_ID/producer.json",
      "mode": "policy"
    }
  }
}
```

This configuration references already registered report-v1 producers. It cannot
register a new repository or silently replace a target. Complete policies are
copied byte-for-byte. Paths, Git blob identity, size, JSON keys/schema, repository,
target and the current workflow blob are checked before preparing a candidate.
Producer scripts are never executed by the sync job.

## Proposal flow

The independent `Producer policy sync` workflow checks sources every 30 minutes
when the site variable `POLICY_SYNC_ENABLED` is `true`. GitHub schedules may be
delayed. The owner can dispatch it immediately, including before enabling the
schedule:

```sh
gh workflow run policy-sync.yml --repo SITE_OWNER/SITE_REPO --ref main \
  -f project=game-slug -f dry_run=true
```

Omit `project` to check every configured source. Set `dry_run=false` to propose
PRs. The CLI defaults to a dry-run:

```sh
uv run --locked python tools/sync_policies.py --all
```

An unchanged policy does nothing. A changed policy is prepared in an isolated
checkout of trusted site code. The job restores accepted state, preserves only
the selected producer's restored pointer/proof cache, archives the previous
policy, and imports a real successful package through the standard importer.
The producing revision must contain the same proposed policy. The normal
history, identity, artifact and aggregation checks still apply. The site builder
then validates the candidate. No unrelated project pointers are committed.

Only a successful candidate gets a PR. Its immutable content-keyed branch is
never overwritten or force-pushed. An existing matching PR is reused; a closed
proposal stays closed. A newer proposed policy gets a different branch. The PR
links the validation run, inspected source revision, workflow blob and actual
report run/revision. Results, the validated patch and PR body are retained as
workflow artifacts, including when PR creation fails.

Review the policy diff and producing workflow before merging under the site's
merge policy. Merging triggers normal site CI and deployment. A green producer
run does not by itself widen the site's trust. Until approval, refresh can reject
new reports and leave the last successful public deployment unchanged.

## Site-owned credentials and enablement

Use a dedicated GitHub App installed **only on the site repository**, with
**Contents: read/write** and **Pull requests: read/write**. Keep approval and
merge manual. Set the site variable `POLICY_SYNC_APP_CLIENT_ID` and secret
`POLICY_SYNC_APP_PRIVATE_KEY`. The pinned official action creates a short-lived
installation token for each run and revokes it afterwards. Do not store an
expiring installation token as a permanent secret. The repository setting that
allows Actions to create and approve PRs is not needed with this App.

The same App can power producer completion notifications below. Its private key
is held in each participating producer's Actions secrets; it grants access to
the site, not to other producer repositories. Restrict who can change trusted
main workflows and Actions secrets. Notification jobs request only Contents
write; policy proposal jobs additionally request Pull requests write. Both
permissions belong to the App, so possession of its private key can mint either;
these job-specific requests are not separate security boundaries.

An appropriately scoped alternative token may be supplied as `POLICY_SYNC_TOKEN`.
The built-in `GITHUB_TOKEN` fallback requires the owner's **Allow GitHub Actions
to create and approve pull requests** setting, and bot PR CI may require an
additional workflow approval. This is an alternative setup, not a requirement
for the App approach.

Producer reads and package validation use the built-in token; the App
or alternative token is used only for branch/PR writes. The job runs only from trusted site
main, never from producer PR code or untrusted event input. Project selection is
passed as an environment value and checked against the site-owned registry.

First run a dry-run. Then exercise a real changed-policy proposal, review its
validation and merge behavior, and set `POLICY_SYNC_ENABLED=true` to enable the
schedule. Manual dispatch remains available. Credentials and repository settings
are owner setup; never commit them.

See GitHub's [workflow triggering rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
and [repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

## Failure recovery

- **No tracked policy:** publish one and configure its path. A source with
  `{"disabled":"setup reason"}` is explicitly skipped and reported. Runtime
  exporter code is not parsed or executed to guess a policy.
- **Current workflow blob is missing:** update the producer's tracked policy
  using the committed workflow blob and let its validated main run complete.
- **No matching successful report:** the bot creates no PR. Fix producer CI and
  rerun, or allow the next scheduled check to retry. Do not relax authentication.
- **Wrong target/repository, frozen import or pending migration:** handle that
  registration/transition manually; sync will not override it.
- **PR permission failure:** results/patch/body remain in the run artifact. Set
  up the selected credentials. If the branch was pushed before PR creation
  failed, inspect it and open the PR manually using its retained body; the bot
  refuses to overwrite an occupied branch without a matching PR.
- **Rejected/closed proposal:** it is not reopened automatically. Reopen it under
  the site's review policy, or land a revised producer policy for a new proposal.
- **One source fails:** remaining configured sources are still checked; the run
  fails visibly and lists individual outcomes. Existing live data stays intact.

Keep all old policy archives while retained reports depend on them. Never delete
history, reset locks, or weaken validators to make a policy proposal pass.

## Prompt report refresh

Add a separate `.github/workflows/notify-portfolio.yml` to each producer. It runs
on `workflow_run` completion for the registered report workflow, only after a
successful same-repository main push or manual run. It never checks out producer
code or executes artifacts with the App key. Keeping this file separate leaves
the approved report workflow blob unchanged.

Generate the caller after the site's reusable notifier has merged and passed CI:

```sh
uv run --locked python tools/build_notifier.py --project game-slug \
  --site-revision FULL_APPROVED_SITE_SHA \
  --output /path/to/producer/.github/workflows/notify-portfolio.yml
```

The generator discovers the registered workflow's actual name. The caller pins
`notify-site.yml` to that full site revision. On the producer, set variable
`PORTFOLIO_APP_CLIENT_ID` and secret `PORTFOLIO_APP_PRIVATE_KEY`, using the same
site-only App. Install nothing on the producer. Review and merge the notifier
under that project's own merge policy.

The notifier sends `producer-report-ready` to the site with exactly `project`,
`repository`, and `runId`. The site independently fetches that run and checks its
registered repository, workflow path, branch, event and successful completion.
A notification is only a hint: the standard importer still authenticates the
workflow blob, jobs, steps, artifact, package, ancestry, history and measurements.
A new unapproved policy cannot be admitted by notifying.

The `Refresh producer reports` workflow checks all registered producers' latest
successful main runs, importing only changed run/attempts. This makes coalesced
notifications safe across different projects. The five-minute fallback schedule
runs when `REPORT_REFRESH_ENABLED=true`; GitHub can delay schedules. Unchanged
batches skip report import, assembly and deployment. Manual dispatch is available:

```sh
gh workflow run report-refresh.yml --repo SITE_OWNER/SITE_REPO --ref main
```

This lane deploys only site source that has already completed the normal main
`Portfolio` workflow successfully. Source edits still take normal CI. It validates
reports and builds the site without rerunning the source regression suite for
every producer commit. Full and data-only publications share a deployment queue.
Current-main checks prevent an older source revision from publishing.

If one producer fails, its pointer stays at last-good data; healthy projects can
still publish. Failures remain visible and invoke the policy proposal check.
Approval and merge remain manual. If the durable store advanced but Pages failed,
a later refresh retries publication by comparing the public and stored locks.

Enable the fallback only after manual refresh succeeds. Verify a real producer
completion through notifier, site refresh and public commit/metrics. Notifications
are prompt requests, not a guarantee of instant deployment: producer runtime,
runner availability, queues and Pages publication still take time.
