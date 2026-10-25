# mitsevox decompilation portfolio

Shared portfolio frontend and project wiki for mitsevox’s decompilation projects.

This repository owns the portfolio frontend, wiki and GitHub Pages publication. Production includes authenticated NFL Street 2 data; other projects appear when their registered standard reports are verified. Game CI and reporting workflows are unchanged.

Build with `uv run --locked python tools/build_site.py --output build/site`, then serve that directory with `python3 -m http.server 54872 --bind 127.0.0.1 --directory build/site`. Use a fresh output path for each retained candidate.

## Structure

- `/`: project hub.
- `/wiki/`: searchable project handbook, shared shell, deep-linked chapters and starter downloads.
- `docs/wiki/`: handbook Markdown and editable starter files; rebuild with `uv run tools/build_wiki.py`.
- `/games/nflstreet2/`, `/games/mvp2005/`, `/games/tw2004/`: static entry points to one shared renderer.
- `assets/app.js`: History API routing; the header/footer stay mounted while page content changes. Normal links, deep-link refresh, and browser back/forward keep working.
- `assets/hub.html` and `assets/game.html`: shared page layouts.
- `assets/lifecycle.js`: page-scoped request, listener, and animation cleanup when navigating.
- `assets/projects.js`: game identity, artwork, repository URLs, and fixture locations.
- `assets/progress.js` and `assets/activity.js`: shared progress map, bars, timeline, and contributor rendering.
- `assets/style.css` and `assets/portfolio.css`: shared visual styling.

## Registered projects and reports

This is a personal shared platform for owner-registered repositories. `config/site.json` declares the owner/site identity; `config/producers.json` registers approved report sources; `config/projects.json` supplies identity, artwork and enabled modules. Conforming `report-v1` producers use one importer, validator, installer, store and renderer. See [the platform interface](docs/reporting/platform.md) for schemas, packaging metadata, execution policy and commands.

The existing production source remains on its isolated compatibility adapter until its producer exports the standard format. Its current CI, measurements and history are preserved. Other games' old layout fixtures remain unregistered and never enter production output.

```sh
uv sync --locked
uv run --locked python tools/import_reports.py --all
uv run --locked python tools/build_site.py --output build/site
```

Each immutable package is selected by `data/reports.lock.json`. The builder validates all archived reports, generates routes for displayed projects, and fingerprints the shared release. Optional map/count/history/credit sections and contribution links are configured independently. Artwork is maintained centrally in the website repository.

The [generic handbook](docs/wiki/start-here.md) and [integration template](docs/reporting/onboarding.md) describe repository/CI responsibilities. The [legacy integration reference](docs/reporting/nflstreet2.md) records the existing compatibility path.

## Artwork

Game covers are owner-supplied files, organized as `assets/covers/<project-slug>.webp`. All retain the original pixel dimensions. JPEG inputs were encoded to lossless WebP to avoid additional compression loss; the existing Tiger Woods WebP was copied unchanged.

| Project | Asset | Dimensions |
| --- | --- | --- |
| NFL Street 2 | `assets/covers/nflstreet2.webp` | 630 × 908 |
| MVP Baseball 2005 | `assets/covers/mvp2005.webp` | 640 × 905 |
| Tiger Woods PGA Tour 2004 | `assets/covers/tw2004.webp` | 640 × 908 |

NFL Street 2 logo: existing public project website asset.

Cover artwork belongs to its respective rights holders and is used here to identify the games in the portfolio.

Homepage banners: owner-provided NFL Street 2 artwork from Downloads/decomp.dev art; updated MVP Baseball 2005 and Tiger Woods PGA Tour 2004 artwork from Downloads/Thumbnail.

GameCube menu glyph: Simple Icons v5.0.0, CC0-1.0 (https://github.com/simple-icons/simple-icons/tree/5.0.0). Nintendo GameCube is a Nintendo trademark.

Latest commit titles and descriptions in the summary fixtures are public GitHub snapshots captured on 2026-10-25; they are independent of progress report revisions and are not a live feed.

## Checks and automation

Run `uv sync --locked` and `uv run --locked python -m unittest discover -s tests -v`. Site CI validates and assembles candidates. Push/manual/scheduled refreshes restore all durable last-good packages and refresh registered producers. Successful current-main runs preserve snapshots on this repository’s data-only `report-data` branch before deploying Pages. PRs and work branches cannot publish. A failed refresh keeps the live site unchanged. Game repositories are never written. See [operations and rollout boundaries](docs/reporting/nflstreet2.md#automation-and-rollout-boundary).
