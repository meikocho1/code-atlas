---
name: visualize-data-flow
description: Trace how a specific input, event, or record moves through code, transforms, and storage, then draw a source-backed data-flow view. Use for provenance, processing, or handoff questions rather than a static component map.
---

# Visualize Data Flow

Answer “where does this data come from, what changes it, and where does it go?” for one named datum or workflow. Ask for the datum if no useful starting point can be inferred.

1. Establish the revision and starting boundary: user input, API request, event, file, database row, or job. Find the actual producer, transformation points, and sinks. Use a structural index for caller/callee paths when available, then inspect the exact source ranges that establish transformations and side effects. Search narrowly when there is no index. Verify any wiki map against current code.
2. Track **value and meaning**, not just function calls: field name, validation, normalization, mapping, persistence, emitted event, and consumer. Check whether a branch drops, rejects, retries, or duplicates data. Distinguish a declared schema from runtime transformations. Stop at an external boundary whose behavior is not visible.
3. Choose a flowchart for stages and branching, or a Sequence Diagram when ordering among actors is the hard part. Do not draw both unless they answer different requested questions. Label arrows with the data or event carried, and mark transforms on the nodes. Omit unrelated components; do not guess sensitive-data handling or retention.
4. Provide **BUSINESS** meaning, **SYSTEM** path, and **CODE** anchors in concise prose. State the input/output contract, important alternate path, and any unverified step. Cite paths and line numbers for nodes and edges. Include a one-sentence text alternative to the diagram.

For persisted entity relationships, use an ER view only when keys and cardinality are explicit in the schema. For static dependencies, use `visualize-architecture`.

When asked to retain the result, use the installed `code-atlas history add` command with the exact Markdown report and correct scope. Do not silently add files to the target repository.
