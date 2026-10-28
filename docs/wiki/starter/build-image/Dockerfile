# Private build environment for owner/game. It contains the original executable: keep this
# repository and its container package private, and never publish the image anywhere else.
#
# PARAMETERS: the toolchain archives and their checksums, the decomp-toolkit tag and commit,
# and one COPY plus one checksum line per active target. The base images are pinned by digest;
# update the digests when you move to newer bases.

ARG ALPINE=docker.io/library/alpine:3.22@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f
ARG RUST=docker.io/library/rust:1.90-alpine3.22@sha256:b4b54b176a74db7e5c68fdfe6029be39a02ccbcfe72b6e5a3e18e2c61b57ae26

FROM ${ALPINE} AS dependencies
RUN apk add --no-cache curl libarchive-tools
# PARAMETER: the GameCube/Wii toolchain (binutils and the compiler pack that dtk-template downloads).
# Replace the archives and checksums for another platform.
RUN curl -fsSL -o binutils.zip https://github.com/encounter/gc-wii-binutils/releases/download/2.42-2/linux-x86_64.zip \
    && echo "64e4bf7aee5c06075d8fa818ebd2a0a3a72e0eeef3896bdec2f198b0e950fe63  binutils.zip" | sha256sum -c - \
    && mkdir /binutils && bsdtar -xf binutils.zip -C /binutils && chmod +x /binutils/*
RUN curl -fsSL -o compilers.zip https://files.decomp.dev/compilers_20251118.zip \
    && echo "69b0d4980a2eccea4ae6e70b486714b5190cb6c75e3bc7b8fb5878a8854d0d1c  compilers.zip" | sha256sum -c - \
    && mkdir /compilers && bsdtar -xf compilers.zip -C /compilers

# PARAMETER: the decomp-toolkit tag (the same tag as config.dtk_tag in configure.py) and the commit
# it must resolve to. Apply a project patch here if the project needs one.
FROM ${RUST} AS dtk
RUN apk add --no-cache git musl-dev
RUN git clone --branch v1.8.3 https://github.com/encounter/decomp-toolkit /src \
    && test "$(git -C /src rev-parse HEAD)" = e4219e7644fb7b96d920d5bc3d1d950f5569dcaf \
    && cargo build --release --locked --manifest-path /src/Cargo.toml \
    && cp /src/target/release/dtk /dtk

FROM ${ALPINE}
# PARAMETER: one COPY and one checksum per active target. The file lands at
# /orig/<target id>/<original path>; validate.yml copies it to orig/<target id>/<original path>
# and tools/verify_target.py checks the SHA-1 against config/targets.json.
COPY orig/GAME01-rev0/main.dol /orig/GAME01-rev0/sys/main.dol
RUN echo "0000000000000000000000000000000000000000  /orig/GAME01-rev0/sys/main.dol" | sha1sum -c -
COPY --from=dependencies /binutils /binutils
COPY --from=dependencies /compilers /compilers
COPY --from=dtk /dtk /usr/local/bin/dtk
# git, python3 and sh are required by validate.yml (checkout, the tools/ scripts and the publish
# action). gcompat lets the Actions runner's own Node.js run inside an Alpine container.
RUN apk add --no-cache gcompat git ninja python3
CMD [ "sh" ]
