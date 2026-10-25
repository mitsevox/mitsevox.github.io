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
