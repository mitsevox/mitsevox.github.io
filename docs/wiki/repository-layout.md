# Repository layout

What the public repository tracks, what it ignores and where each file lives.

## The public repository

This is the layout of a GameCube or Wii project built with [dtk-template](https://github.com/encounter/dtk-template), with the files the starter kit provides marked. Keep the names: the CI workflow, the tools, the scaffold check and the publish action refer to them.

```text
game/
  README.md                      targets, owner, build commands; seven fixed headings
  CONTRIBUTING.md                tiers, task loop, matching integrity, checklist  (starter)
  AGENTS.md                      fixed header, then the project's own section    (starter)
  CLAUDE.md                      one line: @AGENTS.md                            (starter)
  CREDITS.md                     origin and license of imported source           (starter)
  .gitignore, .gitattributes     originals, generated output; LF for toolkit files (starter)
  configure.py                   build configuration: libraries, objects, flags (dtk-template)
  config/
    targets.json                 the target list, schema 1                      (starter)
    site.json                    presentation on the site                       (starter)
    ci-targets.json              which shared paths affect every target         (starter)
    README.md                    evidence record format                         (starter)
    GAME01-rev0/                 one directory per target, named by its id
      config.yml                 decomp-toolkit project: original path, hash, symbols, splits
      splits.txt, symbols.txt    toolkit inputs
      build.sha1                 expected hash of the built executable
      evidence.tsv               curated claims
      README.md                  the target in one paragraph
  src/                           reconstructed source, shared by every target
  include/
    version.h                    the version-difference rule and group macros   (starter)
  tools/
    __init__.py                                                                 (starter)
    targets.py                   reads config/targets.json, derives the define  (starter)
    ci_targets.py                selects affected targets in CI                 (starter)
    versions.py                  view, diff and check version differences       (starter)
    evidence.py                  checks evidence.tsv                            (starter)
    new_target.py                scaffolds config/<id>/                         (starter)
    matching_scope.py            shows, pins and checks what each unit claims to link on (starter)
    measuring_tools.py           lists tool versions for provenance, verifies them (starter)
    tier.py                      the review tier a diff needs, checked in CI    (starter)
    credits.py                   the credits a merge will publish, checked in CI (starter)
    project.py, ninja_syntax.py, download_tool.py, ...   dtk-template
  tests/
    test_targets.py                                                             (starter)
  docs/                          durable project knowledge
  references/                    text only, regenerable by a named tool, no file over 4 MB
  licenses/                      license texts of imported source
  orig/GAME01-rev0/.gitkeep      where the original goes locally; the file itself is ignored
  build/                         generated, ignored
  .github/
    workflows/validate.yml                                                      (starter)
    pull_request_template.md                                                    (starter)
```

Three directories are keyed by the target id and nothing else: `config/<target id>/` for inputs, `orig/<target id>/` for the original, `build/<target id>/` for everything generated, including `build.ninja`, `objdiff.json` and `report.json`. Switching targets never overwrites another target's files. This holds for a project with a single target too: there is no flat, unkeyed layout to grow out of later.

## Shared and per target

A file is per target only when it holds an address, a hash or a unit list of one binary: `config/<id>/config.yml`, `splits.txt`, `symbols.txt`, `build.sha1`, `evidence.tsv`, `README.md`, an `ldscript.tpl` when the toolkit needs one, and tool reports. Everything else has one copy: `src/`, `include/`, `configure.py` listing the union of units, `tools/`, `tests/`, `docs/`, `references/` and the three JSON files under `config/`. A unit that exists on some targets only is simply absent from the other targets' `splits.txt`; there is no per-target source file and no unit-to-target table. Version differences inside a shared file are `#if VERSION_<ID>` blocks, described in [Build, verify, measure](/wiki/build-verify-measure/#version-differences).

## The root allowlist

The root holds the required files plus these directories and nothing else: `src/`, `include/`, `extern/` (verbatim imported source trees, each with its own credits), `tools/`, `tests/`, `docs/`, `references/`, `licenses/`, `orig/`, `build/`, `config/`, `.github/`, `.vscode/`, and the files `LICENSE`, `CLAUDE.md` and `.flake8`. Anything else at the root is a warning from the scaffold check; project material goes under `docs/`, `tools/` or `references/`. Two things never exist: a copy of upstream toolkit documentation under `docs/dtk/`, and `config/<id>/config.example.yml`; link dtk-template at its pinned revision from the README instead.

## Tracked and ignored

Public Git holds reviewed source, headers, tools, curated evidence and configuration. It never holds:

- original executables, disc images or extracted assets (`orig/*/*` is ignored; `orig/<target id>/.gitkeep` marks the directory);
- generated objects, build directories, objdiff and editor configuration (`build/`, `build.ninja`, `objdiff.json`, `compile_commands.json`);
- complete debug exports, private analysis databases or discarded trial variants.

The starter `.gitignore` covers these for a dtk-template project; the scaffold check requires it to cover `orig/*/*`, `build/`, `*.dol` and `*.elf` at least. A `.gitignore` entry does not remove a file already tracked; inspect `git status` before every commit that touches `orig/`.

## The private repository

```text
game-build/
  Dockerfile                     originals + toolchain into one image      (starter)
  .github/workflows/image.yml    builds, verifies and publishes the image  (starter)
  README.md                                                                (starter)
  orig/GAME01-rev0/main.dol      the original, committed here
```

The private repository is the only place the original is stored. It is committed there because the image build copies it in and checks its hash; see [Build environment](/wiki/build-environment/).

## The data repository

You do not create this one; the publish action writes into it. For reference, it looks like this after the first publish of `game`:

```text
decomp-data/
  index.json                     {"schema": 1, "games": ["game", ...]}
  .nojekyll
  .github/workflows/deploy.yml   Pages deploy on every push
  data/game/game.json            presentation and the target list
  data/game/cover.webp           optional, committed by hand
  data/game/GAME01-rev0/latest.json
  data/game/GAME01-rev0/history.json
  data/game/GAME01-rev0/map.json
```

Only active targets have a directory. See [Data contract](/wiki/data-contract/).

## Naming

- Target ids are `[A-Za-z0-9._-]+` and stable forever: they name directories, the site's `?target=` value and the data directory. The convention is `<label>-rev<N>` for discs with a game id (`GAME01-rev0`) and `<serial>-v<version>` where the platform carries a serial and a version (`SLUS-20349-v1.01`).
- A target's define is `VERSION_<ID>` with the id upper-cased and `-` and `.` replaced by `_`: `GAME01-rev0` gives `VERSION_GAME01_REV0`, `SLUS-20349-v1.01` gives `VERSION_SLUS_20349_V1_01`. `tools/targets.py define <id>` prints it; nothing stores it.
- The slug is `[a-z0-9][a-z0-9-]*` and names the game on the site: `/games/<slug>/` and `data/<slug>/`.
- Unit names are source paths. Unknown functions keep tool-generated address labels (`fn_<hex>` with decomp-toolkit, `func_<hex>` with splat). The publish action counts a function as `named` only when its symbol is not such a label, so a descriptive name is a claim and needs evidence.
- Files under `src/` use recovered paths when established; a descriptive file name counts as named while its boundaries remain provisional.
- Branch names are free. The aggregate CI check is always named `Validate targets`.
