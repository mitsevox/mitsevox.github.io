# Build environment

The private image that holds the originals and the toolchain, pinned by digest.

CI must build with the original executable, and the original must never be public. The solution is a second, private repository whose only job is to build a container image containing the original and the exact toolchain, and to publish that image to GitHub Container Registry as a private package that the public repository's workflow may pull. The public repository then references the image by digest, so every build runs against a known set of bytes.

## The private repository

Create `owner/game-build` as a private repository. Copy the three files from the starter kit's `build-image/` directory to its root and commit the original under `orig/<target id>/`:

```text
game-build/
  Dockerfile
  .github/workflows/image.yml
  README.md
  orig/GAME01-rev0/main.dol
```

The original is committed to this repository on purpose: the image build copies it in and verifies its SHA-1, so the image can only be produced from the right file.

## The Dockerfile

The starter Dockerfile is a three-stage build for a GameCube or Wii project:

1. `dependencies`: downloads the binutils and compiler archives, checks their SHA-256 and unpacks them to `/binutils` and `/compilers`.
2. `dtk`: clones decomp-toolkit at the tag `configure.py` pins, checks the commit and builds it to `/dtk`. A project patch to the toolkit is applied in this stage.
3. The final image: copies every original to `/orig/<target id>/<original path>`, checks each SHA-1 against the value you also put in `config/targets.json`, copies the tools in, and installs `gcompat git ninja python3`.

Parameters, each marked `PARAMETER` in the file: the archive URLs and checksums, the toolkit tag and commit, and one `COPY` plus one `sha1sum -c` line per active target. The base images are pinned by digest; keep them that way.

What the final image must provide, whatever the platform, because `validate.yml` and the publish action run inside it:

| Requirement | Why |
| --- | --- |
| `/orig/<target id>/<original path>` for every active target | The `Provide target original` step copies it into the checkout |
| `sh`, `git`, `python3` | Composite action steps run with `sh`; `tools/` and `publish.py` are Python; `publish.py` runs `git log`, `git clone` and `git push` |
| `gcompat` on Alpine | The Actions runner mounts its own glibc Node.js into the container to run `actions/checkout` and the token-minting action |
| The toolchain at fixed paths | The configure command in `validate.yml` names them (`/usr/local/bin/dtk`, `/binutils`, `/compilers` in the starter) |

## The image workflow

`image.yml` runs on every push and pull request:

1. `Build image`: `docker build --tag ghcr.io/owner/game-build:candidate .`
2. `Verify toolchain inside image`: runs `sha1sum` on each original and probes the tool files. Edit this step to match your Dockerfile (`PARAMETER`).
3. `Publish image`, on `main` only: logs in to `ghcr.io` with the workflow's `GITHUB_TOKEN`, pushes the tags `:main` and `:<commit sha>`, and appends the image digest (`ghcr.io/owner/game-build@sha256:...`) to the run summary.

The job has `packages: write`; nothing else in either repository does.

## Owner setup after the first publish

These steps are done once, on GitHub, by the owner:

1. Open the package `game-build` under the owner's packages and confirm its visibility is **private**. A package created by a workflow from a private repository starts private; check anyway.
2. In the package settings, under **Manage Actions access**, add the repository `owner/game` with the **Read** role. This is what lets the public repository's workflow pull the image with its own `GITHUB_TOKEN`.
3. Copy the digest from the `Publish image` step summary into `validate.yml` (the `BUILD_IMAGE` variable).

The public workflow's `target` job declares `permissions: packages: read` and pulls with `credentials: {username: github.actor, password: secrets.GITHUB_TOKEN}`. No personal token is involved.

## Referencing the image by digest

`validate.yml` names the image once, as `BUILD_IMAGE: ghcr.io/owner/game-build@sha256:<64 hex digits>`, never `:main`; the target job runs in it and the variable is exported to every step. The digest is part of the measurement's provenance: `tools/measuring_tools.py` reads `BUILD_IMAGE` and the publish action records it as the `build-environment` tool in `latest.json`. The scaffold check warns on an image referenced by tag. Changing the digest is a reviewed change to `validate.yml`, and it is an owner decision: the image defines the compiler and the original, so a different image can change every number.

Keep the digest line commented with the image workflow run that produced it. Pulling `:main` in `validate.yml` is never acceptable, and no bot bumps the digest.

Two later conveniences have known triggers and are not built before them: a small tool that reads the image run summary and rewrites the digest line, once the third bump has been done by hand; and a shared toolchain base image with each game's image adding only `/orig/<id>/`, once two repositories build on the same compiler pack.

## Other platforms

The pattern does not depend on the platform. For another console, the Dockerfile's `dependencies` stage fetches that platform's toolchain, the original goes under `/orig/<target id>/` at whatever path your build expects (`PARAMETER 2` in `validate.yml` and the toolchain's own configuration name it), and the configure and build commands in `validate.yml` change. A single image may hold several targets, and a reference binary from another platform may be added for comparison in the same way; it is just one more `COPY` with a checksum.

## Local builds

Contributors build locally with their own copy of the game and their own tool installation; the image is for CI. Running the image locally is possible with `docker run --rm -it -v "$PWD:/work" -w /work ghcr.io/owner/game-build@sha256:... sh` after `docker login ghcr.io`, but only for people who already hold the original, because pulling the image requires read access to the private package.
