# Review & approval

Independent evidence, exact revisions and an owner-controlled merge decision.

## Contribution sequence

Claim scope → establish evidence → reconstruct and measure → self-check → blind accuracy review → hostile review → resolve findings → final-revision CI → owner clearance → owner merge → verified publication.

A source author cannot supply its own independent review. For reconstruction, the accuracy reviewer first examines the scoped target with proposed names/comments withheld, then reconciles its interpretation. The hostile reviewer checks fidelity, compiler settings, layouts, names, comments, boundaries, comparisons and validation. A documentation-only change can justify accuracy N/A; it cannot claim binary checks it did not run.

## Review partial source fairly

Review useful partial source for fidelity, evidence and comparison integrity. A measured mismatch is not automatically a review failure. A reviewer may return SHIP with documented matching incompleteness when the applicable checks pass. Original bytes remain linked until promotion is validated.

## Records tied to a revision

NFL posts the two passes as separate PR discussion comments, with each header field appearing once at the start. Replace placeholders only after the review actually occurs.

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

## Rechecks and integration

After a localized fix, recheck the finding and affected behavior, declarations, callers, boundaries, compiler/comparison configuration and evidence. Carry forward adequate independent coverage with its revision and links. Do not restart an entire review without a concrete coverage gap.

After bringing in main, inspect the delta, conflict resolutions and shared dependencies. Produce final-head review records explaining what was rechecked and why earlier coverage still applies. Run required CI on the final integrated inputs. Constituent PR reports cannot be combined into proof of a batch build.

When batching contributions, preserve original PRs, author revisions and review coverage. Close originals as incorporated after the batch merges. Compiler-profile and comparison changes need their own appropriate review; do not bury them inside unrelated source work.

## Owner clearance

Only the configured owner posts clearance after checking reviewer independence, coverage, findings and final CI. NFL's current format is:

```text
<!-- owner-review-clearance -->
Revision: FULL_COMMIT_SHA
Accuracy: https://github.com/OWNER/REPO/pull/NUMBER#issuecomment-ID
Hostile: https://github.com/OWNER/REPO/pull/NUMBER#issuecomment-ID
```

The record links must be distinct comments on the same PR, identify the current head and contain passing verdicts. A new commit makes old clearance stale. The check verifies record identity and formatting; it cannot prove reviewer independence or quality of reasoning.

Agents may prepare a clearance draft when asked, but must not impersonate the owner or post it without explicit authorization. Clearance never gives an agent merge authority. Only the owner performs the merge under the NFL model.

## New-project bootstrap

Adapt the owner identity, check names and record rules deliberately. Install the clearance logic using trusted base-branch code before requiring the check. Test missing, malformed, stale and withdrawn clearance plus draft PRs. Do not mark a status successful because a workflow file exists.

The [NFL contribution policy](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/CONTRIBUTING.md#review-records-and-owner-clearance) and [trusted clearance workflow](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/.github/workflows/review.yml) are the reference implementations. Their current same-repository contribution policy is a project choice; do not silently claim fork builds have private reference access.
