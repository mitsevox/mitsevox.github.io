# Start here

A reusable structure for a decompilation repository, its CI and its place on the shared site.

Use this handbook to establish a new project or align an existing one. It defines repository responsibilities, naming conventions, evidence standards, validation stages, review records and the public report contract. Each project supplies its own target facts, tools and build commands.

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

## Fixed contracts and project decisions

The fixed reporting boundary is the versioned public contract, authenticated execution, honest metric meanings, optional-capability declarations and history preservation. The site owner curates registrations and artwork. A new project uses the common importer and renderer rather than a copied game-specific website pipeline.

The project chooses its console/executable format, tools, supported hosts, source layout, evidence vocabulary, build commands, promotion objective and review/merge policy. Owner-only merging with independent accuracy and hostile reviews is the starter default; the owner can adopt a different documented model. Attribution is optional. Caching and publication reuse start disabled until fresh validation works.

The starter supplies an editable GitHub Actions workflow, configuration example and exact adapter interface. It cannot supply a target's extraction, compiler profile, linker geometry or disassembly interpretation. An implementing agent maps those contracts to the project's real tools, tests them and records unresolved gaps. It must not replace missing implementation with successful no-ops.

## Use the handbook with an agent

Give the agent this wiki, the repository and its current instructions. For site integration, also supply the shared site's report contract and registration access. The [starter prompt](/wiki/starter-kit/#prompt-for-an-agent) specifies the work without prescribing a particular game's implementation.

The agent fills project facts, adapts the template to established tools, implements missing checks and supplies evidence for the acceptance checklist. Unknown inputs remain explicit. A copied template is a starting structure; real successful and failing runs establish that the project works.

## Maintain the template

Keep this handbook reusable. Project targets, repository names, workflow revisions, run IDs, migration plans and one-off status belong in their project's records. Update the template when a reusable convention or public contract changes, and version any incompatible reporting change.
