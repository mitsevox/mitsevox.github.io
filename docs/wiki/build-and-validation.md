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
