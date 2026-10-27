# CI & publication

Implement fresh validation first, then optionally accelerate it without changing what a published result proves.

## Responsibilities and authority

A matching project verifies the complete accepted-source executable against its declared target, measures full registered comparison extents, reconciles optional attribution, and derives public reports from those results. A different source objective needs explicit corresponding validation; it must not claim byte identity it does not establish. CI cannot prove original names, intent, types or file boundaries: source/evidence review remains separate.

Separate responsibilities and permissions; they need not be separate jobs. Keeping a dependent build/measure/export chain in one job avoids copying private build output between runners. Use separate privileged jobs/workflows where authority changes.

| Responsibility | Authority |
| --- | --- |
| Candidate validation | Source/packages read and approved private input access; no site deployment or repository write |
| Owner clearance, if selected | Trusted metadata-only logic; read PR records and write only the named status |
| Producer report publication | Read authenticated upstream artifacts; narrow history writes only when the selected storage needs them |
| Site import | Read registered public source/artifacts; validate packages without executing their contents |
| Site storage/deployment | Owner-controlled site main; preserve accepted packages before Pages deployment |

The [starter archive](/wiki/downloads/repository-starter.zip) includes `.github/workflows/validate.yml.template`, `config/ci.example.json` and `CI.md`. Copy/adapt the workflow and configuration, implement the documented adapter operations using actual project tools, and prove the acceptance cases below. Templates do not configure repository settings or compile an unknown target automatically.

## Triggers and lanes

The reference workflow assumes default branch `main`; change every branch/eligibility guard together if the project uses another name. It defaults to same-repository contribution branches. Forks need an explicitly designed reference/secret-access policy before their code runs with private build inputs.

| Event | Validation | Shared cache save | Public result |
| --- | --- | --- | --- |
| PR | Fresh full path, or valid input-keyed reuse when enabled | Never | Candidate only; reusable proof only if zero compiled/measured results reused |
| Main push | Authenticate eligible proof when enabled; otherwise full fresh validation/audit | After successful full main validation when caching is enabled | Validated report artifact for shared-site ingestion |
| Main manual, normal | Same selection/fallback as main push | No build-cache save | Validated main report |
| Main manual, explicit audit | Skip proof selection; force full fresh validation/audit | Yes when caching is enabled | Validated main report |
| Other-branch manual | Validation only | Never | No production publication |

Cancel superseded PR/branch runs; keep main runs uncancelled by the workflow's concurrency policy. Main still needs ancestry/current-state checks because queue order does not guarantee safe publication order.

Three internal decisions are independent: `full` means run source build/comparisons/tests/export; `inventory` means validate/regenerate inventory; `receipts` means run the host live-receipt re-export. Fresh validation sets all applicable lanes. Reused source proof can still require inventory maintenance. An audit request on another branch must not grant main publication or save rights.

## Step-by-step implementation

The adapter contract in starter `CI.md` specifies input/output paths, GitHub outputs and fail-closed behavior for every operation. Existing tools can keep their names; one thin adapter gives the workflow stable boundaries.

| Order | Operation | Result/failure boundary |
| --- | --- | --- |
| 1 | Checkout exact candidate with required history | Record PR head/base, actual checked-out commit/tree, repository, target and run/attempt |
| 2 | Validate configuration/evidence and runtime pins | Reject unknown target, missing tools/inputs, unsupported policy, placeholders and unsafe publication paths |
| 3 | Compute/restore optional inventory candidate | Restore is provisional; internal input/digest receipt must still validate |
| 4 | Select proof on eligible main unless auditing | Authenticated match selects reuse; unavailable/incompatible proof selects full |
| 5 | Decide full/inventory/receipt lanes | Strict booleans, explicit fresh default; inconsistent state fails |
| 6 | Ledger/provenance preflight if tracking enabled | Check recorded entries on candidate and predicted squash history before expensive work |
| 7 | Baseline/setup and optional build-cache restore | Verify original input/relink where applicable and prepare pinned tools |
| 8 | Build accepted source | Parallel independent compiles; deterministic placement/link order; complete target-objective check |
| 9 | Inventory and tool tests | Validate restored metadata or regenerate; run applicable regression tests |
| 10 | Measure comparisons | Full extents and declared method; validated reuse or fresh measurements; explicit cache statistics |
| 11 | Export from one measured result | Reconcile linked/exact/fuzzy, map, inventories, optional credits and restored history |
| 12 | Host receipt verification | Keep on full main and zero-reuse proof-producing PRs; other host tests still run |
| 13 | Promote selected proof, if reused | Recheck landed tree/attribution/history, preserve original measurement identity |
| 14 | Package and validate public JSON | Versioned manifest/receipt and checksums; no stale output or private files |
| 15 | Upload eligible artifact; save eligible caches | Only exact directories; explicit main/PR-zero-reuse guards |
| 16 | Shared-site import/storage/deployment | Authenticate actual successful run/attempt, preserve history and project isolation, publish one coherent artifact |

An early ledger check validates the existing ledger and Git provenance. It cannot establish coverage of exact functions not yet measured. The exporter later reconciles the complete measured exact inventory and, where selected, compares actual-candidate and synthetic-squash credit results. Disabling tracking records an explicit policy decision; it must not fabricate a contributor feed.

## Candidate and landed identities

On a typical `pull_request` build, GitHub checks out a synthetic merge commit. The API's PR head SHA, that tested commit/tree and the later landed commit are different identities. Record all relevant identities and merge parents; do not label a merge-tree measurement as a head-only build. See [GitHub event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).

A main publication requires successful full validation or authenticated proof covering the complete landed tree. Squash/rebase can change a commit ID without changing its tree; reuse is permitted only after verifying the full tree, target, tools, method and source execution. Never combine independently tested PR reports into an integrated build proof.

Review/owner clearance normally names the current PR head. CI evidence explains which integrated tree it tested. New source/build inputs invalidate earlier validation; review comments alone do not require another binary build.

## Fresh path and public contract

The fresh path is the required starting implementation. Baseline, accepted-source build and independent comparisons remain distinct. Do not report the complete executable as reconstructed simply because original bytes fill unpromoted ranges.

Delete owned stale output before each export/package operation. Generate `summary.json` and only supported module files under `build/public-input/`. Use the [shared packager and schemas](/docs/reporting/platform.md#package-a-producer-report) from an approved pinned site-tool revision. The metadata uses actual target/revision/tree, method/generation, tools, run/attempt, workflow blob and separate measurement/publication times.

Upload the exact resulting `build/public-report/` files as the policy's declared artifact. On PRs it is evidence only; it does not advance public latest or the durable timeline. The website does not run the game compiler, rebuild the binary or execute downloaded scripts.

Register common required steps only when they succeed on every published lane. Put full-build steps in `lanes.full` and proof-authentication steps in `lanes.reused`. Exactly one lane must succeed. Proof selection is a decision step, not a mandatory success on an audit that deliberately skips it. Approve the actual workflow Git blob after inspecting the adopted YAML; editing a trusted workflow requires a reviewed policy update.

## Optional acceleration

Follow [Cache & proof](/wiki/cache-and-proof/) for key construction, shadow dependencies, main-only saves, fresh disagreement audits, bootstrap and complete-tree reuse. Keep acceleration disabled while establishing correctness. Then test inventory reuse, build caches and publication reuse separately.

A warm-cache PR may be faster but causes a fresh main rebuild under this trust model. A cold zero-reuse PR can be slower but give main a reusable proof. Quote observed hosted timings with run/attempt and hit counts; do not inherit another project's duration as a promise.

## History and publication

1. Restore previously accepted history from authenticated storage. A fetch/parse failure must not silently create empty history.
2. Authenticate full or reused execution, including original artifact where required.
3. Validate report schemas, arithmetic, extents, enabled attribution and continuity. Keep original measurement time separate from publication and latest repository commit times.
4. Upload immutable public report artifacts only after applicable checks pass.
5. The shared site authenticates/imports the selected package, installs immutable snapshots and atomically advances only that project's pointer after ancestry checks.
6. Preserve accepted packages in durable site storage before deploying the exact static candidate.

Temporary Actions artifacts are not a durable timeline. An identical rerun is a no-op; conflicting bytes for an existing immutable identity fail. Retain historical policies/schemas when changing producers. Use a new method/generation for a justified measurement change without rewriting old rows.

The current shared site attempts each registered refresh, retains a failed project's last-good data, and blocks deployment if any refresh fails. Successful candidate imports do not imply that a mixed/failing candidate was deployed. A project-owned history archive is optional when durable site storage fulfills the requirement; do not require every project to create another data branch.

## Clearance and private access

When the project adopts review clearance, evaluate it using trusted base/default-branch logic without checking out or running contribution code. Validate current head, distinct actual review comments, verdict format, owner identity, draft/stale/withdrawn cases. The status cannot establish reviewer independence or reasoning quality by itself.

Keep build secrets and private originals out of metadata-only clearance and site jobs. Do not combine privileged `pull_request_target`/follow-up execution with untrusted code checkout. Pin external Actions to reviewed full commit SHAs and the build environment to an approved digest. See [GitHub secure workflow guidance](https://docs.github.com/en/actions/reference/security/secure-use).

The owner adopts required checks and bypass/merge controls after real success, failure and stale cases are observed. A workflow file or starter policy is not enforcement. Projects choosing another review model document and test the corresponding gate instead.

## Acceptance and failure cases

Demonstrate a real passing fresh candidate and main report first. Exercise wrong input hash, stale source/header receipt, overlap/extent errors, missing export, corrupt history, uncredited exact function when tracking, stale clearance and stale/diverged publication. Optional acceleration has its own failure matrix in the next chapter.

The website side must reject unapproved workflow blobs, wrong run attempts, missing lane steps, artifact digest mismatch and malformed payloads while preserving all accepted projects. Verify direct routes, selected manifest identity, and the next successful refresh. A schema-valid fixture or local preview is not evidence of live integration.

For a UI rollback, revert reviewed site source while retaining current accepted measurement history. For a producer failure, fix the failing layer; do not weaken checks, reset history or change private dependency access to get green.

## Multiple targets

Plan an explicit matrix from changed paths and a reviewed dependency map. A target-only config
change validates that target; shared source, headers and toolchain inputs validate their actual
dependents. Include deleted/renamed paths and conservatively validate all buildable targets for
unknown inputs. An archived revision without build support is not a zero-percent build target.

Use independent target jobs with `fail-fast: false`, isolated `build/<targetId>/` outputs and
unique report artifacts. Each job verifies its whole executable before measuring and packaging.
A stable aggregate check blocks a PR if a required target fails. A successful target on main may
publish despite a failed sibling, after its shared prerequisite checks pass. See the complete
[report-v2 CI contract](/docs/reporting/contract-v2.md#target-scoped-ci-and-repository-layout).
Caches remain optional and must bind target ID/hash as well as actual inputs.
