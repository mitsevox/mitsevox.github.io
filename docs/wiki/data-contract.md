# Data contract

The schema-1 files the publish action writes and the checker that enforces them.

The authoritative text is [`contract/README.md`](https://github.com/mitsevox/mitsevox.github.io/blob/main/contract/README.md) in the site repository, and its executable form is `publish.py check <tree>`: if the two ever disagree, the checker is right. A copy of the contract is in the starter archive. This chapter restates it for the producer's point of view.

## Layout

```text
index.json                          {"schema": 1, "games": ["game", ...]}
data/game/game.json                 presentation and the target list
data/game/cover.webp                optional, committed by hand
data/game/GAME01-rev0/latest.json   the newest measurement
data/game/GAME01-rev0/history.json  every measurement, append-only
data/game/GAME01-rev0/map.json      the newest measurement's tile map
data/game/GAME01-rev0/contributors.json   optional
```

A `(game, target)` pair is the unit of everything; a game with one target has one entry. Only `active` targets have a directory. The producer owns `config/targets.json` and `config/site.json` ([Targets](/wiki/targets/)); the action derives everything else from them and from the objdiff report.

## game.json

`site.json` plus `repository` (`owner/game`), `defaultTarget` and `targets` from `targets.json`, with `schema: 1`. Rewritten by every publish of any active target.

## latest.json

```json
{"schema": 1, "game": "game", "target": "GAME01-rev0",
 "source": {"revision": "<commit sha>", "committedAt": "2026-01-02T00:00:00Z", "title": "<commit subject>",
            "url": "https://github.com/owner/game/commit/<sha>",
            "runUrl": "https://github.com/owner/game/actions/runs/<id>"},
 "measuredAt": "2026-01-02T00:01:00Z",
 "tools": [{"name": "build-environment", "version": "ghcr.io/owner/game-build@sha256:..."},
           {"name": "dtk", "version": "v1.8.3"}, {"name": "objdiff", "version": "v3.6.1"}],
 "summary": {
   "code": {"total": 1618968, "linked": 213044, "matched": 260640, "fuzzy": 292438.68},
   "data": {"total": 870056, "linked": 131316, "matched": 157536, "fuzzy": 183267.63},
   "functions": {"total": 4746, "exact": 1253, "named": 2595},
   "files": {"total": 519, "exact": 119, "named": 374}},
 "modules": {"map": "map.json", "contributors": null},
 "digests": {"map.json": "3f0c6a9e5b1d2c47", "history.json": "9a71e0c4d2b8f615"}}
```

| Field | Meaning |
| --- | --- |
| `source` | The measured commit: its SHA, commit time, subject, URL and the CI run that measured it (`runUrl` is the provenance) |
| `digests` | For each of `map.json`, `history.json` and `contributors.json` beside this file: the first 16 hex digits of its SHA-256. The page fetches those files by digest (`?v=<digest>`), so a corrected file is a new URL ([Publishing](/wiki/publishing/), "Correcting published data"). Absent in data published before the digests existed; the page then keys by the revision |
| `measuredAt` | The `measured-at` input, UTC |
| `tools` | The `tools` input, one object per line |
| `summary.code`, `summary.data` | Bytes of the original: `total`, `linked` (units that link into the byte-identical executable), `matched` (bytes matching exactly, linked or not), `fuzzy` (size-weighted similarity; may be `null`) |
| `summary.functions` | `total`, `exact` (100% match) and `named` (symbol is not `fn_<hex>` or `func_<hex>`); may be `null` |
| `summary.files` | Units: `total`, `named` (not tool-generated) and `exact` (named and fully matched); may be `null` |
| `modules` | `map` names the map file; `contributors` names the optional contributors file or is `null` |

`linked`, `matched` and `fuzzy` overlap and are never added together. `matched <= fuzzy <= total`, exactly: there is no tolerance, in the checker or on the page, so a fuzzy value a rounding step below `matched` is refused, which is why the action holds a data section's fuzzy within those bounds when it converts a percentage back into bytes.

## history.json

A JSON array, one row per line, ordered by `measuredAt`, at most one row per revision:

```json
[
{"code":{"total":1610980,"linked":0,"matched":null,"fuzzy":null},"data":{"total":870068,"linked":0,"matched":null,"fuzzy":null},"functions":null,"measuredAt":"2026-10-26T16:34:26Z","revision":"<sha>","legacy":{"provenance":{"kind":"measured","source":"validate.yml run 40360367860"}}},
{"code":{"total":1618968,"linked":213044,"matched":260640,"fuzzy":292438.68},"data":{"total":870056,"linked":131316,"matched":157536,"fuzzy":183267.63},"functions":{"total":4746,"exact":1253,"named":2595},"measuredAt":"2026-10-27T19:52:22Z","revision":"<sha>"}
]
```

Each row carries `revision`, `measuredAt`, `code`, `data` and `functions` from the measurement. The action appends one row per newly measured revision and never edits or removes a row. Rows imported from an older system keep whatever they had (missing measures are `null`) and their original provenance under `legacy`; nothing writes `legacy` today. The latest revision's row equals `latest.json`'s `total` and `linked`. The site draws the history chart from this file, so the first `main` publish starts the chart with one point; there is no way, and no need, to backfill.

## map.json

`{"schema": 1, "files": [<node>, ...], "sections": [<node>, ...]}`: two views of the same bytes. `files` groups function tiles by source unit (what the page draws) and adds one data tile per unit; `sections` groups the same functions by code section plus one `Data sections` group. A node is `{"name", "kind": "code"|"data", "size", "linked", "matched", "fuzzy"}` plus either `address` (a leaf) or `mapped_extents` (`[{"start", "end"}]`, hex), and optionally `children`. Function leaves add `"type": "function"`, `function_address` and `original_size`. Code a unit's functions do not cover (alignment padding, code the producer does not split into functions) is one leaf per section piece named `<unit> (other code)`, without a `type`, holding the matched bytes no exact function accounts for; dtk-template reports have none.

The checker enforces that a parent's measures are its children's sums, that extents never overlap, that both views cover exactly the same bytes, that per kind the top-level nodes sum to the summary, and that every function is covered once with counts matching the summary. The action builds the map from the same report as the summary, so a producer never writes it by hand.

## contributors.json

Optional; `modules.contributors` names it when present. The publish action writes it when the producer's `config/site.json` sets `"contributors": true` ([Publishing](/wiki/publishing/), "Credits"); otherwise it writes `"contributors": null`. The shape is `{"schema": 1, "credited_functions": N, "contributors": [{"id", "login", "functions"}], "functions": [{"id": "<target>:<address>:<size>", "authors": [id], "since"}], "retired": [...], "people": [{"id", "login"}]}`. Every exact function is credited once and the totals agree with the summary; `contributors` is the ranking (everyone with a credit, most functions first, then by login); `since` is the commit time of the earliest measured build in which the function was exact (a credit imported without one is kept as it is); `retired` keeps the credits of functions no longer exact, never overlapping the current ones; `people` names everyone a credit refers to. The page shows contributor rankings only when the file exists.

## Validation rules the producer meets

| Rule | Where it bites |
| --- | --- |
| Target ids `[A-Za-z0-9._-]+`, unique; default listed; platform lower case; `sha1` 40 lower-case hex; status in `active`, `planned`, `archived` | `targets.json` |
| `slug` `[a-z0-9][a-z0-9-]*`; `title` and `console` non-empty strings | `site.json` |
| Report function count and exact count equal its `measures` | The objdiff report; a mismatch means a different objdiff version or an edited report |
| Every function inside a code section of its unit; data sections sum to the unit's `total_data` | The report against `code-sections` |
| Timestamps UTC ISO 8601 | `measured-at` |
| One history row per revision, in `measuredAt` order | Only the action writes it |
| Every digest in `latest.json` equals its file's | A hand correction without `publish.py reseal` |

## Versioning

Adding a field never changes `schema`; readers ignore fields they do not know. A breaking change bumps `schema`, rewrites the whole data repository in one commit and switches the site in the same change; the action at `@main` follows, and producers pick it up on their next run without editing anything. Writers are strict and readers are lenient: the action refuses anything the checker rejects, and the site shows "unavailable" for a target whose files do not parse.

Two readers check the data: `publish.py check` before every push, and the page's own validator before every draw. They must agree, and the site repository keeps them agreeing in two ways: its tests run the page's validator on what the publisher writes, and its `Live data` job runs `python3 tools/check_data_tree.py` on a fresh clone of the data repository, with both readers, on every change to the site and once a day. The job checks every target that has a measurement, archived ones included, which is more than the page shows and exactly what every publish enforces. It is its own job, which the deploy does not wait for: a bad publish in another repository must not block the site, and a red run names the game, target, file and the data repository's commit. If the data is wrong, correct it ([Publishing](/wiki/publishing/)); if the new check is wrong, fix the check.
