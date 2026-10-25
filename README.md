# mitsevox decompilation portfolio

Shared portfolio frontend and project wiki for mitsevox’s decompilation projects.

This repository publishes the approved frontend and documentation source. GitHub Pages remains disabled while the production reporting integration is built and verified. Game CI and reporting workflows are unchanged.

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

NFL Street 2 uses a frozen copy of the public progress and activity reports captured on 2026-10-25 (revision d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211). It is not a live feed.

MVP Baseball 2005 and Tiger Woods PGA Tour 2004 use synthetic layout fixtures. Their counts, file/function maps, timelines, contributor rankings, and revision strings are illustrative, not project measurements. Visual sample badges were removed during design iteration; these fixtures remain synthetic and must not be published as measured progress. Sample contributors do not link to real accounts or request avatars.

The UI is approved. The proposed [shared reporting architecture](docs/reporting/README.md) documents CI standardization, report contracts, modular configuration and migration. Those changes are not implemented yet; the current local data shape is not the new production contract.

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
