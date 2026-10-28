# Review gate

Review records, the owner clearance comment and the status check that verifies them.

The gate is one workflow, `.github/workflows/review.yml`, that publishes a commit status named `Owner review clearance` on the PR head. It is `success` only when the owner has posted a clearance comment that names the current head and links two passing review records on that PR. It runs trusted default-branch code, checks out nothing and holds no build credential; it reads PR comments and writes one status. The starter ships it as `review.yml.template` together with `tests/review_gate.mjs`, which exercises the script without GitHub.

## Review records

Each review pass is one PR discussion comment. The first line is the revision, the second the verdict; each header occurs exactly once in the comment, outside quotes and code fences.

```text
Revision: FULL_COMMIT_SHA
Accuracy: PASS

Reviewer: identity and prior involvement
Scope: functions, files and configuration checked
Evidence: references and validation artifacts used
Findings: results, uncertainties and resolutions
```

```text
Revision: FULL_COMMIT_SHA
Hostile: SHIP

Reviewer: identity and prior involvement
Checklist: PASS / FAIL / BLOCKED / justified N/A per category
Findings: location, evidence and required correction
Coverage: earlier records carried forward and delta checked
```

Accepted values: `Accuracy: PASS` or `Accuracy: N/A - <reason>` (the reason is required; a documentation-only change is the usual case), and `Hostile: SHIP`. `FIX`, `REDO` and `BLOCKED` are valid hostile verdicts but do not clear. The gate parses the headers only; the rest of the comment is for people.

## Owner clearance

After checking reviewer independence, coverage and the resolution of findings, the owner (or the merge gate, acting under the owner's login) posts:

```text
<!-- owner-review-clearance -->
Revision: FULL_COMMIT_SHA
Accuracy: https://github.com/owner/game/pull/NUMBER#issuecomment-ID
Hostile: https://github.com/owner/game/pull/NUMBER#issuecomment-ID
```

The marker is the literal first line. The two links point at two different comments on the same PR. To withdraw clearance, edit the latest clearance comment and remove its revision or links; the gate re-evaluates on every comment edit.

## What the check verifies

On `pull_request_target` (opened, reopened, synchronize, ready for review, converted to draft), on every PR comment created, edited or deleted, and on manual dispatch with a PR number, the job:

1. Fetches the PR. If it is not open, or its head repository differs from the base repository, it stops without setting a status: fork PRs are never cleared.
2. Sets `Owner review clearance` to `pending` on the head SHA.
3. Collects the comments by `REVIEW_OWNER` that start with the marker, takes the most recently updated one, and parses `Revision`, `Accuracy` and `Hostile` from its first three lines.
4. Requires: `Revision` equals the head SHA; both links are `https://github.com/<owner>/<repo>/pull/<number>#issuecomment-<id>` on this PR; the two links differ.
5. Fetches each linked comment and requires: it belongs to this PR; its first line is `Revision: <head SHA>`; its second line is `Accuracy: PASS`, `Accuracy: N/A - <non-empty reason>` or `Hostile: SHIP` for the respective lane. A linked comment that no longer exists makes the clearance invalid.
6. Requires the PR not to be a draft.
7. Sets the status to `success` with the clearance comment as its link, or leaves it `pending`.

| Case | Result |
| --- | --- |
| Current head, owner clearance, two distinct passing records on this PR, PR not a draft | success |
| No clearance, or clearance by another login | pending |
| New commits after the clearance | pending until new records and a new clearance name the new head |
| Same link twice, a link to another PR, malformed headers, a second `Revision:` line, a failing or stale verdict | pending |
| Draft PR | pending |
| Clearance edited to remove its revision or links, or a later clearance comment without them | pending |
| A linked review comment edited to another revision or deleted | pending |
| PR from a fork | no status is set |

`tests/review_gate.mjs` covers each row; `node --test tests/review_gate.mjs` runs it and the `Tool tests` CI job runs it on every push.

## Installing the gate

1. Copy `review.yml.template` to `.github/workflows/review.yml`. The only parameter is `REVIEW_OWNER`: set the repository variable `REVIEW_OWNER` to the owner's login (Settings, Secrets and variables, Actions, Variables), or replace `${{ vars.REVIEW_OWNER }}` with the literal login. The script throws if the value is empty.
2. Copy `tests/review_gate.mjs` and set its `owner` and `repository` constants; run it.
3. Merge the workflow to `main` first. `pull_request_target` and `issue_comment` run the workflow file from the default branch, so the gate does nothing for any PR until it is on `main`.
4. Open a test PR, post records and a clearance, and watch the status change; post a new commit and watch it go back to pending.
5. Only then, in branch protection for `main`, require the status checks `Owner review clearance` and `Validate targets`, require pull requests, and restrict pushes, force pushes and deletion. Verify who can bypass the rules; a documented policy enforces nothing by itself. GitHub's [branch protection documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) describes the options.

The workflow's permissions are `contents: read`, `pull-requests: read`, `issues: read` and `statuses: write`; it pins `actions/github-script` by commit SHA. Keep it that way: it is the one workflow that runs on comment events from anyone who can comment.

## What the gate cannot do

It authenticates the owner's clearance and the record references. It cannot prove that a reviewer was independent or that the review was any good; those judgments stay with the owner, directly or through the merge gate. Agents other than the merge gate must not post clearance on the owner's behalf, and clearance never authorizes anyone but the owner to merge.
