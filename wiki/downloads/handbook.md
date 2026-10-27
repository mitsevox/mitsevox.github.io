# mitsevox project handbook

Reference snapshot: 2026-10-25. Project repository rules take precedence.

# Start here

A reusable structure for a decompilation repository, its CI and its place on the shared site.

Follow this handbook from an empty repository to its first verified build and site report. It defines repository responsibilities, naming conventions, evidence standards, validation stages, review records and the public report contract. Each project supplies its own target facts, tools and build commands.

## Follow the template

1. [Repository setup](/wiki/repository-setup/): identify the owner, target, approved inputs and supported environment.
2. [Layout & naming](/wiki/layout-and-naming/): organize source, declarations, evidence, configuration and generated output.
3. [Evidence](/wiki/evidence-and-reconstruction/): reconstruct from reproducible observations and preserve uncertainty.
4. [Build & validation](/wiki/build-and-validation/): distinguish baseline, accepted-source build and partial comparisons.
5. [Agent workflow](/wiki/agent-workflow/): scope, isolate, investigate, reconstruct and deliver without losing evidence or authorship.
6. [Review & approval](/wiki/review-and-approval/): adopt the project policy and bind review and clearance to the actual revision.
7. [CI & publication](/wiki/ci-and-publication/): implement fresh validation and the editable workflow's stage contracts.
8. [Cache & proof](/wiki/cache-and-proof/): optionally add inventory reuse, audited build caches and PR-to-main proof reuse.
9. [Credits & history](/wiki/credits-and-history/): select attribution policy and preserve measured history.
10. [Website](/wiki/website-integration/): export the shared contract and choose the site's optional modules.
11. [Starter kit](/wiki/starter-kit/): fill the repository templates and give an agent the assignment.

An [optional appendix](/wiki/existing-projects/) covers pre-existing repositories and legacy data. It is separate from this new-project setup path.

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

## Fixed contracts and project decisions

The fixed reporting boundary is the versioned public contract, authenticated execution, honest metric meanings, optional-capability declarations and history preservation. The site owner curates registrations and artwork. A new project uses the common importer and renderer rather than a copied game-specific website pipeline.

The project chooses its console/executable format, tools, supported hosts, source layout, evidence vocabulary, build commands, promotion objective and review/merge policy. Owner-only merging with independent accuracy and hostile reviews is the starter default; the owner can adopt a different documented model. Attribution is optional. Caching and publication reuse start disabled until fresh validation works.

The starter supplies an editable GitHub Actions workflow, configuration example and exact adapter interface. It cannot supply a target's extraction, compiler profile, linker geometry or disassembly interpretation. An implementing agent maps those contracts to the project's real tools, tests them and records unresolved gaps. It must not replace missing implementation with successful no-ops.

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

Before adopting the starter, have the owner settle the following decisions and record them in README/CONTRIBUTING and `config/ci.json`:

| Decision | Starter default | Must be supplied or confirmed |
| --- | --- | --- |
| Target/objective | Faithful matching, explicit target identity/registry | Console, executable format, region/revision, hashes, measurement universe and any different objective |
| Tools/runtime | Pinned approved environment | Actual digest/hash, supported hosts, tools/profiles and reference access |
| Author workflow | Isolated branch/worktree and bounded active scope | Branch convention, reservations, dependencies and push/PR authority |
| Review/merge | Independent accuracy and hostile review; owner-only merge | Adopting owner and any explicit alternative policy |
| Attribution | Explicit decision required | Track or do not track; exact inventory/joint-credit rules if enabled |
| Acceleration | All caches and proof reuse disabled | Enable each only after fresh correctness and failure tests |
| Site capabilities | Honest supported data only | Map, counts, timeline, rankings and independent contribution acceptance |
| Publication | Validated main reports through shared site | Artifact retention, trusted workflow/tool identities and durable history source |

No project names, compiler family or console-specific directory conventions are inherited from another repository. The templates describe responsibilities; the adopted configuration records facts.

Start with README, CONTRIBUTING, AGENTS, .gitignore, target configuration and a bounded build plan. Select and document licensing/provenance appropriate to your own tooling and imported sources; do not blanket-relicense imported code. The [starter files](/wiki/starter-kit/) provide editable scaffolding, not a build system.

Initialize an empty local repository without publishing it:

```sh
mkdir game-slug
cd game-slug
git init -b main
git switch -c work/bootstrap
```

Inspect staged files before the first commit. Generated objects, originals and research dumps should never enter the commit. Create the hosted repository and configure access only when the owner authorizes those actions.

## Work in isolation

Once the repository has an established main branch and origin:

```sh
git fetch origin
git worktree add ../game-slug-task -b work/task-name origin/main
cd ../game-slug-task
git status --short --branch
```

Choose one branch convention at setup; the example uses `work/<task>`. Branch names identify tasks, not approval or author identity. Use isolated checkouts, bounded reservations and explicit push/PR authority. The starter validates contribution PRs without an agent-prefix restriction and runs push validation on its adopted main branch. Existing branch/trigger adaptation is optional appendix material.

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
      contributors.json    # optional original-source attribution
      history.json         # optional reviewed history checkpoint
    ci.json                # adopted CI policy and stage mapping
    producer.json          # approved public-report execution policy
  tools/
    project_ci.py          # thin adapter to existing tools; see starter CI.md
    ...                    # actual build, comparison and export implementations
  tests/                   # meaningful checks for those tools and contracts
  docs/                    # durable design and setup documentation
  .github/
    workflows/
      validate.yml         # fresh build first; optional audited acceleration
      review.yml           # trusted metadata-only clearance, if selected
    pull_request_template.md
  build/                   # ignored generated outputs
  scratch/                 # ignored experiments
```

## Generated output boundaries

Use stable role-based paths so stages cannot accidentally consume yesterday's successful output:

| Path | Contents and lifetime |
| --- | --- |
| `build/baseline/` | Original-byte baseline output/receipt; private and disposable |
| `build/source/` | Accepted-source executable, objects and complete-output receipt; private |
| `build/comparisons/` | Partial/exact comparison objects, linked slices and measurements; private |
| `build/inventory/` | Bounded reusable inventory metadata plus its input/digest receipt |
| `build/cache/` | Optional compile/measurement entries; approved cache storage only |
| `build/ci/` | Run context, lane selection and cache statistics; generated metadata |
| `build/public-input/` | Only canonical `summary.json` and supported public module JSON |
| `build/public-report/` | Validated manifest, execution receipt and allowlisted public payloads |

These are template names, not required engine paths. Document the actual mapping once. Every producer stage clears its owned stale output before work and writes success output only after verification. Upload the explicit public directory, never `build/**`. Public packages cannot contain original binaries, objects, compiler caches or complete debug exports.

Document each JSON/TSV schema next to its validator: required keys, address format, end-exclusive intervals, stable identities, enum meanings and version behavior. A path listed here does not invent a universal source-unit or evidence schema. The shared public schemas are the fixed boundary; target-internal schemas are project-owned.

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

## Explicit target layout

For revision-aware projects, place the registry at `config/targets.json` and target-specific
configuration at `config/<targetId>/`. Use the same ID for private `orig/<targetId>/` and generated
`build/<targetId>/` directories. Keep reusable source in the shared source tree; isolate actual
revision differences without duplicating the entire codebase. Git commit `revision` remains
separate from a disc's numeric `discRevision`. The
[report-v2 contract](/docs/reporting/contract-v2.md) gives exact schemas and CI/storage rules.


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

# Agent workflow

A repeatable assignment, reconstruction and delivery process, with project policy made explicit.

## Adopt the project policy first

The default is an isolated author branch, independent blind accuracy review, a fresh hostile reviewer, final-revision CI and owner-only merge authority. These are defaults for a new project, not assumptions an agent may silently impose on an existing one. Explicit project/task authorization governs actual merge authority; record persistent alternatives in CONTRIBUTING.md so future agents see them. The site contract does not enforce a reconstruction review model.

Record who can assign work, push, open PRs, review, clear and merge. Permission to implement does not automatically authorize publishing or changing repository settings. Attribution tracking, rankings and accepting contributions remain separate decisions.

## Intake and scope

1. Read README.md, CONTRIBUTING.md, AGENTS.md and configuration documentation. Inspect the actual checkout, current main, open PRs and active reservations.
2. Inventory authorized executables, symbols, debug information, maps, source references and tool access. Record what exists and what is missing; distinguish a searched location from a complete absence claim.
3. Identify one bounded question and scope: functions, data ranges, declarations, original units or tooling. Include affected shared files and dependent branches.
4. Reserve active work using the project's chosen mechanism. Establish a dedicated branch/worktree; preserve unrelated dirty work and prior useful partials.
5. Record the base revision, target/hash, evidence locators, applicable compiler profiles, deliverables, exclusions and task authorization in the issue or PR. Keep detailed experiments private.

For an integration task, additionally inventory current CI triggers, job permissions, build stages, cache trust, public outputs, history storage and site registration. Map existing tools onto the contracts in the [starter kit](/wiki/starter-kit/); do not replace working tools just to obtain the example filenames.

## Evidence before reconstruction

Establish behavior, boundaries, references, calling convention and accessed layouts. Distinguish recovered original names from descriptive inferred names and neutral unknown labels. Do not let a desired name or a high matching score decide the interpretation.

Escalate according to the unresolved question: static analysis for behavior/ownership, compiler intermediate output for code-generation questions, bounded runtime tracing for an execution hypothesis. State the question, inputs, tool settings, result and remaining uncertainty. An unavailable essential reference is a named gap, not permission to invent an answer.

Implement useful partial source in its normal location. Keep original bytes in the verified linked build until promotion. Register complete comparison extents, dependencies and the supported profile. Do not move unfinished functions into a separate source tree merely to distinguish their reporting status.

## Iteration and attribution

Run the smallest relevant build/comparison and self-check evidence, names, declarations, comments, boundaries and ranges. Preserve mismatches honestly. Matching-only flags, patched output, invented padding, unsupported assembly and excluded failing bytes are not a valid repair.

When tracking is enabled, register original contributors and source provenance. A source edit can invalidate a pinned blob even if the function's bytes still match: re-pin and check the actual final source. Run ledger-only checks before an expensive build; reconcile coverage against the measured exact inventory after comparisons. Fuzzy source retains provenance without full exact-function credit.

Keep pushes coherent. A new PR push normally cancels that PR's older CI. Tooling/profile changes have wider invalidation than ordinary source changes and deserve their own bounded change where practical.

## Independent review

For the default policy, supply the full revision, scoped source/headers, target evidence, extents, profiles, comparisons and existing validation artifacts. The accuracy reviewer first interprets target behavior without the author's proposed names/comments; then reconciles the interpretation. The hostile reviewer checks the evidence and integrity checklist independently.

Reviewer independence is about authorship and prior reasoning, not a different display name. Creating another agent does not automatically make its work independent. Do not fabricate a review record when no reviewer or evidence was available. Use the project's accepted reviewer arrangement and document limitations.

For the default all-agent arrangement, use reviewers that did not author/edit the scoped reconstruction or participate in its implementation decisions. Give them a fresh context containing the task, target evidence, relevant configuration and validation artifacts rather than the author's conversation/chain of reasoning. An accuracy reviewer first records its target interpretation without proposed names/comments or author conclusions, then compares that result with the submission. A fresh hostile reviewer examines the submitted source and evidence without inheriting the author's or accuracy reviewer's conclusions as its starting verdict.

Each review record declares reviewer identity/session, scoped authorship or prior involvement, supplied inputs, context isolation/blinding method, reviewed revision and independently reached findings. Reusing a model is allowed; changing models or logins is not proof of independence. An author fork carrying its full reasoning does not qualify merely because it has another agent ID. Focused rechecks by the original independent reviewer remain valid under the delta rules. If isolation is impossible or prior involvement exists, disclose it and follow the owner's adopted alternative; never assert an independent pass that did not occur. CI can check record fields and revisions, but cannot mechanically prove what context an agent saw or the quality of its reasoning.

Report findings with a location, evidence and required correction. Measured incompleteness alone is not a failed fidelity review. A useful partial may pass while its original bytes remain linked.

After a fix, the reviewer checks the finding and affected dependencies, carrying forward adequate earlier coverage. A new reviewer may use that record; replacement alone is not grounds to restart everything. Follow the [review record and clearance specification](/wiki/review-and-approval/).

## Refresh, batches and final revision

Fetch current main before final integration. Inspect the changed inputs, conflict resolutions and shared declarations; record the resulting head. Review the delta and affected dependencies, then issue final-head review records that cite carried-forward coverage. A prior verdict does not by itself cover a new head.

A batch preserves each original PR, author revision and review evidence. Reconcile shared metadata by stable identity, resolve overlaps, and validate the combined tree once. Independently passing component builds do not establish the combined build. Close originals as incorporated only after the combined change lands.

Distinguish these identities: the PR head is reviewed and cleared; the synthetic merge tree is usually what PR CI builds; the landed commit is what main publishes. Receipts bind the tested tree and both relevant revisions. Tree equality allows authenticated reuse across a squash; identical commit messages or file counts do not.

## Delivery and owner decision

Post concise separate review records for the actual final revision, resolve findings, and link successful final CI and measured artifacts. The owner then follows the selected clearance/merge policy. A reviewer returning SHIP has not authorized a merge.

After merge, verify the eligible main publication, report identity, prior history and subsequent site refresh. A green PR, a local preview and a deployed page are different evidence. End with changes, tested revision/commands, measured results, unresolved gaps and the precise review/publication state. Never add a running public diary of agent activity.

## Implementing this template with an agent

An agent setting up CI must deliver a command mapping, adopted policy, pinned environment, stage receipts, meaningful invalidation tests, report-v1 packaging and real successful/failing execution evidence. Start with fresh validation. Add caches and proof reuse only after that path works and the owner selects them. The [setup checklist](/wiki/starter-kit/#acceptance-checklist) is the handoff boundary; unchecked items must stay visible.


---

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


---

# CI & publication

Implement fresh validation first, then optionally accelerate it without changing what a published result proves.

## Responsibilities and authority

A matching project verifies the complete accepted-source executable against its declared target, measures full registered comparison extents, reconciles optional attribution, and derives public reports from those results. A different source objective needs explicit corresponding validation; it must not claim byte identity it does not establish. CI cannot prove original names, intent, types or file boundaries: source/evidence review remains separate.

Separate responsibilities and permissions; they need not be separate jobs. Keeping a dependent build/measure/export chain in one job avoids copying private build output between runners. Use separate privileged jobs/workflows where authority changes.

| Responsibility | Authority |
| --- | --- |
| Candidate validation | Source/packages read and approved private input access; no site deployment or repository write |
| Owner clearance, if selected | Trusted metadata-only logic; read PR records and write only the named status |
| Producer report publication | Read authenticated upstream artifacts; narrow history writes only when the selected storage needs them |
| Site import | Read registered public source/artifacts; validate packages without executing their contents |
| Site storage/deployment | Owner-controlled site main; preserve accepted packages before Pages deployment |

The [starter archive](/wiki/downloads/repository-starter.zip) includes `.github/workflows/validate.yml.template`, `config/ci.example.json` and `CI.md`. Copy/adapt the workflow and configuration, implement the documented adapter operations using actual project tools, and prove the acceptance cases below. Templates do not configure repository settings or compile an unknown target automatically.

## Triggers and lanes

The reference workflow assumes default branch `main`; change every branch/eligibility guard together if the project uses another name. It defaults to same-repository contribution branches. Forks need an explicitly designed reference/secret-access policy before their code runs with private build inputs.

| Event | Validation | Shared cache save | Public result |
| --- | --- | --- | --- |
| PR | Fresh full path, or valid input-keyed reuse when enabled | Never | Candidate only; reusable proof only if zero compiled/measured results reused |
| Main push | Authenticate eligible proof when enabled; otherwise full fresh validation/audit | After successful full main validation when caching is enabled | Validated report artifact for shared-site ingestion |
| Main manual, normal | Same selection/fallback as main push | No build-cache save | Validated main report |
| Main manual, explicit audit | Skip proof selection; force full fresh validation/audit | Yes when caching is enabled | Validated main report |
| Other-branch manual | Validation only | Never | No production publication |

Cancel superseded PR/branch runs; keep main runs uncancelled by the workflow's concurrency policy. Main still needs ancestry/current-state checks because queue order does not guarantee safe publication order.

Three internal decisions are independent: `full` means run source build/comparisons/tests/export; `inventory` means validate/regenerate inventory; `receipts` means run the host live-receipt re-export. Fresh validation sets all applicable lanes. Reused source proof can still require inventory maintenance. An audit request on another branch must not grant main publication or save rights.

## Step-by-step implementation

The adapter contract in starter `CI.md` specifies input/output paths, GitHub outputs and fail-closed behavior for every operation. Existing tools can keep their names; one thin adapter gives the workflow stable boundaries.

| Order | Operation | Result/failure boundary |
| --- | --- | --- |
| 1 | Checkout exact candidate with required history | Record PR head/base, actual checked-out commit/tree, repository, target and run/attempt |
| 2 | Validate configuration/evidence and runtime pins | Reject unknown target, missing tools/inputs, unsupported policy, placeholders and unsafe publication paths |
| 3 | Compute/restore optional inventory candidate | Restore is provisional; internal input/digest receipt must still validate |
| 4 | Select proof on eligible main unless auditing | Authenticated match selects reuse; unavailable/incompatible proof selects full |
| 5 | Decide full/inventory/receipt lanes | Strict booleans, explicit fresh default; inconsistent state fails |
| 6 | Ledger/provenance preflight if tracking enabled | Check recorded entries on candidate and predicted squash history before expensive work |
| 7 | Baseline/setup and optional build-cache restore | Verify original input/relink where applicable and prepare pinned tools |
| 8 | Build accepted source | Parallel independent compiles; deterministic placement/link order; complete target-objective check |
| 9 | Inventory and tool tests | Validate restored metadata or regenerate; run applicable regression tests |
| 10 | Measure comparisons | Full extents and declared method; validated reuse or fresh measurements; explicit cache statistics |
| 11 | Export from one measured result | Reconcile linked/exact/fuzzy, map, inventories, optional credits and restored history |
| 12 | Host receipt verification | Keep on full main and zero-reuse proof-producing PRs; other host tests still run |
| 13 | Promote selected proof, if reused | Recheck landed tree/attribution/history, preserve original measurement identity |
| 14 | Package and validate public JSON | Versioned manifest/receipt and checksums; no stale output or private files |
| 15 | Upload eligible artifact; save eligible caches | Only exact directories; explicit main/PR-zero-reuse guards |
| 16 | Shared-site import/storage/deployment | Authenticate actual successful run/attempt, preserve history and project isolation, publish one coherent artifact |

An early ledger check validates the existing ledger and Git provenance. It cannot establish coverage of exact functions not yet measured. The exporter later reconciles the complete measured exact inventory and, where selected, compares actual-candidate and synthetic-squash credit results. Disabling tracking records an explicit policy decision; it must not fabricate a contributor feed.

## Candidate and landed identities

On a typical `pull_request` build, GitHub checks out a synthetic merge commit. The API's PR head SHA, that tested commit/tree and the later landed commit are different identities. Record all relevant identities and merge parents; do not label a merge-tree measurement as a head-only build. See [GitHub event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).

A main publication requires successful full validation or authenticated proof covering the complete landed tree. Squash/rebase can change a commit ID without changing its tree; reuse is permitted only after verifying the full tree, target, tools, method and source execution. Never combine independently tested PR reports into an integrated build proof.

Review/owner clearance normally names the current PR head. CI evidence explains which integrated tree it tested. New source/build inputs invalidate earlier validation; review comments alone do not require another binary build.

## Fresh path and public contract

The fresh path is the required starting implementation. Baseline, accepted-source build and independent comparisons remain distinct. Do not report the complete executable as reconstructed simply because original bytes fill unpromoted ranges.

Delete owned stale output before each export/package operation. Generate `summary.json` and only supported module files under `build/public-input/`. Use the [shared packager and schemas](/docs/reporting/platform.md#package-a-producer-report) from an approved pinned site-tool revision. The metadata uses actual target/revision/tree, method/generation, tools, run/attempt, workflow blob and separate measurement/publication times.

Upload the exact resulting `build/public-report/` files as the policy's declared artifact. On PRs it is evidence only; it does not advance public latest or the durable timeline. The website does not run the game compiler, rebuild the binary or execute downloaded scripts.

Register common required steps only when they succeed on every published lane. Put full-build steps in `lanes.full` and proof-authentication steps in `lanes.reused`. Exactly one lane must succeed. Proof selection is a decision step, not a mandatory success on an audit that deliberately skips it. Approve the actual workflow Git blob after inspecting the adopted YAML; editing a trusted workflow requires a reviewed policy update.

## Optional acceleration

Follow [Cache & proof](/wiki/cache-and-proof/) for key construction, shadow dependencies, main-only saves, fresh disagreement audits, bootstrap and complete-tree reuse. Keep acceleration disabled while establishing correctness. Then test inventory reuse, build caches and publication reuse separately.

A warm-cache PR may be faster but causes a fresh main rebuild under this trust model. A cold zero-reuse PR can be slower but give main a reusable proof. Quote observed hosted timings with run/attempt and hit counts; do not inherit another project's duration as a promise.

## History and publication

1. Restore previously accepted history from authenticated storage. A fetch/parse failure must not silently create empty history.
2. Authenticate full or reused execution, including original artifact where required.
3. Validate report schemas, arithmetic, extents, enabled attribution and continuity. Keep original measurement time separate from publication and latest repository commit times.
4. Upload immutable public report artifacts only after applicable checks pass.
5. The shared site authenticates/imports the selected package, installs immutable snapshots and atomically advances only that project's pointer after ancestry checks.
6. Preserve accepted packages in durable site storage before deploying the exact static candidate.

Temporary Actions artifacts are not a durable timeline. An identical rerun is a no-op; conflicting bytes for an existing immutable identity fail. Retain historical policies/schemas when changing producers. Use a new method/generation for a justified measurement change without rewriting old rows.

The current shared site attempts each registered refresh, retains a failed project's last-good data, and blocks deployment if any refresh fails. Successful candidate imports do not imply that a mixed/failing candidate was deployed. A project-owned history archive is optional when durable site storage fulfills the requirement; do not require every project to create another data branch.

## Clearance and private access

When the project adopts review clearance, evaluate it using trusted base/default-branch logic without checking out or running contribution code. Validate current head, distinct actual review comments, verdict format, owner identity, draft/stale/withdrawn cases. The status cannot establish reviewer independence or reasoning quality by itself.

Keep build secrets and private originals out of metadata-only clearance and site jobs. Do not combine privileged `pull_request_target`/follow-up execution with untrusted code checkout. Pin external Actions to reviewed full commit SHAs and the build environment to an approved digest. See [GitHub secure workflow guidance](https://docs.github.com/en/actions/reference/security/secure-use).

The owner adopts required checks and bypass/merge controls after real success, failure and stale cases are observed. A workflow file or starter policy is not enforcement. Projects choosing another review model document and test the corresponding gate instead.

## Acceptance and failure cases

Demonstrate a real passing fresh candidate and main report first. Exercise wrong input hash, stale source/header receipt, overlap/extent errors, missing export, corrupt history, uncredited exact function when tracking, stale clearance and stale/diverged publication. Optional acceleration has its own failure matrix in the next chapter.

The website side must reject unapproved workflow blobs, wrong run attempts, missing lane steps, artifact digest mismatch and malformed payloads while preserving all accepted projects. Verify direct routes, selected manifest identity, and the next successful refresh. A schema-valid fixture or local preview is not evidence of live integration.

For a UI rollback, revert reviewed site source while retaining current accepted measurement history. For a producer failure, fix the failing layer; do not weaken checks, reset history or change private dependency access to get green.

## Multiple targets

Plan an explicit matrix from changed paths and a reviewed dependency map. A target-only config
change validates that target; shared source, headers and toolchain inputs validate their actual
dependents. Include deleted/renamed paths and conservatively validate all buildable targets for
unknown inputs. An archived revision without build support is not a zero-percent build target.

Use independent target jobs with `fail-fast: false`, isolated `build/<targetId>/` outputs and
unique report artifacts. Each job verifies its whole executable before measuring and packaging.
A stable aggregate check blocks a PR if a required target fails. A successful target on main may
publish despite a failed sibling, after its shared prerequisite checks pass. See the complete
[report-v2 CI contract](/docs/reporting/contract-v2.md#target-scoped-ci-and-repository-layout).
Caches remain optional and must bind target ID/hash as well as actual inputs.


---

# Cache & proof

Optional acceleration after fresh validation and publication work correctly.

## Three mechanisms, three meanings

| Mechanism | Reuses | What still runs |
| --- | --- | --- |
| Inventory cache | Target inventory/analysis metadata | Identity, input and metadata integrity checks; fresh build/measurement unless separate proof covers them |
| Compile/measurement cache | Exact-input objects and comparison results | Dependency validation, complete target verification and report reconciliation |
| Publication proof | A successful integrated build's public report package | Upstream execution/artifact authentication, complete landed-tree check, attribution when enabled and history validation |

An Actions cache is disposable acceleration. An authenticated artifact is execution evidence. The site's durable report store preserves accepted history. None substitutes for the others.

## Adoption sequence

First run fresh input checks, build, comparisons, tests, export and main publication successfully. Test their failure paths. Then enable inventory reuse, audited build caches and publication reuse separately, testing each boundary before enabling the next. They are optional; a project can remain on fresh validation indefinitely.

Use trusted main runs as the only writers of shared compiler/measurement results. PRs restore and validate entries but never save them. A full main build uses audit mode: compile and measure fresh; compare every still-valid cached entry with the fresh result; fail on disagreement; replace the local cache with fresh results before saving. A missing or invalidated key is a fresh computation, not a failed audit.

Branches may be able to read main caches. Do not assume caches can safely contain credentials or restricted originals. Objects may also contain recoverable target bytes: the owner must approve what cache storage and access permit. Keep such files out of public report artifacts and website Git. See GitHub's [cache access and retention rules](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

## Inventory keys

Bind inventory metadata to target hash, approved environment, analysis tool identity, inventory configuration and geometry/data extents that influence discovery. Store an internal receipt with those inputs and the metadata digest. A restore prefix can locate a candidate, but cannot validate it.

If internal identity or integrity fails, delete the restored inventory and regenerate. A broad tools-directory key is conservative and may invalidate inventory after unrelated tooling edits; document that cost. Narrow keys only when dependencies are established and failure-tested.

## Compile keys and invalidation

Bind a compiled object to:

- Source bytes, compiler/linker-driver identities, compiler profile/flags and comparison-build selection.
- Include search order, compile directory and generated compiler inputs.
- Every dependency actually read by the compiler, with content hashes.
- Relevant symlinks and files that can shadow an include, including case-insensitive name collisions where applicable.

Do not derive dependency coverage from the source file alone. If reliable dependency discovery is unavailable, disable object reuse or include a conservative full dependency universe. A same-named newly added header can change resolution even though the old header did not change.

In use mode, restore only a valid object and its dependency receipt. In audit mode, rebuild and compare object bytes and the declared reproducibility outputs for the same valid key. A disagreement fails the run; do not silently accept the cached or fresh version as a repair.

## Measurement keys and invalidation

Bind the result to compared object bytes, configured placement/full function extents, resolved referenced-symbol addresses, overlapping accepted source, relevant data slices, target identity and measurement tools/methodology. Restore referenced linked comparison outputs too, then run the same extent/arithmetic/integrity checks used for fresh results.

Changing a declaration can invalidate compilation; changing a symbol address or accepted placement can invalidate measurement without changing the comparison object's bytes. Retired extents must not remain in the exported inventory. Record compile and measurement hit/miss/audit counts separately.

## Save and bootstrap rules

Save build caches only after successful full main validation, on a main push or an explicitly requested main audit dispatch. Default manual runs validate but do not write shared caches. Other branches and PRs never save. Inventory caching can have its own explicitly documented main-only save policy.

Actions cache entries use immutable keys. Use a save identity including target/environment compatibility, source revision and run/attempt so a later explicit audit can save a new entry even on the same source revision. Restore by a compatible prefix and validate each internal key. A key match is not a proof of trusted origin or input equality.

A cold PR can produce a publishable fresh proof. Main may reuse it and skip the full build, so no compiler cache gets seeded. Provide an explicit main audit input to bypass proof selection and force fresh validation/cache save:

```sh
gh workflow run validate.yml --ref main -f audit_build_cache=true
```

This is the starter workflow's filename/input. An adopted project documents its actual equivalent. A rerun of a failed seed needs a new save identity, not deletion of a valid shared entry to force an overwrite.

## Publication eligibility

For this cache model, a PR that reused any compiled object or measurement may pass validation but cannot upload a reusable full-build proof. Sum reuse counts from all applicable cache layers; missing or malformed enabled-cache statistics must fail eligibility. Zero reuse means computation was fresh, not that no cache was restored.

A zero-reuse PR retains host receipt verification and may upload a full report-v1 package. A cached PR can omit a redundant host live-receipt re-export only after tests establish the primary export already checks those receipts; keep host unit tests and all semantic checks. Main full validation retains that re-export.

Main attempts proof selection unless an explicit audit was requested. Missing, expired or incompatible proof selects full validation. Invalid attribution or history discovered during promotion blocks publication; it must not be bypassed by resetting history or relabeling the result full.

## Authenticate the original proof

Before selecting reuse, verify these independently of downloaded JSON claims:

1. Same registered repository; successful permitted event/workflow/run/attempt and expected validation job/steps.
2. Approved workflow Git blob and tool/environment identities. On PRs, distinguish the API's head SHA from the actual tested merge commit and its parents.
3. Artifact name, originating run, attempt time window, size, digest and bounded safe archive contents.
4. Exact target, complete source tree, method/generation and input/output checksums. The tested integrated tree must equal the landed tree.
5. A successful full lane, zero reused results under the approved producing workflow, and unchanged measured summary/map/credits.

Never combine several PR reports into proof of a combined build. A changed tree requires fresh integrated validation. See [PR event identities](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request) and the [implemented platform receipt contract](/docs/reporting/platform.md#execution-policy-and-reuse).

## Promote without claiming a rebuild

Retain the original revision, tree, run/attempt, artifact digest and measurement time in the reused receipt. Record the landed revision and publication time separately. Recheck enabled attribution against landed history, restore previously accepted history, and append the current publication. Candidate-only PR history must not become a fake landed milestone.

The common importer supports reuse of an original full report-v1 package. A private custom proof layout must first be adapted to that contract; uploading arbitrary JSON with a real run ID is insufficient. Keep historical policies readable when approving a new producer workflow.

## Required experiments before enabling acceleration

| Experiment | Expected result |
| --- | --- |
| Cold then warm PR on identical inputs | Equal measured outputs, excluding explicitly volatile timestamps; observed hit counts and durations |
| Source/header/profile change | Only valid dependencies reuse; affected objects rebuild |
| New shadowing header or changed symlink | Relevant object key invalidates |
| Symbol address, placement, data or target change | Affected measurements invalidate |
| Deliberately altered valid cached object/result | Main audit fails on disagreement |
| Cached PR | Green if valid, but no reusable proof artifact |
| Fresh PR, identical landed tree | Main authenticates reuse, with original measurement time |
| Missing proof or changed tree | Main performs full validation |
| Explicit audit on main | Selection skipped, full fresh path and permitted save |
| Default/branch dispatch | No shared build-cache save |
| Expired evidence or corrupt prior history | No unauthenticated new import or silent history reset |

Measure hosted cold/warm timings after seeding. Local speed, a projected duration or a fixture's log line is not evidence of hosted cache reuse. Do not repeat expensive checks merely to decorate a handoff; rerun when inputs, failures or coverage gaps justify it.


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

## Put checks in both CI phases

Run a cheap ledger-only preflight before compiling: validate identities, duplicate entries, source paths, referenced commits/blobs and reachable attribution on the candidate and predicted squash history. Batch Git fetches/object queries where equivalent results have been established; an optimization must preserve errors and evidence requirements.

After measurement, build the complete exact-function inventory and reconcile it against the ledger. Include eligible exact unlinked comparisons and require complete function extents. This catches newly exact functions that were unknowable to a ledger-only check. Compare candidate and predicted-squash contributor results, then recheck actual landed history during reused publication. Reusing a build does not skip landed attribution validation.

Tracking-disabled projects omit these ledger stages under their explicit policy and publish no contributor payload. They can still build, compare, keep a timeline and integrate with the common site. Never infer tracking requirements from whether contribution links or rankings are shown.

## Start a measured timeline

At the first verified main build, create one row with that measured revision, timestamp and actual raw code/data totals and linked bytes. Record `measured` provenance pointing to its real execution. No prior history is required. If this capability is not implemented yet, declare it unsupported instead of creating placeholder data.

Future verified publications append supported measurements to preserved prior rows. Never invent points for unbuilt commits, interpolate gaps or treat a repository commit as evidence of a measured build. The current row agrees with the report summary; repeated publication remains idempotent.

## Timeline continuity

Keep full commit identity, target, methodology, raw totals/denominators and evidence quality. Preserve measured, reconstructed and inherited legacy entries distinctly. A new inventory can change a percentage without source regression; make the basis change explicit rather than smoothing the graph.

Restore prior verified history; do not use an unauthenticated live page as automatic recovery evidence. An intentional checkpoint recovery needs a documented audit. Latest repository commit metadata is separate from the latest measured build, even when the header displays both near each other.

Document the selected credit policy, ledger schema and recovery procedure in the repository. Publish contributor data only when that policy can be validated.


Legacy history and past-credit recovery belong to the [optional existing-project appendix](/wiki/existing-projects/). New repositories can skip it.


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

Configure the stable source path `/assets/covers/<slug>.webp`. A `/releases/<hash>/...` URL belongs to a built site artifact and must never be copied into project registration; the builder versions real asset references itself.

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

## Map parity and geometry

A supported map includes both `sections` and `files`. For each of code and data separately, their leaf address unions must be identical and each view's top-level metrics must sum to the summary. The views can group bytes differently; matching numeric totals at different addresses still fail.

Use positive, end-exclusive intervals without overlaps inside a view. Preserve disjoint ranges through `mapped_extents`, aggregate child metrics into parents, and represent measured bytes without known file ownership as gap/unmapped nodes. Do not invent ownership or drop unassigned bytes. Function fragments must collectively cover the declared complete extent and reconcile any reported function inventory; fragments alone cannot earn full-function exact credit.

The [map specification and paired examples](/docs/reporting/platform.md#map-semantics) list the exact field/aggregation rules. Validate with the shared packager locally; a schema-valid JSON tree can still fail coverage checks.

### Optional node evidence

Use [map-v2](/docs/reporting/schema/map-v2.schema.json) when the public map carries source or
file-boundary evidence. Set `map.json` to `schemaVersion: 2`; the report manifest stays v1.
The shared packager labels that asset `map-v2`. Pin a site tools revision supporting v2
before publishing it: the package validator and browser reject unknown or mismatched
versions. Existing v1 maps remain supported, with unknown fields still rejected.

| Optional field | Allowed node `type` | Valid values and purpose |
| --- | --- | --- |
| `source` | `file`, `group`, `function` | Repository-relative source file holding the code |
| `comparison_source` | `function` | Repository-relative file used for this function's comparison |
| `complete` | `file` | Boolean: whole file extent accounted for versus partial |
| `auto_generated` | `file` | `true` only for an unmapped placeholder; omit otherwise |
| `boundary` | `file` | `exact`, `provisional`, `open`: established, tentative or unresolved original boundary evidence |
| `scope` | `file` | `mapped-ranges` or `candidate-ranges`: mapped versus candidate extent ownership |

Every field is optional, but a node carrying evidence must explicitly declare an allowed
type. V2 introduces `group`; section and gap nodes cannot carry these fields. Translate
untyped internal nodes deliberately rather than guessing ownership or copying file-only
flags onto functions or groups.

Paths preserve case and use ASCII letters, digits, `_`, `.`, `+` and `-` in components
separated by single `/` characters. They must be canonical repository-relative paths:
no `.`/`..` or empty components, absolute paths, backslashes, URLs, percent escapes,
whitespace or controls. A producer's source tree need not be named `src/`.

The compact hover prefixes the source path when absent from the name and marks “partial
file” when source equals name and `complete` is false. Selecting an evidence-bearing node
shows source, comparison source, boundary, scope and supplied file flags in its details.
Raw evidence stays in the public map. These fields never change byte totals, function IDs,
exact credit or aggregation; `complete` alone does not prove matching or exact original
file boundaries.

See the [full field contract](/docs/reporting/contract-v1.md#optional-map-evidence-map-v2)
and [v2 example](/docs/reporting/examples/map-evidence.json), which uses the existing
[example summary](/docs/reporting/examples/map-summary.json).

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

The downloadable workflow maps its operations onto the canonical report-v1 inputs, not a particular game's old export format. Implement the mapping to `summary.json` and supported `map.json`, `timeline.json`, `contributors.json`; then use the shared packager from an approved pinned tools revision. The starter's `CI.md` lists metadata fields, step policy and full/reused artifact requirements. No separate website importer is needed for a conforming report-v1 producer.

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

Producer `job`, `requiredSteps`, selected-lane steps and artifact names match GitHub's actual run API **exactly**, including case, spaces and matrix suffixes. For a matrix job displayed as `Build (TARGET_ID)`, register that resolved name, not merely `Build` or the YAML job key. Inspect the actual successful run/attempt; there must be one matching producer job and exactly one successful occurrence of every required step. See [policy inspection commands](/docs/reporting/platform.md#execution-policy-and-reuse).

The [platform contract and commands](/docs/reporting/platform.md) specify the public input files, packager metadata, producer policy, full/reused execution lanes, import CLI and preserved historical policies. These are shared interfaces; the project supplies its own measured inputs and approved execution facts.

```sh
uv run --locked python tools/import_reports.py --project game-slug --run RUN_ID
uv run --locked python tools/build_site.py --output build/new-candidate
```

## Policy updates

After initial registration, keep a complete producer policy in a tracked JSON file,
normally `config/TARGET_ID/producer.json`, and use it for packaging. The site records
that path once in its policy-sync configuration. When the workflow, reporting job,
required steps, artifact or tools change, update the policy in the same producer PR.
Record the actual committed workflow Git blob; never substitute a commit SHA.

The site's enabled policy-sync workflow detects changes and prepares a matching
site PR. It copies the policy verbatim, preserves the previous policy for historical
reports, authenticates a real successful package and validates the site candidate.
You no longer need to pass hashes between agents manually. The PR still needs
review/merge under the site's policy; a successful upstream run cannot approve
itself. Until approval, the live site retains its last successful deployment.

Routine progress needs no policy update when the policy is unchanged. A missing
tracked policy or failed package produces a visible setup/validation result rather
than guessed configuration. The [policy-sync guide](/docs/reporting/policy-sync.md)
covers the source registration, immediate/dry-run checks, site-owned token setup,
manual approval and recovery. Producer repositories need no site-write token.
Existing hash-free policy templates are an optional adoption case in the
[existing-project appendix](/wiki/existing-projects/#tracked-policy-sources).

## Integration acceptance

A workflow change is also a consumer trust change. Approve its actual Git blob after reviewing the code, update full/reused step requirements together, and test deliberate audit-step skips. Preserve archived policies and immutable history. A green upstream run must not automatically expand the receiver's trust.

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

### Prompt updates

After registration, add a separate completion notifier using the site's pinned
reusable workflow. A completed main report run requests a site refresh (successful overall for v1; successful target/shared jobs for v2); the site
reauthenticates the run and imports only changed approved packages. No new policy
is trusted automatically. This avoids waiting for the periodic refresh without
rerunning site source tests for every producer commit.

The site-scoped GitHub App, caller generator, exact event fields, repository
variables/secrets, five-minute fallback and recovery behavior are documented in
[Producer policy sync](/docs/reporting/policy-sync.md#prompt-report-refresh).
These are optional delivery automation; the report contract and manual import
remain the same. Keep the notifier separate from the approved report workflow.

## Multiple game IDs and revisions

Use [report-v2](/docs/reporting/contract-v2.md) when a game has multiple executable targets, or
when starting a project with explicit revision identities. Keep one game slug/artwork entry and
publish an independent package, policy and history per target. `config/targets.json` separates
known/archived identities from verified build/report support. The site selects game ID/region
and disc revision without combining their numbers. An archived target without a report has no
fabricated progress.

The versioned schemas, exact registry/registration examples, target-scoped authentication,
optional capabilities, immutable storage layout and rollout order are specified in that contract.
Report-v1 single-target producers keep working unchanged. Declare the report format explicitly;
do not insert new target fields into a v1 object.


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
| New CI works but site refresh rejects it | Approved workflow Git blob, common/selected lane steps and actual run attempt | Automatically trusting changed workflow code |
| Audit run fails the site's step check | Selection may be intentionally skipped; full lane must still prove fresh validation | Requiring proof selection on all lanes or dropping full-build checks |
| Warm PR has no reusable artifact | Actual compile/measurement reuse counters and the zero-reuse publication rule | Relabeling cached work as fresh proof |
| Cache never appears after cold PR/main | Main may reuse proof and skip cache production; run the explicit main audit | Letting PRs save trusted shared caches |
| Main cache audit disagrees | Nondeterminism, incomplete keys or changed dependency resolution | Ignoring the disagreement or silently choosing one result |
| Repeated audit cannot save a refreshed cache | Immutable Actions save key; include run/attempt in build-cache identity | Deleting unrelated valid caches or assuming save overwrote them |

## Investigate with a bounded record

Record failing revision, target, tool environment, command, observed output and the specific question. Reproduce the smallest relevant scope, compare with the base revision, then fix the cause. Expand checks when evidence shows a wider dependency; do not repeat full builds as a reflex.

For source defects, re-run affected comparisons and complete the required final validation. For documentation/style changes, use relevant link, route or visual checks. Do not invent a binary-validation result for an unrelated change.

## Recovery and rollback

An unavailable essential reference/tool is a named blocker for the owner. Invalid publication metadata blocks promotion while the current valid package remains available. Recover history from authenticated archives or an explicitly audited checkpoint. Roll back the site independently from game source/history.

A changed owner policy needs a focused proposal and appropriate review. Do not loosen assertions, change counts, conceal mismatches or alter private dependencies merely to accommodate a patch.

## Keep the handbook accurate

When a command, report format or owner workflow changes, update its project documentation and the relevant handbook chapter together. Link the exact implementation revision. Distinguish established behavior from proposals and examples. Keep recurring tool failures in issues; avoid permanent running diaries of agent activity in public source.

A new agent should finish each handoff with changed files, evidence, checked revision/results, unresolved findings and review/publication state. “Implemented,” “reviewed,” “CI passed,” “owner cleared,” “merged” and “live” are different states.

The handbook stores reusable contracts and decisions, not game-specific run IDs, workflow blobs, timing claims or migration diaries. Record those facts in the adopting project's PR/configuration. When changing CI, review both the producer and the site's approved policy/lane requirements; keep old policies readable for retained reports. Verify an explicit audit and a normal/reused publication before declaring a workflow transition complete.


---

# Starter kit

Repository scaffolding and an agent prompt for applying this handbook.

## Files

Download the [repository starter archive](/wiki/downloads/repository-starter.zip). It contains README, AGENTS, CONTRIBUTING, setup checklist, PR template, .gitignore examples, integration checklist and agent prompt, plus:

| File | Use |
| --- | --- |
| `config/ci.example.json` | Verified project facts, adopted policy, command mapping and acceleration switches |
| `.github/workflows/validate.yml.template` | Editable fresh-validation workflow with optional cache/proof lanes; no deployment authority |
| `.github/workflows/review.yml.template` | Optional metadata-only clearance verifier for the default review policy |
| `CI.md` | Exact adapter operations, GitHub outputs, state/paths, packaging and producer-step policy |
| `reporting/platform.md` and `contract-v1.md` | Implemented shared interface, command usage and metric definitions |
| `reporting/schema/` and `reporting/examples/` | Generic public schemas and unregistered configuration/report examples |
| `OPTIONAL-ADOPTION.md` | Optional existing-workflow and legacy-data guidance; outside the new-project checklist |

Fill visible placeholders from verified project facts. The project supplies its own compiler, build/comparison engines and internal evidence formats. Implement `tools/project_ci.py` as the documented thin adapter to those real tools; the kit does not include a fake success-producing adapter. Existing repositories keep established paths where those responsibilities are implemented.

Adopt project review/merge policy explicitly; independent accuracy/hostile review and owner-only merging are the default, not a site-imposed rule. Attribution is a separate choice. Leave caching and proof reuse disabled until fresh validation works, then enable/test requested mechanisms independently. Rename a workflow `.template` only after its adapter and configuration are ready.

## Prompt for an agent

```prose
Read this wiki and the project's current README, CONTRIBUTING and AGENTS. Use its structure as the template for repository layout, naming, evidence, validation, review, CI, public reporting and shared-site integration. Inspect the existing project before editing and preserve unrelated work. Use a dedicated branch and checkout/worktree.

Record the actual target/hash, approved toolchain, build commands, source objective, current validation and supported report capabilities. Adapt the handbook's responsibilities to this project's established structure.

Read the starter's CI.md and map its exact operations to real project tools. Adopt review/merge policy explicitly, using independent accuracy/hostile and owner-only merges as the default. Implement fresh validation first. Caches and publication reuse are optional later optimizations, with their own invalidation, main-audit, zero-reuse proof and bootstrap acceptance tests.

Implement missing pieces needed for a reproducible build, honest exact/fuzzy measurements, versioned public reports, preserved history and site integration. Keep contribution acceptance, attribution tracking and rankings independent. Use the shared report contract and renderer rather than a separate game UI.

Validate real inputs and both success/failure paths. Retain useful partial source. Do not invent metrics, evidence, authorship, approval or test results. Follow the project's task authorization for pushes, PRs, publication and merge.

Deliver the changes with commands, tested revisions, artifacts, capability settings and remaining limitations. Verify the public route and next refresh before declaring the site integration complete.
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
| Optional acceleration | Off until fresh correctness; actual cold/warm parity, dependency invalidation, main audit and complete-tree proof evidence before enabling |
| Credits | Explicit policy, with evidence reconciliation when enabled |
| Reports | Validated shared manifest, raw parity, supported modules and execution proof |
| History | Durable continuity, idempotence, ordering and recovery |
| Website | Shared presentation, configured modules, direct route, deployment and subsequent refresh |

The [integration checklist](/docs/reporting/onboarding.md) repeats the producer/consumer boundary and completion checks in one handoff. Keep project-specific commands and decisions in that repository, not in this generic template.

## Explicit-target overlay

The starter download includes `optional-targets/`: editable target/CI-dependency registries, a
changed-path planner, a target matrix workflow and exact adapter operations. Use it when starting
a revision-aware project. It preserves shared source and separates originals, generated outputs,
reports and histories by canonical target ID. Its README names every operation an agent must
implement; it contains no fake-success build adapter. Single-target v1 integrations need no change.


---

# Existing projects

**Optional appendix. Skip this when starting a repository from scratch.** The main handbook and starter checklist define the new-project path: choose policy, establish verified tools/inputs, build and measure, start a measured timeline, then register the standard public report.

Use this appendix only when adopting the structure in a repository that already has source, CI, review conventions, attribution or historical data. These are generic adoption procedures; they are not extra prerequisites for new projects.

## Map existing responsibilities

Inventory existing tools, source layout, configuration, validation outputs and owner instructions. Preserve working engines and evidence-supported paths where they fulfill the documented responsibilities. Map them to the adapter contract rather than reorganizing source solely to match example names. Identify actual gaps and test them; do not declare the old workflow equivalent without evidence.

## Adopt policy without overriding authority

Record the review/merge model selected for the project. Existing documented owner/task delegation remains authoritative until explicitly changed; a generic default does not silently grant or revoke merge permission. Preserve review independence and the gates selected by that policy.

The starter uses SHIP/FIX/REDO/BLOCKED. A project retaining SHIP/FIX/REDO must represent missing essential evidence as an explicit blocked state with a nonpassing check, or deliberately adopt BLOCKED across its records and verifier. Never convert blocked evidence into a passing verdict. This is a compatibility decision for an existing workflow; new projects can use the coherent starter vocabulary directly.

## Branch and trigger conventions

Keep a documented existing branch convention if appropriate. A branch prefix is not authorization or a reporting-contract field. Inspect the actual triggers: optional branch-push checks may have prefix filters while PR validation covers all contribution branches. Make any trigger change deliberately and verify both event paths. New projects can use the starter's agent-neutral branch examples and PR/main validation model.

## Recovering past credit

Use surviving original PRs, commit authorship, pinned source blobs, integration records and reviewed evidence. A closed PR or deleted branch may still leave useful records; do not assume they are available indefinitely. Distinguish supported attribution, explicit joint work and unresolved ownership.

Keep a bounded recovery record explaining each decision and uncertainty. Do not give every function to the current file author or merger. If a project promises complete exact-function attribution, unresolved gaps block that capability's publication until resolved or the owner explicitly changes the policy.

## Import legacy history

Existing history is useful even when it predates this pipeline. Migrate it before the first accepted report using a reproducible, reviewed conversion; retain the raw input separately. Do not reset an already accepted timeline during a later refresh.

The same [timeline contract](/docs/reporting/platform.md#timeline-semantics) applies to imported rows. Legacy input does not bypass identity, raw-value, timestamp or continuity requirements.

1. **Inventory the old format.** Record its target, metric meanings, denominators, timestamp basis and evidence sources. Count unresolved rows and preserve the original export/hash in a migration record.
2. **Resolve abbreviated commits.** Fetch required history, resolve each prefix to exactly one commit, and verify it belongs to the intended project's history. A missing or ambiguous prefix is unresolved; never select the first matching object. Use the adopting project's branch name in ancestry checks.
3. **Recover values from evidence.** Prefer preserved reports, receipts, versioned target/placement metadata or a reproducible historical replay. A denominator may be carried across rows only with evidence that the target and measured universe were unchanged. Today's total is not automatically every historical total. Rounded percentages generally do not recover an exact byte numerator uniquely.
4. **Classify provenance.** Use `measured` for supported historical measurement, `reconstructed` for values rebuilt from identified historical evidence, and `inherited` when preserving an already accepted compatible record. A new importer does not turn an old measurement into a newly executed build.
5. **Normalize without inventing.** Resolve duplicate revisions and ordering using a documented deterministic rule before initial acceptance. Preserve the timestamp's actual meaning; a commit time is not a historical build time. If the available timestamp is a commit-time proxy, state that in reconstructed provenance and the migration record.
6. **Validate and reconcile.** Check schema, integer arithmetic, evidence-backed denominators, ordering, current-row parity, and continuity against any previously accepted history. Record conversion method, source records/hashes and unresolved/excluded rows in the project.

For a known abbreviated commit, use Git's ambiguity checks rather than matching a log line by eye. Replace these placeholders and the main ref with actual project values:

```sh
git fetch origin main
git rev-parse --verify --end-of-options 'ABBREVIATED_SHA^{commit}'
# Where the timeline policy requires current-main ancestry:
git merge-base --is-ancestor FULL_COMMIT_SHA origin/main
```

Missing original refs or rewritten history need a documented recovery decision; they are not reasons to choose a different commit with a similar prefix.

A full SHA proves identity, not missing totals. `reconstructed` requires evidence for the values: it does not permit zero-filling, interpolation or repeating today's numbers. Keep initially unrepresentable rows in the project's legacy archive with reasons and publish the supported subset, or defer timeline support until sufficient evidence is available. Do not silently omit rows already accepted by the site; those require an explicit compatible migration/correction.

An `inherited` wrapper may include the exact prior accepted row as `provenance.record`. Its revision, time, code and data values must remain identical. It cannot wrap an abbreviated/missing-total raw row and simultaneously claim the normalized fields are unchanged. Reconstructed rows identify their source/method through `provenance.source` instead.

See the [illustrative legacy timeline](/docs/reporting/examples/timeline-legacy.json). Its placeholder commit identities and values are not production evidence. The site retains provenance in accepted data; the current graph does not display separate provenance badges, so the metadata label alone does not create a visible rebuilt/measured distinction.

## Adoption acceptance

- [ ] Existing commands and selected policies map to the standard responsibilities without lost evidence or unauthorized changes.
- [ ] Any retained verdict/branch conventions agree with their actual verifier and CI triggers.
- [ ] Legacy raw history and credit sources are retained with conversion method, unresolved rows and limitations.
- [ ] Historical identity and raw values are supported; reconstruction labels do not replace evidence.
- [ ] Previously accepted history remains unchanged or moves through an explicit compatible transition.
- [ ] Real report import and the next refresh preserve prior accepted state.

These checks apply only to the adoption being performed. They are intentionally absent from the starter's new-project checklist.

## Changing an accepted report format

Stage the next producer policy as `pending` while the current importer stays active.
Authenticate real outputs in both formats and compare raw summaries, map coverage and
metrics, complete function IDs, optional credits and historical values/provenance. A
pending policy cannot itself admit packages or select the active importer.

When changing history representation, let the last current publisher finish, restore the
durable store and freeze its exact snapshot using the registration's `freeze` fields:
`path`, `revision`, `manifestSha256`. Copy the final stored row's revision and built_at
verbatim to the producer; retain its original timestamp spelling. Do not infer the
cutover from a local preview, an earlier parity run or the latest repository commit.

The freeze permits other projects to refresh but blocks this project's newer imports,
added rows and publication changes. Wait for the producer's cutover pin and successful
main package. Then activate the staged policy, remove the freeze, archive the previous
format policy and require every previously accepted row to survive unchanged or through
an exact inherited record. Retire the producer's former website/artifact jobs only after
the shared-site switch succeeds. See the [platform controls](/docs/reporting/platform.md).

## Tracked policy sources

The normal new-project interface is a complete tracked producer policy JSON. An
existing exporter that generates its policy only at runtime must publish a tracked
policy before automatic synchronization can be enabled. Do not execute exporter
code in the site job to recover that configuration.

For an existing tracked template that omits only `workflowBlobs`, the site can
explicitly register `mode: "template"`. The sync job obtains the current workflow's
Git blob at the pinned producer revision and adds it to the previously approved
list. All other schema, identity, successful-package and review checks are the
same. A template must omit that field; a complete policy must declare its own
approved blobs. Template mode is an optional adoption aid, outside the starter
checklist. Prefer a complete tracked policy for a new repository.

## Explicit target adoption

This optional migration is unnecessary for a working single-target report-v1 producer. Agree
on the new consumer contract before renaming directories or emitted identities.

1. Deploy report-v2 consumer support while the existing producer still emits v1.
2. Register the exact old target object (`id`, `console`, executable `sha1`) in the canonical
   target's `legacyTargets`. Keep its old policy in that target's `archives` and preserve every
   original package byte, receipt, checksum and timeline row. The site adopts the pointer only
   through this explicit same-binary alias. It never guesses a revision from a game ID.
3. Migrate producer/private-original paths and generated outputs, approve the pinned environment,
   implement target-specific CI, and pin a reviewed v2 packager. Coordinate required-check names
   with the owner. Preserve existing compiler profiles and measurement methodology when their
   meaning has not changed. Known targets without validated builds remain archived metadata.
4. Review the new policy and workflow blob for each publishing target. Produce and authenticate
   a real main package, compare old/new totals and geometry, and prove history retention with
   zero lost/changed rows. Switch that producer to report-v2 only after these checks pass.
5. Update policy-sync source paths and completion notifier pins/format. Keep single-target
   projects on their existing wire contract. Do not retain duplicate legacy build/report pipelines.

Legacy rows remain records of their original execution. Function identifiers in newly generated
v2 reports use the explicit target ID; never rewrite already accepted v1 packages to update IDs.
