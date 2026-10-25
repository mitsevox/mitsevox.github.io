# Review & approval

Independent evidence, exact revisions and an owner-controlled merge decision.

## Policy selection

This chapter specifies the starter default: independent blind accuracy review, a fresh hostile review and owner-only merges. The owner may adopt a different project policy explicitly in CONTRIBUTING.md and CI configuration. Record which passes apply, reviewer independence, required records/statuses, clearance authority and merge authority. Do not require a status whose verifier was never installed, or silently weaken an adopted policy for a difficult patch.

The public report contract does not impose this review model. It authenticates the producing build/report execution; project policy governs source acceptance. Attribution and contributor rankings are separate choices.

Choose and document merge authority when establishing the project. The selected policy and explicit task authorization govern actual permission; a template does not itself grant authority. Existing-workflow compatibility belongs to the [optional appendix](/wiki/existing-projects/).

## Contribution sequence

The default sequence is:

Claim scope → establish evidence → reconstruct and measure → self-check → blind accuracy review → hostile review → resolve findings → final-revision CI → owner clearance → owner merge → verified publication.

A source author cannot supply its own independent review. For reconstruction, the accuracy reviewer first examines the scoped target with proposed names/comments withheld, then reconciles its interpretation. The hostile reviewer checks fidelity, compiler settings, layouts, names, comments, boundaries, comparisons and validation. A documentation-only change can justify accuracy N/A; it cannot claim binary checks it did not run.

## Review partial source fairly

Review useful partial source for fidelity, evidence and comparison integrity. A measured mismatch is not automatically a review failure. A reviewer may return SHIP with documented matching incompleteness when the applicable checks pass. Original bytes remain linked until promotion is validated.

## Records tied to a revision

Use two separate PR discussion comments for the reconstruction review passes, with each header field appearing once at the start. Replace placeholders only after the review actually occurs.

```text
Revision: FULL_COMMIT_SHA
Accuracy: PASS

Reviewer: identity and independence
Scope: functions, files and configuration checked
Evidence: reproducible references and validation artifacts
Findings: results, uncertainties and resolutions
```

```text
Revision: FULL_COMMIT_SHA
Hostile: SHIP

Reviewer: identity and independence
Checklist: PASS / FAIL / BLOCKED / justified N/A per category
Findings: location, evidence and required correction
Coverage: earlier records carried forward and delta checked
```

Hostile verdicts are SHIP, FIX, REDO or BLOCKED. SHIP means that review passed; it does not authorize a merge. Missing essential evidence is a blocked check, not permission to infer success.

Use this vocabulary consistently in new project instructions, review records and the selected verifier. Only the declared passing verdict can clear its check; missing essential evidence remains nonpassing. Adapting an older verdict system is covered in the optional appendix.

## Rechecks and integration

After a localized fix, recheck the finding and affected behavior, declarations, callers, boundaries, compiler/comparison configuration and evidence. Carry forward adequate independent coverage with its revision and links. Do not restart an entire review without a concrete coverage gap.

After bringing in main, inspect the delta, conflict resolutions and shared dependencies. Produce final-head review records explaining what was rechecked and why earlier coverage still applies. Run required CI on the final integrated inputs. Constituent PR reports cannot be combined into proof of a batch build.

When batching contributions, preserve original PRs, author revisions and review coverage. Close originals as incorporated after the batch merges. Compiler-profile and comparison changes need their own appropriate review; do not bury them inside unrelated source work.

## Owner clearance

Only the configured owner posts clearance after checking reviewer independence, coverage, findings and final CI. Use a machine-readable clearance format such as:

```text
<!-- owner-review-clearance -->
Revision: FULL_COMMIT_SHA
Accuracy: https://github.com/OWNER/REPO/pull/NUMBER#issuecomment-ID
Hostile: https://github.com/OWNER/REPO/pull/NUMBER#issuecomment-ID
```

The record links must be distinct comments on the same PR, identify the current head and contain passing verdicts. A new commit makes old clearance stale. The check verifies record identity and formatting; it cannot prove reviewer independence or quality of reasoning.

Agents may prepare a clearance draft when asked, but must not impersonate the owner or post it without explicit authorization. Clearance never gives an agent merge authority. The repository documents who may perform the merge and any explicit delegation. Agents follow the authorization given for the task.

## New-project bootstrap

Adapt the owner identity, check names and record rules deliberately. Install the clearance logic using trusted base-branch code before requiring the check. Test missing, malformed, stale and withdrawn clearance plus draft PRs. Do not mark a status successful because a workflow file exists.

Put the review record specification in CONTRIBUTING.md and its verifier in trusted workflow code. Declare whether contributions use same-repository branches or forks; fork builds do not automatically have access to private references. Match review effort to scope: source reconstruction needs fidelity review; presentation and documentation changes need relevant checks without unnecessary binary-build or reconstruction-review passes.

The starter archive includes an editable `review.yml.template` for the default record model. It uses trusted GitHub-script logic without checking out a PR or receiving build secrets. Set the adopted `REVIEW_OWNER` repository variable, inspect the pinned Action, adapt event/branch policies, then exercise it before making its status required. The verifier checks record fields and the owner's clearance; it does not create reviews or decide reviewer independence.

## Verifier acceptance matrix

| Case | Default-policy result |
| --- | --- |
| Current head, owner clearance, two distinct passing comments on that PR, ready PR | Success |
| No clearance or clearance from another identity | Pending |
| Head changed after reviews/clearance | Pending until final-head coverage and owner clearance |
| Same link twice, another PR, malformed headers, wrong revision or failing verdict | Pending |
| Draft PR | Pending |
| Latest clearance edited to remove revision/links or deleted | Re-evaluate; no success without another valid current clearance |
| Linked review comment edited/deleted | Re-evaluate; a missing record must not leave an old success |
| Contribution code or title contains executable-looking text | Treat as data; never execute it |

On every relevant event set the current-head status pending before evaluating evidence. Handle missing/deleted evidence as invalid clearance and finish with pending; do not let a failed fetch leave an earlier success in force. Exercise live event delivery as well as parser tests. An agent must not issue passing records, owner clearance or merge commands simply because the template lists them.
