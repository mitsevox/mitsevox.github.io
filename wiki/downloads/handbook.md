# mitsevox project handbook

Reference snapshot: 2026-10-25. Project repository rules take precedence.

# Start here

A reusable structure for a decompilation repository, its CI and its place on the shared site.

Use this handbook to establish a new project or align an existing one. It defines repository responsibilities, naming conventions, evidence standards, validation stages, review records and the public report contract. Each project supplies its own target facts, tools and build commands.

## Follow the template

1. [Repository setup](/wiki/repository-setup/): identify the owner, target, approved inputs and supported environment.
2. [Layout & naming](/wiki/layout-and-naming/): organize source, declarations, evidence, configuration and generated output.
3. [Evidence](/wiki/evidence-and-reconstruction/): reconstruct from reproducible observations and preserve uncertainty.
4. [Build & validation](/wiki/build-and-validation/): distinguish baseline, accepted-source build and partial comparisons.
5. [Review & approval](/wiki/review-and-approval/): bind review and clearance to the actual revision.
6. [CI & publication](/wiki/ci-and-publication/): validate candidates, authenticate main results and publish coherent reports.
7. [Credits & history](/wiki/credits-and-history/): select attribution policy and preserve measured history.
8. [Website](/wiki/website-integration/): export the shared contract and choose the site's optional modules.
9. [Starter kit](/wiki/starter-kit/): fill the repository templates and give an agent the assignment.

An existing project can keep its working structure and commands. Map these responsibilities onto it instead of reorganizing source just to match a diagram.

## What belongs where

| Location | Responsibility |
| --- | --- |
| Game repository | Source, declarations, evidence, target configuration, build/comparison tools and report exports |
| Approved private inputs | Original executables, restricted tools, complete debug exports and private research |
| Shared website repository | UI, artwork, project registration, report adapters/validators, durable public reports and site deployment |
| PR and issue records | Task scope, reviews, tested revisions, findings and owner decisions |

The game produces measurements. The website validates and presents them through the shared design. Visitors need neither private game inputs nor GitHub credentials.

## Establish the project facts

Record the platform, region/revision, executable hash, source objective, approved build tools, supported hosts and exact local commands in README.md. Put contribution and matching-integrity rules in CONTRIBUTING.md, concise agent instructions in AGENTS.md, and evidence/configuration formats next to their tools.

A faithful matching reconstruction and a nonmatching port have different validation objectives. Declare which one the project promises and label its reports accordingly. Compiler equivalence alone does not establish original names, intent or source-file boundaries.

Attribution tracking, contributor rankings and accepting contributions are three independent choices. Progress reporting can operate without a contributor feed.

## Use the handbook with an agent

Give the agent this wiki, the repository and its current instructions. For site integration, also supply the shared site's report contract and registration access. The [starter prompt](/wiki/starter-kit/#prompt-for-an-agent) specifies the work without prescribing a particular game's implementation.

The agent fills project facts, adapts the template to established tools, implements missing checks and supplies evidence for the acceptance checklist. Unknown inputs remain explicit. A copied template is a starting structure; real successful and failing runs establish that the project works.

## Maintain the template

Keep this handbook reusable. Project targets, repository names, workflow revisions, run IDs, migration plans and one-off status belong in their project's records. Update the template when a reusable convention or public contract changes, and version any incompatible reporting change.


---

# Repository setup

Establish ownership, target identity and a safe working environment before the first reconstruction.

## Record the project identity

Choose a stable lowercase repository slug such as `game-slug`; use the same slug for its site route and reporting identity. Keep its display title separate. A second platform or revision is a separate target, not a silent replacement for the first one.

The README must identify the game, platform, region/revision, target executable hash, owner, supported host requirements, setup/build entry points and links to CONTRIBUTING and AGENTS. Use a full target hash; a filename or disc label alone is insufficient.

For an original executable, an initial local hash check can be:

```sh
# macOS
shasum -a 1 /path/to/original-executable
# Linux
sha1sum /path/to/original-executable
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

Distinguish backlog from active work. Before starting, check open PRs and active branches, then reserve a bounded current batch in an issue or draft PR with the functions/unit action, branch and shared-file dependencies. Do not reserve an entire subsystem or future batches.

Set a documented reservation timeout, such as 48 hours without a meaningful update. Renew with pushed work, concrete findings or an explicit handoff; release paused or abandoned scope. Before taking over expired work, inspect existing branches/PRs and preserve useful partial source and credit. An old backlog claim does not own the code. A live overlap needs coordination even when two tasks touch different functions in the same header, file or compilation group.

Record the chosen timeout and coordination rules in CONTRIBUTING.md so every contributor uses the same policy.

## Tool and reference access

Record required tools, versions, hashes, host architecture and installation instructions. Use the owner's approved build image or tool archive. A working compiler is not proof that its version and flags match the original; those claims need unit/library evidence.

List supported host operating systems and architectures. Document any compatibility wrappers or translation layers alongside the exact tool versions that require them.

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

Use this layout for a new repository. In an existing repository, retain established paths and map these responsibilities onto them. Define and validate the formats of target configuration, accepted placements, comparisons and evidence. Optional contributor ledgers and history checkpoints belong alongside target configuration.

## Naming rules

- **Original names:** preserve spelling and case when target evidence supports them. Keep the evidence locator.
- **Descriptive names:** make them readable, but mark them inferred rather than claiming the original name was recovered.
- **Unknown code/data:** retain stable neutral address labels. Use a documented form such as `fn_XXXXXXXX` and `lbl_XXXXXXXX` with uppercase hexadecimal digits; these receive no named-function credit.
- **Files:** use recovered source paths when established. A descriptive filename can count as named while its original boundaries remain provisional.
- **Tools/docs:** use consistent repository conventions; Python tools commonly use `snake_case.py`, handbook pages use `kebab-case.md`.
- **Site assets:** use stable project slugs, for example `assets/covers/game-slug.webp`. Store display names separately from paths.

Do not invent a source-file split merely to produce a pretty map or increase file counts. Shared headers should have one accepted definition per type/address. Search existing declarations and current main before introducing another layout.

## Source and partial reconstruction

Useful incomplete functions stay in normal source files. Register their measured ranges separately. When accepted and draft bodies coexist, select draft bodies through a documented comparison configuration or guard. Promotion updates accepted placement and removes obsolete selection metadata while keeping the source in place.

Keep source comments about intent, invariants and non-obvious relationships. Matching scores, compiler experiments, agent notes and review history belong in metadata or PR records. Unsupported field meanings stay unresolved; unaccessed regions stay opaque.

## Public and private material

Public Git should contain reviewed source, tools, curated evidence and bounded public reports. Keep original game binaries, generated objects, complete debug exports, private analysis databases and discarded trial variants out. A .gitignore entry does not remove a file already tracked; inspect the index before committing.

Do not copy absolute paths from another contributor's machine into shared configuration. Commands should accept a local reference path or use a documented owner-approved environment.

## Evidence format

A simple evidence ledger can use one claim per TSV row:

```text
kind  start  end  subject  origin  start_boundary  end_boundary  evidence
```

The separators are tabs. Addresses are hexadecimal and end-exclusive. Use `-` where unknown or inapplicable. Origins distinguish `target`, `signature`, `related` and `inferred`; boundaries independently distinguish `exact`, `provisional`, `open` and no claim. Use separate rows for a name, function extent, field layout and source-unit boundary—one claim must not silently prove another.

The project’s `config/README.md` defines the vocabulary, allowed claim types and validation rules. Version that schema and provide a validator before CI relies on it.


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
| Different instruction selection or scheduling | Controlled compiler experiments and relevant compiler intermediate output |
| Competing behavioral interpretations | Bounded debugger/runtime trace with known inputs and conditions |
| Candidate SDK reuse | Fingerprints followed by calls, globals, types and boundary checks |

Record tested revision, tool version/settings, inputs, conclusion and remaining uncertainty. Check decompiler output against instructions. Runtime observations establish what happened under those conditions, not the original source text. Keep bulk experiments private; retain concise reproducible evidence publicly.

## Matching integrity

Do not force a match through patched output, embedded instruction bytes, unsupported inline assembly, per-function flag changes, altered comparison boundaries or excluded mismatches. Do not invent helpers, padding, casts, volatile qualifiers or control flow solely for code generation.

Compiler exceptions require original-scope evidence and explicit owner approval under the project's documented policy. Originally handwritten assembly needs provenance. Labeling a workaround “fake match” does not make it acceptable.

When evidence runs out, preserve the useful partial reconstruction and document the gap. Keep original bytes in the verified linked build until replacement is validated. Partial similarity is useful progress; unsupported certainty is not.

## SDK and imported work

Retain origin, source revision, license/provenance and local modifications. A fingerprint is a candidate, especially for short functions. Inspect target-specific calls, data ownership and compilation boundaries before import. Imported code receives the same relevant fidelity and hostile reviews as new reconstruction.

Record these matching-integrity and investigation rules in CONTRIBUTING.md. Keep evidence-format details and reproducible locators in target configuration.


---

# Build & validation

Define reproducible stages with explicit inputs, outputs and failure conditions.

## Validation stages

| Stage | Required result | Recorded evidence |
| --- | --- | --- |
| Input verification | Authorized executable and required references match declared hashes | Target/hash and input inventory |
| Original-byte baseline | Extraction, placement and relink reproduce the complete target where applicable | Tool identities, geometry and complete-output comparison |
| Accepted-source build | Accepted source replaces its declared ranges while the complete build satisfies the project's objective | Source/configuration tree, placement and build receipt |
| Independent comparisons | Registered functions/data receive full-extent exact and fuzzy measurements | Extents, dependencies, method and comparison receipt |
| Public export | Summaries and supported modules derive from those same measurements | Manifest, checksums and semantic-validation result |

Implement applicable stages for the target's executable format. Document any stage that cannot be supported and its effect on the claims the project can make.

## Command contract

The README must give a concrete command for each implemented stage. Keep local and CI commands aligned. Names may follow the repository's existing tools; the responsibilities remain consistent.

| README entry | Inputs | Expected output |
| --- | --- | --- |
| Setup | Approved tool versions and hashes | Usable pinned tools |
| Baseline | Verified original input and target configuration | Complete baseline comparison and receipt |
| Build | Accepted source, headers and placement/profile configuration | Reproducible target output and receipt |
| Compare | Registered source, full target extents and approved profiles | Exact/fuzzy comparison report |
| Validate | Evidence, configuration, reports and dependencies | Nonzero exit on invalid or stale inputs |
| Export | Validated measured report and prior history | Public package conforming to the site contract |

The template intentionally does not assume a compiler, executable format or build system. Adapt these entries to the tools already used by the project; do not add duplicate build paths solely to rename commands.

## Target and tool identity

Record executable hash, section sizes/addresses, entry point and measurement universe. Preserve unassigned ranges. Document placement, alignment, small-data and relocation rules where applicable.

Pin usable compilers, linkers, wrappers and comparison tools by version and hash. Record evidence for unit/library profiles separately. A successful diagnostic compile establishes compatibility under those conditions; it does not uniquely identify the original compiler.

## Partial reconstruction

Keep useful incomplete bodies in normal source files. Register source path, full target extent, profile and dependencies separately. Compare the complete produced body; do not truncate a mismatch or adjust boundaries to improve a score.

When accepted and draft code coexist, use a documented comparison configuration or guard. Preserve original linked bytes until replacement is validated. Fuzzy coverage describes measured similarity and does not grant exact-function credit.

## Promotion

After review and validation, update accepted placement, remove obsolete comparison selection and verify the complete output. Keep source paths and original attribution stable. Prevent accepted ranges from being counted again through independent comparisons.

Exact function status requires the complete declared extent to match. Exact file status additionally requires original boundary evidence and exact constituent content. A descriptive filename can count as named while its boundaries remain provisional.

## Receipts and stale results

Bind results to target hash, source revision/tree, relevant source/header/configuration hashes, tools, profiles and comparison method. Reject a receipt when any required input has changed. A build cache can accelerate work but cannot establish correctness.

Validate wrong target, missing dependency, overlapping ranges, missing symbol, changed extent, unsupported placement and corrupt report through meaningful failure cases. Test the code that decides validity rather than reproducing its implementation in assertions.

Run focused checks during iteration and required final checks for the actual integrated inputs. Broaden testing when a changed dependency, failure or coverage gap justifies it.


---

# Review & approval

Independent evidence, exact revisions and an owner-controlled merge decision.

## Contribution sequence

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


---

# CI & publication

Build once, validate the result, then publish an authenticated report.

## Workflow structure

Use separate jobs for the responsibilities below. Map the commands to the repository's documented build tools.

| Job | Runs when | Work | Permissions |
| --- | --- | --- | --- |
| Configuration and evidence checks | PRs and main | Validate target configuration, declarations, evidence and changed dependencies | Source read |
| Build and measure | PRs and eligible main runs | Verify inputs; build/compare; generate a candidate report and receipt | Source/packages read; approved private inputs only |
| Review clearance | Relevant PR changes | Check revision, required review records and owner decision using trusted code | Read PR records; write its named status |
| Report publication | Successful eligible main result | Authenticate the measured tree, validate prior history, export public data | Read artifacts; narrowly scoped history/report writes if needed |
| Website validation | Site PRs and refreshes | Authenticate/import reports and assemble a coherent site candidate | Public source/artifact read |
| Website deployment | Successful current site main | Preserve accepted reports, then deploy the exact candidate | Site data-store writes, Pages and deployment identity |

Game build jobs do not need website deployment permissions. Publishing jobs process report data without executing scripts downloaded from artifacts. Keep private originals, complete debug exports and build credentials out of the website job.

## PR validation

Run the project's required baseline, accepted-source and comparison stages for the actual candidate inputs. Cheap checks should fail before expensive work where possible. Delete stale output before export; a failed exporter must not leave an earlier report available for upload.

Emit a candidate artifact containing public measurements and a receipt binding repository, target/hash, full tested revision/tree, tools, methodology and payload checksums. Candidate artifacts support review; they do not advance public latest or the production timeline.

Pin Actions/shared tools to reviewed commits, images to approved digests and downloaded tools by version/hash. Cache keys include target, toolchain, relevant configuration and source inputs. Document the cache's scope and invalidation rules.

## Main validation and reuse

A main publication must have either a successful full validation or authenticated proof for the complete landed tree. Reuse requires matching target, tools/environment, methodology, complete tested inputs and original artifact integrity. Validate landed attribution too when the project's policy enables it.

A missing or incompatible reusable proof requires the full validation path. An inventory-only change can regenerate inventory separately when source-build proof remains valid. Never combine reports from several independently tested branches into proof of an integrated build.

Keep original measurement time separate from publication time. Latest repository commit metadata is another input and does not make a previous build newly measured.

## Publication sequence

1. Select an eligible successful main run and its actual attempt.
2. Authenticate repository, workflow revision, job/lane, tested tree and artifact digest.
3. Restore validated prior history; an established history must not reset after a fetch/parse failure.
4. Generate the public package from measured input and validate schema, arithmetic, extents, capabilities and history continuity.
5. Store immutable snapshot files before updating the latest pointer atomically.
6. Preserve the accepted package before deploying the matching website artifact.

An identical rerun is a no-op. Different bytes for an existing immutable identity fail. A correction needs a new version/generation and recorded provenance. Check ancestry before advancing latest; concurrent job ordering alone cannot prevent stale publication.

The shared website owns a durable data-only report store so accepted measurements outlive temporary CI artifacts. Individual projects can retain their existing history/archive mechanism. A separate data branch in each game repository is optional.

## Failure behavior

| Failure | Required behavior |
| --- | --- |
| Missing or malformed required report | Fail the refresh and keep the prior accepted package |
| Unsupported optional capability | Declare it unsupported and configure its UI off |
| Failed export of a supported capability | Fail; do not silently change it to unsupported |
| Stale or diverged measured revision | Reject promotion and retain history |
| Existing immutable identity with changed content | Reject the collision |
| Concurrent store writer | Reread and reconcile after a normal push conflict; never force overwrite |
| Obsolete site-source workflow | Reject deployment |
| Missing private build access | Report the missing input; do not change dependency access or substitute tools |

Define whether a refresh failure blocks the whole site deployment or allows other validated projects to publish. Test and document that policy explicitly. In either case, a failed project retains its last-good data.

## Workflow security and approval

Evaluate clearance using trusted base/default-branch logic. PR text, payload JSON and filenames are data, not commands. A privileged follow-up workflow must authenticate its upstream execution before using its artifacts. Declare how fork contributions receive build validation without assuming private secret access.

See GitHub's [secure workflow guidance](https://docs.github.com/en/actions/reference/security/secure-use) and [workflow_run behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run). Configure required statuses after real passing, failing and stale cases have been observed; a workflow file alone does not enforce approval.

## Website deployment

Build one static artifact with fingerprinted assets. The deploy job depends on successful validation and storage and receives only the permissions it needs. GitHub Pages supports [custom Actions workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Verify home, direct project/wiki routes, refresh, back/forward and the selected report identity at the public URL. Use a reviewed site-source revert for a UI rollback while retaining current accepted measurement history. Do not deploy an obsolete workflow or rewrite measured history to roll back styling.


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

Choose the tracking policy when the repository is established; site integration does not impose function-level attribution. If tracking is disabled, mark the contributor capability unavailable and keep rankings off; enabling accurate rankings later may require reconstruction that is not fully possible.

## Function-credit model

Credit follows the original source contributor, not the person who merges or batches the PR. Store stable function extents, original contribution references, original revision/source blob and integration provenance as required by the ledger. Retain the original identity when imports are corrected or squash-merged.

The ledger covers complete exact functions, including exact unlinked comparisons. Fuzzy source retains provenance without exact-function credit. Promotion creates no duplicate credit. Retired or no-longer-exact functions leave current exact totals while their provenance remains recorded.

Explicit joint credit is allowed: each person receives that function once. Personal totals can therefore overlap; the union of credited functions, not the sum of personal counts, must equal the exact inventory. Sort current distinct function counts deterministically.

## Before submitting a tracked contribution

Open the authorized draft PR to obtain its real number; never guess a future PR number. Record its actual original/integration references and validate the complete ledger against the candidate exact inventory. For a batch, use the actual batch PR as integration metadata while preserving original authorship.

Validate the introduced source blob in reachable landed history. If squash merging is supported, check the actual landed or predicted squash tree against the PR base. Pinned original commits must be accessible; missing provenance is a validation gap, not a reason to attribute the function to the integrator.

## Recovering past credit

Use surviving original PRs, commit authorship, pinned source blobs, integration records and reviewed evidence. A closed PR or deleted branch may still leave useful records; do not assume they are available indefinitely. Distinguish supported attribution, explicit joint work and unresolved ownership.

Keep a bounded recovery record explaining each decision and uncertainty. Do not give every function to the current file author or merger. If a project promises complete exact-function attribution, unresolved gaps block that capability's publication until resolved or the owner explicitly changes the policy.

## Timeline continuity

Keep full commit identity, target, methodology, raw totals/denominators and evidence quality. Preserve measured, reconstructed and inherited legacy entries distinctly. A new inventory can change a percentage without source regression; make the basis change explicit rather than smoothing the graph.

Restore prior verified history; do not use an unauthenticated live page as automatic recovery evidence. An intentional checkpoint recovery needs a documented audit. Latest repository commit metadata is separate from the latest measured build, even when the header displays both near each other.

Document the selected credit policy, ledger schema and recovery procedure in the repository. Publish contributor data only when that policy can be validated.


---

# Website

Export a versioned public report and register it with the shared renderer.

## Responsibilities

| Game repository | Shared website |
| --- | --- |
| Defines target/hash, approved tools and validation objective | Owns the shared layout, navigation, styling and interactions |
| Produces source-derived measurements and execution evidence | Authenticates imports and validates the public contract |
| Maintains supported map, inventory, history and credit data | Stores accepted snapshots and selects one exact package per project |
| Documents build/export commands and capability policy | Registers projects, selects modules and publishes the static site |

Use the repository's existing structure and build tools. The integration boundary is the public report contract. A site adapter translates the project's actual export into that contract and the renderer's view model; game code does not need to adopt another project's compiler, source paths or internal ledgers.

## Project identity and presentation

Choose a stable lowercase slug. Use it consistently in report identity, `/games/<slug>/`, project registration and artwork names. Keep display title, console, target ID/hash and repository URL explicit. Different targets must not silently replace each other's histories.

The shared site renders each project using the same header, gutters, code/data bars, metric rows, map controls, tooltips, timeline and contributor style. Register data and capabilities through the shared renderer rather than copying a standalone page per game.

Store cover artwork as `assets/covers/<slug>.webp` with the original aspect ratio. Use authorized artwork and retain required license/provenance notes. The latest commit title/time is independent of measured build progress.

## Required public contract

Use the [manifest schema](/docs/reporting/schema/report-v1.schema.json), [project configuration schema](/docs/reporting/schema/project-v1.schema.json) and [metric definitions](/docs/reporting/contract-v1.md). A producer and its site adapter must agree on schema and methodology versions before registration.

A package contains a manifest, a validated summary, an execution receipt, and JSON assets for each supported module. Paths are package-relative and checksummed. Keep raw public measurement output available for parity checks. A manifest or valid checksum alone does not authenticate a build.

| Manifest group | Required content |
| --- | --- |
| Identity | Project/repository, platform, target/hash, full measured revision and source tree |
| Method | Methodology, generation and pinned tool identities |
| Time | Measurement time and publication time separately |
| Summary | Raw code/data totals, linked/exact bytes, independently supported fuzzy coverage and optional inventories |
| Validation | Full/reused mode, run/attempt, workflow revision and checksummed receipt |
| Modules | Each optional capability declared supported with a typed asset, or unsupported with a reason |

Receipts bind the public files to the producing execution. The consumer verifies repository/workflow/job identity, success, attempt, target/tree, artifact digest and main eligibility against its trusted producer policy. Never execute a report package.

## Measurement rules

| Metric | Meaning |
| --- | --- |
| Linked | Source-produced bytes incorporated into the validated target build |
| Matched | Exact measured bytes, including eligible unlinked comparisons |
| Fuzzy | Target-size-weighted similarity; null when unsupported |
| Functions exact / named | Complete exact extents / names accepted under the naming policy |
| Files exact / named | Exact original boundaries and content / descriptive source groups, including provisional groups |

Derive percentages from raw totals. Keep code and data denominators stable and account for all declared ranges. Linked, matched and fuzzy overlap; never add them. Preserve the actual relationship between linked and matched under the project's promotion policy.

A function fragment cannot earn full-function exactness. A compiled unit marked complete does not establish an original file boundary. Address labels do not count as descriptive names. Support code and data fuzzy independently; never copy one into the other or label a fallback as measured fuzzy progress.

## Choose modules independently

Presentation settings belong in the site's project registration, such as `config/projects.json`:

```json
{
  "schemaVersion": 1,
  "slug": "game-slug",
  "title": "Game title",
  "console": "Console name",
  "artwork": {
    "cover": "/assets/covers/game-slug.webp",
    "width": 640,
    "height": 900
  },
  "repository": "OWNER/REPO",
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

Replace identity placeholders with verified facts. Enable a module only when the producer supplies data validated by its adapter. A disabled module leaves no heading, empty space or section listeners. Shared payloads can still serve another enabled module, but a timeline must not require contributor data and summaries must not require an invented map.

Attribution tracking, contributor rankings and accepting contributions are independent. `contributions.accepting: true` adds the Contribute button and lower contribution section and requires an HTTPS `guideUrl`. It does not enable tracking or rankings.

Unsupported data remains unavailable. Valid zero stays zero. If a supported export unexpectedly fails, retain last-good data and report the failure instead of silently hiding the capability.

## Producer template

1. Run the project's documented validation and comparison commands.
2. Export raw byte measures and supported modules from the same measured inputs.
3. Validate ranges, recursive totals, complete function extents and inventory policy.
4. Restore history and append the measurement without rewriting existing records.
5. Reconcile contributor evidence only when the selected tracking policy requires it.
6. Generate the versioned manifest, payload checksums and execution receipt.
7. Upload only public JSON after all required checks pass.

Do not upload original binaries, object code, complete debug exports, credentials or private experiment files. Retain the existing decomp.dev feed where used; compare fields supported by that format against the same raw measurements.

## Consumer template

1. Register a trusted producer policy and an adapter for the export format.
2. Select a successful eligible main execution and authenticate its actual artifact.
3. Parse a bounded, exact allowlist of public files; reject unsafe paths, links and malformed values.
4. Validate schema, target/revision, arithmetic, optional modules and raw-report parity.
5. Check the new package against prior accepted history and Git ancestry.
6. Install immutable files and atomically update only this project's lock entry.
7. Build one coherent static site from the selected locked packages.
8. Preserve accepted snapshots in durable storage before deployment.

Keep project-specific field translation inside the adapter. The website owns shared contract validation, storage and rendering. An import must preserve every other project's lock and snapshots. A report's strings must not select arbitrary executable code.

Consumers may reuse an identical previously authenticated package after temporary upstream artifacts expire. A changed or previously unaccepted package still needs original execution proof. Latest commit metadata never changes the selected measurement identity.

## Register and use the platform

The site owner registers a producer in `config/producers.json` and its presentation in `config/projects.json`. Producer policy and artifact data follow the shared versioned schemas. A conforming producer uses the common importer and renderer; adding a project does not require a separate site implementation. Artwork stays in the website repository.

The [platform contract and commands](/docs/reporting/platform.md) specify the public input files, packager metadata, producer policy, full/reused execution lanes, import CLI and preserved historical policies. These are shared interfaces; the project supplies its own measured inputs and approved execution facts.

```sh
uv run --locked python tools/import_reports.py --project game-slug --run RUN_ID
uv run --locked python tools/build_site.py --output build/new-candidate
```

## Integration acceptance

| Area | Required evidence |
| --- | --- |
| Producer | Successful validated main result with target, source/tree, tool and artifact identities |
| Summary | Raw total/linked/exact parity; correct independent fuzzy support |
| Optional modules | Enabled modules work; absent map/count/history/credits do not create empty sections or fake data |
| History and storage | Existing records survive, identical reruns are no-ops, stale/diverged updates and immutable collisions fail |
| Isolation | Updating or failing one project preserves the other projects' accepted data |
| Build | No fixtures or private files; exact lock selection and fingerprinted assets |
| Browser | Shared styling, direct route/refresh, navigation, hover and map behavior |
| Publication | Public page and manifest agree; the next refresh preserves the same accepted state |

Record commands, revisions, run/attempt, artifact/package hashes, module settings and limitations in the integration PR. The [integration checklist](/docs/reporting/onboarding.md) and [starter files](/wiki/starter-kit/) provide a reusable handoff. Each repository supplies its own implementation details.


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

Repository scaffolding and an agent prompt for applying this handbook.

## Files

Download the [repository starter archive](/wiki/downloads/repository-starter.zip). It contains README, AGENTS, CONTRIBUTING, setup checklist, PR template, .gitignore examples, an integration checklist and an agent prompt.

Fill visible placeholders from verified project facts. The files define responsibilities and conventions; the project supplies its own compiler, build system, evidence formats, CI commands and report adapter. Existing repositories keep their established paths where those responsibilities are already implemented.

## Prompt for an agent

```text
Read this wiki and the project's current README, CONTRIBUTING and AGENTS.
Use its structure as the template for repository layout, naming, evidence,
validation, review, CI, public reporting and shared-site integration.
Inspect the existing project before editing and preserve unrelated work.
Use a dedicated branch and checkout/worktree.

Record the actual target/hash, approved toolchain, build commands, source
objective, current validation and supported report capabilities. Adapt the
handbook's responsibilities to this project's established structure.

Implement missing pieces needed for a reproducible build, honest exact/fuzzy
measurements, versioned public reports, preserved history and site integration.
Keep contribution acceptance, attribution tracking and rankings independent.
Use the shared report contract and renderer rather than a separate game UI.

Validate real inputs and both success/failure paths. Retain useful partial
source. Do not invent metrics, evidence, authorship, approval or test results.
Follow the project's task authorization for pushes, PRs, publication and merge.

Deliver the changes with commands, tested revisions, artifacts, capability
settings and remaining limitations. Verify the public route and next refresh
before declaring the site integration complete.
```

## Acceptance checklist

| Stage | Evidence |
| --- | --- |
| Identity | Owner, source objective, platform/region/revision and executable hash |
| Structure | Source, declarations, configuration, evidence, tools and generated output are discoverable |
| Tools | Approved versions/hashes, supported hosts and reproducible setup |
| Baseline and build | Applicable complete-target checks and accepted-source result |
| Comparisons | Full extents, profiles, dependencies and exact/fuzzy measurements |
| Review | Scope-appropriate independent coverage, actual revision and resolved findings |
| CI | Documented command mapping; real passing/failing/stale cases; appropriately scoped permissions |
| Credits | Explicit policy, with evidence reconciliation when enabled |
| Reports | Validated shared manifest, raw parity, supported modules and execution proof |
| History | Durable continuity, idempotence, ordering and recovery |
| Website | Shared presentation, configured modules, direct route, deployment and subsequent refresh |

The [integration checklist](/docs/reporting/onboarding.md) repeats the producer/consumer boundary and completion checks in one handoff. Keep project-specific commands and decisions in that repository, not in this generic template.
