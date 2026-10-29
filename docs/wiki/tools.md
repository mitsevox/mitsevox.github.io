# Tools

Tools worth knowing, grouped by the question each one answers, and what to check before a project relies on one.

This chapter recommends; it does not require anything beyond the base. Each project's agents decide which tools earn a place, by running the check on the tool's card against that project's own code, with the owner's go-ahead to install the tool. A tool that passes the check is pinned in the project (a version tag or a commit) and its licence is recorded in `CREDITS.md`. One that fails is left out, with the reason in the project's notes.

Each tool card says which toolchain the tool suits: CodeWarrior (`mwcc`, most GameCube games), ProDG (SN Systems' GCC 2.95, many EA and third-party games) or any. "Agent fit" says whether an agent can drive it: run from the command line, no screen, text output. The two methods in this chapter (the compiler probe and the declaration-order search) are scripts a project writes, not tools it installs.

## The base

These are the tools every project in this standard already uses. [Build, verify, measure](/wiki/build-verify-measure/) covers how they fit together; this section says what each is for.

- **decomp-toolkit (dtk).** Splits the original executable into objects, names functions it recognises by signature, writes the linker script and explains why a relinked file differs (`dol diff`). Also reads DWARF 1.1 from an ELF (`dwarf dump`) and extracts files from a disc image. MIT or Apache-2.0.
- **objdiff.** Compares each compiled object with the original, produces the progress report and lists the changes, regressions included, between two reports. MIT or Apache-2.0.
- **The compiler pack.** The compiler binaries the project's `configure.py` pins; dtk-template downloads the decomp.dev pack. See [Risks and licences](#risks-and-licences).
- **wibo.** Runs those Windows compilers on Linux and macOS. MIT.
- **ninja.** Runs the build.

Keep the dtk and objdiff versions the same across a project's targets and say which version a result came from.

## Test one variant of a function

**objdiff one-shot diff.** `objdiff-cli diff` with `-o -` prints the diff of a whole object as JSON (`--format json`, the default; also `json-pretty` or `proto`) instead of opening the viewer. It takes either two objects (`-1` target, `-2` base) or a project directory (`-p`) with a unit name (`-u`); without `-u`, a symbol name selects the unit that contains it.

- **For:** the inner loop of matching. A script compiles a scratch copy of the unit with the unit's own compile command from `build.ninja`, diffs it, picks the one function out of the JSON, and exits 0 when that function is identical. No full rebuild, no report regeneration, and the source tree is never touched.
- **Toolchain:** any. **Agent fit:** good; structured output.
- **Check before relying on it:** for a few functions, the script's verdict agrees with the full build's report (identical where the report says 100%, different elsewhere).

A trial script built this way is worth writing early in any project, because it tries a variant without rebuilding the whole report.

## An objdiff 100% isn't proof of exact

objdiff can score a function 100% while its source loads the wrong constant. How strictly it compares relocations is set by `functionRelocDiffs`: `none`, `name_address` (the viewer's default), `data_value`, or `all` (name or address, and data value). The progress report (`objdiff-cli report generate`) uses `none` unless the project's `objdiff.json` options or `-c` override it, and dtk-template sets no override; `none` does not compare relocation targets at all. The viewer's default is not safe either: under `name_address`, two compiler-generated literal names (CodeWarrior's `@1234`, GCC's `$LC12`) count as equal whatever they hold. A load of a float or double from a literal pool (`.sdata2`, `.rodata`) is the same instruction whichever literal it points at, so `1.59155f` where the original holds 5/π, or a constant one unit in the last place away from `221.0f / 30.0f`, still scores 100%. Two loads of different literals in swapped order pass too.

The build does not catch it. In a dtk-template project, a unit that is not yet `Matching` links the original object, so the wrong source is never compiled into the checked executable: CI stays green and the report counts the function as matched. The error only shows when the whole unit is switched to `Matching`. Any project that counts per-function progress in units not yet linked as `Matching` is exposed; every dtk-template project does by default. A wrong value (not a swapped pair) does lower the unit's data score, since the report compares data sections byte for byte, so a unit at 100% code but under 100% data is worth a look.

- Treat a function's 100% as provisional until its unit links as `Matching`.
- Write float constants at full precision, or as the expression the original likely used (`5.0f / PI`), never as a rounded decimal.
- When checking a match by hand, set `functionRelocDiffs` to `data_value` or `all`, which compare the literal each relocation points at. dtk-template's `configure.py` carries `--config functionRelocDiffs=data_value` in `progress_report_args`, commented out; enabling it makes the progress report strict too.
- Best: a CI check that, for every function claimed exact, compares each relocation's target value and the order of the loads with the original, and fails on a mismatch.

The Scooby-Doo! Night of 100 Frights project found this in October 2026, when review caught wrong float literals in a HUD unit that objdiff scored 100%, and built that check: [`tools/literal_check.py`](https://github.com/mitsevox/n100f/blob/main/tools/literal_check.py) ([mitsevox/n100f#191](https://github.com/mitsevox/n100f/pull/191)). For every function whose code equals the original's with the relocated fields masked, it compares where each relocation lands: a name `symbols.txt` gives must have the original's address, and an anonymous literal or table must hold the original executable's bytes there. It reads only `objdiff.json` and the objects it lists, `symbols.txt`, `splits.txt` and the original, and CI runs it per target after the build. Its first run checked 2,813 exact functions on one target and found 13 that disagreed: loads and stores in swapped order, a jump table with two cases swapped (a behaviour bug in the reconstruction), and calls through `fn_` placeholders that `symbols.txt` had since named, which would fail to link once their units went `Matching`.

## Get a first C draft

**m2c** ([matt-kempster/m2c](https://github.com/matt-kempster/m2c)). Turns a function's assembly into C. Targets are written platform-compiler-language, for example `ppc-mwcc-c`; `--context` takes a header file for types (dtk-template's `decompctx.py` makes one), and `--valid-syntax` aims for output that compiles without edits, using macros from m2c's own `m2c_macros.h` that do not belong in committed source. GPL-3.0.

- **For:** many small and medium functions at the start of a project, or a function too long to write by hand from nothing. Run it over the unmatched functions under a size limit, compile each draft, keep the ones that match, and hand-fix the near misses.
- **Toolchain:** CodeWarrior is supported directly. Its GCC-specific heuristics are MIPS patterns; `ppc-gcc` is accepted, but output for ProDG is untested.
- **Agent fit:** good. `--deterministic-vars` names temporaries after their place in the assembly, so they do not shift when other temporaries change and drafts diff cleanly.
- **Limits:** a draft is m2c's form, not the original's: it invents temporaries and casts. In our use it has also added call arguments that were not there and let functions fall off their end. A matching draft is still a draft: it needs the project's names, types and style before it is committed.
- **Check before relying on it:** on ten functions the project has already matched, how many m2c drafts compile and how close they come.

## Why does my C compile differently?

**mwcc-debugger** ([cadmic/mwcc-debugger](https://github.com/cadmic/mwcc-debugger)). Runs the compiler under a debugging emulator and writes out its internal state for one function: the parsed source, the code after the frontend's optimisations and between backend passes, and the register allocator's priority order. It turns "the registers are different" into a reason.

- **For:** a function that is close but will not match, when the difference is register choice or instruction order. The dumps show how the allocator ranked the function's values (most are compiler temporaries); that points at the declaration, the expression or the loop shape the original used.
- **Toolchain:** CodeWarrior only. It supports two compiler versions: GC/1.1 (its README: "usually good enough for GC/1.0 - GC/1.2.5") and GC/2.6 ("usually good enough for GC/1.3.2 - GC/2.7"). Frontend optimisations cannot be debugged. **Agent fit:** text dumps, one function per run; Linux and macOS.
- **Setup:** gdb, cmake and Rust, and a build of encounter's `retrowin32` fork with GDB support. Done once per machine; not for CI.
- **Licence:** the repository has no licence file. Clone it at a pinned commit on each machine, record it as "no licence" in `CREDITS.md`, and do not copy it into a project repository.
- **Limits:** the dumps are facts about the compiler; what a project does with them is not. The usual shortcut, adding dead code that steers the allocator, is a fake match ([Evidence](/wiki/evidence/#matching-integrity)).
- **Check before relying on it:** if the project's compiler is not one of the two the debugger supports, first compile the project's matched units with the debugger's version and compare. If they come out byte-identical, the dumps are a reasonable guide for your compiler; for units that differ, they are not.

**GCC dump flags (ProDG).** ProDG's compiler is GCC 2.95, which writes its internal representation after each pass when asked: `-da` for every pass, or single passes such as `-dr`, `-dc`, `-dS`, `-dl`, `-dg` and `-dR` (`-dl` and `-dg` are the local and global register allocation). This is the ProDG counterpart of the debugger and needs nothing new.

- **For:** the same questions on ProDG code: why a value lives in a different register, why an instruction moved.
- **Toolchain:** ProDG. **Agent fit:** text files, written by the normal compile.
- **Setup:** the compile wrapper has to pass the flags through to `cc1` and keep the dump files. Keep dumps private; they contain the game's code.
- **Check before relying on it:** that the project's `cc1` writes the dump files for one known function.

**Compiler probe.** A method worth a script in any project: compile a piece of source the original certainly contains under every candidate compiler version and flag set, and search the original executable for each result, with relocation fields masked (relocated fields differ until link time). Each version whose output appears stays a candidate for that library; versions that compile the probe identically are not told apart by it, so probe with several functions until one candidate remains, or record the set that remains. A hit says nothing about other libraries: SDK and runtime libraries were often built with another compiler than the game code. Probe the game's own code with source the project has already matched, and record each result per library as evidence for that library's profile.

## Search for a near-miss fix

**decomp-permuter** ([simonlindholm/decomp-permuter](https://github.com/simonlindholm/decomp-permuter)). Makes random changes to one function's source, compiles each, and keeps the ones that score closer to the original. It supports PowerPC and has a CodeWarrior compile example; its `import.py` can read a ninja build. MIT.

- **For:** late in a function, when only register allocation differs.
- **Toolchain:** any it can compile; set up per function (a directory with the function, the original object, a compile script and a settings file).
- **Agent fit:** runs headless, but it is a random search: many cores, minutes to hours, and output that needs sorting.
- **Limits:** its own README warns that it "often finds lots of nonsensical changes that improve regalloc 'by accident'". Most of what it finds is a fake match. Use its result as a hint and rewrite the idea by hand in plausible C: a moved declaration, a value read once into a local, two statements swapped. Never commit its output.
- **Check before relying on it:** on a few near misses, how many of its hits survive being rewritten as plain C.

**Declaration-order search.** A narrower, deterministic search: try the orders of a function's local declarations and keep the one that matches. On CodeWarrior, the order of local declarations often changes which register each local gets, because the allocator's priority depends on how the variables are numbered. Permute only declarations of types with trivial construction and destruction (scalars, pointers, plain structs and arrays) that have no initializer or an initializer with no side effects that reads none of the other permuted locals, so the reorder cannot change what the code does. In C++, a constructor or destructor makes the order part of the behaviour. Any project can script it on top of its trial script.

## Find the same functions in another build

These answer "which functions here are the same as functions there": a sequel or sibling game on the same engine, a library shared between games, or a cross-check of a second revision of the same game. For a new target of the same game, the transfer follows [Multiple targets](/wiki/multi-target/#carrying-a-map-to-a-new-target); these tools only cross-check it, because a similarity threshold breaks ties that procedure leaves open. Results suggest names; they are `related` evidence, never proof. Record each run as one evidence row: the tool and its version, the inputs and their revisions, and the report's path ([Evidence](/wiki/evidence/#what-earns-a-row)). The report (function pairs and scores, no code) is committed; the database stays private.

**coddog** ([ethteck/coddog](https://github.com/ethteck/coddog)). Finds identical and similar functions within one binary (`cluster`), between a function and a binary (`match`, `submatch`), between projects (`compare2`, `compare-n`, marked experimental) and between a raw binary and projects (`compare-raw`). MIT or Apache-2.0.

- **Toolchain:** any. **Agent fit:** command line, text output.
- **Limits:** every subcommand reads a project description file (`decomp.yaml`) that dtk-template projects do not have; with more than one version in it, `match`, `submatch` and `cluster` stop at an interactive prompt. Its code lists a GameCube/Wii platform, but its documentation shows no PowerPC example.
- **Check before relying on it:** a known answer. Run it between two revisions of the same game where a byte-identical relink already ties each function to its sibling, and count how many pairs it finds and how many it gets wrong.

**Ghidra BSim.** Part of Ghidra (Apache-2.0). Compares functions by what Ghidra's decompiler makes of them rather than by bytes, so it can pair functions that differ slightly in code. It needs Ghidra and a GameCube loader ([Cuyler36/Ghidra-GameCube-Loader](https://github.com/Cuyler36/Ghidra-GameCube-Loader), Apache-2.0, built from source against the Ghidra version in use; its README installs the zip through Ghidra's window, so for headless use unzip it into `<GhidraInstallDir>/Ghidra/Extensions`).

- **For:** the same job as coddog where the builds are further apart: another compiler version, another platform, small source changes.
- **Toolchain:** any. **Agent fit:** headless, but slow. `analyzeHeadless` imports and analyses each binary; the `bsim` command in Ghidra's `support` directory creates a local database (a `file:` URL, no server) and generates and commits signatures; the comparison itself runs as a script under `analyzeHeadless`. Ghidra's `QueryWithFiltersScript` prints function pairs with similarity and significance, but its example filters (architecture, compiler, a self-significance floor, skipping functions whose names came from Ghidra's analyzers, and keeping only matches in the queried executable) would leave a GameCube comparison empty or one-sided. A project's script starts from it with every example filter removed, sets its own similarity threshold and match limit, and takes the database URL as an argument.
- **Check before relying on it:** the same known-answer test as coddog.

## What does this code do in the game?

**Ghidra** (Apache-2.0, with the loader above). Its decompiler and cross-references answer what a function does, who calls it and what data it touches. dtk and objdiff already give a project its split, its symbols and its assembly, so Ghidra is for understanding, not for matching. **Toolchain:** any. **Agent fit:** headless analysis and scripts; the decompiler output is text. Keep Ghidra projects private; they contain the game.

**Dolphin.** The GameCube emulator (mostly GPL-2.0 or later); `dolphin-emu-nogui -p headless` runs without a window. A bounded trace answers what only running the game shows: a value at run time, which branch runs, what a function is for. **Toolchain:** any. **Agent fit:** limited; it needs the owner's own disc image on the machine and is not for CI. Record what was traced, on which build, and what stays uncertain ([Evidence](/wiki/evidence/)).

## Risks and licences

- **The compiler pack.** The Metrowerks and SN Systems compilers are proprietary. Every GameCube decompilation uses the community's redistributed pack, and a project that adopts this standard accepts that. Pin the pack by its file name and never commit a compiler to a project repository.
- **Patched compilers.** The pack includes community-patched builds, for example `GC/1.3.2r`. A patched compiler can be a useful tool, but its output is evidence of the original toolchain only for behaviour the project has shown it shares with an unpatched release.
- **Licences.** Record each tool and its licence in `CREDITS.md`. A tool with no licence (mwcc-debugger) is used from its own clone on each machine and never copied into a repository.
- **Private output.** Dumps, traces, Ghidra projects and similarity databases contain the game's code. They stay on the machine or in the private build repository, like the originals.
- **Fake matches.** No tool here makes a forced match acceptable. A tool's result is a hint until it reads as plausible original source ([Evidence](/wiki/evidence/#matching-integrity)).
