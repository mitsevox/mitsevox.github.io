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
