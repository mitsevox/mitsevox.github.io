# Credits & history

Choose attribution policy deliberately, and preserve the meaning of every historical measurement.

## Three independent choices

| Choice | Controls |
| --- | --- |
| Track attribution | Whether the game maintains and validates function-level contributor provenance |
| Show contributor rankings | Whether the site renders verified credit data |
| Accept contributions | Whether the Contribute button and contribution guide are offered |

A game can publish progress without function attribution. Turning rankings off does not inherently turn tracking off. Changing tracking policy is an explicit repository decision; hiding a UI section must not silently delete evidence already recorded.

NFL requires exact-function attribution today. MVP, Tiger Woods and future projects do not acquire that requirement merely by joining the site. If tracking is disabled, mark the contributor capability unavailable and keep rankings off; enabling accurate rankings later may require reconstruction that is not fully possible.

## NFL's credit model

Credit follows the original source contributor, not the person who merges or batches the PR. Store stable function extents, original contribution references, original revision/source blob and integration provenance as required by the ledger. Retain the original identity when imports are corrected or squash-merged.

The ledger covers complete exact functions, including exact unlinked comparisons. Fuzzy source retains provenance without exact-function credit. Promotion creates no duplicate credit. Retired or no-longer-exact functions leave current exact totals while their provenance remains recorded.

Explicit joint credit is allowed: each person receives that function once. Personal totals can therefore overlap; the union of credited functions, not the sum of personal counts, must equal the exact inventory. Sort current distinct function counts deterministically.

## Before submitting a tracked contribution

Open the authorized draft PR to obtain its real number; never guess a future PR number. Record its actual original/integration references and validate the complete ledger against the candidate exact inventory. For a batch, use the actual batch PR as integration metadata while preserving original authorship.

NFL validates the introduced source blob in reachable landed history, including a synthetic squash against the actual PR base. Pinned original commits must be accessible; missing provenance is a validation gap, not a reason to attribute the function to the integrator.

## Recovering past credit

Use surviving original PRs, commit authorship, pinned source blobs, integration records and reviewed evidence. A closed PR or deleted branch may still leave useful records; do not assume they are available indefinitely. Distinguish supported attribution, explicit joint work and unresolved ownership.

Keep a bounded recovery record explaining each decision and uncertainty. Do not give every function to the current file author or merger. If a project promises complete exact-function attribution, unresolved gaps block that capability's publication until resolved or the owner explicitly changes the policy.

## Timeline continuity

Keep full commit identity, target, methodology, raw totals/denominators and evidence quality. Preserve measured, reconstructed and inherited legacy entries distinctly. A new inventory can change a percentage without source regression; make the basis change explicit rather than smoothing the graph.

Restore prior verified history; do not use an unauthenticated live page as automatic recovery evidence. An intentional checkpoint recovery needs a documented audit. Latest repository commit metadata is separate from the latest measured build, even when the header displays both near each other.

See [NFL timeline and contributor rules](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/GN7E69/README.md#timeline-and-contributor-credits) and [history recovery](https://github.com/mitsevox/nflstreet2/blob/d7a6f8e830baf4ac083dc52c2ad3e80cfbf13211/config/README.md#history-recovery).
