# mitsevox decompilation portfolio

Shared portfolio frontend and project wiki for mitsevox’s decompilation projects.

This repository owns the portfolio frontend, wiki and GitHub Pages publication. Production includes authenticated NFL Street 2 data; the other games remain local previews until their adapters are verified. Game CI and reporting workflows are unchanged.

Run `python3 -m http.server 54872 --bind 127.0.0.1` from this directory, then open http://127.0.0.1:54872/.

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

## Data boundary

NFL Street 2 uses an authenticated, immutable package selected by `data/reports.lock.json`. Run `uv run --locked python tools/import_nfl.py` to refresh from its existing verified main artifacts. The browser reads packaged files, not a live GitHub feed. The original NFL fixture is retained only for design reference.

MVP Baseball 2005 and Tiger Woods PGA Tour 2004 use synthetic layout fixtures. Their counts, file/function maps, timelines, contributor rankings, and revision strings are illustrative, not project measurements. Visual sample badges were removed during design iteration; these fixtures remain synthetic and must not be published as measured progress. Sample contributors do not link to real accounts or request avatars.

The UI is approved. The [NFL adapter](docs/reporting/nflstreet2.md) implements authenticated ingestion, package validation, modular configuration and static assembly. The [shared architecture](docs/reporting/README.md) distinguishes this implementation from the remaining multi-game work.

Build the production candidate with `uv run --locked python tools/build_site.py --output build/site`, then serve that directory. It includes only verified, configured projects (currently NFL), and never copies synthetic fixtures. The source preview above retains all three layouts.

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

Run `uv sync --locked` and `uv run --locked python -m unittest discover -s tests -v`. Site CI validates and assembles candidates. Push/manual/scheduled refreshes restore the durable last-good package and read NFL artifacts. Successful current-main runs preserve snapshots on this repository’s data-only `report-data` branch before deploying Pages. PRs and work branches cannot publish. A failed refresh keeps the live site unchanged. Game repositories are never written. See [operations and rollout boundaries](docs/reporting/nflstreet2.md#automation-and-rollout-boundary).
