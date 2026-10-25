# mitsevox project handbook

Reference snapshot: 2026-10-25. Project repository rules take precedence.

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


---

# Repository setup

Establish ownership, target identity and a safe working environment before the first reconstruction.

## Record the project identity

Choose a stable lowercase repository slug such as `nflstreet2`; use the same slug for its site route and reporting identity. Keep its display title separate. A second platform or revision is a separate target, not a silent replacement for the first one.

The README must identify the game, platform, region/revision, target executable hash, owner, supported host requirements, setup/build entry points and links to CONTRIBUTING and AGENTS. Use a full target hash; a filename or disc label alone is insufficient.

For a GameCube DOL, an initial local hash check can be:

```sh
# macOS
shasum -a 1 /path/to/main.dol
# Linux
sha1sum /path/to/main.dol
```

Compare the result with a verified target identity before using it. This identifies the input; it does not prove source fidelity. Keep the original executable outside public Git.

## Bootstrap the repository

Start with README, CONTRIBUTING, AGENTS, .gitignore, target configuration and a bounded build plan. Select and document licensing/provenance appropriate to your own tooling and imported sources; do not blanket-relicense imported code. The [starter files](/wiki/starter-kit/) provide editable scaffolding, not a build system.

Initialize an empty local repository without publishing it:

```sh
mkdir game-slug
cd game-slug
git init -b main
git switch -c codex/bootstrap
```

Inspect staged files before the first commit. Generated objects, originals and research dumps should never enter the commit. Create the hosted repository and configure access only when the owner authorizes those actions.

## Work in isolation

Once the repository has an established main branch and origin:

```sh
git fetch origin
git worktree add ../game-slug-task -b codex/task-name origin/main
cd ../game-slug-task
git status --short --branch
```

Use `codex/<task>` for agent branches by default; a project's own convention takes precedence. Do not reuse another contributor's dirty checkout. Claim the unit or shared-file scope in an issue or draft PR and identify dependency branches. An agent should receive explicit authority before pushing or opening a PR.

## Active work reservations

NFL distinguishes backlog from active work. Before starting, check open PRs and active branches, then reserve a bounded current batch in an issue or draft PR with the functions/unit action, branch and shared-file dependencies. Do not reserve an entire subsystem or future batches.

At the pinned NFL revision, a reservation expires after 48 hours without a meaningful update. Renew with pushed work, concrete findings or an explicit handoff; release paused or abandoned scope. Before taking over expired work, inspect existing branches/PRs and preserve useful partial source and credit. An old backlog claim does not own the code. A live overlap needs coordination even when two tasks touch different functions in the same header, file or compilation group.

A new project should choose and document its reservation policy rather than silently inheriting this timeout. See [NFL work coordination](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/CONTRIBUTING.md#work-coordination).

## Tool and reference access

Record required tools, versions, hashes, host architecture and installation instructions. Use the owner's approved build image or tool archive. A working compiler is not proof that its version and flags match the original; those claims need unit/library evidence.

NFL's current baseline supports macOS ARM64 and Linux x86-64; its macOS Wibo path requires existing Rosetta support. Those requirements are NFL examples, not universal requirements for every platform.

If access is missing, report exactly which input or tool is unavailable. Do not change private package permissions, rebuild supporting images or substitute a different compiler to make a patch pass. Keep credentials out of scripts, report packages and source control.

## Owner-configured GitHub controls

After the checks exist and their failing cases have been exercised, the owner configures the default branch rules: PR-based changes, the intended validation checks, review clearance, and restrictions on direct pushes, force pushes and deletion appropriate to the account. Verify who can bypass those rules; documentation alone does not enforce owner-only merging.

Use unique check names and verify which revision each required check evaluates. Bootstrap the review workflow on trusted default-branch code before requiring its status. Configure Pages separately for the website repository when deployment is authorized. Do not give game build jobs deployment or repository-write permissions merely because another job needs them.

[GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) and [required-check behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks) describe the available controls; verify them for the actual account.

## Ready to begin

A fresh contributor can identify the correct input, reproduce the baseline, locate the contribution rules and understand who may merge. Any missing item is a named setup gap—not a reason to report the repository as ready.


---

# Layout & naming

Keep source readable, evidence discoverable and generated material disposable.

## Recommended layout

This is a starter convention. Preserve evidence-supported original source paths and an established project's structure instead of reorganizing working code to fit a template.

```text
game-slug/
  README.md
  CONTRIBUTING.md
  AGENTS.md
  CREDITS.md
  .gitignore
  src/                     # recovered and useful partial source
  include/                 # shared declarations
  config/
    README.md              # evidence and configuration conventions
    TARGET_ID/
      README.md            # target-specific mechanics
      baseline.json        # verified executable identity and geometry
      units.json           # accepted source placement / compiler profiles
      comparisons.json     # independent partial/exact comparisons
      evidence.tsv         # curated claims and reproducible locators
  tools/                   # reproducible build, comparison and export tools
  tests/                   # meaningful checks for those tools and contracts
  docs/                    # durable design and setup documentation
  .github/
    workflows/
    pull_request_template.md
  build/                   # ignored generated outputs
  scratch/                 # ignored experiments
```

File names above reflect NFL's pattern; their formats must be defined by the new project's tools. Creating an empty `units.json` does not make NFL's builder work on a different game. Optional contributor ledgers and history checkpoints belong in target configuration when the project's policy enables them.

## Naming rules

- **Original names:** preserve spelling and case when target evidence supports them. Keep the evidence locator.
- **Descriptive names:** make them readable, but mark them inferred rather than claiming the original name was recovered.
- **Unknown code/data:** retain stable neutral address labels. NFL uses `fn_XXXXXXXX` and `lbl_XXXXXXXX` with uppercase hexadecimal digits; these receive no named-function credit.
- **Files:** use recovered source paths when established. A descriptive filename can count as named while its original boundaries remain provisional.
- **Tools/docs:** use consistent repository conventions; Python tools commonly use `snake_case.py`, handbook pages use `kebab-case.md`.
- **Site assets:** use stable project slugs, for example `assets/covers/game-slug.webp`. Store display names separately from paths.

Do not invent a source-file split merely to produce a pretty map or increase file counts. Shared headers should have one accepted definition per type/address. Search existing declarations and current main before introducing another layout.

## Source and partial reconstruction

Useful incomplete functions stay in normal source files. Register their measured ranges separately. In NFL, an existing linked file can keep draft bodies behind the fixed `DECOMP_COMPARE` guard; promotion changes accepted placements and removes the guard, not the file location.

Keep source comments about intent, invariants and non-obvious relationships. Matching scores, compiler experiments, agent notes and review history belong in metadata or PR records. Unsupported field meanings stay unresolved; unaccessed regions stay opaque.

## Public and private material

Public Git should contain reviewed source, tools, curated evidence and bounded public reports. Keep original game binaries, generated objects, complete debug exports, private analysis databases and discarded trial variants out. A .gitignore entry does not remove a file already tracked; inspect the index before committing.

Do not copy absolute paths from another contributor's machine into shared configuration. Commands should accept a local reference path or use a documented owner-approved environment.

## Evidence format

NFL uses one claim per TSV row:

```text
kind  start  end  subject  origin  start_boundary  end_boundary  evidence
```

The separators are tabs. Addresses are hexadecimal and end-exclusive. Use `-` where unknown or inapplicable. Origins distinguish `target`, `signature`, `related` and `inferred`; boundaries independently distinguish `exact`, `provisional`, `open` and no claim. Use separate rows for a name, function extent, field layout and source-unit boundary—one claim must not silently prove another.

The [NFL evidence specification](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/README.md) defines the full vocabulary. Adopt its schema intentionally and provide validators before relying on it in another repository.


---

# Evidence

Recover what the target supports, and keep uncertainty explicit.

## Inventory before interpretation

Inventory the target's parsed filesystem and available executables, symbols, ELF/STABS/DWARF data, linker maps, diagnostic strings, SDK references and related builds. Record hashes/revisions and which files were parsed. If claiming an artifact does not exist, document the coverage of the search; a filename search or a few strings alone is insufficient.

Related builds can suggest names and behavior. They do not prove the target's offsets, field widths, original names or source boundaries. Keep target evidence separate from reference evidence and inferred meaning.

## Define a bounded task

Identify the functions, target ranges, candidate source unit, shared headers and dependencies before editing. Confirm accepted declarations on current main. Establish each function's full extent and the limits of any provisional unit; unresolved boundaries must remain visible.

For a field or signature, cite actual loads/stores and relevant caller/callee behavior. A nearby subsystem's access is not proof of the same layout. Preserve unknown offsets without inventing a convenient struct.

## The reconstruction loop

1. Describe the behavior and evidence-backed types before optimizing for a score.
2. Write plausible source in the codebase's style.
3. Compile with the documented unit/library profile.
4. Compare full function bytes, referenced data and relocations under the documented comparison method.
5. Investigate the remaining uncertainty, record the result and retain useful partial source.

A byte match establishes compiler equivalence for the measured scope. It does not by itself prove names, intent, type correctness or original file boundaries.

## Escalate the question, not the guesswork

| Uncertainty | Useful investigation |
| --- | --- |
| Behavior, references or ownership | Target disassembly and bounded Ghidra/static analysis |
| Different instruction selection or scheduling | Controlled compiler experiments and relevant ProDG RTL dumps |
| Competing behavioral interpretations | Bounded debugger/runtime trace with known inputs and conditions |
| Candidate SDK reuse | Fingerprints followed by calls, globals, types and boundary checks |

Record tested revision, tool version/settings, inputs, conclusion and remaining uncertainty. Check decompiler output against instructions. Runtime observations establish what happened under those conditions, not the original source text. Keep bulk experiments private; retain concise reproducible evidence publicly.

## Matching integrity

Do not force a match through patched output, embedded instruction bytes, unsupported inline assembly, per-function flag changes, altered comparison boundaries or excluded mismatches. Do not invent helpers, padding, casts, volatile qualifiers or control flow solely for code generation.

Compiler exceptions require original-scope evidence and explicit owner approval under NFL's policy. Originally handwritten assembly needs provenance. Labeling a workaround “fake match” does not make it acceptable.

When evidence runs out, preserve the useful partial reconstruction and document the gap. Keep original bytes in the verified linked build until replacement is validated. Partial similarity is useful progress; unsupported certainty is not.

## SDK and imported work

Retain origin, source revision, license/provenance and local modifications. A fingerprint is a candidate, especially for short functions. Inspect target-specific calls, data ownership and compilation boundaries before import. Imported code receives the same relevant fidelity and hostile reviews as new reconstruction.

[NFL investigation, matching integrity and source standards](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/CONTRIBUTING.md) are the reference for this chapter.


---

# Build & validation

Separate a working baseline, reconstructed source and independent comparison measurements.

## Three different results

| Result | Establishes | Does not establish |
| --- | --- | --- |
| Original-object relink | Target extraction, placement and relink can reproduce the executable | Recovered source, original compiler identity or progress |
| Accepted-source build | Selected source replaces its accepted ranges and complete output still matches | Exactness of every original file boundary |
| Independent comparison | Full registered functions/data have measured exact or fuzzy similarity | Permission to replace their original linked bytes |

A new project must implement and document these distinctions for its executable format. NFL's DOL section layout and tool profiles cannot simply be copied to another target.

## NFL command reference

These commands are executable entry points in NFL Street 2, not commands available in an empty repository. Follow its README host/setup requirements first.

```sh
python3 tools/setup_compiler.py
python3 tools/baseline.py --original /path/to/main.dol
python3 tools/source_build.py --original /path/to/main.dol
python3 tools/analyze.py --original /path/to/main.dol
python3 tools/matching.py --original /path/to/main.dol
python3 -m unittest discover -s tests -v
```

NFL additionally validates its SN-linker original-object relink. Run relevant focused checks during iteration and the required final checks before submission; do not repeatedly run the entire suite when nothing affecting it changed.

## Establish the new project's baseline

Record executable identity, section sizes/addresses, entry point and target hash. Verify the complete reconstructed executable against the original, not only selected functions or a summary score. Document all placement, alignment, small-data and relocation handling. Keep unassigned bytes represented.

Pin the usable compiler, linker, wrappers and conversion tools with hashes. Record unit/library compiler-profile evidence separately. A successful diagnostic compile can establish compatibility without uniquely identifying the original compiler version.

## Register partial comparisons

Define source path, profile, full target extents, code/data placement and dependencies. Reject overlaps, missing functions, unresolved references and stale receipts. Compare compiler-produced bodies without truncating mismatches. Weight fuzzy similarity by the target extent, not the size of an expanded draft.

Use normal source files for partial work. Where accepted and draft code coexist, a documented comparison guard can select draft bodies for measurement while preserving the accepted build. Keep original bytes linked until promotion; partial mismatch alone is not a reason to reject a well-supported reconstruction.

## Promotion

After review and validation, change the accepted source-placement configuration, remove obsolete guards/registrations and verify the entire executable. Do not move a function into a different source tree merely because it became exact. Preserve its attribution if tracking is enabled, and avoid counting a linked range again through a comparison entry.

Uninitialized storage has no speculative fuzzy byte score. Validate its layout and the project's stated accounting rules. Code/data classification follows the declared target measurement universe, including documented data embedded in executable sections; do not silently change denominators for the chart.

## Bind results to inputs

Reports should identify target hash, tested revision/tree, source/header hashes, unit manifest, profile, tool versions and comparison methodology. Reject a stale report after its inputs change. A successful earlier build is not proof of the current tree.

Validation tools need meaningful failure tests: wrong target, stale dependency, overlapping range, missing symbol, changed compiled extent, unsupported data placement and corrupt report. Do not weaken validators to accept the current patch. Record failures and unresolved questions honestly.

See [NFL target mechanics and comparison workflow](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/GN7E69/README.md) for concrete formats, constraints and implementation details.


---

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


---

# CI & publication

Validate once, preserve the evidence and publish only a coherent verified result.

## Jobs and authority

| Job | Inputs and purpose | Authority |
| --- | --- | --- |
| Build/measure | Approved references and pinned tools; baseline, source and comparisons | Read source/packages; no source-branch writes |
| Review clearance | Trusted workflow code and PR discussion records | Read PR records; write the named status |
| Data publication | Authenticated successful measurements and prior history | Narrowly scoped report-store writes |
| Website build | Public verified report packages and site source | Read packages; produce static artifact |
| Pages deployment | Successful site artifact | Pages and deployment identity permissions |

Pin reviewed Actions and shared tools to commits, build images to approved digests, and downloaded compilers/linkers by version and hash. Do not copy mutable image tags into the new archetype. Cache keys include target, environment and relevant configuration/source inputs; caches are acceleration, not validation evidence.

## PR path

Validate the candidate revision and emit a receipt binding target, tested tree, environment, methodology, inputs and artifact checksums. Produce candidate reports for review without advancing public latest. Keep failures actionable and prevent stale output from an earlier successful run being uploaded after a failed export.

CI must fail if required inputs or enabled measurements are unavailable. Scope cheap validation separately from expensive reconstruction builds. The owner should enable required statuses only after observing real passing and failing behavior.

## Main path and proof reuse

NFL can reuse the final integrated PR's verified reports when trusted execution, artifact integrity, pinned environment and complete tested tree match the landed tree. Validate contributor provenance against actual landed/squashed history when that policy is enabled. Missing or incompatible proof falls back to full validation; invalid required attribution or history blocks publication.

An inventory-cache miss does not invalidate otherwise valid source-build proof. Regenerate the affected inventory separately. Do not repeat complete builds solely because review comments changed or an unchanged artifact can be authenticated.

Keep these guarantees when extracting reusable steps. Do not replace NFL's mature handoff checks with “download the latest artifact.”

## History and ordering

Restore prior verified history before appending. Fetch or parse failure must not reset an established timeline. Make identical reruns idempotent. Distinguish commit time, measurement time and publication time.

The proposed shared store is a data-only branch per game with immutable snapshot packages and a latest-good pointer. It is not implemented yet. Preserve current archives until migration is verified. Git ancestry, immutable identity and an atomic pointer update prevent an older slow run from replacing newer progress; concurrency settings alone are insufficient.

A timeline records available verified measurements, not a guaranteed build for every commit. Preserve gaps and legacy evidence quality. Do not manufacture measurements by repeating a previous value and labeling it a fresh build.

## Privileged workflows

Treat PR text and report payloads as data. Never execute scripts from downloaded artifacts or untrusted PR code in a privileged publication/clearance job. Keep private references and build credentials out of the website job. The NFL clearance workflow evaluates trusted logic without checking out a contribution branch.

[GitHub's security guidance](https://docs.github.com/en/actions/reference/security/secure-use) covers pinned Actions and untrusted code. [workflow_run guidance](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run) explains why an upstream result must be authenticated before privileged follow-up work.

## Website deployment

Use a separate build artifact and deployment job. GitHub Pages deployment needs `pages: write`, `id-token: write`, the appropriate environment and a dependency on the artifact-producing job. See [custom Pages workflows](https://docs.github.com/en/enterprise-cloud%40latest/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Build fingerprinted assets and publish one coherent site artifact, so a browser cannot mix old CSS with new markup. Verify home, direct game/wiki URLs, refresh and back/forward behavior at the deployed base path. To roll back UI, have the owner merge a source revert and let the current-main workflow rebuild with the latest verified reports. Old workflow reruns are rejected; measurement history is never rewound.

The [NFL consumer implementation](/docs/reporting/nflstreet2.md) verifies existing artifacts and builds a locked static candidate without adding game CI work. Validation uses read-only permissions. A separate current-main job has site-repository write access for the data-only `report-data` branch, plus Pages and deployment-identity permissions. It preserves snapshots before deployment, rejects stale site revisions and never writes a game repository or merges main.

The [pipeline audit](/docs/reporting/pipeline-audit.md) records the three current producers. The [shared workflow proposal](/docs/reporting/workflow.md) describes the remaining cross-game migration; distinguish it from the implemented site-only workflow.


---

# Credits & history

Choose attribution policy deliberately, and preserve the meaning of every historical measurement.

## Three independent choices

| Choice | Controls |
| --- | --- |
| Track attribution | Whether the game maintains and validates function-level contributor provenance |
| Show contributor rankings | Whether the site renders verified credit data |
| Accept contributions | Whether the Contribute button and contribution guide are offered |

A game can publish progress without function attribution. Turning rankings off does not inherently turn tracking off. Changing tracking policy is an explicit repository decision; hiding a UI section must not silently delete evidence already recorded.

NFL requires exact-function attribution today. MVP, Tiger Woods and future projects do not acquire that requirement merely by joining the site. If tracking is disabled, mark the contributor capability unavailable and keep rankings off; enabling accurate rankings later may require reconstruction that is not fully possible.

## NFL's credit model

Credit follows the original source contributor, not the person who merges or batches the PR. Store stable function extents, original contribution references, original revision/source blob and integration provenance as required by the ledger. Retain the original identity when imports are corrected or squash-merged.

The ledger covers complete exact functions, including exact unlinked comparisons. Fuzzy source retains provenance without exact-function credit. Promotion creates no duplicate credit. Retired or no-longer-exact functions leave current exact totals while their provenance remains recorded.

Explicit joint credit is allowed: each person receives that function once. Personal totals can therefore overlap; the union of credited functions, not the sum of personal counts, must equal the exact inventory. Sort current distinct function counts deterministically.

## Before submitting a tracked contribution

Open the authorized draft PR to obtain its real number; never guess a future PR number. Record its actual original/integration references and validate the complete ledger against the candidate exact inventory. For a batch, use the actual batch PR as integration metadata while preserving original authorship.

NFL validates the introduced source blob in reachable landed history, including a synthetic squash against the actual PR base. Pinned original commits must be accessible; missing provenance is a validation gap, not a reason to attribute the function to the integrator.

## Recovering past credit

Use surviving original PRs, commit authorship, pinned source blobs, integration records and reviewed evidence. A closed PR or deleted branch may still leave useful records; do not assume they are available indefinitely. Distinguish supported attribution, explicit joint work and unresolved ownership.

Keep a bounded recovery record explaining each decision and uncertainty. Do not give every function to the current file author or merger. If a project promises complete exact-function attribution, unresolved gaps block that capability's publication until resolved or the owner explicitly changes the policy.

## Timeline continuity

Keep full commit identity, target, methodology, raw totals/denominators and evidence quality. Preserve measured, reconstructed and inherited legacy entries distinctly. A new inventory can change a percentage without source regression; make the basis change explicit rather than smoothing the graph.

Restore prior verified history; do not use an unauthenticated live page as automatic recovery evidence. An intentional checkpoint recovery needs a documented audit. Latest repository commit metadata is separate from the latest measured build, even when the header displays both near each other.

See [NFL timeline and contributor rules](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/GN7E69/README.md#timeline-and-contributor-credits) and [history recovery](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/README.md#history-recovery).


---

# Website

One shared renderer, game-owned measurements and modules selected per project.

## Current state

The shared renderer now consumes authenticated NFL Street 2 report packages. The importer verifies NFL’s existing main CI artifacts; it adds no game build steps. The production builder includes only verified configured projects. MVP and Tiger Woods remain layout previews until their own adapters are validated. A successful current-main site workflow preserves verified reports and deploys Pages.

## Refresh and build NFL

In the website repository, with Python 3.11+, uv and an authenticated GitHub CLI:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python tools/import_nfl.py
uv run --locked python tools/build_site.py --output build/site
python3 -m http.server 54872 --bind 127.0.0.1 --directory build/site
```

Use a new output directory for each retained candidate. The [NFL integration reference](/docs/reporting/nflstreet2.md) documents authentication, immutable packages, failure handling and the remaining production-promotion step.

## Project identity and artwork

Use the same slug for repository identity, `/games/<slug>/` and asset names. Configure title, console, target ID/hash, repository link, cover dimensions and contribution policy. Keep region/revision explicit. A different target must not overwrite another target's report history.

Store covers as `assets/covers/<slug>.webp` with their original aspect ratio. Use owned or authorized presentation artwork; do not export raw game assets through build reports. Console icons and other reused assets retain their provenance/license notes.

The local prototype's `assets/projects.js` is the current registration point. Adding a fixture there enables a layout preview, not production measurement. Production registration uses `config/projects.json`; `data/reports.lock.json` selects authenticated snapshots.

## Report semantics

| Metric | Meaning |
| --- | --- |
| Linked | Source incorporated into the verified target build |
| Matched | Exact measured source bytes, including eligible unlinked functions |
| Fuzzy | Target-size-weighted similarity; never exact-function credit |
| Functions exact / named | Complete exact extents / supported descriptive names within the declared inventory |
| Files exact / named | Exact evidenced file boundaries and contents / descriptive file identities, including provisional ones |

Overlapping progress layers are not additive percentages. A neutral name does not earn naming credit. A complete file claim requires its own boundary evidence. Map groups can be provisional without earning source progress. Preserve unmapped ranges.

Data and code fuzzy measurements need separate support. NFL's decomp.dev scalar is code-only; data similarity is in sections while its current data bar exposes linked/exact progress. Never copy a code score into a data metric to fill a missing field.

## Modular configuration

The project configuration independently enables maps, function counts, file counts, timeline and contributor rankings. Core code/data measurements are required by this initial site contract. Producer capabilities describe what actually exists; site preferences select what appears.

```json
{
  "schemaVersion": 1,
  "slug": "game-slug",
  "title": "Game title",
  "repository": "owner/game-slug",
  "target": "TARGET_ID",
  "modules": {
    "map": true,
    "functionCounts": true,
    "fileCounts": false,
    "timeline": true,
    "contributors": false
  },
  "contributions": { "accepting": false }
}
```

Add a project to `config/projects.json` only after its adapter and first package are validated. This example shows the configuration shape; it does not make an unsupported game ready by itself. Enabling Contribute requires a guide URL. Attribution tracking is a separate game-repository policy; rankings require supported verified attribution data.

A disabled module creates no empty section or section listeners. NFL shares payloads between map/counts and timeline/rankings; an enabled sibling can still require that shared file. Unsupported data is not zero. If an already-supported enabled module fails to export, retain the last valid package and fail the refresh rather than silently hiding it.

## Producer adapter checklist

1. Establish target and tool identity; verify build/comparison inputs.
2. Translate raw measurements into the common manifest without changing denominators or losing partial progress.
3. Supply typed map/history/credit payloads for supported modules; attach checksums and provenance.
4. Validate ranges, inventory, arithmetic, target identity, history continuity and the project's attribution policy.
5. Produce website and decomp.dev outputs from the same verified computation where possible.
6. Publish immutable snapshots and advance latest only after success.

The [manifest schema](/docs/reporting/schema/report-v1.schema.json), [configuration schema](/docs/reporting/schema/project-v1.schema.json) and [semantic contract](/docs/reporting/contract-v1.md) are available. NFL has payload schemas, semantic checks and a working consumer adapter. New games still need their own producer authentication and mapping. JSON-schema validation alone does not authenticate CI.

## Consumer and rollout checklist

The NFL importer authenticates and locks packages before static assembly. The builder verifies checksums and semantics, rejects fixture origins and copies selected data into the static output. Browser visitors need no GitHub credentials. Load heavy map/history payloads only when their module needs them.

If one game's refresh fails, keep its last verified package; another game's valid update can still publish. Never present newest-commit metadata as a newly measured build. Test direct routes, custom menus, keyboard navigation, disabled modules, cached assets and rollback before deployment.

Migrate NFL first, compare both consumers at the same revision, then add MVP and Tiger Woods. Preserve their current decomp.dev artifact feeds and histories throughout. Redirect existing game Pages only after owner-approved live parity. The [migration plan](/docs/reporting/migration.md) lists the acceptance gates.

## Current publication boundary

Site CI validates PRs and produces candidates. Push/manual/scheduled refreshes restore the durable last-good package and use read-only access to NFL. A failed refresh fails CI and leaves the live site unchanged. Only current-main publication jobs can append verified snapshots to this site repository’s `report-data` branch and deploy the validated Pages artifact. Historical snapshots remain in Git when candidate artifacts expire after 90 days. No workflow writes game source branches or changes NFL’s existing publication.


---

# Troubleshooting & upkeep

Diagnose the failing layer before changing source, configuration or publication.

## Common failure patterns

| Symptom | First checks | Avoid |
| --- | --- | --- |
| Baseline fails | Target hash, section geometry, approved tools and complete-output diff | Editing the target or ignoring differing bytes |
| Source scores well but looks wrong | Types, calling convention, bounds and comparison coverage | Treating a percentage as semantic proof |
| A header edit breaks comparison | Dependency hashes, generated symbols and storage maps | Reusing stale reports |
| Linked/matched/fuzzy are equal | Actual registered partial comparisons and report numerators | Artificially separating values for appearance |
| Function tiles show only 0/100 | Per-function fuzzy fields and renderer mapping | Inferring scores from whole-file averages |
| Files exact stays low | Whole-unit boundary evidence and mapped extents | Equating green functions with known original files |
| Owner clearance stays pending | Current full head SHA, distinct valid records, draft status and owner identity | Bypassing the gate |
| History disappears | Restore source, artifact identity/digest and parser failure | Reinitializing an established timeline to empty |
| Older progress replaces newer | Run ordering, ancestry and latest-pointer promotion | Sorting publication by completion time |
| Site mixes old and new styling | Asset versions, deployment artifact and browser cache | Assuming a correct local page proves production |
| Missing contributors | Declared tracking policy, exact inventory and preserved provenance | Assigning everything to the merger |

## Investigate with a bounded record

Record failing revision, target, tool environment, command, observed output and the specific question. Reproduce the smallest relevant scope, compare with the base revision, then fix the cause. Expand checks when evidence shows a wider dependency; do not repeat full builds as a reflex.

For source defects, re-run affected comparisons and complete the required final validation. For documentation/style changes, use relevant link, route or visual checks. Do not invent a binary-validation result for an unrelated change.

## Recovery and rollback

An unavailable essential reference/tool is a named blocker for the owner. Invalid publication metadata blocks promotion while the current valid package remains available. Recover history from authenticated archives or an explicitly audited checkpoint. Roll back the site independently from game source/history.

A changed owner policy needs a focused proposal and appropriate review. Do not loosen assertions, change counts, conceal mismatches or alter private dependencies merely to accommodate a patch.

## Keep the handbook accurate

When a command, report format or owner workflow changes, update its project documentation and the relevant handbook chapter together. Link the exact implementation revision. Distinguish established behavior from proposals and examples. Keep recurring tool failures in issues; avoid permanent running diaries of agent activity in public source.

A new agent should finish each handoff with changed files, evidence, checked revision/results, unresolved findings and review/publication state. “Implemented,” “reviewed,” “CI passed,” “owner cleared,” “merged” and “live” are different states.


---

# Starter kit

A clean handoff for a new project, without pretending the game-specific build already exists.

## Download and read

- [Repository starter files](/wiki/downloads/repository-starter.zip) — README, AGENTS, CONTRIBUTING, setup checklist, PR template and .gitignore examples.
- [Report schema](/docs/reporting/schema/report-v1.schema.json) and [project configuration schema](/docs/reporting/schema/project-v1.schema.json).

The starter files contain visible placeholders. Fill them and review them with the owner before adoption. They do not contain a compiler, original game data, a functioning generic CI pipeline, or working multi-game reporting adapters. Do not claim setup is complete because the files were copied.

## Prompt for a fresh agent

```text
Read this handbook and this project's README, CONTRIBUTING and AGENTS files.
Inspect the existing repository before editing; preserve unrelated work.
Use a dedicated branch and checkout/worktree.

First establish:
- Owner, repository slug, target platform/region/revision and executable hash.
- Authorized reference inventory and missing evidence/tool access.
- Approved build environment, compiler/linker profiles and baseline status.
- Existing CI, review rules, attribution policy and public reporting capability.

Adapt the starter files to verified project facts. Keep placeholders explicit.
Build a bounded implementation plan with acceptance evidence for each stage.
Do not assume NFL's compiler flags, layout, source boundaries or target IDs apply.
Retain useful partial source and measure it honestly.
Keep original binaries, bulk debug exports and experiments out of public Git.
Do not change private dependency access, push, open PRs, publish, or merge without
appropriate authorization. Only the documented project owner merges main.
Distinguish implemented behavior, verified results, proposed work and blockers.
```

## New-project acceptance record

| Stage | Evidence to record |
| --- | --- |
| Identity | Owner, platform/region/revision, original executable hash |
| References | Parsed input inventory, reference hashes, missing evidence |
| Baseline | Pinned tools, command, full-output comparison and tested revision |
| Source build | Accepted ranges/profiles and complete-target validation |
| Comparisons | Registered partial/exact functions, method, extent and receipt checks |
| Reviews | Independent coverage, final revision, resolved findings |
| CI | Real successful and intentionally failing runs; required check configuration |
| Optional credits | Declared policy, provenance coverage, exact-inventory reconciliation |
| Reports | Supported fields/modules, semantic validation and decomp.dev parity |
| Site | Verified package, no fixtures, direct routes, freshness and rollback |

Do not prefill results or sign off another person's review. A missing stage remains pending with an owner and next action. Establish the first valid baseline before taking on broad reconstruction.

## Reference implementation

Start from the [NFL README](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/README.md), [contribution policy](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/CONTRIBUTING.md), [agent instructions](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/AGENTS.md), [evidence specification](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/README.md), [target mechanics](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/GN7E69/README.md), [build workflow](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/.github/workflows/baseline.yml) and [review workflow](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/.github/workflows/review.yml). These are pinned examples of a working project's architecture, not permission to copy its assumptions into another game.

The website-side NFL adapter is documented in [Website](/wiki/website-integration/) and the [NFL integration reference](/docs/reporting/nflstreet2.md). New-game agents can follow its acceptance checks, but must implement their own report mapping and trusted producer policy before registering a production project.
