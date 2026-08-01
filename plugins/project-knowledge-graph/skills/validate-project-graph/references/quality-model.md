# Quality assessment model

Assess quality against the graph's intended use.

## Accuracy

- **Syntactic:** files parse, IDs and datatypes conform, endpoints exist.
- **Semantic:** assertions match what their cited sources actually support.
- **Timeliness:** source hashes and observation freshness are current.

## Coverage

- **Schema completeness:** declared vocabulary supports the competency
  questions.
- **Property completeness:** required attributes are present for targeted
  entities.
- **Population completeness:** the represented sources and entities match the
  declared boundary.
- **Representativeness:** coverage is not skewed toward whichever source class
  was easiest to ingest.

Open-world semantics allow incomplete coverage. Report it. Do not turn absence
into a negative fact.

## Coherency

- **Consistency:** no contradictory functional values, incompatible types, or
  mutually exclusive identity claims.
- **Validity:** nodes and assertions conform to declared shapes, domains,
  ranges, and cardinalities.

Detecting inconsistency does not by itself identify which assertion is wrong.

## Succinctness and understandability

Remove out-of-scope material, identity splits, redundant relation vocabulary,
and unnecessary reification. Keep enough label, alias, and description context
for a future agent to distinguish similarly named entities.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapter 7. The chapter frames quality as fitness for purpose across
accuracy, coverage, coherency, succinctness, and related dimensions.
