# game-build

Private build environment for owner/game. **This repository and its container package must stay
private:** they contain the original game executable.

The image provides:

| Path | Contents |
| --- | --- |
| `/orig/GAME01-rev0/sys/main.dol` | The target original, SHA-1 checked at build time against the value in the public repository's `config/targets.json` |
| `/usr/local/bin/dtk` | decomp-toolkit at the tag `configure.py` pins |
| `/compilers` | The compiler pack, SHA-256 checked |
| `/binutils` | GameCube/Wii binutils, SHA-256 checked |

Base images are pinned by digest. Pushes to `main` publish `ghcr.io/owner/game-build:main` and
`:<commit>`; the workflow summary records the digest. The public repository's `validate.yml` must
reference the image **by digest**, and changing that digest is an owner decision.

## Owner setup after the first publish

1. Open the `game-build` package settings on GitHub and keep its visibility **private**.
2. Under **Manage Actions access**, add `owner/game` with the **Read** role.

## Layout

```text
Dockerfile
.github/workflows/image.yml
orig/GAME01-rev0/main.dol      # the original, committed here and nowhere else
```
