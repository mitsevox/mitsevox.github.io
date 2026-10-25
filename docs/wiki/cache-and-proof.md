# Cache & proof

Optional acceleration after fresh validation and publication work correctly.

## Three mechanisms, three meanings

| Mechanism | Reuses | What still runs |
| --- | --- | --- |
| Inventory cache | Target inventory/analysis metadata | Identity, input and metadata integrity checks; fresh build/measurement unless separate proof covers them |
| Compile/measurement cache | Exact-input objects and comparison results | Dependency validation, complete target verification and report reconciliation |
| Publication proof | A successful integrated build's public report package | Upstream execution/artifact authentication, complete landed-tree check, attribution when enabled and history validation |

An Actions cache is disposable acceleration. An authenticated artifact is execution evidence. The site's durable report store preserves accepted history. None substitutes for the others.

## Adoption sequence

First run fresh input checks, build, comparisons, tests, export and main publication successfully. Test their failure paths. Then enable inventory reuse, audited build caches and publication reuse separately, testing each boundary before enabling the next. They are optional; a project can remain on fresh validation indefinitely.

Use trusted main runs as the only writers of shared compiler/measurement results. PRs restore and validate entries but never save them. A full main build uses audit mode: compile and measure fresh; compare every still-valid cached entry with the fresh result; fail on disagreement; replace the local cache with fresh results before saving. A missing or invalidated key is a fresh computation, not a failed audit.

Branches may be able to read main caches. Do not assume caches can safely contain credentials or restricted originals. Objects may also contain recoverable target bytes: the owner must approve what cache storage and access permit. Keep such files out of public report artifacts and website Git. See GitHub's [cache access and retention rules](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

## Inventory keys

Bind inventory metadata to target hash, approved environment, analysis tool identity, inventory configuration and geometry/data extents that influence discovery. Store an internal receipt with those inputs and the metadata digest. A restore prefix can locate a candidate, but cannot validate it.

If internal identity or integrity fails, delete the restored inventory and regenerate. A broad tools-directory key is conservative and may invalidate inventory after unrelated tooling edits; document that cost. Narrow keys only when dependencies are established and failure-tested.

## Compile keys and invalidation

Bind a compiled object to:

- Source bytes, compiler/linker-driver identities, compiler profile/flags and comparison-build selection.
- Include search order, compile directory and generated compiler inputs.
- Every dependency actually read by the compiler, with content hashes.
- Relevant symlinks and files that can shadow an include, including case-insensitive name collisions where applicable.

Do not derive dependency coverage from the source file alone. If reliable dependency discovery is unavailable, disable object reuse or include a conservative full dependency universe. A same-named newly added header can change resolution even though the old header did not change.

In use mode, restore only a valid object and its dependency receipt. In audit mode, rebuild and compare object bytes and the declared reproducibility outputs for the same valid key. A disagreement fails the run; do not silently accept the cached or fresh version as a repair.

## Measurement keys and invalidation

Bind the result to compared object bytes, configured placement/full function extents, resolved referenced-symbol addresses, overlapping accepted source, relevant data slices, target identity and measurement tools/methodology. Restore referenced linked comparison outputs too, then run the same extent/arithmetic/integrity checks used for fresh results.

Changing a declaration can invalidate compilation; changing a symbol address or accepted placement can invalidate measurement without changing the comparison object's bytes. Retired extents must not remain in the exported inventory. Record compile and measurement hit/miss/audit counts separately.

## Save and bootstrap rules

Save build caches only after successful full main validation, on a main push or an explicitly requested main audit dispatch. Default manual runs validate but do not write shared caches. Other branches and PRs never save. Inventory caching can have its own explicitly documented main-only save policy.

Actions cache entries use immutable keys. Use a save identity including target/environment compatibility, source revision and run/attempt so a later explicit audit can save a new entry even on the same source revision. Restore by a compatible prefix and validate each internal key. A key match is not a proof of trusted origin or input equality.

A cold PR can produce a publishable fresh proof. Main may reuse it and skip the full build, so no compiler cache gets seeded. Provide an explicit main audit input to bypass proof selection and force fresh validation/cache save:

```sh
gh workflow run validate.yml --ref main -f audit_build_cache=true
```

This is the starter workflow's filename/input. An adopted project documents its actual equivalent. A rerun of a failed seed needs a new save identity, not deletion of a valid shared entry to force an overwrite.

## Publication eligibility

For this cache model, a PR that reused any compiled object or measurement may pass validation but cannot upload a reusable full-build proof. Sum reuse counts from all applicable cache layers; missing or malformed enabled-cache statistics must fail eligibility. Zero reuse means computation was fresh, not that no cache was restored.

A zero-reuse PR retains host receipt verification and may upload a full report-v1 package. A cached PR can omit a redundant host live-receipt re-export only after tests establish the primary export already checks those receipts; keep host unit tests and all semantic checks. Main full validation retains that re-export.

Main attempts proof selection unless an explicit audit was requested. Missing, expired or incompatible proof selects full validation. Invalid attribution or history discovered during promotion blocks publication; it must not be bypassed by resetting history or relabeling the result full.

## Authenticate the original proof

Before selecting reuse, verify these independently of downloaded JSON claims:

1. Same registered repository; successful permitted event/workflow/run/attempt and expected validation job/steps.
2. Approved workflow Git blob and tool/environment identities. On PRs, distinguish the API's head SHA from the actual tested merge commit and its parents.
3. Artifact name, originating run, attempt time window, size, digest and bounded safe archive contents.
4. Exact target, complete source tree, method/generation and input/output checksums. The tested integrated tree must equal the landed tree.
5. A successful full lane, zero reused results under the approved producing workflow, and unchanged measured summary/map/credits.

Never combine several PR reports into proof of a combined build. A changed tree requires fresh integrated validation. See [PR event identities](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request) and the [implemented platform receipt contract](/docs/reporting/platform.md#execution-policy-and-reuse).

## Promote without claiming a rebuild

Retain the original revision, tree, run/attempt, artifact digest and measurement time in the reused receipt. Record the landed revision and publication time separately. Recheck enabled attribution against landed history, restore previously accepted history, and append the current publication. Candidate-only PR history must not become a fake landed milestone.

The common importer supports reuse of an original full report-v1 package. A private custom proof layout must first be adapted to that contract; uploading arbitrary JSON with a real run ID is insufficient. Keep historical policies readable when approving a new producer workflow.

## Required experiments before enabling acceleration

| Experiment | Expected result |
| --- | --- |
| Cold then warm PR on identical inputs | Equal measured outputs, excluding explicitly volatile timestamps; observed hit counts and durations |
| Source/header/profile change | Only valid dependencies reuse; affected objects rebuild |
| New shadowing header or changed symlink | Relevant object key invalidates |
| Symbol address, placement, data or target change | Affected measurements invalidate |
| Deliberately altered valid cached object/result | Main audit fails on disagreement |
| Cached PR | Green if valid, but no reusable proof artifact |
| Fresh PR, identical landed tree | Main authenticates reuse, with original measurement time |
| Missing proof or changed tree | Main performs full validation |
| Explicit audit on main | Selection skipped, full fresh path and permitted save |
| Default/branch dispatch | No shared build-cache save |
| Expired evidence or corrupt prior history | No unauthenticated new import or silent history reset |

Measure hosted cold/warm timings after seeding. Local speed, a projected duration or a fixture's log line is not evidence of hosted cache reuse. Do not repeat expensive checks merely to decorate a handoff; rerun when inputs, failures or coverage gaps justify it.
