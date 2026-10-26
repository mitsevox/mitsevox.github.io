# Shared reporting platform

A curated platform for the owner's repositories. Game projects supply validated public reports; one shared website authenticates, stores and renders them.

## Implemented interfaces

- [Platform](platform.md): registration, typed payloads, packaging, execution proof, import, history and storage.
- [Contract](contract-v1.md): measurement semantics and independent feature controls.
- [Project template](onboarding.md): repository/CI structure and acceptance checklist.
- [Workflow](workflow.md): candidate validation, main publication, proof reuse and recovery.
- [Manifest schema](schema/report-v1.schema.json), [producer policy](schema/producer-v1.schema.json), and [presentation configuration](schema/project-v1.schema.json).
- Map [v1](schema/map-v1.schema.json) / [v2 with optional evidence](schema/map-v2.schema.json), [timeline](schema/timeline-v1.schema.json), [contributors](schema/contributors-v1.schema.json), and [execution](schema/execution-v1.schema.json) payloads.

## Ownership

| Game repositories | Shared website |
| --- | --- |
| Target and tool identities, source/evidence, builds/comparisons, public measurements, supported history and attribution | Owner registrations, artwork, producer authentication, shared validation/storage, routes and UI, site deployment |

The website accepts only checked-in registrations for its configured owner. It has no visitor registration or public submission API. New report-v1 producers require configuration/artwork and a conforming artifact; project-specific importer or page code is unnecessary.

All current producers use report-v1. Archived compatibility validates retained historical packages; it does not select old artifacts or refresh a production feed. The [NFL integration record](nflstreet2.md) records that completed cutover. New producers follow the common interface above.

The generic [wiki](../../wiki/) defines reusable project conventions. Keep actual targets, approved policies, tools and validation evidence in the repositories that own them.
