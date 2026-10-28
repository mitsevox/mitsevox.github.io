# Build, verify, measure

Relink the original byte for byte, replace units with source and produce objdiff's report.

Three things happen in one `ninja` invocation, locally and in CI: the original is split into objects and relinked, the objects marked `Matching` are replaced by compiled source and the result is checked against the expected hash, and objdiff measures every unit against its original. The publish action reads only the last step's output, `build/<target id>/report.json`.

The commands below are for decomp-toolkit and dtk-template, which the reference repositories use for GameCube. The section at the end says what another platform must provide instead.

## Local setup for a dtk-template project

1. Start from [dtk-template](https://github.com/encounter/dtk-template) (`configure.py`, `tools/project.py` and the rest of its `tools/`). dtk-template names its config folder after the game ID (`config/GAMEID/`); rename it to the target id (`config/GAME01-rev0/`) before adding anything, and use the target id wherever the template says version. Follow its documentation for `config/<target id>/config.yml`, `splits.txt` and `symbols.txt`; those are the platform-specific part this guide cannot write for you. Record the template's revision in `CREDITS.md` and link its documentation from the README rather than copying it into the repository.
2. Wire `configure.py` to the target list so the active targets are the only versions it accepts, `--version` takes a target id and the target's define is derived. Replace dtk-template's hard-coded `VERSIONS` list with:

    ```python
    from tools.targets import registry, build_targets, define

    TARGET_REGISTRY = registry()
    VERSIONS = build_targets(TARGET_REGISTRY)
    DEFAULT_VERSION = VERSIONS.index(TARGET_REGISTRY['defaultTarget'])
    ```

    add `Path("config/targets.json")` and `Path("tools/targets.py")` to `config.reconfig_deps`, point `config.config_path` and `config.check_sha_path` at `config/<version>/config.yml` and `config/<version>/build.sha1`, and pass `f"-D{define(config.version)}"` in `cflags_base` next to the template's `-DBUILD_VERSION=`. Remove `type=str.upper` from the `--version` argument: dtk-template upper-cases it, which no target id with a lower-case revision (`GAME01-rev0`) can pass. dtk-template compiles each version into `build/<version>/` and writes `report.json` there, but its `tools/project.py` writes `build.ninja`, `objdiff.json` and `compile_commands.json` at the repository root, and the next `configure.py` run overwrites them. The kit's `validate.yml` and README expect them under `build/<target id>/` with everything else generated ([Repository layout](/wiki/repository-layout/)): either edit `generate_build_ninja`, `generate_objdiff_config` and `generate_compile_commands` in `tools/project.py` to write under `config.build_dir / config.version`, or keep the stock paths and write PARAMETER 3 and the README's build lines without `-f` (`ninja progress build/<id>/report.json`), configuring one target at a time.
3. Keep `config.dtk_tag` and `config.objdiff_tag` in `configure.py` as the single place tool versions are pinned; `tools/measuring_tools.py` reads them, and the Dockerfile builds the same dtk tag. The two can drift apart, since the build uses the image's dtk and not the tag; in CI `tools/measuring_tools.py --verify` runs the image's `dtk --version` and fails the job unless it reports the pinned tag, as a whole word. It verifies the version word only: a project that patches dtk and names the patch in the reported version (its hash, say) gets the stock version from the patched binary, so the patch itself is the image's to carry and the Dockerfile's to check. objdiff is downloaded at the pinned tag by the build itself, so the pin is what runs.
4. Place your own copy of the original at `orig/<target id>/sys/main.dol`, the path `config.yml` names (`orig/*/*` is ignored by Git). The toolkit refuses an original whose hash differs from `config.yml`, and `python3 tools/targets.py check` confirms that `config.yml`, `build.sha1` and `targets.json` agree.
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

With more than one active target, repeat steps 5 and 6 per target; the README's Building section shows the loop. A shared change is safe for every target only when every target has been built.

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

## Version differences

Every target has one preprocessor define, `VERSION_<ID>`: the id upper-cased with `-` and `.` replaced by `_`, so `GAME01-rev0` compiles with `VERSION_GAME01_REV0`. `tools/targets.py` derives it and `configure.py` passes it; no file stores it. dtk-template also passes a numeric `BUILD_VERSION`; it stays defined for compatibility and is never read, because `BUILD_VERSION >= 1` stops meaning anything the day a region is inserted between two revisions.

- A difference lives in the shared file under `#if VERSION_GAME01_REV0`. A condition is a boolean expression of `VERSION_` tokens and group macros, with `!`, `&&` and `||` only, and nothing else: no numeric comparison, no other macro in the same condition. A version condition nested inside an ordinary `#ifdef` is fine; the two must not mix in one line.
- When two or more targets share a difference, name the group once in `include/version.h`: `#define REGION_USA (VERSION_GAME01_REV0 || VERSION_GAME01_REV1)`. The header exists from the first commit with the rule as its comment, so the first divergent PR cannot invent a second scheme.
- A condition names the targets it includes. The rule is exact: a branch is broad when a target listed later would take it, that is, when its condition holds with every `VERSION_` token false (`#if !VERSION_GAME01_REV0`, `#if !REGION_USA`), or when it is the `#else` of a chain none of whose conditions does. `VERSION_GAME01_REV0 && !VERSION_GAME01_REV1` is not broad, and neither is a double negation through a group. With two targets listed a broad branch is the other target's and `versions.py check` only warns; from the third listed target on it is an error, so the pull request that lists a third target makes every such block explicit, with `#elif VERSION_GAME01_REV1` or a group. `view` and `diff` resolve a broad branch like any other.
- Inline blocks are the default. When a function would carry three or more blocks, or more than about a third of its lines inside blocks, write the whole function once per variant under one function-level `#if ... #else ... #endif`, in the same file. Never a `src/<id>/` file for a unit two targets share.
- A unit that matches on some targets only is `Object(MatchingFor("GAME01-rev0"), "unit.cpp")`; a unit absent from a target is absent from that target's `splits.txt`. With two or more active targets a plain `Matching` claims every one of them, so `python3 tools/matching_scope.py check` fails it in `Tool tests` until the claim names its targets. Compiler or flag differences between targets are whole profiles chosen by `config.version` in `configure.py`, with a `compiler` evidence row in each target's `evidence.tsv`.

`tools/versions.py` reads this convention back:

```sh
python3 tools/versions.py view --target GAME01-rev0 src/unit.cpp
python3 tools/versions.py diff --target GAME01-rev0 --target GAME01-rev1 src/unit.cpp
python3 tools/versions.py check
```

`view` prints the file as one target compiles it: it resolves exactly the directives whose condition is a version expression and leaves every other directive and all macros untouched, so what you read is still source, not preprocessor output. `diff` is the unified diff between two targets' views; a reviewer of a change to a file with version blocks reads it instead of tracing the branches by eye. `check` fails on a `VERSION_` token that is not a known define or group, a `MatchingFor` argument that is not a known target id, a version condition mixed with other macros, any `BUILD_VERSION` in `src/` or `include/`, and, once three targets are listed, a branch a later target would take (a printed warning while two are listed). The `Tool tests` job runs `check`; the scaffold check runs it too.

A function decompiled for one target counts for another automatically when, on that target, `splits.txt` names the unit, `configure.py` says `Matching` or `MatchingFor` for it, and `symbols.txt` gives the function the same name, because objdiff pairs by symbol name. Different addresses are a per-target `symbols.txt` and `splits.txt` matter and never touch source; a function present on one target only, or data that differs, is an `#if` block with `MatchingFor` until both targets link. How a second target is activated without inheriting any claim, and how a map is carried across, is in [Multiple targets](/wiki/multi-target/).

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

The per-target directory, the define rule, the planner, the tiers, the Targets table and the settings are toolchain-neutral. The publish action converts objdiff reports and nothing else, and objdiff supports several architectures, so a project on another platform that produces `report.json` with `objdiff-cli report generate` can use the whole pipeline unchanged apart from these parameters:

- the original's path under `orig/<target id>/` (`PARAMETER 2` in `validate.yml`, the `COPY` in the Dockerfile, the toolchain's own config);
- the configure and build commands (`PARAMETER 3` in `validate.yml`), which must fail unless the complete executable matches and must write `build/<target id>/report.json`;
- `config/<target id>/` holds a splat or custom configuration instead of dtk's three files; `tools/versions.py` reads the same `#if` convention, and the `MatchingFor` equivalent lives in whatever generates the build;
- the `code-sections` and `unit-prefix` inputs of the publish action and of the report check if the defaults do not fit;
- in `tools/measuring_tools.py`, `TAGS` (the version lines of `configure.py` to report) or `PINS` (the JSON pin files of a build without `configure.py`), and `VERIFY`, the commands that confirm each image-installed tool's version against the pin.

A producer that writes its own report sets a unit's `metadata.complete` only when the whole unit links from source into the byte-identical executable: that is what `linked` means on the site. A status of the producer's own, such as whether a unit's boundaries have evidence, stays in the repository's files; the contract has no field for it and it never sets `complete`. Bytes of a code section that no function covers (alignment padding, code the producer does not split into functions) become one `(other code)` tile per piece on the site, holding the matched bytes no exact function accounts for ([Data contract](/wiki/data-contract/)).

A project that cannot produce an objdiff report cannot use the publish action as shipped; that is a site-side change and outside this guide.
