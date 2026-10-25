# Build & validation

Separate a working baseline, reconstructed source and independent comparison measurements.

## Three different results

| Result | Establishes | Does not establish |
| --- | --- | --- |
| Original-object relink | Target extraction, placement and relink can reproduce the executable | Recovered source, original compiler identity or progress |
| Accepted-source build | Selected source replaces its accepted ranges and complete output still matches | Exactness of every original file boundary |
| Independent comparison | Full registered functions/data have measured exact or fuzzy similarity | Permission to replace their original linked bytes |

A new project must implement and document these distinctions for its executable format. NFL's DOL section layout and tool profiles cannot simply be copied to another target.

## NFL command reference

These commands are executable entry points in NFL Street 2, not commands available in an empty repository. Follow its README host/setup requirements first.

```sh
python3 tools/setup_compiler.py
python3 tools/baseline.py --original /path/to/main.dol
python3 tools/source_build.py --original /path/to/main.dol
python3 tools/analyze.py --original /path/to/main.dol
python3 tools/matching.py --original /path/to/main.dol
python3 -m unittest discover -s tests -v
```

NFL additionally validates its SN-linker original-object relink. Run relevant focused checks during iteration and the required final checks before submission; do not repeatedly run the entire suite when nothing affecting it changed.

## Establish the new project's baseline

Record executable identity, section sizes/addresses, entry point and target hash. Verify the complete reconstructed executable against the original, not only selected functions or a summary score. Document all placement, alignment, small-data and relocation handling. Keep unassigned bytes represented.

Pin the usable compiler, linker, wrappers and conversion tools with hashes. Record unit/library compiler-profile evidence separately. A successful diagnostic compile can establish compatibility without uniquely identifying the original compiler version.

## Register partial comparisons

Define source path, profile, full target extents, code/data placement and dependencies. Reject overlaps, missing functions, unresolved references and stale receipts. Compare compiler-produced bodies without truncating mismatches. Weight fuzzy similarity by the target extent, not the size of an expanded draft.

Use normal source files for partial work. Where accepted and draft code coexist, a documented comparison guard can select draft bodies for measurement while preserving the accepted build. Keep original bytes linked until promotion; partial mismatch alone is not a reason to reject a well-supported reconstruction.

## Promotion

After review and validation, change the accepted source-placement configuration, remove obsolete guards/registrations and verify the entire executable. Do not move a function into a different source tree merely because it became exact. Preserve its attribution if tracking is enabled, and avoid counting a linked range again through a comparison entry.

Uninitialized storage has no speculative fuzzy byte score. Validate its layout and the project's stated accounting rules. Code/data classification follows the declared target measurement universe, including documented data embedded in executable sections; do not silently change denominators for the chart.

## Bind results to inputs

Reports should identify target hash, tested revision/tree, source/header hashes, unit manifest, profile, tool versions and comparison methodology. Reject a stale report after its inputs change. A successful earlier build is not proof of the current tree.

Validation tools need meaningful failure tests: wrong target, stale dependency, overlapping range, missing symbol, changed compiled extent, unsupported data placement and corrupt report. Do not weaken validators to accept the current patch. Record failures and unresolved questions honestly.

See [NFL target mechanics and comparison workflow](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/GN7E69/README.md) for concrete formats, constraints and implementation details.
