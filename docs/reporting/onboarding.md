# Project integration template

Use this structure for a new decompilation project or adapt it to an existing repository. The project supplies its target facts, tools and commands; the shared site supplies a common report contract and presentation.

Read the [handbook](../../wiki/), [repository layout](../../wiki/layout-and-naming/), [CI structure](../../wiki/ci-and-publication/), [website contract](../../wiki/website-integration/) and [metric definitions](contract-v1.md). The [starter archive](../../wiki/downloads/repository-starter.zip) contains repository templates and an agent prompt.

The starter includes editable validation/clearance workflows, CI configuration and `CI.md`'s exact adapter interface. Follow the [agent workflow](../../wiki/agent-workflow/) for scoped implementation and final-revision handoff. Start with fresh validation; [cache/proof acceleration](../../wiki/cache-and-proof/) is optional after its failure tests pass. Review/merge policy is project-configurable, with independent accuracy/hostile and owner-only merging as the starter default.

## Project facts

Fill these from verified information:

| Item | Value to supply |
| --- | --- |
| Identity | Project slug, display title, repository and owner |
| Target | Platform, region/revision, executable and verified hash |
| Objective | Faithful matching reconstruction or another explicitly documented objective |
| Environment | Approved compiler/linker/comparison tools, hashes, supported hosts and setup |
| Commands | Input verification, baseline, accepted-source build, comparisons, validation and public export |
| Policy | Review/merge authority, matching integrity, attribution tracking and contribution acceptance |
| Capabilities | Code/data measures and supported map, inventory, history and contributor modules |

Keep those values and the exact implementation commands in the project's README, configuration and contribution rules. Existing source paths and working build tools can stay in place.

## Repository responsibilities

```text
game-slug/
  README.md                  identity, setup and exact commands
  CONTRIBUTING.md            scope, evidence, integrity, review and authority
  AGENTS.md                  concise instructions pointing to project rules
  src/                       recovered and useful partial source
  include/                   shared declarations
  config/                    target, placement, profiles, comparisons and evidence
  tools/                     reproducible build, validation and report export
  tests/                     meaningful validation and failure checks
  docs/                      durable technical decisions
  .github/workflows/         validation, clearance and publication jobs
  build/                     ignored generated output
  scratch/                   ignored investigation output
```

Do not reorganize an established repository solely to match these folder names. Preserve the responsibility boundaries and document the local equivalents.

## CI responsibilities

| Stage | Required behavior |
| --- | --- |
| Validate configuration/evidence | Fail early on inconsistent target, malformed evidence or invalid declarations |
| Build and compare | Use approved inputs/tools; validate the complete objective and measure full registered extents |
| Review clearance | Evaluate scope-appropriate records on the actual revision through trusted logic |
| Export candidate | Produce public report data and a checksummed execution receipt without advancing latest |
| Publish main report | Authenticate full/reused proof, preserve history and install an immutable snapshot |
| Consume and deploy | Validate the public contract, preserve project isolation, build one coherent shared site and verify it live |

Use the project's documented commands for each stage. Give build jobs read access and approved input access; restrict writes and deployment permissions to their publication jobs. Pin tools and workflow dependencies. Scope cache keys to the inputs they accelerate.

Test failures as well as success: wrong target, stale dependency/report, missing export, corrupt history, unchanged rerun, stale main run and immutable collision. Carry adequate prior validation forward and recheck changed dependencies.

## Public report contract

The game exports source-derived measurements and evidence. A conforming report-v1 export uses the shared importer, validator, store and renderer without a new project-specific importer. The shared site owns registration, presentation, accepted report storage and deployment.

Use [manifest v1](schema/report-v1.schema.json) and [project configuration v1](schema/project-v1.schema.json). Record full target/revision/tree, methodology/generation, tools, separate measurement/publication times and run/attempt. Every supported module has a typed checksummed asset; unsupported modules have a reason. Validate the raw measurements against the manifest and renderer view model.

Code/data summaries are required. Preserve raw byte denominators and distinguish linked, exact and fuzzy coverage. Support code and data fuzzy separately. Inventories, maps, history and contributor rankings can be disabled when unsupported. A timeline must work without a contributor feed; a summary must work without a fabricated map.

Attribution tracking, displayed rankings and accepting contributions are independent. Keep recorded provenance when display is disabled. Enable contribution links only with an approved guide URL.

Treat artifacts as bounded data. Reject unsafe paths, symlinks, duplicate keys, nonfinite values, wrong target/revision and inconsistent totals. Verify producing execution and artifact identity against a trusted policy. Never include original binaries, private tools, complete debug exports or credentials.

## Shared presentation

Register identity, artwork, verified report bindings and module settings with the shared renderer. Use the common header, width/gutters, code/data colors, layered bars, tooltips, count rows, map interactions, timeline and contributor styling. Keep cover aspect ratios and use consistent `<slug>.webp` names.

The browser reads public static files without a token or compiler. Latest repository commit metadata is independent from the measured build. Build fingerprinted assets as one coherent release.

## Acceptance

- [ ] Identity, environment, commands and responsibility mapping are documented.
- [ ] Applicable baseline/source/comparison stages have real evidence.
- [ ] Review and CI evaluate the actual integrated inputs.
- [ ] Public manifest and supported assets validate against the declared versions.
- [ ] Raw total/linked/exact and supported fuzzy metrics agree at one revision.
- [ ] Naming, full-function exactness and file-boundary policies are respected.
- [ ] Optional modules are genuinely optional, with no empty headings or invented data.
- [ ] Contribution acceptance, tracking and rankings behave independently.
- [ ] Prior history survives; identical reruns are no-ops; stale/corrupt updates fail safely.
- [ ] One project's import/failure preserves all other accepted projects.
- [ ] Only verified public files enter the static production build.
- [ ] Direct routes, refresh/back/forward, shared layout and hover/map behavior work.
- [ ] The public page/manifest agree and the next refresh preserves the accepted state.

Record commands, tested revisions, producing run/attempt, artifact/package identities, capability settings and limitations in the integration PR. Unchecked items remain explicit. A repository structure or schema-valid example does not establish that a build or integration passed.
