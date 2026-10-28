# Troubleshooting

Failure messages from the build, the publish action and the page, with their causes.

Find the layer that failed before changing anything: the plan, the tool tests, the image pull, the original, the build, the report conversion, the push, the deploy or the page. Each layer has its own messages, listed below as they appear in the job log.

## Plan and tool tests

| Message | Cause and fix |
| --- | --- |
| `Invalid target registry`, `Unknown target fields`, `Invalid target identity`, `Invalid target status`, `Duplicate target` | `config/targets.json` breaks a rule in [Targets](/wiki/targets/): exactly the seven fields per target, lower-case platform, 40 lower-case hex digits, status in `active`, `planned`, `archived`. |
| `Default target is not active` | `defaultTarget` names a planned or archived target. |
| `Invalid CI dependency map`, `CI dependencies must cover every known target`, `Unsafe CI dependency patterns` | `config/ci-targets.json`: the four keys, an entry for every target in `targets.json`, no leading `/` or `..` in patterns. |
| `Diff endpoints must be full commit SHAs` | The planner ran outside Actions or with an unusual event; run it with `--force-all` to audit everything. |
| `Configure REVIEW_OWNER before adopting clearance` | The `REVIEW_OWNER` variable is empty; `tests/review_gate.mjs` passes its own value, so this appears in the live workflow only. |
| `node --test` fails after editing `review.yml` | The test reads the script from the workflow file; keep the `script: |` block and its indentation intact. |

## Image and original

| Message | Cause and fix |
| --- | --- |
| The job fails while initializing the container (pull denied, unauthorized, manifest unknown) | The package is not readable by the public repository, or the digest is wrong. In the private package's settings add `owner/game` under Manage Actions access with Read, and copy the digest from the image workflow's summary. |
| `cp: cannot stat '/orig/<id>/sys/main.dol'` | The image does not hold that target, or the path differs from PARAMETER 2. Add the `COPY` and checksum to the Dockerfile and rebuild, or fix the path in both places. |
| `Missing/unsafe target original` | `orig/<id>/<ORIGINAL>` is absent or a symlink; locally, put your copy there. |
| `Original executable SHA-1 differs` | The file is not the binary `targets.json` names. Fix the file or, if the file is right, the `sha1` field (then the image's checksum line too). |
| `Target is not active` | `verify_target.py` was run for a planned or archived target. |
| `sha1sum: WARNING: 1 computed checksum did NOT match` during `docker build` | The original committed to the private repository differs from the Dockerfile's checksum line. |

## Build and measurement

| Symptom | Cause and fix |
| --- | --- |
| `configure.py` rejects `--version` | The id is not an active target in `config/targets.json`, or `configure.py` was not wired to `tools/targets.py` ([Build, verify, measure](/wiki/build-verify-measure/)). |
| The link succeeds but the hash check against `config/<id>/build.sha1` fails | A `Matching` object no longer matches, or `build.sha1` is wrong. Mark the object `NonMatching` until it matches; `build.sha1` must equal the original's `sha1`. |
| `ninja: error: ... report.json` or no report written | The `progress`/`report.json` targets need objdiff; check `config.objdiff_tag` and network access from the image, or pass `--objdiff` to a local binary. |
| Numbers look wrong on the page but the build is green | Compare with `ninja ... progress` locally at the same commit. `linked` only counts `Matching` units; `matched` counts exact functions anywhere; `fuzzy` is size-weighted. A new split or a renamed unit changes `files` counts without changing bytes. |
| `measuring_tools: validate.yml names no single pinned build image` | The `image:` line is not of the form `ghcr.io/<name>@sha256:<64 hex>`, or appears more than once. |
| `measuring_tools: configure.py has no objdiff_tag` | The `config.<tag> = "<version>"` line is missing or formatted differently; edit `TAGS` in `tools/measuring_tools.py` or the line. |

## Publish step

Every message from `publish.py` is prefixed `publish:` and fails the step; nothing is pushed.

| Message | Cause and fix |
| --- | --- |
| The `Mint a data-repository token` step fails | The App is not installed on the data repository, the client id or private key is wrong or empty, or the App lacks Contents read and write. Check the variable and secret names in `validate.yml` against the repository settings. |
| `DATA_TOKEN is not set` | The script ran outside the action without the token; use `--dry-run` locally. |
| `--repository or GITHUB_REPOSITORY is required` | Local run: pass `--repository owner/game`. |
| `Target <id> is not an active target of <slug>` | The published target is `planned` or `archived` in `targets.json`. |
| `targets.json lists no targets`, `Duplicate target id`, `Default target is not listed`, `Invalid target id`, `<id>: platform must be a lower-case name`, `<id>: sha1 must be 40 lower-case hex digits`, `<id>: status must be active, planned or archived` | `config/targets.json`; `tools/targets.py` would have rejected these too, so the tool tests catch them first. |
| `site.json: invalid slug`, `site.json: title is required`, `site.json: console is required` | `config/site.json`. |
| `Report lists N functions, its measures say M`, `Report has N exact functions, its measures say M` | The report's own totals disagree with its function list: an objdiff version with different semantics, or an edited report. Pin `config.objdiff_tag` to a known-good version. |
| `<unit>: <function> lies outside the code sections .init, .text` | The platform's code sections are named differently; pass `code-sections` to the action. |
| `<unit>: data sections do not add up to total_data` | A unit's `total_data` disagrees with its section sizes; usually the same objdiff version problem. |
| `history: duplicate revision`, `history: rows out of order`, `<slug>/<id>: history lacks the latest revision` | The data repository's existing files are inconsistent; someone edited them by hand. Revert that commit in the data repository. |
| `push failed (attempt N), retrying` then `push failed after 5 attempts` | Five consecutive lost races or a rejected push. Re-run the job; if it persists, check the App's permission and branch rules on the data repository. |
| `<slug>/<id> <sha> already published` | Not an error: the revision was published before (a re-run). The first measurement of a revision wins. |

## Deploy and page

| Symptom | Cause and fix |
| --- | --- |
| The data repository has the commit but the page is old | The data repository's `Deploy` workflow takes about a minute and queues bursts; wait, then reload. If `Deploy` did not run, the Pages source is not set to GitHub Actions. |
| A target shows "unavailable" | Its `latest.json` does not load or parse. A `map.json` or `history.json` that fails the page's checks hides only its own section ("Progress history unavailable"). Run `publish.py check` on a clone of the data repository to find the file. |
| The game is missing from the hub | Its slug is not in `index.json`; the first publish adds it. Check that the publish step ran on `main` (the condition is `github.ref == 'refs/heads/main' && github.event_name != 'pull_request'`). |
| `/games/<slug>/` returns 404 with the application shell | Normal for a game added since the last site deploy; the page still renders. The next site deploy stages a real file. |
| No cover | Both halves are needed: `data/<slug>/cover.webp` in the data repository and `artwork` in `config/site.json` followed by a publish. |
| No Contribute link | `contributions.accepting` is `false`, or there is no `guideUrl`, or the target has no report. |
| The history chart has one point | Expected after the first publish; every later `main` publish adds one. |

## Review gate

| Symptom | Cause and fix |
| --- | --- |
| `Owner review clearance` stays pending | In order: the PR is a draft; the clearance is not by `REVIEW_OWNER`; `Revision:` is not the current head; the two links are the same, malformed or point at another PR; a linked record's revision or verdict is wrong; a header line appears twice. The acceptance matrix in [Review gate](/wiki/review-gate/) lists every case. |
| The workflow does not run on comments | It is not on the default branch yet, or the comment is on an issue rather than a PR. |
| The status never appears on a PR from a fork | By design; fork PRs are not cleared and not built. |

## Recovery

A bad publish is a `git revert` in the data repository; the next publish appends on top. A bad image digest is a revert of the `validate.yml` change. Never edit measurement files in the data repository by hand, and never loosen a check, change a count or alter the build image to make a contribution pass; report the problem in an issue for the owner.
