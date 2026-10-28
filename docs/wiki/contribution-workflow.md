# Contribution workflow

Bounded tasks, isolated branches, independent reviews and an owner-only merge.

This is the default contribution policy. It is written for people and agents alike: the same rules, the same records, the same gate. The starter `CONTRIBUTING.md` states it in full and `AGENTS.md` summarizes it for agents; both go into the repository with the parameters filled in. The owner may adopt a different policy, but then `CONTRIBUTING.md`, `AGENTS.md` and the [review gate](/wiki/review-gate/) change together.

## Authority

Only the owner (`OWNER_LOGIN`) merges into `main`. Contributors and agents prepare branches, open PRs and review. A `SHIP` verdict, a green CI run and an owner clearance comment are three different states, and none of them lets a contributor merge.

Optionally, the owner delegates clearance and merging to a **merge gate**: one agent acting under the owner's account, on a standing basis the owner can revoke. The gate checks reviewer independence, commissions missing reviews from fresh reviewers, posts clearance and squash-merges; it never authors contributions, never pushes to `main`, and escalates to the owner anything the rules reserve for the owner (matching-integrity exceptions, workflow and approval-control changes, dependency changes). If there is no merge gate, delete that section of the starter `CONTRIBUTING.md` and the references to it in `AGENTS.md`.

Nobody but the owner changes branch protection, `review.yml`, `REVIEW_OWNER`, the build image or its access controls. A dependency problem is reported in an issue, not fixed by changing the dependency.

## One task, start to finish

1. **Reserve.** Check open PRs and active branches. Record a bounded reservation in an issue or draft PR: the specific functions or unit, the branch and the shared files it touches. Reserve the batch being worked on, not a subsystem. A reservation expires after 48 hours without a progress update; release scope you abandon, and check existing branches before taking over expired work.
2. **Branch.** Work on a dedicated branch from current `main`, in your own checkout or worktree: `git switch -c your-task`. Branches live in the repository, not in forks; CI refuses to build a fork's pull request because fork builds would otherwise reach the private image.
3. **Establish evidence.** Boundaries, types and references before source; see [Evidence](/wiki/evidence/). Search existing headers and accepted units before declaring a shared address.
4. **Reconstruct and measure.** Compile and compare with objdiff. Keep discarded variants local. Register partial work as a `NonMatching` object in `configure.py` so CI measures it; promote to `Matching` when the unit links byte-identically. The source file does not move on promotion.
5. **Record.** Add `evidence.tsv` rows for every name, boundary, type and compiler claim in the same PR. Keep source comments free of scores and process notes.
6. **Self-check.** Build the complete executable (`ninja -f build/<target id>/build.ninja`) and confirm it still matches; run `ninja ... progress` and compare with the base revision; list unresolved functions and shared-file changes.
7. **Blind accuracy review.** A reviewer who did not author or shape the reconstruction interprets the scoped functions with the proposed names and comments withheld, then reconciles that interpretation with the submission and posts an `Accuracy:` record.
8. **Hostile review.** A fresh reviewer applies the checklist in `CONTRIBUTING.md` (source fidelity, compiler settings, types and layouts, names, comments, unit boundaries, comparison integrity, validation) and posts a `Hostile:` record with `SHIP`, `FIX`, `REDO` or `BLOCKED`.
9. **Resolve and recheck.** Fix findings; the reviewer rechecks the delta, not the whole PR, and posts a final-revision record that cites the earlier one.
10. **Submit.** Fill the PR template: scope, evidence and validation, review records. Request the owner's decision only when CI and both records cover the final revision.
11. **Owner clearance and merge.** The owner (or merge gate) posts the clearance comment; `Owner review clearance` turns green; the owner merges. On `main`, CI builds and publishes.

## Reviewer independence

Independence is about authorship and prior reasoning, not display names. A second agent spawned with the author's conversation is not independent; a reviewer given the task, the target evidence, the relevant configuration and the validation artifacts in a fresh context is. Each record states the reviewer's identity, prior involvement, supplied inputs and the reviewed revision. If isolation is impossible, disclose it; never assert an independent pass that did not occur.

Partial source is reviewed for fidelity, evidence and comparison integrity. A measured mismatch is not a finding. A reviewer may return `SHIP` with documented incompleteness.

## Rechecks, refreshes and batches

After a fix, the reviewer checks the finding, the correction and its affected dependencies and carries the rest of the coverage forward by linking the earlier record and its revision. A replacement reviewer may continue from that record. A full restart needs a concrete reason that invalidates coverage across the PR.

After refreshing from `main`, verify the diff, conflict resolutions and shared declarations, then post final-revision records that cite the earlier ones and name the checked delta. An earlier verdict does not cover a new head; the review gate enforces this mechanically by comparing the revision in each record with the PR head.

Compatible bounded contributions may be batched into one PR with each original PR, author revision and review coverage identified; the combined delta is reviewed and CI runs on the combined tree. Compiler-profile and comparison changes get their own review and never ride along in unrelated work.

## Delivery

Every handoff states: changed files, evidence, the validation commands and their results on which revision, unresolved findings and the exact review and publication state. "Implemented", "reviewed", "CI passed", "owner cleared", "merged" and "published" are different states. Do not keep running diaries of agent activity in the repository; PRs and issues are the record.

## The files

| File | What to fill in |
| --- | --- |
| `CONTRIBUTING.md` | `OWNER_LOGIN`, `owner/game`, the target directory, the README's build section link; delete the merge-gate section if unused |
| `AGENTS.md` | `OWNER_LOGIN`, the target directory; delete the merge-gate sentence if unused |
| `.github/pull_request_template.md` | Nothing; it is generic |
| `README.md` | Yours: the game, platform, region and revision, the original's SHA-1, the owner, the build commands, links to `CONTRIBUTING.md` and `AGENTS.md`; the README is what the other two files point readers at |

The record formats and the clearance comment the gate checks are specified in the next chapter and repeated in `CONTRIBUTING.md`.
