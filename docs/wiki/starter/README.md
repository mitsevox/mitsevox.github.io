# PROJECT_TITLE

DRAFT STARTER: replace every placeholder using verified project facts before adoption.

## Target

- Owner: OWNER_LOGIN
- Adopted merge authority: owner-only by default; confirm/document any alternative
- Repository: OWNER/PROJECT_SLUG
- Platform / region / revision: TO_VERIFY
- Executable and verified hash: TO_VERIFY
- Objective: faithful matching reconstruction (confirm with owner)

## Setup and build

Supported hosts, approved reference access, pinned tools and exact commands: TO_IMPLEMENT.
Document baseline relink, accepted-source build and independent comparison separately.
Do not present an empty scaffold as a verified build.

## Contributing

Read CONTRIBUTING.md; agents also read AGENTS.md.
Attribution policy: TO_DECIDE (independent from website rankings and accepting contributions).
Reporting capabilities and site integration status: TO_IMPLEMENT.

## CI adoption

Read CI.md, fill config/ci.example.json as config/ci.json and implement its adapter using the
project's actual engines. Adopt the validation workflow template only after placeholders are
resolved. The optional review workflow implements the default clearance-record format;
set REVIEW_OWNER and test actual event behavior before making its status required.

Document exact local commands for inputs, baseline, source build, inventory, comparisons,
ledger-only preflight when enabled, export, tests and packaging. Record supported hosts and
private reference setup so a fresh runner or agent does not depend on one developer's machine.
Start with fresh validation; optional caches and publication reuse need separate acceptance.
