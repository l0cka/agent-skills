# Query patterns

## Basic patterns and joins

A triple pattern allows variables in subject, relation, or object position:

```text
?component depends_on ?dependency
```

Patterns sharing a variable form a natural join. Results are mappings from
variables to graph terms.

## Optional and negative conditions

Use optional patterns when a missing field should not remove the entity from
results. Use anti-joins only for a bounded absence question. Under open-world
semantics, failure to match is generally unknown rather than false.

```bash
kg.py query "?s type Strategy" --optional "?s killed_by ?decision"
kg.py query "?e type Experiment" --not "?e concluded_by ?outcome"
kg.py query "?s type Strategy" --filter "?s.props.status=killed,retired"
kg.py query "?x depends_on ?y" --count-by "?x"
```

## Navigation

Use `relation+` for transitive reachability and `path` when the shortest route
itself matters. Avoid enumerating every route in cyclic graphs.

```bash
kg.py query "?x depends_on+ component:database"
kg.py path component:web component:database --directed
```

Use search, context, and navigation as a sequence. Resolve the intended entity.
Inspect its sourced neighbourhood. Traverse the relation relevant to the
question.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapter 2, especially basic, complex, and navigational graph patterns
and query interfaces.
