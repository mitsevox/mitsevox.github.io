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
