# Optional explicit-target starter

Use this overlay for a revision-aware project, including a new project with one target.
Single-target report-v1 remains supported; do not combine both workflow templates.

1. Fill `config/targets.example.json` with verified identities, validate against the included
   `targets.schema.json`, then save as `config/targets.json`. Unknown/unvalidated revisions use
   `status: archived`, `support.build: false`, and an empty `reportFormats` array.
2. Fill `config/ci-targets.example.json`, covering every registry target and actual shared inputs,
   then save as `config/ci-targets.json`. Copy the editable `tools/ci_targets.py` planner. Unknown
   changed files select all buildable targets. Its CLI requires GitHub event/SHA environment and
   full Git history; `--force-all` audits all buildable targets.
3. Adapt `validate.yml.template` into the repository's sole validation workflow. Replace its
   approved environment/packager pins. Keep stage display names identical to each producer policy.
   The planner output is `matrix={"include":[{"target":"..."}]}` and `has_targets=true|false`.
4. Implement the exact `project_ci.py` operations below. A missing implementation fails nonzero;
   this overlay intentionally provides no stub that claims to verify a binary.
5. For each reportable target, create producer-v2 policy and site registration using the
   bundled `reporting/contract-v2.md`. Pin the reviewed consumer before exporting v2. Register a
   successful real package before treating that target as live. Coordinate required checks.

## Adapter operations

Every operation takes `--target <canonicalId>`, rejects unknown or archived/unbuildable targets,
uses only that target's private original/configuration/output directories, and exits nonzero
on failure. Use the same operation implementation locally and in CI.

| Operation | Required result |
| --- | --- |
| `verify-inputs` | Verify original executable SHA-1, target identity/media evidence, approved toolchain and target configuration. Never infer a disc revision from Git SHA. |
| `build` | Freshly compile/link the complete target and hash-check it against the verified original; retain the log and unresolved comparisons. |
| `measure` | Independently measure linked/exact/fuzzy and inventory on that target, preserving mismatches; write public inputs under `build/<id>/public-input/` and actual measurement time. |
| `export` | Write summary/module JSON and restore only this target's prior/accepted history, fail on history loss, and append this real measurement. Unsupported modules are explicit. |
| `metadata` | Write `build/<id>/public-metadata.json`: exact v2 target, full Git revision/tree, policy-matching tools, methodology/generation, measuredAt/publishedAt, GitHub run/attempt/workflow blob. |

The site's pinned `package_report.py` produces `build/<id>/public-report/` from those inputs and
`config/<id>/producer.json`. Upload only that directory, as `report-v2-<id>`; never private inputs.
History recovery is target-scoped and authenticates canonical identity or an explicitly declared
same-binary legacy alias. No automatic cross-target history or cache fallback is permitted.

`Tool tests` exercises planners, adapters, failure paths and metric parity. `Validate targets` is
an aggregate merge gate, not the publishing job. Each `Validate <id>` target job is independently
publishable after shared `Plan affected targets` and `Tool tests` succeed, even if a sibling fails.
Use the v2 completion notifier from the reviewed site revision; v1 callers stay unchanged.
