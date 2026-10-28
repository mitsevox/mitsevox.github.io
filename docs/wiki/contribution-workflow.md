# Contribution workflow

Review tiers sized to what a PR touches, draft PRs as reservations, independent records and an owner-only merge.

This is the contribution policy for a one-owner project where agents do most of the work. It is written for people and agents alike: the same rules, the same records, the same authority. The starter `CONTRIBUTING.md` states it in full and `AGENTS.md` summarizes it for agents; both go into the repository with the parameters filled in, and the scaffold check keeps their section headings and `AGENTS.md`'s header matching the kit.

## What protects matching integrity

In order: CI proves that the complete executable of every affected target is byte-identical and measures each unit per target; the matching-integrity rules in `CONTRIBUTING.md`; a reviewer who did not write the code reads reconstructed source against the disassembly and the evidence before an inferred name or boundary is published; the owner decides what merges. Everything else is proportionate to the risk a change carries.

## Authority

Only the owner (`OWNER_LOGIN`) merges into `main`. Contributors and agents prepare branches, open PRs and review. A `SHIP` verdict and a green CI run are two different states, and neither lets a contributor merge. The authority is procedural for agents, which author under the owner's login, so a native approval rule would not tell an author from a reviewer; the `main` ruleset requires a pull request and the `Validate targets` check and nothing else, and the `merges` ruleset lets only the Repository admin role merge, so a contributor with write access cannot ([Repository settings](/wiki/repository-settings/)).

Nobody but the owner changes branch rules, repository settings, the build image or its digest, or the access controls around them. A dependency problem is reported in an issue, not fixed by changing the dependency.

## Tiers

The paths a PR touches decide what it needs before merge. The author states the tier in the PR's Scope line; CI's `Check the declared tier` step (`tools/tier.py`) fails a claim below what the diff needs, and the owner checks the rest.

| Tier | Touches | Required before merge |
| --- | --- | --- |
| A | `src/` or `include/` with new or changed inferred names, types, fields or unit boundaries; `splits.txt`; `symbols.txt`; compiler profiles | CI green, one blind accuracy record, one hostile record |
| B | `src/` or `include/` where every name and layout is `target`, `signature` or `related` (library imports, already-named code); promotions from `NonMatching` to `Matching` | CI green, one hostile record |
| C | `tools/`, `tests/`, `docs/`, `references/`, workflows, `config/*.json`, root documents | CI green |

The blind accuracy pass stays for tier A only: it is the one check that catches a wrong inferred name, and it reconciles nothing when the names come from an SDK or a sibling build.

## One task, start to finish

1. **Claim.** Check open PRs and branches. Open a draft PR early with the unit names and target ids in its title; that is the reservation, and it ends when the PR closes. There is no expiry bookkeeping.
2. **Branch.** Work on a dedicated branch from current `main`, in your own checkout or worktree: `git switch -c your-task`. Branches live in the repository, not in forks; CI refuses to build a fork's pull request because fork builds would otherwise reach the private image.
3. **Establish evidence.** Boundaries, types and references before source; see [Evidence](/wiki/evidence/). Search existing headers and accepted units before declaring a shared address.
4. **Reconstruct and measure.** Compile and compare with objdiff. Keep discarded variants local. Register partial work as a `NonMatching` object in `configure.py` so CI measures it; promote to `Matching` when the unit links byte-identically. The source file does not move on promotion. A version difference goes under `#if VERSION_<ID>` in the shared file ([Build, verify, measure](/wiki/build-verify-measure/#version-differences)).
5. **Record.** Add `evidence.tsv` rows for every name, boundary, type and compiler claim in the same PR, to each affected target's file. Keep source comments free of scores and process notes.
6. **Check every target.** Before calling a shared change safe for every target: build every active target and confirm `build.sha1` on each; run objdiff per target for each touched unit; run `python3 tools/versions.py diff` on every file you added a block to and read the result; add the evidence rows per target. CI enforces the first two; the hostile checklist's `Unit boundaries` and `Validation` rows cover the rest. Fill the Targets table of the PR template from these results, one row per active target.
7. **Review.** Tier A: a reviewer who did not author or shape the reconstruction interprets the scoped functions with the proposed names and comments withheld, reconciles that interpretation with the submission and posts an `Accuracy:` record; then a fresh reviewer applies the checklist in `CONTRIBUTING.md` (source fidelity, compiler settings, types and layouts, provenance and licence, names, comments, unit boundaries, comparison integrity, validation) and posts a `Hostile:` record with `SHIP`, `FIX`, `REDO` or `BLOCKED`. Tier B: the hostile record only. Tier C: none.
8. **Resolve and recheck.** Fix findings; the reviewer rechecks the delta, not the whole PR, and posts a final-revision record that cites the earlier one.
9. **Submit.** Fill the PR template: scope with the tier, the Targets table, evidence and validation, the records. Request the owner's decision only when CI and the records cover the final revision.
10. **Merge.** The owner merges. On `main`, CI builds and publishes each affected target.

## Review records

Each pass is one PR comment. The first line is the revision, the second the targets the record covers, the third the verdict; each header occurs once, outside quotes and code fences, so a record covering one target can never be read as covering both.

```text
Revision: FULL_COMMIT_SHA
Targets: GAME01-rev0, GAME01-rev1
Accuracy: PASS

Reviewer: identity and prior involvement
Scope: functions, files and configuration checked
Evidence: references and validation artifacts used
Findings: results, uncertainties and resolutions
```

```text
Revision: FULL_COMMIT_SHA
Targets: GAME01-rev0
Hostile: SHIP

Reviewer: identity and prior involvement
Checklist: PASS / FAIL / BLOCKED / justified N/A per category
Findings: location, evidence and required correction
Coverage: earlier records carried forward and delta checked
```

Accepted values: `Accuracy: PASS` or `Accuracy: N/A - <reason>` (the reason is required), and `Hostile: SHIP`, `FIX`, `REDO` or `BLOCKED`. Nothing parses these comments; they are for the owner and the next reviewer to read, and the format exists so that they can be read at a glance.

## Reviewer independence

Independence is about authorship and prior reasoning, not display names. A second agent spawned with the author's conversation is not independent; a reviewer given the task, the target evidence, the relevant configuration and the validation artifacts in a fresh context is. Each record states the reviewer's identity, prior involvement, supplied inputs and the reviewed revision. If isolation is impossible, disclose it; never assert an independent pass that did not occur.

Partial source is reviewed for fidelity, evidence and comparison integrity. A measured mismatch is not a finding. A reviewer may return `SHIP` with documented incompleteness.

## Rechecks, refreshes and batches

After a fix, the reviewer checks the finding, the correction and its affected dependencies and carries the rest of the coverage forward by linking the earlier record and its revision. A replacement reviewer may continue from that record. A full restart needs a concrete reason that invalidates coverage across the PR.

After refreshing from `main`, verify the diff, conflict resolutions and shared declarations, then post final-revision records that cite the earlier ones and name the checked delta. An earlier verdict does not cover a new head.

Compatible bounded contributions may be batched into one PR with each original PR, author revision and review coverage identified; the combined delta is reviewed and CI runs on the combined tree. Compiler-profile and comparison changes get their own review and never ride along in unrelated work.

## Delivery

Every handoff states: changed files, evidence, the validation commands and their results per target on which revision, unresolved findings and the exact review and publication state. "Implemented", "reviewed", "CI passed", "merged" and "published" are different states. Do not keep running diaries of agent activity in the repository; PRs and issues are the record.

## The files

| File | What to fill in |
| --- | --- |
| `CONTRIBUTING.md` | `OWNER_LOGIN` and `owner/game`; the section headings stay as in the kit |
| `AGENTS.md` | Nothing in the header; the project's own facts (toolchain, references, style guide, project tools) go under `## Project`, never process rules |
| `CLAUDE.md` | Nothing; it imports `AGENTS.md` |
| `.github/pull_request_template.md` | The target ids in the Targets table |
| `README.md` | Yours, under the seven headings of the kit template: the targets table, the build commands per target, the owner, links to `CONTRIBUTING.md` and `AGENTS.md`, the layout table, the credits |
