# ASD-STE100 Issue 9 implementation reference

Use this reference to apply the standard. It is a concise implementation aid,
not a replacement for the standard or its controlled dictionary.

## Source and permitted use

- Source: Aerospace, Security and Defence Industries Association of Europe
  (ASD), *ASD-STE100 Simplified Technical English: Standard for technical
  documentation*, Issue 9, 15 January 2025.
- Reviewed source file SHA-256:
  `40d66f0cea84d1fff67f36d560c04eab4034c6bcf64014d43bd6d4c19795f3f0`.
- Official information and distribution: <https://www.asd-ste100.org/> and
  <https://www.asd-stan.org/>.
- ASD owns the copyright and the registered trademark. Do not copy or bundle
  the supplied PDF or reproduce its controlled dictionary in this skill.

## Scope

STE controls technical content, grammar, vocabulary, and style. It does not set
document typography, numbering, units of measurement, or project-specific
abbreviation policy. Use it with the applicable publication specification,
style guide, terminology database, contract, and official directives. See the
General introduction, pages i-iii.

## Mandatory writing controls

### Vocabulary and terminology

- Use only dictionary-approved words, approved technical nouns, and approved
  technical verbs. Check the approved part of speech, meaning, and form for each
  dictionary word. See rules 1.1-1.4.
- Use technical nouns and verbs only in an applicable category and context. Use
  the project or company glossary when it exists. Do not turn a technical noun
  into a verb or a technical verb into a noun. See rules 1.5-1.13.
- Prefer technical nouns of no more than three words. If an approved term is
  longer, first write it in full and then introduce an unambiguous short form or
  use hyphens to show word groups. See rules 1.9 and 2.1-2.2.
- Do not use regional, slang, or jargon terms. Use one term for one item and keep
  wording consistent. See rules 1.10-1.11 and 9.4.
- Use American English spelling unless a controlling directive requires a
  different spelling. Preserve quoted text. See rule 1.14.

### Verbs and sentence structure

- Use only the permitted verb forms: infinitive, imperative, simple present,
  simple past, simple future, and past participle as an adjective. Do not build
  complex verb constructions. Restrict `-ing` forms to technical nouns or
  modifiers in technical nouns. See rules 3.1-3.5.
- Use active voice. Use passive voice in descriptive writing only when the agent
  is unknown. Express actions with verbs, not abstract nouns. See
  rules 3.6-3.7.
- Write complete, direct sentences. Do not omit subjects, verbs, nouns, or
  articles. Do not use contractions. See rules 4.1-4.2 and 4.5.
- Use a vertical list for complex sets or sequences. Introduce it with a colon,
  keep its grammar parallel, and do not mix procedures and descriptions in one
  list. See rules 4.3 and 8.4.

### Procedures, descriptions, and safety text

- Procedures: use no more than 20 words per sentence, one instruction per
  sentence, and the imperative form. Use multiple actions only when they occur
  at the same time. Put a necessary condition first. Separate it from the
  command with a comma. See rules 5.1-5.4.
- Notes: give information only, use no more than 25 words per sentence, and do
  not hide instructions, limits, results, or safety content in a note. See rule
  5.5.
- Descriptions: give information gradually. Keep one topic in each sentence and
  paragraph. Use no more than 25 words per sentence. Use no more than six
  sentences per paragraph. Do not use imperative verbs. See rules 6.1-6.6.
- Safety text: identify the risk level, start with a clear command or condition,
  and state the risk or possible result. A warning covers injury or death. A
  caution covers damage to objects. Use the domain's controlling risk taxonomy.
  See rules 7.1-7.3.

### Punctuation and count

- Do not use semicolons. Use two sentences instead. Use hyphens to connect words
  that operate as one unit. See rules 8.1-8.2.
- In a vertical list, a colon ends the introductory sentence for word-count
  purposes. Each list item is a new sentence. See rule 8.4.
- Parenthetical text counts as one word in its containing sentence and as a
  separate sentence itself. Numbers with units, abbreviations, alphanumeric
  identifiers, quoted text, specified titles or labels, and proper names count
  as one word. Hyphenated words count as one word. See rules 8.5-8.7.
- Rewrite the sentence when a direct word replacement changes meaning or
  grammar. Do not create unapproved phrasal verbs from approved words. See rules
  9.1-9.3.

## What the checker can prove

`scripts/check_ste.py` detects semicolons, common contractions, approximate
sentence and paragraph limits, likely passive voice, common non-American
spellings, likely multiple commands, and incomplete safety or note patterns.

The checker cannot prove dictionary approval, approved meaning, approved part of
speech, or technical-term category. It also cannot prove one topic per sentence,
the identity of an unknown agent, simultaneous actions, risk classification, or
preservation of technical meaning. Review these controls manually against Issue
9 and the project glossary before you report `STE PASS`.
