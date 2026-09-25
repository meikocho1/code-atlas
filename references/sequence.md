# Sequence view

Use when the change hinges on **ordering** among at least two real actors or components. Read the changed entry point and the relevant outbound calls, events, responses, and error handling. Give each participant a real name from code or configuration. Label arrows with actual calls or messages, and distinguish synchronous calls from asynchronous events when the source does.

Include an alternate or failure path only if it affects the outcome and the code supports it. Do not draw a sequence for a purely local helper or invent downstream behavior beyond an external boundary. Anchor the version of the flow to the analyzed diff.
