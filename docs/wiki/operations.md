# Troubleshooting & upkeep

Diagnose the failing layer before changing source, configuration or publication.

## Common failure patterns

| Symptom | First checks | Avoid |
| --- | --- | --- |
| Baseline fails | Target hash, section geometry, approved tools and complete-output diff | Editing the target or ignoring differing bytes |
| Source scores well but looks wrong | Types, calling convention, bounds and comparison coverage | Treating a percentage as semantic proof |
| A header edit breaks comparison | Dependency hashes, generated symbols and storage maps | Reusing stale reports |
| Linked/matched/fuzzy are equal | Actual registered partial comparisons and report numerators | Artificially separating values for appearance |
| Function tiles show only 0/100 | Per-function fuzzy fields and renderer mapping | Inferring scores from whole-file averages |
| Files exact stays low | Whole-unit boundary evidence and mapped extents | Equating green functions with known original files |
| Owner clearance stays pending | Current full head SHA, distinct valid records, draft status and owner identity | Bypassing the gate |
| History disappears | Restore source, artifact identity/digest and parser failure | Reinitializing an established timeline to empty |
| Older progress replaces newer | Run ordering, ancestry and latest-pointer promotion | Sorting publication by completion time |
| Site mixes old and new styling | Asset versions, deployment artifact and browser cache | Assuming a correct local page proves production |
| Missing contributors | Declared tracking policy, exact inventory and preserved provenance | Assigning everything to the merger |
| New CI works but site refresh rejects it | Approved workflow Git blob, common/selected lane steps and actual run attempt | Automatically trusting changed workflow code |
| Audit run fails the site's step check | Selection may be intentionally skipped; full lane must still prove fresh validation | Requiring proof selection on all lanes or dropping full-build checks |
| Warm PR has no reusable artifact | Actual compile/measurement reuse counters and the zero-reuse publication rule | Relabeling cached work as fresh proof |
| Cache never appears after cold PR/main | Main may reuse proof and skip cache production; run the explicit main audit | Letting PRs save trusted shared caches |
| Main cache audit disagrees | Nondeterminism, incomplete keys or changed dependency resolution | Ignoring the disagreement or silently choosing one result |
| Repeated audit cannot save a refreshed cache | Immutable Actions save key; include run/attempt in build-cache identity | Deleting unrelated valid caches or assuming save overwrote them |

## Investigate with a bounded record

Record failing revision, target, tool environment, command, observed output and the specific question. Reproduce the smallest relevant scope, compare with the base revision, then fix the cause. Expand checks when evidence shows a wider dependency; do not repeat full builds as a reflex.

For source defects, re-run affected comparisons and complete the required final validation. For documentation/style changes, use relevant link, route or visual checks. Do not invent a binary-validation result for an unrelated change.

## Recovery and rollback

An unavailable essential reference/tool is a named blocker for the owner. Invalid publication metadata blocks promotion while the current valid package remains available. Recover history from authenticated archives or an explicitly audited checkpoint. Roll back the site independently from game source/history.

A changed owner policy needs a focused proposal and appropriate review. Do not loosen assertions, change counts, conceal mismatches or alter private dependencies merely to accommodate a patch.

## Keep the handbook accurate

When a command, report format or owner workflow changes, update its project documentation and the relevant handbook chapter together. Link the exact implementation revision. Distinguish established behavior from proposals and examples. Keep recurring tool failures in issues; avoid permanent running diaries of agent activity in public source.

A new agent should finish each handoff with changed files, evidence, checked revision/results, unresolved findings and review/publication state. “Implemented,” “reviewed,” “CI passed,” “owner cleared,” “merged” and “live” are different states.

The handbook stores reusable contracts and decisions, not game-specific run IDs, workflow blobs, timing claims or migration diaries. Record those facts in the adopting project's PR/configuration. When changing CI, review both the producer and the site's approved policy/lane requirements; keep old policies readable for retained reports. Verify an explicit audit and a normal/reused publication before declaring a workflow transition complete.

## Shared site UI

When maintaining the shared site's interface, use its [UI components and contracts](/docs/ui/components.md)
for progress bars, searches, dropdowns, commit rows and other reusable controls. Page modules
supply content and callbacks; components own control markup, accessibility, motion and cleanup.
Preserve the accepted page/compact variants when refactoring. These presentation components
do not replace producer reporting, CI validation or per-target data contracts.
