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
