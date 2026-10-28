# Repository layout

What the public repository tracks, what it ignores and where each file lives.

## The public repository

This is the layout of a GameCube or Wii project built with [dtk-template](https://github.com/encounter/dtk-template), with the files this guide adds marked. Keep the names: the CI workflow, the tools and the publish action refer to them.

```text
game/
  README.md                      target, owner, build commands
  CONTRIBUTING.md                contribution, review and merge policy   (starter)
  AGENTS.md                      agent instructions                      (starter)
  .gitignore                     originals, generated output             (starter)
  .gitattributes                 optional: line endings for toolkit files
  configure.py                   build configuration: libraries, objects, flags (dtk-template)
  config/
    targets.json                 the target list, schema 1               (starter)
    site.json                    presentation on the site                (starter)
    ci-targets.json              which paths affect which target         (starter)
    README.md                    evidence record format                  (starter)
    GAME01-rev0/                 one directory per target, named by its id
      config.yml                 decomp-toolkit project: original path, hash, symbols, splits
      splits.txt, symbols.txt    toolkit inputs
      build.sha1                 expected hash of the built executable
      evidence.tsv               curated claims
  src/                           reconstructed source, complete and partial
  include/                       shared declarations
  tools/
    __init__.py                                                          (starter)
    targets.py                   reads and validates config/targets.json (starter)
    ci_targets.py                selects affected targets in CI          (starter)
    verify_target.py             checks the original's SHA-1             (starter)
    measuring_tools.py           lists tool versions for provenance      (starter)
    project.py, ninja_syntax.py, download_tool.py, ...   dtk-template
  tests/
    test_targets.py                                                      (starter)
    review_gate.mjs                                                      (starter)
  docs/                          durable documentation
  orig/GAME01-rev0/.gitkeep      where the original goes locally; the file itself is ignored
  build/                         generated, ignored
  .github/
    workflows/validate.yml                                               (starter)
    workflows/review.yml                                                 (starter)
    pull_request_template.md                                             (starter)
```

Three directories are keyed by the target id and nothing else: `config/<target id>/` for inputs, `orig/<target id>/` for the original, `build/<target id>/` for everything generated, including `build.ninja`, `objdiff.json` and `report.json`. Switching targets never overwrites another target's files. This holds for a project with a single target too: there is no flat, unkeyed layout to grow out of later.

## Tracked and ignored

Public Git holds reviewed source, headers, tools, curated evidence and configuration. It never holds:

- original executables, disc images or extracted assets (`orig/*/*` is ignored; `orig/<target id>/.gitkeep` marks the directory);
- generated objects, build directories, objdiff and editor configuration (`build/`, `build.ninja`, `objdiff.json`, `compile_commands.json`);
- complete debug exports, private analysis databases or discarded trial variants.

The starter `.gitignore` covers these for a dtk-template project. A `.gitignore` entry does not remove a file already tracked; inspect `git status` before every commit that touches `orig/`.

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

- Target ids are `[A-Za-z0-9._-]+` and stable forever: they name directories, the site's `?target=` value and the data directory. `<label>-rev<revision>` is the convention the examples use.
- The slug is `[a-z0-9][a-z0-9-]*` and names the game on the site: `/games/<slug>/` and `data/<slug>/`.
- Unknown functions keep tool-generated address labels (`fn_<hex>` with decomp-toolkit, `func_<hex>` with splat). The publish action counts a function as `named` only when its symbol is not such a label, so a descriptive name is a claim and needs evidence.
- Files under `src/` use recovered paths when established; a descriptive file name counts as named while its boundaries remain provisional.
