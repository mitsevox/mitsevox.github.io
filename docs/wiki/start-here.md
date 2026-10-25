# Start here

From an empty repository to a measured, reviewable decompilation project.

This handbook carries forward the practices behind NFL Street 2: reproducible builds, evidence-backed reconstruction, useful partial source, independent reviews and honest reporting. Use it with a new project and a fresh agent, then record the choices in that project's own repository.

## Choose the right starting point

- **Starting a game:** follow [Repository setup](/wiki/repository-setup/) and [Layout & naming](/wiki/layout-and-naming/), then establish a [verified baseline](/wiki/build-and-validation/).
- **Starting a task:** read the project's README, CONTRIBUTING and AGENTS files, claim a bounded scope, and use a separate worktree.
- **Preparing a PR:** follow [Review & approval](/wiki/review-and-approval/). Passing CI and reviewer approval are separate from permission to merge.
- **Connecting a project:** read [Website](/wiki/website-integration/). NFL’s consumer integration is implemented; other games need adapters against their actual verified reports.
- **Handing off to an agent:** use [Starter kit](/wiki/starter-kit/) for repository templates and an agent handoff prompt.

## What belongs where

| Location | Responsibility |
| --- | --- |
| Game repository | Source, evidence, target configuration, build tools, validation, comparison reports and history |
| Private local research / approved build environment | Original binaries, complete debug exports, analysis databases and discarded experiments |
| Shared website repository | UI, artwork, project configuration, report contracts and static-site assembly |
| PR and issue records | Task ownership, reviews, findings, tested revisions and the owner's decision |

A new game normally needs one source repository and access to this shared website. An additional private tooling repository is only needed when its build inputs require that arrangement; it is not a mandatory extra repository for every game.

## The first-project sequence

1. Identify owner, repository slug, platform, region, revision, executable and verified hash.
2. Inventory authorized evidence before reconstructing anything. Record what was actually inspected and what remains unavailable.
3. Establish a reproducible original-byte baseline, then an accepted-source build that validates the complete output.
4. Document compiler profiles, comparison rules, evidence format and project-specific commands.
5. Put review rules and owner authority in CONTRIBUTING and concise agent instructions in AGENTS.
6. Add CI that enforces those rules on the actual tested revision. Test its failure paths before making checks required.
7. Recover a bounded unit with provenance; retain measured partial source where appropriate.
8. Connect verified reports to the site when the reporting adapter is available. Never substitute layout fixtures for measurements.

## Defaults, not assumptions

The recommended process is faithful matching reconstruction. A nonmatching port may adopt the evidence and review practices, but must define a different validation objective and label its measurements accordingly. Copying NFL's target hash, compiler flags or function counts does not establish anything about a new game.

Attribution tracking, contributor rankings and accepting contributions are three independent project choices. NFL requires exact-function attribution; the website itself does not require every project to adopt that policy. See [Credits & history](/wiki/credits-and-history/).

Existing repository rules govern work there. Adopting or changing those rules requires its owner's agreement. This handbook does not override them.

## Source and maintenance

The NFL reference is pinned to `d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211`, inspected on October 25, 2026. Links throughout the handbook identify the source policy or implementation. Check current repository instructions before applying a pinned example to live work.

Edit the Markdown under `docs/wiki/`, then run `uv run tools/build_wiki.py` in the website repository to rebuild the pages, search index, Markdown handbook and starter archive. The website serves the generated static files; it needs no documentation backend. Review handbook changes with the workflow or tooling changes they describe.
