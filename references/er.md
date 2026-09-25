# ER view

Use when changed persistence structure is central to understanding the change. Inspect migrations or schema definitions for entities, primary and foreign keys, nullability, and cardinality. Show only entities and fields needed for the changed relationship.

Do not infer a one-to-many relation from a variable name or application code alone. If the schema does not establish cardinality, say what is known in prose instead of guessing in Mermaid. A column rename or small constraint change may need only a Before/After table.
