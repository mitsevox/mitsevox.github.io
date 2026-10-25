# Evidence

Recover what the target supports, and keep uncertainty explicit.

## Inventory before interpretation

Inventory the target's parsed filesystem and available executables, symbols, ELF/STABS/DWARF data, linker maps, diagnostic strings, SDK references and related builds. Record hashes/revisions and which files were parsed. If claiming an artifact does not exist, document the coverage of the search; a filename search or a few strings alone is insufficient.

Related builds can suggest names and behavior. They do not prove the target's offsets, field widths, original names or source boundaries. Keep target evidence separate from reference evidence and inferred meaning.

## Define a bounded task

Identify the functions, target ranges, candidate source unit, shared headers and dependencies before editing. Confirm accepted declarations on current main. Establish each function's full extent and the limits of any provisional unit; unresolved boundaries must remain visible.

For a field or signature, cite actual loads/stores and relevant caller/callee behavior. A nearby subsystem's access is not proof of the same layout. Preserve unknown offsets without inventing a convenient struct.

## The reconstruction loop

1. Describe the behavior and evidence-backed types before optimizing for a score.
2. Write plausible source in the codebase's style.
3. Compile with the documented unit/library profile.
4. Compare full function bytes, referenced data and relocations under the documented comparison method.
5. Investigate the remaining uncertainty, record the result and retain useful partial source.

A byte match establishes compiler equivalence for the measured scope. It does not by itself prove names, intent, type correctness or original file boundaries.

## Escalate the question, not the guesswork

| Uncertainty | Useful investigation |
| --- | --- |
| Behavior, references or ownership | Target disassembly and bounded Ghidra/static analysis |
| Different instruction selection or scheduling | Controlled compiler experiments and relevant compiler intermediate output |
| Competing behavioral interpretations | Bounded debugger/runtime trace with known inputs and conditions |
| Candidate SDK reuse | Fingerprints followed by calls, globals, types and boundary checks |

Record tested revision, tool version/settings, inputs, conclusion and remaining uncertainty. Check decompiler output against instructions. Runtime observations establish what happened under those conditions, not the original source text. Keep bulk experiments private; retain concise reproducible evidence publicly.

## Matching integrity

Do not force a match through patched output, embedded instruction bytes, unsupported inline assembly, per-function flag changes, altered comparison boundaries or excluded mismatches. Do not invent helpers, padding, casts, volatile qualifiers or control flow solely for code generation.

Compiler exceptions require original-scope evidence and explicit owner approval under the project's documented policy. Originally handwritten assembly needs provenance. Labeling a workaround “fake match” does not make it acceptable.

When evidence runs out, preserve the useful partial reconstruction and document the gap. Keep original bytes in the verified linked build until replacement is validated. Partial similarity is useful progress; unsupported certainty is not.

## SDK and imported work

Retain origin, source revision, license/provenance and local modifications. A fingerprint is a candidate, especially for short functions. Inspect target-specific calls, data ownership and compilation boundaries before import. Imported code receives the same relevant fidelity and hostile reviews as new reconstruction.

Record these matching-integrity and investigation rules in CONTRIBUTING.md. Keep evidence-format details and reproducible locators in target configuration.
