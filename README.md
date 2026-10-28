# mitsevox decompilation tracker

A static site that shows progress for the owner's decompilation projects. It builds nothing and
imports nothing: each project's CI publishes its measurements to
[mitsevox/decomp-data](https://github.com/mitsevox/decomp-data), and this site reads them from
`/decomp-data/` at view time.

## How data gets here

1. A project's CI builds a target and runs objdiff, producing `report.json`.
2. On main, the publish action in [`.github/actions/publish/`](.github/actions/publish) converts it into the
   [schema-1 contract](contract/README.md), checks it, and pushes it to decomp-data.
3. decomp-data deploys itself to Pages; the next page view shows it.

Adding a game is a change to that game's repository only (`config/site.json`, `config/targets.json`
and the publish step); nothing here changes.

## Layout

- `index.html`, `404.html`: the app shell. Pages serves `404.html` for every path without a file,
  so `/games/<slug>/` needs no per-game file.
- `assets/projects.js`: reads `index.json`, each `game.json` and each target's `latest.json`.
- `assets/targets.js`: the view of a game at one target, and the target picker.
- `assets/reports.js`: summary, map and history readers, cached per revision; maps parse in
  `assets/report-worker.js`.
- `assets/progress.js`, `assets/activity.js`, `assets/identity.js`, `assets/hub.js`: rendering.
- `assets/pages/game.js`: the game page, composed from `assets/features/` (identity, summary, map,
  history, contributors). A feature is `mount(root, ctx) -> {ready, destroy}`; adding one is a module,
  a section in `assets/game.html` and one entry in the page's feature list.
- `assets/components/ui/`: shared controls (progress bars, search, dropdowns, commit rows, tooltips).
  Pages supply content and callbacks; components own markup, accessibility, motion and cleanup. See
  [the component contracts](docs/ui/components.md).
- `docs/wiki/`: wiki source; `uv run tools/build_wiki.py` renders it into `wiki/`.
- `redirects/`: aliases for retired URLs, copied to the site root on deploy.

## Develop

```sh
python3 -m unittest discover -s tests
```

To view locally, serve this directory at `/` and a decomp-data checkout at `/decomp-data/`, with
`404.html` as the fallback for unknown paths.
