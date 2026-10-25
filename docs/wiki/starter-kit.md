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
