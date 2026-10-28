# Evidence

Recover what the target supports, record it, and never manufacture a match.

A byte match proves that the compiler produced the same code from the submitted source; it proves nothing about names, types, intent or where the original source file boundaries were. The project's value is the evidence behind those claims, so the evidence is recorded in the repository next to the configuration it supports and is reviewed with it.

## Inventory before interpretation

Inventory what the target and its references actually contain: the parsed filesystem, executables, symbols, debug information, linker maps, diagnostic strings, SDK references and related builds. Record hashes or revisions and which files were parsed. A claim that an artifact does not exist must say how thoroughly it was searched; a file-name search or a few strings is not enough.

Related builds (another platform, another revision, another game on the same engine) suggest names and behavior. They do not prove the target's offsets, field widths, original names or source boundaries. Keep target evidence, reference evidence and inferred meaning separate. A claim is per target, because it carries addresses: a name recovered on one target and carried to a sibling is a `related` row in the sibling's `evidence.tsv`, with `provisional` edges on its unit rows, until the sibling's own bytes confirm it ([Multiple targets](/wiki/multi-target/)).

Reference material that agents read on every task lives under `references/`: text only, regenerable by a named tool, no file over 4 MB. The scaffold check warns on anything larger.

## Bounded tasks

Identify the functions, address ranges, candidate source unit, shared headers and dependencies before editing. Confirm accepted declarations on current `main`. Establish each function's full extent and the limits of any provisional unit; unresolved boundaries stay visible.

For a field or signature, cite the actual loads and stores and the relevant caller or callee behavior. A nearby subsystem's access is not proof of the same layout. Preserve unknown offsets instead of inventing a convenient struct.

## The reconstruction loop

1. Describe the behavior and the evidence-backed types before optimizing for a score.
2. Write plausible source in the codebase's style.
3. Compile with the documented unit or library profile.
4. Compare the full function bytes, referenced data and relocations with objdiff.
5. Investigate the remaining uncertainty, record the result and retain useful partial source.

| Uncertainty | Useful investigation |
| --- | --- |
| Behavior, references or ownership | Target disassembly and bounded static analysis |
| Different instruction selection or scheduling | Controlled compiler experiments and the compiler's intermediate output |
| Competing behavioral interpretations | A bounded debugger or emulator trace with known inputs and conditions |
| Candidate SDK or library reuse | Fingerprints followed by calls, globals, types and boundary checks |

Record the tested revision, tool version and settings, inputs, conclusion and remaining uncertainty. Check decompiler output against instructions. Runtime observations establish what happened under those conditions, not the original source text. Keep bulk experiments private; retain concise reproducible evidence publicly.

## The evidence record

Each target keeps `config/<target id>/evidence.tsv`, one claim per row, tab separated:

```text
kind  start  end  subject  origin  start_boundary  end_boundary  evidence
```

| Column | Values |
| --- | --- |
| `kind` | `name`, `function`, `data`, `unit-anchor`, `unit`, `type`, `field`, `external`, `compiler`, `assembly`, `source-form`, `linker` |
| `start`, `end` | Virtual addresses as `0x` plus eight upper-case hex digits, end exclusive; `-` when unknown or inapplicable |
| `subject` | The symbol, source path, type or field concerned |
| `origin` | `target` (present in the target's bytes, symbols or debug information), `signature` (a named tool signature), `related` (another identified build), `inferred` (interpretation of the code) |
| `start_boundary`, `end_boundary` | `exact`, `provisional`, `open` or `-`, claimed independently of each other; anything but `-` only on `function`, `data`, `unit`, `assembly` and `linker` rows |
| `evidence` | A reproducible locator and what it establishes and leaves unknown |

Use separate rows for a name, a function extent, a field layout and a source-unit boundary: one claim never silently proves another. A `name` row with origin `target` needs explicit name evidence in the target; a name supported only by behavior is `inferred`. Compiler profiles are `compiler` rows at the unit or library level. The starter `config/README.md` is the full definition and goes into the repository as is.

## What earns a row

A row is a claim a person or agent made that a reviewer must be able to challenge: an `inferred` name, a `unit` boundary, a `type` or `field` layout read from loads and stores, a `compiler`, `source-form` or `linker` claim. Tool output is not transcribed row by row. Symbol extents from the toolkit, debug names from a related build, signature hits from a library map: these are reproducible from `references/` plus a tool at a pinned revision, so they get one row per tool run, with kind `unit-anchor` or `name`, origin `related` or `signature`, a subject that names the tool with its inputs and revision, and the regenerable report's path as the evidence. The table then stays readable in review, and the report is the evidence.

`python3 tools/evidence.py check` runs in the `Tool tests` job and in the scaffold check: the header row, eight columns, the address format, the kinds and origins, edges only on the rows that have extents, non-empty subject and evidence. It checks form, not truth; the hostile checklist's `Names` row is the provenance check, and the publish action counts a function as named only when its symbol is not a tool label, so an unnamed function can never be published as named.

## Matching integrity

Do not force a match through:

- per-function flags, optimization pragmas or compiler attributes introduced to force code generation;
- inline assembly, embedded instruction bytes or patched compiler output in place of compiled source;
- invented helpers, casts, volatile qualifiers, padding or control flow whose only justification is the bytes;
- altered symbol boundaries, excluded comparisons or progress categories that hide mismatches;
- behavioral changes made to satisfy the compiler.

Compiler versions and flags need evidence at the compilation-unit or library level. A function-specific exception needs evidence that the original used it and the owner's explicit approval. Originally handwritten assembly needs provenance. Labeling a workaround a fake match does not make it acceptable; it stays a local experiment outside accepted source.

When evidence runs out, keep the useful partial reconstruction as a `NonMatching` unit, keep the original bytes linked and record the gap. Partial similarity is progress; unsupported certainty is not.

## Imported and SDK code

Retain the origin, source revision, license and local modifications of anything imported, in `CREDITS.md` and under `licenses/`; a verbatim imported tree goes under `extern/` with its own credits. A fingerprint match is a candidate, especially for a short function; inspect target-specific calls, data ownership and compilation boundaries before importing. Imported code whose every name is `target`, `signature` or `related` is a tier B change: it gets the hostile review, not the blind accuracy pass.

Comments in source explain intent, invariants and non-obvious relationships. Matching scores, compiler experiments, agent notes and review history belong in `evidence.tsv` or the PR, never in source comments.
