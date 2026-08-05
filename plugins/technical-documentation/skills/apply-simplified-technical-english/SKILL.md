---
name: apply-simplified-technical-english
description: Apply ASD-STE100 Simplified Technical English Issue 9 to human-facing technical documentation while preserving technical meaning, code, identifiers, quotations, and required legal text. Use when creating, editing, reviewing, or sweeping READMEs, guides, tutorials, procedures, runbooks, API prose, help text, support content, or other English documentation intended for people. Use it as the language gate within Docs Sweep and whenever a user requests ASD-STE100, Simplified Technical English, STE, controlled English, or globally readable technical prose.
---

# Apply Simplified Technical English

Rewrite human-facing technical prose so that it obeys ASD-STE100 Issue 9 and
keeps the source meaning accurate.

## Operating contract

- Read [asd-ste100-issue-9.md](references/asd-ste100-issue-9.md) before editing.
- Treat repository instructions and more specific legal, regulatory, safety, or
  publication requirements as additional controls. Report a direct conflict.
- Apply STE to explanatory prose, instructions, notes, safety text, headings,
  captions, and user-facing messages. Preserve code, commands, identifiers,
  schema keys, quoted interface text, external quotations, and required legal
  wording. Change them only when you can also change the authoritative source.
- Preserve technical meaning. Do not simplify away a prerequisite, condition,
  limit, warning, exception, source, or qualification.
- Use an authorized copy of Issue 9 for dictionary, part-of-speech, approved-
  meaning, and approved-form checks. The bundled reference is not a substitute
  for the controlled dictionary.
- Do not claim certification or complete ASD-STE100 conformance from automated
  checks alone.

## Workflow

### 1. Set the scope

1. Inventory the requested human-facing documentation.
2. Mark each prose block as procedural, descriptive, safety, note, quoted, or
   machine-facing.
3. Identify the company or project glossary and the controlling publication
   style. Preserve historical release text unless the user asks to revise it.

### 2. Rewrite without changing meaning

1. Use approved dictionary words only with their approved part of speech,
   meaning, and form. Use approved technical nouns and verbs consistently.
2. Use short, direct sentences, active voice, explicit subjects, articles, and
   complete words. Do not use contractions or semicolons.
3. Give one topic per descriptive sentence and one instruction per procedural
   sentence, except when actions occur at the same time.
4. Put conditions before commands. Keep safety commands and their consequences
   explicit. Keep notes informational.
5. Use the sentence, paragraph, multi-word-noun, punctuation, and word-count
   limits in the reference.

### 3. Run the deterministic check

Run the checker on each changed human-facing file. Select `procedural` or
`descriptive` when a document has one type. Use `auto` for mixed Markdown:

```bash
python3 <skill-root>/scripts/check_ste.py --mode auto path/to/document.md
```

`<skill-root>` is this skill's own directory. Under Claude Code it resolves to
`${CLAUDE_PLUGIN_ROOT}/skills/apply-simplified-technical-english`.

For repository-wide checks, pass the documentation roots. Use
`--fail-on-warning` only when the project has reviewed the heuristic rules and
accepts them as blocking:

```bash
python3 <skill-root>/scripts/check_ste.py --mode auto README.md docs/
```

The checker skips fenced code, indented code, Markdown tables, block quotes,
link targets, and frontmatter. Treat its sentence count, passive-voice result,
and procedural classification as review aids when Markdown or domain terms make
the result ambiguous.

### 4. Complete the manual gate

For every changed prose block, verify:

- Dictionary approval, part of speech, approved meaning, and approved form.
- Technical terms against the project glossary and the applicable STE category.
- One meaning per term and consistent terminology across the document set.
- Procedural, descriptive, note, and safety controls that heuristics cannot
  prove.
- Every checker finding, including documented false positives or controlling-
  directive exceptions.

## Completion status

- Report `STE PASS` only when the checker has no unresolved errors and the
  manual gate is complete.
- Report `STE PARTIAL` when safe edits are complete but a dictionary, glossary,
  source, or non-critical decision is unavailable.
- Report `STE BLOCKED` when an unresolved issue could change technical meaning,
  safety, legal effect, or a required instruction.

State the files and text types reviewed, checker commands and results, manual
checks completed, and each exception. Never convert `STE PARTIAL` or
`STE BLOCKED` into a complete Docs Sweep result.
