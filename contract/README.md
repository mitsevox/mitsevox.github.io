# Data contract (schema 1)

The site renders exactly one data format. Producers write it with the publish action
(`.github/actions/publish`); the action validates everything it writes, and the site reads it without
an import step. `publish.py check <tree>` is the executable form of this page: if this page and the
checker ever disagree, the checker is right and this page is the bug.

## Layout of the data repository

```
index.json                      {"schema": 1, "games": ["<game>", ...]}
data/<game>/game.json           presentation and the target list
data/<game>/cover.webp          optional, committed by hand
data/<game>/cover-thumb.webp    generated on deploy: 360px wide, what the site displays
data/<game>/<target>/latest.json    the newest measurement
data/<game>/<target>/history.json   every measurement, append-only
data/<game>/<target>/map.json       the newest measurement's tile map
```

A `(game, target)` pair is the unit of everything. A game with one target has one entry; nothing is
special about it. Only `active` targets have a directory.

## Versioning

- Adding a field never changes `schema`. Readers ignore fields they do not know.
- A breaking change bumps `schema`, ships a script that rewrites the whole data repository in one
  commit, and switches the site in the same change. The site never reads two schema versions.
- Writers are strict and readers are lenient: the publisher refuses anything the checker rejects, the
  site shows "unavailable" for a target whose files do not parse.

## Inputs the producer owns

`config/targets.json`, one entry per binary the project matches:

```json
{"schema": 1, "defaultTarget": "GAME01-rev0", "targets": [
  {"id": "GAME01-rev0", "platform": "gamecube", "label": "GAME01", "region": "USA", "revision": "0",
   "sha1": "<40 lower-case hex digits of the original binary>", "status": "active"}
]}
```

| Field | Meaning |
| --- | --- |
| `id` | `[A-Za-z0-9._-]+`, stable forever; it is the directory name and the `?target=` value |
| `platform` | lower-case platform name (`gamecube`, `ps2`, ...); identifies the toolchain family. The site's icon and console filter come from `site.json`'s `console` |
| `label`, `region`, `revision` | display strings; the target picker groups by `label`, then `revision` |
| `sha1` | identity of the original binary |
| `status` | `active` (built and measured), `planned` or `archived` (listed, never measured) |

`config/site.json`, presentation only:

```json
{"schema": 1, "slug": "game", "title": "A Game: Full Title", "shortTitle": "A Game",
 "console": "GameCube", "year": "2002", "contributions": {"accepting": false},
 "artwork": {"cover": "cover.webp", "width": 1112, "height": 1600}}
```

`slug` is `[a-z0-9][a-z0-9-]*` and names the game everywhere. `title` and `console` are required;
the rest is optional.

## game.json

`site.json` plus `repository` (`owner/name`), `defaultTarget` and `targets` from `targets.json`,
with `schema: 1`. Rewritten by every publish, so editing either input file and merging is how a
game's presentation changes.

## latest.json

```json
{"schema": 1, "game": "game", "target": "GAME01-rev0",
 "source": {"revision": "<commit sha>", "committedAt": "2026-01-02T00:00:00Z", "title": "<commit subject>",
            "url": "https://github.com/owner/game/commit/<sha>",
            "runUrl": "https://github.com/owner/game/actions/runs/<id>"},
 "measuredAt": "2026-01-02T00:01:00Z",
 "tools": [{"name": "objdiff", "version": "v3.6.1"}],
 "summary": {
   "code": {"total": 1618968, "linked": 213044, "matched": 260640, "fuzzy": 292438.68},
   "data": {"total": 870056, "linked": 131316, "matched": 157536, "fuzzy": 183267.63},
   "functions": {"total": 4746, "exact": 1253, "named": 2595},
   "files": {"total": 519, "exact": 119, "named": 374}},
 "modules": {"map": "map.json", "contributors": null},
 "digests": {"map.json": "3f0c6a9e5b1d2c47", "history.json": "9a71e0c4d2b8f615"}}
```

Measures, all in bytes of the original binary:

| Field | Meaning |
| --- | --- |
| `total` | bytes of that kind (code or data) in the original |
| `linked` | bytes in units that link from source into a byte-identical executable |
| `matched` | bytes that match exactly, linked or not |
| `fuzzy` | size-weighted similarity: each function or data section counts `size × match%`; may be `null` |

`linked`, `matched` and `fuzzy` overlap; they are never added together. `matched ≤ fuzzy ≤ total`,
exactly: no tolerance, or the page refuses the measure.
`functions` and `files` may be `null` when a producer cannot count them. A function is `named` when
its symbol is not a tool-generated address label (`fn_<hex>`, `func_<hex>`); a file is a source unit,
`named` when it is not a tool-generated address range, `exact` when it is named and fully matched.

`source.runUrl` is the provenance: the CI run that measured these numbers.

`digests` names, for each of `map.json`, `history.json` and `contributors.json` that exists beside
`latest.json`, the first 16 hex digits of the file's SHA-256. The page fetches `latest.json` with
revalidation and the three files by digest (`?v=<digest>`), so their URLs are immutable and a
corrected file is a new URL. The publisher writes the digests on every publish; a hand correction
in the data repository is followed by `publish.py reseal <tree>`, and `publish.py check` refuses a
digest that differs from its file. Data published before the digests existed has none; readers
then key the files by the revision.

## history.json

A JSON array, one row per line, ordered by `measuredAt`, at most one row per revision:

```json
[
{"code":{"total":1610980,"linked":0,"matched":null,"fuzzy":null},"data":{"total":870068,"linked":0,"matched":null,"fuzzy":null},"functions":null,"measuredAt":"2026-10-26T16:34:26Z","revision":"<sha>","legacy":{"provenance":{"kind":"measured","source":"validate.yml run 40360367860"}}},
{"code":{...},"data":{...},"functions":{"total":4746,"exact":1253,"named":2595},"measuredAt":"2026-10-27T19:52:22Z","revision":"<sha>"}
]
```

Rows carry the same measures as `latest.json`. Rows imported from an older system keep whatever they
had (missing measures are `null`) and their original provenance under `legacy`. Rows are never edited
or removed by the publisher; the latest revision's row always equals `latest.json`'s `total` and
`linked`.

## map.json

```json
{"schema": 1, "files": [<node>, ...], "sections": [<node>, ...]}
```

Two views of the same bytes: `files` groups tiles by source unit (what the page draws), `sections` by
binary section (a cross-check). A node is
`{"name", "kind": "code"|"data", "size", "linked", "matched", "fuzzy"}` plus either `address`
(a leaf occupying `size` bytes from there) or `mapped_extents` (`[{"start", "end"}]`, hex), and
optionally `children`. Function leaves add `"type": "function"`, `function_address` and
`original_size`. Optional evidence fields: `source` and `comparison_source` (repository-relative
paths), `complete`, `auto_generated`, `boundary`, `scope`. Code a unit's functions do not cover (alignment padding, code
the producer does not split into functions) is one leaf per section piece named `<unit> (other code)`,
without a `type`; the matched bytes no exact function accounts for are given to it.

The checker enforces: a parent's measures are its children's sums; extents never overlap; both views
cover exactly the same bytes; per kind, the top-level nodes sum to the summary; every function is
covered once and the function counts match the summary.

## contributors.json

Optional; `modules.contributors` names it when present. The publish action writes it when the
producer's `site.json` sets `"contributors": true`.

```json
{"schema": 1, "credited_functions": 2,
 "contributors": [{"id": 1, "login": "someone", "functions": 2}],
 "functions": [{"id": "<target>:0x80003100:36", "authors": [1], "since": "2026-01-01T00:00:00Z"}, ...],
 "retired": [{"id": "<target>:0x80003200:16", "authors": [1], "since": "2026-01-01T00:00:00Z"}],
 "people": [{"id": 1, "login": "someone"}]}
```

Every exact function is credited once; `credited_functions` equals the summary's exact function count,
and each person's `functions` equals the number of credits naming them. `contributors` is the ranking:
every person with at least one credit, most functions first, then by login. `since` is the commit time
of the earliest measured build in which the function was exact; a credit imported without one is kept as
it is. `retired` keeps the credits of
functions that are no longer exact, so a function that returns gets its first credit back; a retired id
is never also current. `people` names every person any credit refers to.
