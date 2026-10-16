# Synthetic examples

Task: create a demo lecture from examples/demo-source.md. Executor: the current AI assistant, platform as actually observed.
Input: local filesystem, exact resolved demo-source.md path; do not infer the computer hostname.
Output: exact generated lecture path, version and observed accessibility. If no file was written, state response-only.
A second event may record validation success. A later correction references the earlier event rather than replacing history.
A search for missing files reports the searched location, range and unavailable parts; it does not prove the task never happened.
