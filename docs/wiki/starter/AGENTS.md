# Agent instructions

PARAMETERS: replace `OWNER_LOGIN` with the owner's GitHub login and `config/GAME01-rev0/` with the real
target directory; delete the merge-gate sentence if the owner has not delegated clearance.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before working. It defines the contribution passes, [investigation and escalation](CONTRIBUTING.md#investigation-and-escalation), matching integrity, source comments and the approval process. Consult the [README](README.md) for the target and build entry point.

- Follow [work coordination](CONTRIBUTING.md#work-coordination): reserve only a bounded active batch, not a subsystem backlog. Work on a dedicated branch in your own checkout or worktree. Preserve unrelated changes and coordinate live overlaps and shared-file edits; old blanket claims do not reserve code.
- Use authorized reference material when relevant. Keep raw binaries, disc images, assets and trial output out of public Git. If required evidence or tools are unavailable, report the gap rather than invent a result.
- Keep contribution branches, PRs and reviews in this repository. Use the pinned, owner-approved build environment; do not alter supporting dependencies or their access controls. Report dependency problems in an issue for the owner's decision.
- Keep recovered facts, hypotheses, function-level matches, combined-build results and review verdicts distinct. Report what was actually checked and on which revision.
- Preserve useful partial reconstruction in normal source files and register it as a `NonMatching` object so CI measures it. Commit and submit it without requiring 100% matching; reviewed partial source may merge and publish fuzzy and exact-unlinked progress. Original bytes remain in the verified linked build until promotion. Matching incompleteness alone is not a review failure.
- Record evidence for names, boundaries, types and compiler profiles in `config/GAME01-rev0/evidence.tsv` ([format](config/README.md)) in the same PR as the change it supports.
- Complete the required accuracy and hostile-review passes. An author cannot provide its own independent review. A `SHIP` verdict means that review passed; it does not approve a merge.
- **Only the project owner (`OWNER_LOGIN`), or the owner's designated [merge gate](CONTRIBUTING.md#owner-delegation-merge-gate), authorizes and performs merges into `main`.** No agent enables auto-merge, pushes to `main`, force-pushes `main` or another contributor's branch, or changes approval controls (branch protection, `review.yml`, `REVIEW_OWNER`). Agents other than the merge gate do not merge PRs or post owner clearance. Push a work branch or open a PR only when authorized for the task, then leave it for the owner's decision.
- After fixes or a branch refresh, default to reviewing the delta and affected dependencies. Cite and carry forward adequate independent coverage; do not restart full reviews or duplicate full validation without a concrete coverage gap. Follow the recheck and final-revision rules in CONTRIBUTING.md.
- Address review feedback without weakening checks, hiding mismatches or changing project rules to accommodate a patch. Propose workflow improvements through the contribution process.
- Keep handoffs concise: changes, evidence, validation, unresolved findings and review state. Use PRs and issues for feedback and private research for detailed experiment histories; do not add running public status diaries.
