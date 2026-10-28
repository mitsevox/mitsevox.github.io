# The site

How the data repository is served and read, cover art, URLs and local preview.

The site is static. It builds nothing and imports nothing: `mitsevox/mitsevox.github.io` deploys its own HTML, scripts and this wiki to GitHub Pages, and at view time the page fetches `/decomp-data/` from the same origin, which is the data repository's Pages deployment. A producer therefore never needs a pull request against the site. The one thing committed to the data repository by hand is cover art.

## The data repository's deploy

[`mitsevox/decomp-data`](https://github.com/mitsevox/decomp-data) holds `index.json`, `.nojekyll`, `data/` and one workflow, [`deploy.yml`](https://github.com/mitsevox/decomp-data/blob/main/.github/workflows/deploy.yml). Every publish is a push to `main`, and a push made with a GitHub App token starts the workflow, which checks out `main` and deploys the whole repository to Pages with `actions/upload-pages-artifact` and `actions/deploy-pages`. Its concurrency group is `pages` with `cancel-in-progress: false`: one deploy runs, one waits, and a burst of publishes collapses into a couple of deploys that each publish the branch tip. Pages serves it at `https://mitsevox.github.io/decomp-data/`.

For a new data repository of your own: create it public, add `index.json` with `{"schema": 1, "games": []}`, an empty `.nojekyll` and the same `deploy.yml`, and set the repository's Pages source to **GitHub Actions** ([documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)). The site repository's frontend reads `/decomp-data/` on its own origin, so a separate site would be a fork of the site repository with that path changed; that is outside this guide.

## How a page is composed

For `/games/game/?target=GAME01-rev0` the page reads:

1. `index.json`, to know the games.
2. `data/game/game.json`: title, console, year, repository link, `contributions`, `artwork`, `defaultTarget` and the target list. The target picker appears when there is more than one target and groups them by `label`, then `revision`.
3. `data/game/GAME01-rev0/latest.json` for each `active` target: the summary bars (linked, matched and fuzzy for code and data), the function and file counts when they are not `null`, the measured commit and run links, and the tools list.
4. `data/game/GAME01-rev0/map.json` when the summary's `modules.map` names it: the tile map.
5. `data/game/GAME01-rev0/history.json`: the progress chart.
6. `data/game/GAME01-rev0/contributors.json` when `modules.contributors` names it: rankings.

Without `?target=`, the page shows `defaultTarget`. A target that is not `active` is listed without a measurement. A target whose `latest.json` fails to load shows "unavailable" and leaves the rest of the game alone; a map or history file that fails the page's checks hides only its own section. The hub at `/` lists every game in `index.json` with its default target's code and data bars, the cover, the console icon chosen from `console`, and the latest commit.

## Cover art

Covers are committed by hand to the data repository, not published by CI, so that rights-sensitive images never pass through the producer or the automation:

1. Prepare `cover.webp` at the original aspect ratio (the reference covers are 1112 by 1600 pixels).
2. Commit it as `data/<slug>/cover.webp` in the data repository. The directory exists after the first publish; committing the cover earlier is fine too, since the publish only writes its own files.
3. Add `"artwork": {"cover": "cover.webp", "width": 1112, "height": 1600}` to the producer's `config/site.json` and merge. The next publish carries it into `game.json`.

Until both halves are in place the page shows no cover; an `artwork` entry without the file is a broken image.

## URLs

| URL | Serves |
| --- | --- |
| `https://mitsevox.github.io/` | The hub |
| `https://mitsevox.github.io/games/<slug>/` | The game at its default target |
| `https://mitsevox.github.io/games/<slug>/?target=<id>` | The game at one target |
| `https://mitsevox.github.io/decomp-data/data/<slug>/<id>/latest.json` | The raw data, same for every file in the data repository |
| `https://mitsevox.github.io/wiki/` | This guide |

The site repository's deploy stages one `games/<slug>/index.html` for every slug in the live `index.json`, so an established game's page answers with status 200. A game added since the last site deploy renders through the `404.html` shell, which is the same application; it becomes a real file at the next site deploy, which the owner can trigger with `workflow_dispatch` on the site's `Site` workflow.

## Previewing locally

Clone the site repository and the data repository, then serve the site at `/` and the data checkout at `/decomp-data/` with `404.html` as the fallback for unknown paths. The dry-run tree from [Publishing](/wiki/publishing/) can stand in for the data checkout to preview a game before its first real publish. The site repository's README has the same instructions and the test command (`python3 -m unittest discover -s tests`).

## What never needs a site change

Adding a game, adding a target, renaming a title, changing the cover, accepting contributions: all of these are edits to `config/site.json`, `config/targets.json` or the data repository. The site changes only when the contract changes or the presentation does.
