# CI & publication

Build once, validate the result, then publish an authenticated report.

## Workflow structure

Use separate jobs for the responsibilities below. Map the commands to the repository's documented build tools.

| Job | Runs when | Work | Permissions |
| --- | --- | --- | --- |
| Configuration and evidence checks | PRs and main | Validate target configuration, declarations, evidence and changed dependencies | Source read |
| Build and measure | PRs and eligible main runs | Verify inputs; build/compare; generate a candidate report and receipt | Source/packages read; approved private inputs only |
| Review clearance | Relevant PR changes | Check revision, required review records and owner decision using trusted code | Read PR records; write its named status |
| Report publication | Successful eligible main result | Authenticate the measured tree, validate prior history, export public data | Read artifacts; narrowly scoped history/report writes if needed |
| Website validation | Site PRs and refreshes | Authenticate/import reports and assemble a coherent site candidate | Public source/artifact read |
| Website deployment | Successful current site main | Preserve accepted reports, then deploy the exact candidate | Site data-store writes, Pages and deployment identity |

Game build jobs do not need website deployment permissions. Publishing jobs process report data without executing scripts downloaded from artifacts. Keep private originals, complete debug exports and build credentials out of the website job.

## PR validation

Run the project's required baseline, accepted-source and comparison stages for the actual candidate inputs. Cheap checks should fail before expensive work where possible. Delete stale output before export; a failed exporter must not leave an earlier report available for upload.

Emit a candidate artifact containing public measurements and a receipt binding repository, target/hash, full tested revision/tree, tools, methodology and payload checksums. Candidate artifacts support review; they do not advance public latest or the production timeline.

Pin Actions/shared tools to reviewed commits, images to approved digests and downloaded tools by version/hash. Cache keys include target, toolchain, relevant configuration and source inputs. Document the cache's scope and invalidation rules.

## Main validation and reuse

A main publication must have either a successful full validation or authenticated proof for the complete landed tree. Reuse requires matching target, tools/environment, methodology, complete tested inputs and original artifact integrity. Validate landed attribution too when the project's policy enables it.

A missing or incompatible reusable proof requires the full validation path. An inventory-only change can regenerate inventory separately when source-build proof remains valid. Never combine reports from several independently tested branches into proof of an integrated build.

Keep original measurement time separate from publication time. Latest repository commit metadata is another input and does not make a previous build newly measured.

## Publication sequence

1. Select an eligible successful main run and its actual attempt.
2. Authenticate repository, workflow revision, job/lane, tested tree and artifact digest.
3. Restore validated prior history; an established history must not reset after a fetch/parse failure.
4. Generate the public package from measured input and validate schema, arithmetic, extents, capabilities and history continuity.
5. Store immutable snapshot files before updating the latest pointer atomically.
6. Preserve the accepted package before deploying the matching website artifact.

An identical rerun is a no-op. Different bytes for an existing immutable identity fail. A correction needs a new version/generation and recorded provenance. Check ancestry before advancing latest; concurrent job ordering alone cannot prevent stale publication.

The shared website owns a durable data-only report store so accepted measurements outlive temporary CI artifacts. Individual projects can retain their existing history/archive mechanism. A separate data branch in each game repository is optional.

## Failure behavior

| Failure | Required behavior |
| --- | --- |
| Missing or malformed required report | Fail the refresh and keep the prior accepted package |
| Unsupported optional capability | Declare it unsupported and configure its UI off |
| Failed export of a supported capability | Fail; do not silently change it to unsupported |
| Stale or diverged measured revision | Reject promotion and retain history |
| Existing immutable identity with changed content | Reject the collision |
| Concurrent store writer | Reread and reconcile after a normal push conflict; never force overwrite |
| Obsolete site-source workflow | Reject deployment |
| Missing private build access | Report the missing input; do not change dependency access or substitute tools |

Define whether a refresh failure blocks the whole site deployment or allows other validated projects to publish. Test and document that policy explicitly. In either case, a failed project retains its last-good data.

## Workflow security and approval

Evaluate clearance using trusted base/default-branch logic. PR text, payload JSON and filenames are data, not commands. A privileged follow-up workflow must authenticate its upstream execution before using its artifacts. Declare how fork contributions receive build validation without assuming private secret access.

See GitHub's [secure workflow guidance](https://docs.github.com/en/actions/reference/security/secure-use) and [workflow_run behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run). Configure required statuses after real passing, failing and stale cases have been observed; a workflow file alone does not enforce approval.

## Website deployment

Build one static artifact with fingerprinted assets. The deploy job depends on successful validation and storage and receives only the permissions it needs. GitHub Pages supports [custom Actions workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Verify home, direct project/wiki routes, refresh, back/forward and the selected report identity at the public URL. Use a reviewed site-source revert for a UI rollback while retaining current accepted measurement history. Do not deploy an obsolete workflow or rewrite measured history to roll back styling.
