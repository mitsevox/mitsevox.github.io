# Build, verify, measure

Relink the original byte for byte, replace units with source and produce objdiff's report.

Three things happen in one `ninja` invocation, locally and in CI: the original is split into objects and relinked, the objects marked `Matching` are replaced by compiled source and the result is checked against the expected hash, and objdiff measures every unit against its original. The publish action reads only the last step's output, `build/<target id>/report.json`.

The commands below are for decomp-toolkit and dtk-template, which the reference repositories use for GameCube. The section at the end says what another platform must provide instead.

## Local setup for a dtk-template project

1. Start from [dtk-template](https://github.com/encounter/dtk-template) (`configure.py`, `tools/project.py` and the rest of its `tools/`). Follow its documentation for `config/<target id>/config.yml`, `splits.txt` and `symbols.txt`; those are the platform-specific part this guide cannot write for you.
2. Wire `configure.py` to the target list so the active targets are the only versions it accepts and `--version` takes a target id. Replace dtk-template's hard-coded `VERSIONS` list with:

    ```python
    from tools.targets import registry, build_targets

    TARGET_REGISTRY = registry()
    VERSIONS = build_targets(TARGET_REGISTRY)
    DEFAULT_VERSION = VERSIONS.index(TARGET_REGISTRY['defaultTarget'])
    ```

    and add `Path("config/targets.json")` and `Path("tools/targets.py")` to `config.reconfig_deps`. dtk-template already builds each version into `build/<version>/`, which is what makes `build/<target id>/` the generated directory.
3. Keep `config.dtk_tag` and `config.objdiff_tag` in `configure.py` as the single place tool versions are pinned; `tools/measuring_tools.py` reads them, and the Dockerfile builds the same dtk tag.
4. Place your own copy of the original at `orig/<target id>/sys/main.dol` (the path `config.yml` and `tools/verify_target.py` name; `orig/*/*` is ignored by Git) and verify it:

    ```sh
    python3 tools/verify_target.py --target GAME01-rev0
    ```

5. Configure and build:

    ```sh
    python3 configure.py --version GAME01-rev0
    ninja -f build/GAME01-rev0/build.ninja
    ```

    The generated build downloads dtk, objdiff and the compilers at their pinned tags unless `--dtk`, `--objdiff` and `--compilers` point at local copies. The build fails unless the linked executable's SHA-1 equals `config/<target id>/build.sha1`, which must equal the original's hash from `targets.json`.

6. Measure:

    ```sh
    ninja -f build/GAME01-rev0/build.ninja progress build/GAME01-rev0/report.json
    ```

    `progress` prints the per-category summary; `build/<target id>/report.json` is the objdiff report CI publishes. This is exactly the command the starter `validate.yml` runs, after the same `configure.py` call with the image's tool paths.

## What the three measures mean

Each object in `configure.py` is declared `Matching` or `NonMatching` (dtk-template's `Equivalent` is for `--non-matching` builds and never counts). The publish action turns objdiff's report into the contract's three measures:

| Measure | Source in the report | What it says |
| --- | --- | --- |
| `linked` | `complete_code` and `complete_data`: units whose `metadata.complete` is true, which dtk-template's generated `objdiff.json` sets for `Matching` objects | Bytes that compile from source into the byte-identical executable |
| `matched` | `matched_code` and `matched_data`: functions at 100% and data sections at 100%, in any unit | Bytes that match exactly, linked or not |
| `fuzzy` | `size * fuzzy_match_percent / 100` summed over functions, and over data sections, by the action itself | Size-weighted similarity |

So a `NonMatching` unit with three exact functions out of ten contributes those three functions' bytes to `matched`, their fuzzy score to `fuzzy`, and nothing to `linked`; the original bytes stay linked. Promoting the unit to `Matching` moves its whole size into `linked`. Function counts come from the report too: `exact` is functions at 100%, `named` is functions whose symbol is not `fn_<hex>` or `func_<hex>`. File counts treat each unit as a file, `named` when the unit is not `auto_generated` and `exact` when it is named and both its code and data are fully matched.

The action checks the report's own totals against its function list and refuses a report whose numbers disagree, so a report from an unexpected objdiff version fails the publish step rather than publishing wrong numbers. Pin `config.objdiff_tag` and change it deliberately.

## Partial source

Useful partial reconstruction stays in its normal file under `src/` and is registered as a `NonMatching` object. The combined executable still matches because the original bytes for that unit remain linked; objdiff measures the source separately. Reviewers and CI treat matching incompleteness as progress, not as a failure. See [Contribution workflow](/wiki/contribution-workflow/) for how partial units are reviewed and promoted.

## Reading the report

The publish action reads these parts of `report.json`, so any producer must write them the way objdiff does:

| Path in the report | Use |
| --- | --- |
| `measures.total_code`, `matched_code`, `complete_code`, `total_data`, `matched_data`, `complete_data`, `total_functions`, `matched_functions` | The summary; 64-bit values are strings, zero values may be absent |
| `units[].name` | Unit name; the `unit-prefix` input (default `main/`) is stripped for display |
| `units[].metadata.complete`, `units[].metadata.auto_generated` | Linked status and tool-generated units |
| `units[].measures.total_data`, `matched_data`, and `matched_code`, `total_code` | Per-unit data tile and the exact-file test |
| `units[].sections[]`: `name`, `size`, `fuzzy_match_percent`, `metadata.virtual_address` | Section extents; sections named in `code-sections` (default `.init,.text`) are code, all others data |
| `units[].functions[]`: `name`, `size`, `fuzzy_match_percent`, `metadata.virtual_address` | Function tiles and counts |

Every function must lie inside one of the code sections of its unit, or the action stops with `<unit>: <function> lies outside the code sections`. A platform whose code lives in differently named sections passes `code-sections` to the action ([Publishing](/wiki/publishing/)).

## Other platforms

The publish action converts objdiff reports and nothing else. objdiff supports several architectures, so a project on another platform that produces `report.json` with `objdiff-cli report generate` can use the whole pipeline unchanged apart from these parameters:

- the original's path under `orig/<target id>/` (`ORIGINAL` in `tools/verify_target.py`, `PARAMETER 2` in `validate.yml`, the `COPY` in the Dockerfile);
- the configure and build commands (`PARAMETER 3` in `validate.yml`), which must fail unless the complete executable matches and must write `build/<target id>/report.json`;
- the `code-sections` and `unit-prefix` inputs of the publish action if the defaults do not fit;
- the `TAGS` dictionary in `tools/measuring_tools.py`, which names the version lines of `configure.py` to report.

A project that cannot produce an objdiff report cannot use the publish action as shipped; that is a site-side change and outside this guide.
