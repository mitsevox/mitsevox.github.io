# CI implementation contract

This kit supplies generic orchestration, not a compiler or a target-specific build system.
An agent implements the adapter below using the repository's real tools. No adapter is
installed that returns fake success. An unavailable required operation is a setup gap and
must exit nonzero. A copied workflow alone is not a working pipeline.

## Adoption

1. Read the wiki's repository, agent-workflow, CI, cache/proof and website chapters.
2. Copy `config/ci.example.json` to `config/ci.json`, fill verified project facts, and map
   command arrays to existing tools. Values shown are illustrative filenames, not installed tools.
3. Confirm review/merge policy with the owner. The example defaults to independent accuracy
   and hostile review and owner-only merging. Alternatives are explicit project policy.
4. Decide attribution separately; leave all acceleration disabled initially. Record optional
   reporting capabilities and contribution acceptance in their appropriate producer/site settings.
5. Implement `tools/project_ci.py` with these operations and meaningful failure tests. It is
   a thin coordinator, not a replacement engine. Run argument arrays without `shell=True`;
   do not execute report-provided commands. Validate config keys/types and reject unresolved
   placeholders, unknown policies, missing inputs or nonexistent commands before building.
6. Adopt `.github/workflows/validate.yml.template` as `validate.yml`. Confirm branch names,
   host/runtime access and all pinned Actions. The default permits same-repository PRs;
   reject a foreign head before exposing private inputs. No deployment writes are granted.
7. Exercise fresh validation and report consumption. Enable acceleration one mechanism at a
   time only after Cache & proof's test matrix passes. Approve the workflow blob in site policy.

The internal config example is an editable project-owned format, not a site JSON schema.
`review` and `attribution` are deliberate policy choices; do not silently derive them from
whether a website section is visible. Record any different source objective and its checks.
`environment` must become the actual approved immutable tool identity. For a container,
wrap build/compare/test engine calls in that exact image; never execute them on whichever
compiler happens to exist on the CI host. Host Git/provenance checks can remain host-side.

## State and outputs

Every operation reads validated `config/ci.json` and current run context. Write generated
context/plan atomically under `build/ci/`; never take lane booleans from an artifact claim.
Success output is created only after its checks pass. Clear owned stale outputs before work.
GitHub outputs are single-line validated values appended to `GITHUB_OUTPUT`; missing/malformed
required output fails. Strict booleans are lowercase `true` or `false`. Cache counts are
nonnegative integers, not truthy strings. An enabled feature without its implementation fails.

`configure` records repository, target/hash, workflow blob, tool identities, event, actual
checkout SHA/tree, PR head/base/number when applicable, run ID/attempt and requested audit.
On PRs validate the actual merge parents; do not conflate API head SHA with checkout SHA.
Derive Git facts using Git and authenticated event/API metadata rather than caller text.
Read untrusted PR titles/bodies as data, never shell code.

## Operation interface

All commands use `python3 tools/project_ci.py OPERATION`; local equivalent commands must be
listed in README. Flags can be added for local reference paths, target or an explicit revision;
CI must bind them to actual event/checkout identities rather than accept arbitrary report claims.

| Operation | Required behavior and generated result |
| --- | --- |
| `configure` | Validate project facts/evidence/runtime pins and permitted source repository. Emit `inventory_cache`, `build_cache`, `proof_reuse`; each false until adopted. When inventory caching is enabled emit `inventory_key` and compatible `inventory_prefix`. When build caching is enabled emit compatible `build_prefix`. Prefixes bind OS, target and approved environment/tool identities; exact keys add real input digests. |
| `select-proof` | Only eligible main, proof reuse enabled, no explicit audit. Authenticate complete original execution/artifact/tree as specified below. Emit `reused=true` only with a complete locally checksummed selection receipt in `build/ci/proof.json`; unavailable/incompatible proof emits false and selects full validation. Do not swallow local config/programming errors as a valid reuse. |
| `plan` | Read strict `PROOF_REUSED`, `INVENTORY_HIT`, `AUDIT_REQUESTED` and verified configuration/event. Treat the Actions hit as a hint: verify the restored inventory's target/input receipt and metadata digest before accepting an exact hit. Emit `reused`, `full`, `inventory`. `full = not reused`; `inventory = full or not verified_inventory_hit`, with disabled/invalid caching treated as a miss. Audit forces full and forbids a reused selection. Exactly one full/reused lane is selected. |
| `ledger` | If tracking enabled, validate every existing entry's people, extents and original Git/source blobs, including predicted squash history when that merge policy applies. Fetch missing provenance in bounded batches; fail missing/invalid evidence. If disabled, record explicit policy reason; never invent credits. Full exact coverage is checked after measurement. |
| `baseline` | Verify original hash/geometry and tools; reproduce applicable original-byte baseline and linker checks; prepare pinned compiler stages. Produce bounded private receipts. Unsupported stages require documented objective-specific checks, not an unqualified byte-identical claim. |
| `build` | Clear stale output; run accepted-source build with cache off, use on PRs or fresh audit on main/non-PR validation. Compile independent units in parallel, link in deterministic manifest order, verify complete target objective and bind receipt to source/headers/config/profiles/tools/target. Preserve original bytes for unpromoted ranges. Record source compile stats when enabled. |
| `inventory` | Validate restored input/metadata receipt. Regenerate if absent/incompatible/corrupt. A restore prefix does not prove validity. Emit complete bounded inventory and its internal digest/inputs receipt under `build/inventory/`. |
| `test` | Run tool/contract/config/regression tests in approved runtime, including clearance logic if selected. Do not report reconstruction fidelity from unit tests alone. |
| `compare` | Measure every registered full comparison extent, enforce ranges/overlap/symbol/dependency integrity, and validate restored results like fresh ones. Emit actual measurements and `cache_reused`: sum source compile, comparison compile and measurement hits. With caching disabled emit 0; with caching enabled missing stats fails. |
| `export` | Derive all public views from the same verified measurement. Reconcile exact credit coverage and candidate/squash equality if tracking. Restore authenticated previous history on main; restore/append candidate history separately for PR evidence. Write only summary and supported module JSON under `build/public-input/`, plus actual packaging metadata outside that public-input directory. |
| `host-check` | Keep host provenance/export tests on every full run. If `LIVE_RECEIPTS=true`, also re-export/revalidate live receipts. A cached PR may skip only a demonstrated duplicate live re-export; it retains primary export validation and all other host checks. |
| `promote-proof` | Recheck selected proof integrity and actual landed tree, target, tools/method; reconcile landed credits when enabled and restore/append history. Populate public-input and reused packaging metadata. Preserve original measurement time/source proof; candidate-only merge snapshots are not landed history. Invalid attribution/history fails publication. |
| `package` | Call approved pinned shared `tools/package_report.py` with canonical public-input, actual execution metadata and approved policy; output a new `build/public-report/`. Mode is full or reused from verified plan. Never label a cache-derived PR as a reusable full proof. |
| `validate-package` | Run the common package/semantic validator against approved policy, target, files and checksums, then enforce exact public-file allowlist and no symlinks/private files. Fail before upload on any discrepancy. |

## Public packager wiring

The packager lives in the shared website tools. Acquire an owner-approved checkout at
`reportToolsRevision`, use its locked dependencies and invoke it from that checkout:

```sh
uv sync --locked
uv run --locked python tools/package_report.py \
  --input /absolute/path/to/project/build/public-input \
  --metadata /absolute/path/to/project/build/ci/execution-metadata.json \
  --policy /absolute/path/to/approved-producer.json \
  --output /absolute/path/to/project/build/public-report
```

Those are path examples, not shared configuration values. Runtime setup may use another
approved installation method, but tool/dependency versions and command results stay pinned.
The template pins uv setup; the adapter still acquires/verifies the configured site-tools
repository and commit. Do not assume an untracked sibling checkout exists on a fresh runner.
The packager validates the new output; the adapter's final validation additionally checks
its export allowlist and declared policy. Do not copy a packager from an unpinned branch.

Full metadata includes `project`, `repository`, `target`, actual `revision`/`tree`,
`methodology`, `generation`, `measuredAt`, `publishedAt`, `tools`, `runId`, `attempt`,
`workflowBlob`, `mode: full`, `source: null`. For reused metadata, `mode: reused` and
`source` carry the original revision/tree, run/attempt, artifact ID/SHA-256 and measurement
time exactly as the execution schema requires. Derive them from verified proof, not examples.

Canonical module files and schemas are defined by the platform contract, not internal engine
report names. A project implements that export mapping once. Unsupported modules are omitted
with the contract's unsupported declarations; no placeholder data or fake accounts.

## Producer policy mapping

Copy/adapt the shared producer-policy example with actual owner/project/target/tool/workflow
facts. For this workflow, set `workflow` to `.github/workflows/validate.yml`, `job` to
`Build and measure`, `artifact` to `public-report`, and the adopted default branch. Use the
actual workflow Git blob, not the source commit ID (`git rev-parse HEAD:.github/workflows/validate.yml`).

Recommended step mapping for the supplied flow:

```json
{
  "requiredSteps": [
    "Validate configuration and evidence", "Decide validation lanes",
    "Package public report", "Validate public report", "Upload public report"
  ],
  "lanes": {
    "full": [
      "Verify ledger provenance", "Verify baseline and prepare tools",
      "Build complete target", "Verify inventory", "Verify tools and contracts",
      "Measure source", "Export measured report", "Verify host receipts"
    ],
    "reused": ["Authenticate complete source proof"]
  }
}
```

This is only the step portion; a complete approved producer policy also needs its other schema
fields. Omit `lanes.reused` until implemented/enabled. `Select complete source proof` is not
common-required: an audit deliberately skips it. Exactly one lane succeeds on a published run.

The expected publisher is main push/manual, with actual final job/run success. PR full artifacts
are original proof candidates only. The source PR's API head SHA differs from its tested merge
revision; the consumer verifies both, parents, tree and same-repository identity. Renaming a
step or changing workflow code requires the site's reviewed producer-policy update. Keep prior
policies available for existing immutable reports; never widen trust automatically on refresh.

## Proof and cache contracts

The full original artifact is the standard report-v1 package, including manifest/receipt.
`select-proof` verifies upstream repository/workflow/job success, approved blob/tools,
run attempt, permitted event, artifact run/name/time/digest/size, tested merge parents and
exact landed tree. Main's `promote-proof` checks the selection receipt again, then validates
landed attribution/history. Missing/expired/incompatible original proof falls back to full;
invalid landed evidence never becomes an excuse to erase history.

Under this template, PRs with any cache hits get no public-report artifact. They still run
export checks and may pass candidate validation. Source and comparison caches are saved only
by successful full main pushes or explicit main audits. A restored cache entry is validated
per dependency key, not merely by Actions key. Main audit recomputes everything, compares
still-valid entries, fails disagreement and saves fresh output. Statistics and absence of
handoff must be demonstrated in real hosted runs before enabling proof reuse.

## Default permissions and deliberate adaptations

The workflow has no Pages/deployment or source-write permission. The game uploads public JSON;
the shared site imports, stores and renders it. If project-owned history needs a write job,
isolate that authority and authenticate its input first. The site store can satisfy durable
preservation without a second per-game history branch. Public temporary artifacts alone cannot.

The reference assumes a pinned Linux CI runtime and same-repository branches. Adapting to
another host, runner, default branch, executable format, fork policy or review model is a
project decision: update config, guards, tests and site policy together. A privileged clearance
workflow must not execute PR code. Implement/test its actual owner/record checks separately;
the chapter gives the complete record contract without assuming one review implementation.

## Verification record

Prove fresh PR and main success, wrong target/dependency/export/history failure and final-head
clearance behavior for the selected policy. Then, if enabled, prove warm equality, invalidation,
audit disagreement, zero/nonzero reuse handoff rules, identical/different-tree selection,
explicit main seed and branch/no-save guards. Check report values, artifact identity and the
next site refresh. Record revision, command, run/attempt, hashes, outcomes and remaining gaps.
Do not copy another project's timing, target or successful status as evidence for this setup.
