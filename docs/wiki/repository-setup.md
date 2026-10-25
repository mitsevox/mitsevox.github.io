# Repository setup

Establish ownership, target identity and a safe working environment before the first reconstruction.

## Record the project identity

Choose a stable lowercase repository slug such as `game-slug`; use the same slug for its site route and reporting identity. Keep its display title separate. A second platform or revision is a separate target, not a silent replacement for the first one.

The README must identify the game, platform, region/revision, target executable hash, owner, supported host requirements, setup/build entry points and links to CONTRIBUTING and AGENTS. Use a full target hash; a filename or disc label alone is insufficient.

For an original executable, an initial local hash check can be:

```sh
# macOS
shasum -a 1 /path/to/original-executable
# Linux
sha1sum /path/to/original-executable
```

Compare the result with a verified target identity before using it. This identifies the input; it does not prove source fidelity. Keep the original executable outside public Git.

## Bootstrap the repository

Before adopting the starter, have the owner settle the following decisions and record them in README/CONTRIBUTING and `config/ci.json`:

| Decision | Starter default | Must be supplied or confirmed |
| --- | --- | --- |
| Target/objective | Faithful matching, one explicit target | Console, executable format, region/revision, hashes, measurement universe and any different objective |
| Tools/runtime | Pinned approved environment | Actual digest/hash, supported hosts, tools/profiles and reference access |
| Author workflow | Isolated branch/worktree and bounded active scope | Branch convention, reservations, dependencies and push/PR authority |
| Review/merge | Independent accuracy and hostile review; owner-only merge | Adopting owner and any explicit alternative policy |
| Attribution | Explicit decision required | Track or do not track; exact inventory/joint-credit rules if enabled |
| Acceleration | All caches and proof reuse disabled | Enable each only after fresh correctness and failure tests |
| Site capabilities | Honest supported data only | Map, counts, timeline, rankings and independent contribution acceptance |
| Publication | Validated main reports through shared site | Artifact retention, trusted workflow/tool identities and durable history source |

No project names, compiler family or console-specific directory conventions are inherited from another repository. The templates describe responsibilities; the adopted configuration records facts.

Start with README, CONTRIBUTING, AGENTS, .gitignore, target configuration and a bounded build plan. Select and document licensing/provenance appropriate to your own tooling and imported sources; do not blanket-relicense imported code. The [starter files](/wiki/starter-kit/) provide editable scaffolding, not a build system.

Initialize an empty local repository without publishing it:

```sh
mkdir game-slug
cd game-slug
git init -b main
git switch -c codex/bootstrap
```

Inspect staged files before the first commit. Generated objects, originals and research dumps should never enter the commit. Create the hosted repository and configure access only when the owner authorizes those actions.

## Work in isolation

Once the repository has an established main branch and origin:

```sh
git fetch origin
git worktree add ../game-slug-task -b codex/task-name origin/main
cd ../game-slug-task
git status --short --branch
```

Use `codex/<task>` for agent branches by default; a project's own convention takes precedence. Do not reuse another contributor's dirty checkout. Claim the unit or shared-file scope in an issue or draft PR and identify dependency branches. An agent should receive explicit authority before pushing or opening a PR.

## Active work reservations

Distinguish backlog from active work. Before starting, check open PRs and active branches, then reserve a bounded current batch in an issue or draft PR with the functions/unit action, branch and shared-file dependencies. Do not reserve an entire subsystem or future batches.

Set a documented reservation timeout, such as 48 hours without a meaningful update. Renew with pushed work, concrete findings or an explicit handoff; release paused or abandoned scope. Before taking over expired work, inspect existing branches/PRs and preserve useful partial source and credit. An old backlog claim does not own the code. A live overlap needs coordination even when two tasks touch different functions in the same header, file or compilation group.

Record the chosen timeout and coordination rules in CONTRIBUTING.md so every contributor uses the same policy.

## Tool and reference access

Record required tools, versions, hashes, host architecture and installation instructions. Use the owner's approved build image or tool archive. A working compiler is not proof that its version and flags match the original; those claims need unit/library evidence.

List supported host operating systems and architectures. Document any compatibility wrappers or translation layers alongside the exact tool versions that require them.

If access is missing, report exactly which input or tool is unavailable. Do not change private package permissions, rebuild supporting images or substitute a different compiler to make a patch pass. Keep credentials out of scripts, report packages and source control.

## Owner-configured GitHub controls

After the checks exist and their failing cases have been exercised, the owner configures the default branch rules: PR-based changes, the intended validation checks, review clearance, and restrictions on direct pushes, force pushes and deletion appropriate to the account. Verify who can bypass those rules; documentation alone does not enforce owner-only merging.

Use unique check names and verify which revision each required check evaluates. Bootstrap the review workflow on trusted default-branch code before requiring its status. Configure Pages separately for the website repository when deployment is authorized. Do not give game build jobs deployment or repository-write permissions merely because another job needs them.

[GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) and [required-check behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks) describe the available controls; verify them for the actual account.

## Ready to begin

A fresh contributor can identify the correct input, reproduce the baseline, locate the contribution rules and understand who may merge. Any missing item is a named setup gap—not a reason to report the repository as ready.
