# Setup acceptance checklist

Leave unknowns unresolved; do not check items without evidence.

- [ ] Owner, repository slug, target platform/region/revision and executable hash recorded.
- [ ] Authorized reference inventory and missing inputs documented.
- [ ] Public/private material boundary and ignored outputs checked.
- [ ] Approved tool versions/hashes and supported host setup documented.
- [ ] Full original-object baseline reproduced and result recorded.
- [ ] Accepted-source build and partial comparisons implemented separately.
- [ ] Complete range, dependency, overlap and stale-report failures tested.
- [ ] Contribution policy and independent-review process adopted by owner.
- [ ] Attribution tracking decision recorded independently from site module visibility.
- [ ] Final-head CI and owner-clearance logic exercised for passing/failing/stale cases.
- [ ] Owner configures required checks and verifies bypass/merge authority.
- [ ] Supported report capabilities and durable history verified.
- [ ] Website adapter implemented; production fixtures rejected.
- [ ] Site routes, freshness, failure behavior and rollback verified.

For each completed item, record the revision, command/artifact and limitations in the appropriate
project document or PR—not a fabricated checklist result. No generic CI is supplied in this kit.
