# Tools

Tools worth knowing, grouped by the question each one answers, and what to check before a project relies on one.

This chapter recommends; it does not require anything beyond the base. Each project's agents decide which tools earn a place, by running the check on the tool's card against that project's own code. A tool that passes the check is pinned in the project (a version tag or a commit) and its licence is recorded in `CREDITS.md`. One that fails is left out, with the reason in the project's notes.

Every card says which toolchain the tool suits: CodeWarrior (`mwcc`, most GameCube games), ProDG (SN Systems' GCC 2.95, many EA and third-party games) or any. "Agent fit" says whether an agent can drive it: run from the command line, no screen, text output.

## The base

These are the tools every project in this standard already uses. [Build, verify, measure](/wiki/build-verify-measure/) covers how they fit together; this section says what each is for.

- **decomp-toolkit (dtk).** Splits the original executable into objects, names functions it recognises by signature, writes the linker script and explains why a relinked file differs (`dol diff`). Also reads DWARF 1 (`dwarf dump`) and extracts files from a disc image. MIT.
- **objdiff.** Compares each compiled object with the original, produces the progress report and lists regressions between two reports. MIT or Apache-2.0.
- **The compiler pack.** The Metrowerks and ProDG compiler binaries that dtk-template downloads by default. See [Risks and licences](#risks-and-licences).
- **wibo.** Runs those Windows compilers on Linux and macOS. Open source.
- **ninja.** Runs the build.

Keep the dtk and objdiff versions the same across a project's targets and say which version a result came from.

## Test one variant of a function

**objdiff one-shot diff.** `objdiff-cli diff` with `-o -` prints one function's diff as JSON (`--format json`) instead of opening the viewer. It takes either two objects (`-1` target, `-2` base) or a project directory (`-p`) and a unit name (`-u`), then the function's symbol.

- **For:** the inner loop of matching. A script compiles a scratch copy of the unit with the unit's own compile command from `build.ninja`, diffs the one function, and exits 0 when it is identical. No full rebuild, no report regeneration, and the source tree is never touched.
- **Toolchain:** any. **Agent fit:** good; structured output.
- **Check before relying on it:** for a few functions, the script's verdict agrees with the full build's report (identical where the report says 100%, different elsewhere).

A trial script built this way is worth writing early in any project; the alternative, rebuilding the whole report for each variant, takes seconds per try instead of a fraction of one.

## Get a first C draft

**m2c** ([matt-kempster/m2c](https://github.com/matt-kempster/m2c)). Turns a function's assembly into C. Targets are written platform-compiler-language, for example `ppc-mwcc-c`; `--context` takes a header file for types (dtk-template's `decompctx.py` makes one), and `--valid-syntax` aims for output that compiles without edits. GPL-3.0.

- **For:** many small and medium functions at the start of a project, or a function too long to write by hand from nothing. Run it over the unmatched functions under a size limit, compile each draft, keep the ones that match, and hand-fix the near misses.
- **Toolchain:** CodeWarrior is supported directly. Its GCC mode is written for MIPS; output for ProDG on PowerPC is untested.
- **Agent fit:** good; deterministic with `--deterministic-vars`.
- **Limits:** a draft is m2c's form, not the original's. It invents temporaries and casts, can add arguments that are not there, and can let a function fall off its end. A matching draft is still a draft: it needs the project's names, types and style before it is committed.
- **Check before relying on it:** on ten functions the project has already matched, how many m2c drafts compile and how close they come.

## Why does my C compile differently?

**mwcc-debugger** ([cadmic/mwcc-debugger](https://github.com/cadmic/mwcc-debugger)). Runs the compiler under a debugging emulator and writes out its internal state for one function: the parsed source, the code after each optimisation pass, and the register allocator's decisions. It turns "the registers are different" into a reason.

- **For:** a function that is close but will not match, when the difference is register choice or instruction order. The dumps show which variable got which register and why; that points at the declaration, the expression or the loop shape the original used.
- **Toolchain:** CodeWarrior only. It runs two compiler versions: GC/1.1 (its README: "usually good enough for GC/1.0 - GC/1.2.5") and GC/2.6 ("usually good enough for GC/1.3.2 - GC/2.7"). Linux and macOS.
- **Setup:** gdb, cmake and Rust, and a build of encounter's `retrowin32` fork with GDB support. Done once per machine; not for CI.
- **Licence:** the repository has no licence file. Clone it at a pinned commit on each machine, record it as "no licence" in `CREDITS.md`, and do not copy it into a project repository.
- **Limits:** the dumps are facts about the compiler; what a project does with them is not. The usual shortcut, adding dead code that steers the allocator, is a fake match ([Evidence](/wiki/evidence/#matching-integrity)).
- **Check before relying on it:** the project's compiler is not one of the two the debugger runs, so first compile the project's matched units with the debugger's version and compare. If they come out byte-identical, the dumps describe your compiler; if some differ, the dumps cannot be trusted for those.

**GCC dump flags (ProDG).** ProDG's compiler is GCC 2.95, which writes its internal representation after each pass when asked: `-da` for every pass, or single passes such as `-dr`, `-dc`, `-dS`, `-dg` and `-dR`. This is the ProDG counterpart of the debugger and needs nothing new.

- **For:** the same questions on ProDG code: why a value lives in a different register, why an instruction moved.
- **Setup:** the compile wrapper has to pass the flags through to `cc1` and keep the dump files. Keep dumps private; they contain the game's code.
- **Check before relying on it:** that the project's `cc1` writes the dump files for one known function.

**Compiler probe.** Not a downloadable tool but a method worth a script in any project: compile a piece of source the original certainly contains (a public SDK or runtime function) under every candidate compiler version and flag set, and search the original executable for each result. The version whose output appears is the one the original used. The result is evidence for the compiler profile, recorded as such.

## Search for a near-miss fix

**decomp-permuter** ([simonlindholm/decomp-permuter](https://github.com/simonlindholm/decomp-permuter)). Makes random changes to one function's source, compiles each, and keeps the ones that score closer to the original. It supports PowerPC and has a CodeWarrior compile example. MIT.

- **For:** late in a function, when only register allocation differs.
- **Toolchain:** any it can compile; set up per project (a directory with the function, the original object, a compile script and a settings file).
- **Agent fit:** runs headless, but it is a random search: many cores, minutes to hours, and output that needs sorting.
- **Limits:** its own README warns that it "often finds lots of nonsensical changes that improve regalloc". Most of what it finds is a fake match. Use its result as a hint and rewrite the idea by hand in plausible C: a moved declaration, a value read once into a local, two statements swapped. Never commit its output.
- **Check before relying on it:** on a few near misses, how many of its hits survive being rewritten as plain C.

**Declaration-order search.** A narrower, deterministic search: try the orders of a function's local declarations and keep the one that matches. On CodeWarrior, register numbering follows declaration order, so this fixes a common class of register differences and cannot change what the code does. Any project can script it on top of its trial script.

## Find the same functions in another build

These answer "which functions here are the same as functions there": a second revision of the same game, a sequel or sibling game on the same engine, or a library shared between games. Results suggest names; they are `related` evidence, never proof ([Multiple targets](/wiki/multi-target/#carrying-a-map-to-a-new-target)).

**coddog** ([ethteck/coddog](https://github.com/ethteck/coddog)). Finds identical and similar functions within one binary (`cluster`), between a function and a binary (`match`, `submatch`) and between projects (`compare2`, `compare-n`, marked experimental). MIT or Apache-2.0.

- **Toolchain:** any. **Agent fit:** command line, text output.
- **Limits:** it reads a project description file (`decomp.yaml`) that dtk-template projects do not have, and its documentation shows no PowerPC example.
- **Check before relying on it:** a known answer. Run it between two revisions of the same game where a byte-identical relink already ties each function to its sibling, and count how many pairs it finds and how many it gets wrong.

**Ghidra BSim.** Part of Ghidra (Apache-2.0). Compares functions by what Ghidra's decompiler makes of them rather than by bytes, so it can pair functions that differ slightly in code. It needs Ghidra and a GameCube loader ([Cuyler36/Ghidra-GameCube-Loader](https://github.com/Cuyler36/Ghidra-GameCube-Loader), Apache-2.0, built from source against the Ghidra version in use).

- **For:** the same job as coddog where the builds are further apart: another compiler version, another platform, small source changes.
- **Agent fit:** runs headless, but slowly: a full Ghidra analysis of each binary first.
- **Check before relying on it:** the same known-answer test as coddog.

## What does this code do in the game?

**Ghidra** (Apache-2.0, with the loader above). Its decompiler and cross-references answer what a function does, who calls it and what data it touches. dtk and objdiff already give a project its split, its symbols and its assembly, so Ghidra is for understanding, not for matching. Keep Ghidra projects private; they contain the game.

**Dolphin.** The GameCube emulator (GPL-2.0 or later); `dolphin-emu-nogui` runs without a window. A bounded trace answers what only running the game shows: a value at run time, which branch runs, what a function is for. It needs the owner's own disc image on the machine and is not for CI. Record what was traced, on which build, and what stays uncertain ([Evidence](/wiki/evidence/)).

## Risks and licences

- **The compiler pack.** The Metrowerks and SN Systems compilers are proprietary. Every GameCube decompilation uses the community's redistributed pack, and a project that adopts this standard accepts that. Pin the pack by its file name and never commit a compiler to a project repository.
- **Patched compilers.** The pack includes community-patched builds (for example `GC/1.3.2r`). A patched compiler can be a useful tool, but output from it is never evidence of the original toolchain.
- **Licences.** Record each tool and its licence in `CREDITS.md`. A tool with no licence (mwcc-debugger) is used from its own clone on each machine and never copied into a repository.
- **Private output.** Dumps, traces, Ghidra projects and similarity databases contain the game's code. They stay on the machine or in the private build repository, like the originals.
- **Fake matches.** No tool here makes a forced match acceptable. A tool's result is a hint until it reads as plausible original source ([Evidence](/wiki/evidence/#matching-integrity)).
